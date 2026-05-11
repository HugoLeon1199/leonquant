import argparse
import copy
import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_FINAL_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "content.json"
DEFAULT_MARKET_SNAPSHOT_FILE = PROJECT_DIR / "market_snapshot.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 LEONQuantLabs/1.0"
)

_LIST_MINS: dict[str, int] = {
    "global_macro_drivers": 3,
    "quick_actions": 4,
    "allocation_guide": 3,
    "sector_priority": 6,
    "increase_risk_signals": 4,
    "reduce_risk_signals": 4,
}


class MetadataExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.image_url = ""
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}

        if tag == "meta":
            prop = attr_map.get("property", "").lower()
            name = attr_map.get("name", "").lower()
            content = attr_map.get("content", "")
            if not content:
                return

            if prop in {"og:image", "og:image:url", "twitter:image"} and not self.image_url:
                self.image_url = content.strip()
            elif name in {"twitter:image", "twitter:image:src"} and not self.image_url:
                self.image_url = content.strip()
            elif (
                prop in {"og:description", "twitter:description"}
                or name
                in {
                    "description",
                    "twitter:description",
                }
            ) and not self.description:
                self.description = clean_text(content)
            return

        if tag == "link":
            rel = attr_map.get("rel", "").lower()
            href = attr_map.get("href", "")
            if rel == "image_src" and href and not self.image_url:
                self.image_url = href.strip()


def load_market_snapshot_json(path: Path | None = None) -> dict[str, Any]:
    """Đọc market_snapshot.json; không raise. Trả về skeleton nếu thiếu/lỗi."""
    p = path or DEFAULT_MARKET_SNAPSHOT_FILE
    if not p.exists():
        return {
            "generated_at": "",
            "assets": [],
            "coverage_note": "Chưa có market_snapshot.json — có thể bổ sung để neo số liệu.",
        }
    try:
        data = load_json(p)
        if not isinstance(data, dict):
            raise ValueError("not an object")
        data.setdefault("generated_at", "")
        data.setdefault("assets", [])
        if not isinstance(data.get("assets"), list):
            data["assets"] = []
        data.setdefault("coverage_note", "")
        return data
    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "generated_at": "",
            "assets": [],
            "coverage_note": "Không đọc được market_snapshot.json (JSON lỗi hoặc file hỏng).",
        }


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_metadata(url: str, timeout: int) -> dict[str, str]:
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(300_000)
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        extractor = MetadataExtractor()
        extractor.feed(html)
        return {
            "image_url": extractor.image_url,
            "description": extractor.description,
            "metadata_status": "ok",
        }
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
        return {
            "image_url": "",
            "description": "",
            "metadata_status": f"error: {error}",
        }


def _macro_world(summary: dict[str, Any]) -> str:
    s = str(summary.get("macro_world", "") or "").strip()
    if s:
        return s
    parts = [summary.get("macro_global"), summary.get("international_markets")]
    merged = "\n\n".join(str(p).strip() for p in parts if str(p or "").strip())
    if merged:
        return merged
    return str(summary.get("global_watch", "") or "").strip()


def _vietnam_macro(summary: dict[str, Any]) -> str:
    s = str(summary.get("vietnam_macro", "") or "").strip()
    if s:
        return s
    vi = str(summary.get("vietnam_implications", "") or "").strip()
    if vi:
        return vi
    return str(summary.get("vietnam_watch", "") or "").strip()


def build_all_article_cards(
    enriched_payload: dict[str, Any],
    fetch_images: bool,
    timeout: int,
) -> list[dict[str, Any]]:
    """Mọi bài trong enriched_news.json: minh bạch, có ảnh/ mô tả khi fetch được."""
    articles = list(enriched_payload.get("articles", []))

    def sort_key(a: dict[str, Any]) -> str:
        return str(a.get("published_at") or "")

    articles.sort(key=sort_key, reverse=True)
    cards: list[dict[str, Any]] = []

    for article in articles:
        url = str(article.get("url", ""))
        if not url:
            continue
        metadata = (
            fetch_metadata(url, timeout)
            if fetch_images
            else {"image_url": "", "description": "", "metadata_status": "skipped"}
        )
        summary_text = clean_text(str(article.get("summary") or metadata.get("description") or ""))
        cards.append(
            {
                "title": article.get("title", "Tin"),
                "url": url,
                "source": article.get("source", ""),
                "category": article.get("category", ""),
                "region": article.get("region", ""),
                "published_at": article.get("published_at", ""),
                "summary": summary_text,
                "image_url": metadata.get("image_url", ""),
                "metadata_status": metadata.get("metadata_status", ""),
            }
        )
    return cards


def _default_strategy_snake(*, brief_date: str, generated_at: str) -> dict[str, Any]:
    """Shell hợp lệ cho website khi thiếu dữ liệu — giữ tone nghiên cứu, không nhắc tooling."""
    return {
        "title": "LEON Quant Labs — Góc nhìn vĩ mô và chiến lược thị trường",
        "date": brief_date,
        "generated_at": generated_at,
        "publication_intro": {
            "headline": "Góc nhìn vĩ mô và chiến lược thị trường dành cho nhà đầu tư Việt Nam",
            "description": (
                "LEON Quant Labs tập trung vào việc chuyển biến động vĩ mô toàn cầu thành góc nhìn đầu tư "
                "có thể hành động tại thị trường Việt Nam."
            ),
        },
        "main_thesis": {
            "regime": "Thận trọng có chọn lọc",
            "thesis": (
                "Thị trường toàn cầu chịu ảnh hưởng từ lãi suất Mỹ, đồng USD, giá dầu và dòng vốn quốc tế. "
                "Với Việt Nam, cơ hội vẫn tồn tại nhưng phụ thuộc vào thanh khoản nội địa, nhóm dẫn dắt và hoạt động của khối ngoại."
            ),
            "action_conclusion": (
                "Không cần rút lui hoàn toàn, nhưng cũng không nên mua đuổi. Ưu tiên cổ phiếu khỏe, giữ tỷ trọng vừa phải, "
                "hạn chế margin và chờ xác nhận từ dòng tiền."
            ),
        },
        "global_macro_drivers": [
            {
                "title": "Lãi suất Mỹ còn cao",
                "analysis": (
                    "Khi Fed chưa vội hạ lãi suất, lợi suất trái phiếu Mỹ dễ duy trì ở vùng tương đối cao. "
                    "Chi phí vốn toàn cầu đắt hơn và tài sản rủi ro khó mở rộng định giá mạnh nếu không có tin tích cực rõ ràng."
                ),
                "vietnam_impact": (
                    "Kênh tâm lý risk-off và dòng vốn: nhà đầu tư mới nổi thường thận trọng hơn; cổ phiếu Việt Nam cần dựa nhiều vào dòng tiền nội."
                ),
            },
            {
                "title": "Đồng USD mạnh gây áp lực tỷ giá",
                "analysis": (
                    "USD mạnh thường kéo chi phí nhập khẩu hàng hóa USD và làm thắt tài chính cho các DN có nợ ngoại tệ."
                ),
                "vietnam_impact": "Áp lực lên USD/VND và kỳ vọng chính sách; khối ngoại có thể cân nhắc tốc độ phân bổ.",
            },
            {
                "title": "Giá dầu là rủi ro lạm phát",
                "analysis": (
                    "Dầu cao không chỉ tác động nhóm năng lượng mà lan sang vận tải, sản xuất và kỳ vọng lạm phát."
                ),
                "vietnam_impact": (
                    "Biên lợi nhuận DN sử dụng năng lượng và logistics chịu áp lực; tâm lý thị trường dễ nhạy với shock giá."
                ),
            },
        ],
        "vietnam_transmission": {
            "summary": (
                "Chuỗi tác động thường gặp: lãi suất Mỹ cao → USD mạnh → áp lực USD/VND → khối ngoại thận trọng hơn "
                "→ VN-Index cần dựa nhiều hơn vào dòng tiền nội và nhóm dẫn dắt."
            ),
            "chains": [
                "Lãi suất Mỹ cao → USD mạnh → áp lực USD/VND → khối ngoại thận trọng.",
                "Giá dầu biến động → lạm phát kỳ vọng → tâm lý risk-off → định giá tài sản rủi ro thắt lại.",
            ],
        },
        "quick_actions": [
            {"investor_state": "Cầm nhiều tiền mặt", "action": "Chưa cần mua vội; theo dõi thanh khoản và độ rộng."},
            {"investor_state": "Đang nắm cổ phiếu tốt", "action": "Có thể tiếp tục nắm; đặt điểm hạ tỷ trọng nếu thị trường suy yếu đồng loạt."},
            {"investor_state": "Đang lãi ngắn hạn", "action": "Chốt lời một phần để bảo toàn lợi thế; tránh mua thêm đuổi đỉnh."},
            {"investor_state": "Đang dùng margin cao", "action": "Hạ đòn bẩy về mức an toàn; ưu tiên sống sót qua nhịp biến động."},
            {"investor_state": "Muốn mua mới", "action": "Chỉ tích sườn nhỏ; chọn cổ phiếu khỏe có dòng tiền xác nhận."},
            {"investor_state": "Đang kẹt cổ phiếu yếu", "action": "Cơ cấu sang mã có cơ bản và thanh khoản tốt hơn."},
        ],
        "allocation_guide": [
            {"profile": "Thận trọng", "stocks": "30–40%", "cash": "60–70%", "margin": "Không dùng"},
            {"profile": "Cân bằng", "stocks": "50–60%", "cash": "40–50%", "margin": "Rất thấp khi thị trường xác nhận"},
            {"profile": "Chủ động", "stocks": "60–70%", "cash": "30–40%", "margin": "Chỉ khi sóng và thanh khoản rõ ràng"},
        ],
        "sector_priority": [
            {"sector": "Ngân hàng", "view": "Tích cực có chọn lọc", "action": "Ưu tiên mã nền tảng và room tín dụng lành mạnh."},
            {"sector": "Dầu khí", "view": "Tích cực ngắn hạn có điều kiện", "action": "Theo giá dầu; quản trị nhịp điều chỉnh."},
            {"sector": "Chứng khoán", "view": "Phụ thuộc thanh khoản", "action": "Chỉ mạnh khi dòng tiền cá nhân bền."},
            {"sector": "Khu công nghiệp", "view": "Trung tính tích cực", "action": "Chọn KCN có lấp đầy và khách ổn định."},
            {"sector": "Xuất khẩu", "view": "Trung tính", "action": "Lưu ý USD/VND và cầu bên ngoài."},
            {"sector": "Bất động sản", "view": "Thận trọng", "action": "Chỉ xem dự án có dòng tiền và pháp lý rõ."},
            {"sector": "Thép", "view": "Trung tính thận trọng", "action": "Bám giá nguyên liệu và biên."},
            {"sector": "Bán lẻ", "view": "Chọn lọc", "action": "Ưu tiên chuỗi có động lực same-store."},
        ],
        "increase_risk_signals": [
            {"signal": "VN-Index tăng cùng thanh khoản cải thiện", "meaning": "Dòng tiền xác nhận nhịp tăng có thể lan rộng."},
            {"signal": "Số mã tăng lan rộng", "meaning": "Độ rộng tốt giảm rủi ro chỉ số ‘giả vờ’."},
            {"signal": "Ngân hàng giữ vai trò dẫn dắt", "meaning": "Nhóm nền ổn định thường củng cố xu hướng."},
            {"signal": "Khối ngoại giảm bán hoặc mua ròng", "meaning": "Áp lực bán có thể hạ nhiệt."},
            {"signal": "USD/VND ổn định", "meaning": "Giảm rủi ro tâm lý tỷ giá."},
            {"signal": "Cổ phiếu vượt nền với volume tốt", "meaning": "Xác nhận kỹ thuật có hỗ trợ dòng tiền."},
        ],
        "reduce_risk_signals": [
            {"signal": "VN-Index tăng nhưng độ rộng yếu", "action": "Tránh mua đuổi đỉnh hẹp."},
            {"signal": "Thanh khoản giảm trong nhịp tăng", "action": "Thận trọng; dễ đảo chiều nhanh."},
            {"signal": "Khối ngoại bán ròng mạnh", "action": "Ưu tiên giữ tiền mặt bảo vệ vốn."},
            {"signal": "USD/VND tăng nhanh", "action": "Xem xét giảm tỷ trọng nhóm nhạy FX và margin."},
            {"signal": "Ngân hàng suy yếu đồng loạt", "action": "Tín hiệu stress hệ thống; giảm rủi ro."},
            {"signal": "Cổ phiếu đầu cơ tăng nóng", "action": "Rủi ro bull trap; không chasing nhóm mỏng thanh khoản."},
        ],
        "scenario_plan": {
            "base_case": {
                "title": "Kịch bản cơ sở",
                "description": "Thị trường phân hóa; vĩ mô vẫn có điểm nghẽn nhưng chưa vỡ trận.",
                "action": "Giữ tỷ trọng vừa phải; ưu tiên cổ phiếu chất lượng và quản trị margin.",
            },
            "bull_case": {
                "title": "Kịch bản tích cực",
                "description": "USD hạ nhiệt, thanh khoản cải thiện, rủi ro hệ thống không leo thang.",
                "action": "Tăng tỷ trọng từng phần theo nhịp xác nhận; giữ cash để còn quyền chủ động.",
            },
            "bear_case": {
                "title": "Kịch bản tiêu cực",
                "description": "USD mạnh, khối ngoại bán ròng, VN-Index mất các ngưỡng hỗ trợ quan trọng.",
                "action": "Giảm cổ phiếu, hạ margin; ưu tiên an toàn vốn.",
            },
        },
        "final_takeaway": (
            "Bối cảnh hiện tại không ủng hộ chiến lược all-in, nhưng cũng chưa yêu cầu phải rút lui hoàn toàn. "
            "Vĩ mô thế giới vẫn còn áp lực từ lãi suất Mỹ, đồng USD và giá dầu. Thị trường Việt Nam vẫn có cơ hội nếu dòng tiền nội "
            "duy trì và nhóm ngân hàng giữ vai trò dẫn dắt. Chiến lược hợp lý là giữ danh mục gọn, nắm cổ phiếu khỏe, tránh mua đuổi, "
            "hạn chế margin và giữ tiền mặt để có quyền chủ động."
        ),
    }


def _is_investment_strategy_brief(summary: dict[str, Any]) -> bool:
    mt = summary.get("main_thesis")
    pi = summary.get("publication_intro")
    return isinstance(mt, dict) and isinstance(pi, dict) and (
        bool(str(mt.get("thesis", "")).strip()) or bool(str(mt.get("regime", "")).strip())
    )


def _is_legacy_macro_block(summary: dict[str, Any]) -> bool:
    if isinstance(summary.get("market_regime"), dict):
        return True
    if str(summary.get("daily_thesis", "") or "").strip():
        return True
    if isinstance(summary.get("top_macro_drivers"), list) and summary["top_macro_drivers"]:
        return True
    if isinstance(summary.get("vietnam_investor_lens"), dict) and summary["vietnam_investor_lens"]:
        return True
    if isinstance(summary.get("scenario_map"), dict) and all(
        k in summary["scenario_map"] for k in ("base_case", "bull_case", "bear_case")
    ):
        return True
    return False


def _legacy_to_strategy_snake(summary: dict[str, Any], *, brief_date: str, generated_at: str) -> dict[str, Any]:
    mr = summary.get("market_regime") if isinstance(summary.get("market_regime"), dict) else {}
    thesis_body = (
        str(summary.get("daily_thesis", "") or "").strip()
        or str(summary.get("thirty_second_summary", "") or "").strip()
        or _macro_world(summary)
        or _vietnam_macro(summary)
    )
    takeaway = str(summary.get("final_takeaway", "") or "").strip()
    action_line = takeaway
    if len(action_line) > 520:
        action_line = action_line[:520] + "…"

    drivers_out: list[dict[str, str]] = []
    for d in summary.get("top_macro_drivers") or []:
        if not isinstance(d, dict):
            continue
        fact = str(d.get("fact", "") or "").strip()
        wim = str(d.get("why_it_matters", "") or "").strip()
        analysis = fact if not wim else (fact + "\n\n" + wim if fact else wim)
        chain = d.get("transmission_chain")
        vn_imp = " → ".join(str(x) for x in chain) if isinstance(chain, list) and chain else ""
        drivers_out.append(
            {
                "title": str(d.get("headline", "") or "").strip() or "Nhịp vĩ mô",
                "analysis": analysis or "—",
                "vietnam_impact": vn_imp or "Cần theo dõi kênh USD/VND, khối ngoại và thanh khoản nội.",
            }
        )

    vil = summary.get("vietnam_investor_lens") if isinstance(summary.get("vietnam_investor_lens"), dict) else {}
    vsum = str(vil.get("summary", "") or "").strip()
    chains: list[str] = []
    for d in summary.get("top_macro_drivers") or []:
        if isinstance(d, dict) and isinstance(d.get("transmission_chain"), list):
            ch = d["transmission_chain"]
            if ch:
                chains.append(" → ".join(str(x) for x in ch))
    for c in vil.get("channels") or []:
        if isinstance(c, dict):
            lab = str(c.get("channel", "") or "").strip()
            ana = str(c.get("analysis", "") or "").strip()
            if lab and ana:
                chains.append(f"{lab}: {ana}")

    sm = summary.get("scenario_map") if isinstance(summary.get("scenario_map"), dict) else {}

    def _scen(case: str, title_vi: str) -> dict[str, str]:
        sub = sm.get(case) if isinstance(sm.get(case), dict) else {}
        desc = str(sub.get("description", "") or "").strip()
        sig = sub.get("signals_to_watch")
        watch = ", ".join(str(s) for s in sig) if isinstance(sig, list) and sig else ""
        action = f"Theo dõi: {watch}" if watch else "Giữ kỷ luật vốn; ưu tiên cổ phiếu chất lượng."
        return {"title": title_vi, "description": desc or "—", "action": action}

    return {
        "title": str(summary.get("title", "") or "").strip()
        or "LEON Quant Labs — Góc nhìn vĩ mô và chiến lược thị trường",
        "date": str(summary.get("date", "") or "").strip() or brief_date,
        "generated_at": str(summary.get("generated_at", "") or "").strip() or generated_at,
        "publication_intro": {
            "headline": "Góc nhìn vĩ mô và chiến lược thị trường dành cho nhà đầu tư Việt Nam",
            "description": (
                "LEON Quant Labs tập trung vào việc chuyển biến động vĩ mô toàn cầu thành góc nhìn đầu tư "
                "có thể hành động tại thị trường Việt Nam."
            ),
        },
        "main_thesis": {
            "regime": str(mr.get("regime", "") or "").strip() or "Thận trọng có chọn lọc",
            "thesis": thesis_body or (
                "Thị trường toàn cầu chịu ảnh hưởng từ lãi suất Mỹ, đồng USD và giá dầu. "
                "Việt Nam phụ thuộc thanh khoản nội địa và nhóm dẫn dắt."
            ),
            "action_conclusion": action_line
            or (
                "Không cần rút lui hoàn toàn, nhưng cũng không nên mua đuổi. Giữ tỷ trọng vừa phải, hạn chế margin."
            ),
        },
        "global_macro_drivers": drivers_out,
        "vietnam_transmission": {
            "summary": vsum
            or (
                "Luồng tâm lý và tỷ giá từ USD/lãi suất toàn cầu thường truyền vào thanh khoản và khối ngoại của TTCK Việt Nam."
            ),
            "chains": chains or [],
        },
        "quick_actions": [],
        "allocation_guide": [],
        "sector_priority": [],
        "increase_risk_signals": [],
        "reduce_risk_signals": [],
        "scenario_plan": {
            "base_case": _scen("base_case", "Kịch bản cơ sở"),
            "bull_case": _scen("bull_case", "Kịch bản tích cực"),
            "bear_case": _scen("bear_case", "Kịch bản tiêu cực"),
        },
        "final_takeaway": takeaway
        or (
            "Ưu tiên danh mục gọn, xác nhận dòng tiền và tránh đuổi theo các nhịp không bền vững."
        ),
    }


def coerce_summary_to_strategy_brief(
    summary: Any,
    *,
    brief_date: str,
    generated_at: str,
) -> dict[str, Any]:
    if not isinstance(summary, dict):
        summary = {}
    base = _default_strategy_snake(brief_date=brief_date, generated_at=generated_at)

    if _is_legacy_macro_block(summary) and not _is_investment_strategy_brief(summary):
        summary = _legacy_to_strategy_snake(summary, brief_date=brief_date, generated_at=generated_at)
    elif not _is_investment_strategy_brief(summary):
        return base

    out = copy.deepcopy(base)
    if str(summary.get("title", "")).strip():
        out["title"] = str(summary["title"]).strip()
    if str(summary.get("date", "")).strip():
        out["date"] = str(summary["date"]).strip()
    if str(summary.get("generated_at", "")).strip():
        out["generated_at"] = str(summary["generated_at"]).strip()

    pub = summary.get("publication_intro")
    if isinstance(pub, dict):
        if str(pub.get("headline", "")).strip():
            out["publication_intro"]["headline"] = str(pub["headline"]).strip()
        if str(pub.get("description", "")).strip():
            out["publication_intro"]["description"] = str(pub["description"]).strip()

    mt = summary.get("main_thesis")
    if isinstance(mt, dict):
        for k in ("regime", "thesis", "action_conclusion"):
            if str(mt.get(k, "")).strip():
                out["main_thesis"][k] = str(mt[k]).strip()

    vt = summary.get("vietnam_transmission")
    if isinstance(vt, dict):
        if str(vt.get("summary", "")).strip():
            out["vietnam_transmission"]["summary"] = str(vt["summary"]).strip()
        ch = vt.get("chains")
        if (
            isinstance(ch, list)
            and len(ch) > 0
            and all(isinstance(x, str) and x.strip() for x in ch)
        ):
            out["vietnam_transmission"]["chains"] = ch

    sp = summary.get("scenario_plan")
    if isinstance(sp, dict):
        for case in ("base_case", "bull_case", "bear_case"):
            blk = sp.get(case)
            if not isinstance(blk, dict):
                continue
            for f in ("title", "description", "action"):
                if str(blk.get(f, "")).strip():
                    out["scenario_plan"][case][f] = str(blk[f]).strip()

    if str(summary.get("final_takeaway", "")).strip():
        out["final_takeaway"] = str(summary["final_takeaway"]).strip()

    for key, fields in (
        ("global_macro_drivers", ("title", "analysis", "vietnam_impact")),
        ("quick_actions", ("investor_state", "action")),
        ("allocation_guide", ("profile", "stocks", "cash", "margin")),
        ("sector_priority", ("sector", "view", "action")),
        ("increase_risk_signals", ("signal", "meaning")),
        ("reduce_risk_signals", ("signal", "action")),
    ):
        min_n = _LIST_MINS[key]
        inc = summary.get(key)
        if isinstance(inc, list):
            rows = [
                r
                for r in inc
                if isinstance(r, dict) and all(str(r.get(f, "") or "").strip() for f in fields)
            ]
            if len(rows) >= min_n:
                out[key] = rows

    return out


def _camel_case_scenario_plan(sp: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    mapping = (("base_case", "baseCase"), ("bull_case", "bullCase"), ("bear_case", "bearCase"))
    for snake, camel in mapping:
        blk = sp.get(snake, {})
        if not isinstance(blk, dict):
            blk = {}
        result[camel] = {
            "title": blk.get("title", ""),
            "description": blk.get("description", ""),
            "action": blk.get("action", ""),
        }
    return result


def strategy_brief_to_public_json(snake: dict[str, Any]) -> dict[str, Any]:
    """Chuyển summary snake_case (final_summary) sang camelCase cho landing page."""
    pub = snake.get("publication_intro", {})
    mt = snake.get("main_thesis", {})
    vt = snake.get("vietnam_transmission", {})
    sp = snake.get("scenario_plan", {})
    return {
        "publicationIntro": {
            "headline": pub.get("headline", "") if isinstance(pub, dict) else "",
            "description": pub.get("description", "") if isinstance(pub, dict) else "",
        },
        "mainThesis": {
            "regime": mt.get("regime", "") if isinstance(mt, dict) else "",
            "thesis": mt.get("thesis", "") if isinstance(mt, dict) else "",
            "actionConclusion": mt.get("action_conclusion", "") if isinstance(mt, dict) else "",
        },
        "globalMacroDrivers": [
            {
                "title": r.get("title", ""),
                "analysis": r.get("analysis", ""),
                "vietnamImpact": r.get("vietnam_impact", ""),
            }
            for r in snake.get("global_macro_drivers", [])
            if isinstance(r, dict)
        ],
        "vietnamTransmission": {
            "summary": vt.get("summary", "") if isinstance(vt, dict) else "",
            "chains": vt.get("chains", []) if isinstance(vt, dict) and isinstance(vt.get("chains"), list) else [],
        },
        "quickActions": [
            {"investorState": r.get("investor_state", ""), "action": r.get("action", "")}
            for r in snake.get("quick_actions", [])
            if isinstance(r, dict)
        ],
        "allocationGuide": [
            {
                "profile": r.get("profile", ""),
                "stocks": r.get("stocks", ""),
                "cash": r.get("cash", ""),
                "margin": r.get("margin", ""),
            }
            for r in snake.get("allocation_guide", [])
            if isinstance(r, dict)
        ],
        "sectorPriority": [
            {"sector": r.get("sector", ""), "view": r.get("view", ""), "action": r.get("action", "")}
            for r in snake.get("sector_priority", [])
            if isinstance(r, dict)
        ],
        "increaseRiskSignals": [
            {"signal": r.get("signal", ""), "meaning": r.get("meaning", "")}
            for r in snake.get("increase_risk_signals", [])
            if isinstance(r, dict)
        ],
        "reduceRiskSignals": [
            {"signal": r.get("signal", ""), "action": r.get("action", "")}
            for r in snake.get("reduce_risk_signals", [])
            if isinstance(r, dict)
        ],
        "scenarioPlan": _camel_case_scenario_plan(sp if isinstance(sp, dict) else {}),
        "finalTakeaway": str(snake.get("final_takeaway", "") or ""),
    }


def build_payload(
    final_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    all_articles: list[dict[str, Any]],
    *,
    market_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_summary = final_payload.get("summary", {})
    if not isinstance(raw_summary, dict):
        raw_summary = {}
    generated_at = (
        str(raw_summary.get("generated_at", "")).strip()
        or str(final_payload.get("generated_at", "")).strip()
        or datetime.now(timezone.utc).isoformat()
    )
    brief_date = str(raw_summary.get("date", "")).strip()
    if not brief_date and isinstance(final_payload.get("generated_at"), str):
        brief_date = final_payload["generated_at"][:10]

    snake = coerce_summary_to_strategy_brief(
        raw_summary,
        brief_date=brief_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        generated_at=generated_at,
    )
    brief = strategy_brief_to_public_json(snake)
    ms_payload = market_snapshot if market_snapshot is not None else load_market_snapshot_json()

    meta = final_payload.get("meta") if isinstance(final_payload.get("meta"), dict) else {}

    return {
        "siteTitle": "LEON Quant Labs",
        "sectionLabel": "Góc nhìn vĩ mô và chiến lược thị trường",
        "generatedAt": generated_at,
        "schemaVersion": "investment-strategy-brief-v1",
        "publicationIntro": brief["publicationIntro"],
        "mainThesis": brief["mainThesis"],
        "globalMacroDrivers": brief["globalMacroDrivers"],
        "vietnamTransmission": brief["vietnamTransmission"],
        "quickActions": brief["quickActions"],
        "allocationGuide": brief["allocationGuide"],
        "sectorPriority": brief["sectorPriority"],
        "increaseRiskSignals": brief["increaseRiskSignals"],
        "reduceRiskSignals": brief["reduceRiskSignals"],
        "scenarioPlan": brief["scenarioPlan"],
        "finalTakeaway": brief["finalTakeaway"],
        "allArticles": all_articles,
        "stats": {
            "articlesCrawled": len(all_articles),
            "articlesInEnriched": enriched_payload.get("count", len(enriched_payload.get("articles", []))),
        },
        "editorialMeta": {
            "briefDate": snake.get("date", ""),
            "briefTitle": snake.get("title", ""),
            "sourcesScanned": meta.get("sources_scanned"),
            "articlesSelected": meta.get("articles_selected"),
            "verifiedLinks": meta.get("verified_links"),
            "usedFallback": meta.get("used_fallback"),
        },
        "marketSnapshot": ms_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build content.json: brief chiến lược + toàn bộ bài enriched.",
    )
    parser.add_argument("--final-input", default=str(DEFAULT_FINAL_FILE), help="Path to final_summary.json")
    parser.add_argument("--enriched-input", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched_news.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to content.json")
    parser.add_argument(
        "--metadata-timeout",
        type=int,
        default=10,
        help="Seconds per URL when fetching og:image/description",
    )
    parser.add_argument("--skip-images", action="store_true", help="Do not fetch og metadata (faster)")
    args = parser.parse_args()

    final_payload = load_json(Path(args.final_input))
    enriched_payload = load_json(Path(args.enriched_input))
    all_cards = build_all_article_cards(
        enriched_payload,
        not args.skip_images,
        args.metadata_timeout,
    )
    payload = build_payload(
        final_payload,
        enriched_payload,
        all_cards,
        market_snapshot=load_market_snapshot_json(),
    )
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(all_cards)} article cards -> {args.output}")
    return 0


def rebuild_content_json(
    final_payload_path: Path,
    enriched_path: Path,
    output_path: Path,
    *,
    fetch_images: bool = True,
    metadata_timeout: int = 6,
    market_snapshot_path: Path | None = None,
) -> int:
    """Dựng payload website từ final_summary.json + enriched_news.json."""
    final_payload = load_json(final_payload_path)
    enriched_payload = load_json(enriched_path)
    all_cards = build_all_article_cards(
        enriched_payload,
        fetch_images,
        metadata_timeout,
    )
    ms = load_market_snapshot_json(market_snapshot_path)
    payload = build_payload(final_payload, enriched_payload, all_cards, market_snapshot=ms)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(all_cards)


if __name__ == "__main__":
    raise SystemExit(main())
