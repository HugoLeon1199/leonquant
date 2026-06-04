import argparse
import copy
import json
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DIGEST_FILE = PROJECT_DIR / "gemini_digest_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "news_for_ai_clean.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "content.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 LEONQuantLabs/1.0"
)
FETCH_HTML_MAX_BYTES = 450_000
IMG_TAG_RE = re.compile(
    r'(?is)<img\b[^>]*?\b(?:src|data-src|data-original|data-lazy-src)\s*=\s*'
    r'["\']([^"\'>\s]+)["\']',
)
PLAIN_HTTP_IMAGE_RE = re.compile(
    r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^\s"\'<>]*)?',
    re.IGNORECASE,
)
SKIP_IMAGE_SUBSTR = (
    "pixel",
    "tracking",
    "1x1",
    "spacer",
    "blank.gif",
    "transparent",
    "analytics",
    "emoji",
    "favicon",
    "/icon",
    "logo-small",
)


def normalize_media_url(page_url: str, raw: str) -> str:
    u = (raw or "").strip()
    if not u or u.startswith("data:"):
        return ""
    u = u.replace("&amp;", "&")
    if u.startswith("//"):
        u = "https:" + u
    elif not urlparse(u).netloc:
        u = urljoin(page_url, u)
    low = u.lower()
    if any(s in low for s in SKIP_IMAGE_SUBSTR):
        return ""
    return u


def _json_ld_image_urls(html: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html):
        blob = m.group(1)
        if '"image"' not in blob and "'image'" not in blob:
            continue
        for um in re.finditer(
            r'(?i)"image"\s*:\s*"(https?:[^"]+)"',
            blob,
        ):
            out.append(um.group(1))
        for um in re.finditer(
            r'(?i)"image"\s*:\s*\[\s*"(https?:[^"]+)"',
            blob,
        ):
            out.append(um.group(1))
    return out


def extract_image_from_html(html: str, page_url: str) -> str:
    """Khi og:image thiếu: thử JSON-LD, rồi thẻ <img> (lazy-load)."""
    for cand in _json_ld_image_urls(html):
        nu = normalize_media_url(page_url, cand)
        if nu:
            return nu
    for m in IMG_TAG_RE.finditer(html[:400_000]):
        nu = normalize_media_url(page_url, m.group(1))
        if nu:
            return nu
    return ""


def extract_image_from_plaintext(text: str) -> str:
    """Một số bài có URL ảnh lẫn trong text thuần (không HTML)."""
    for m in PLAIN_HTTP_IMAGE_RE.finditer(text[:50_000]):
        u = m.group(0)
        low = u.lower()
        if any(s in low for s in SKIP_IMAGE_SUBSTR):
            continue
        return u
    return ""

_LIST_MINS: dict[str, int] = {
    "global_macro_drivers": 3,
    "what_changed": 4,
    "quick_actions": 6,
    "allocation_guide": 4,
    "increase_risk_signals": 5,
    "reduce_risk_signals": 5,
    "intermarket_map": 6,
    "transmission_chains": 3,
    "intraday_playbook": 5,
    "market_regime_axes": 5,
}


def regime_label_for_total_score(total: int) -> str:
    """Nhãn regime khớp rubric chiến lược (tổng điểm trục -1/0/+1)."""
    if total >= 3:
        return "Risk-on"
    if total >= 1:
        return "Tích cực có chọn lọc"
    if total == 0:
        return "Trung tính"
    if total >= -2:
        return "Thận trọng có chọn lọc"
    return "Phòng thủ"


def _normalize_market_regime_score(mrs: dict[str, Any]) -> None:
    """Cộng lại total_score, kẹp điểm trục {-1,0,1}, gán regime đúng rubric."""
    items_raw = mrs.get("items")
    if not isinstance(items_raw, list):
        return
    norm_items: list[dict[str, Any]] = []
    for it in items_raw:
        if not isinstance(it, dict):
            continue
        ax = str(it.get("axis", "") or "").strip()
        sig = str(it.get("signal", "") or "").strip()
        if not ax or not sig:
            continue
        try:
            sc = int(it.get("score", 0) or 0)
        except (TypeError, ValueError):
            sc = 0
        sc = max(-1, min(1, sc))
        norm_items.append({"axis": ax, "signal": sig, "score": sc})
    if len(norm_items) < _LIST_MINS["market_regime_axes"]:
        d = _default_market_regime_score()
        mrs.clear()
        mrs.update(d)
        return
    if len(norm_items) > 6:
        norm_items = norm_items[:6]
    total = sum(int(x["score"]) for x in norm_items)
    mrs["items"] = norm_items
    mrs["total_score"] = total
    mrs["regime"] = regime_label_for_total_score(total)

SAFE_ALLOCATION_GUIDE_V2: list[dict[str, str]] = [
    {
        "profile": "Thận trọng",
        "stocks": "30–40%",
        "cash": "45–55%",
        "gold_defense": "10–15%",
        "crypto_high_risk": "0–5%",
        "leverage": "Không dùng",
    },
    {
        "profile": "Cân bằng",
        "stocks": "50–60%",
        "cash": "30–40%",
        "gold_defense": "5–10%",
        "crypto_high_risk": "0–5%",
        "leverage": "Rất thấp",
    },
    {
        "profile": "Chủ động",
        "stocks": "60–70%",
        "cash": "20–30%",
        "gold_defense": "5–10%",
        "crypto_high_risk": "5–10%",
        "leverage": "Chỉ dùng khi xác nhận",
    },
    {
        "profile": "Rủi ro cao",
        "stocks": "70–80%",
        "cash": "10–20%",
        "gold_defense": "0–10%",
        "crypto_high_risk": "5–15%",
        "leverage": "Có kỷ luật chặt",
    },
]

# Back-compat alias
SAFE_ALLOCATION_GUIDE = SAFE_ALLOCATION_GUIDE_V2

SAFE_ACTION_CONCLUSION = (
    "Không cần rút lui hoàn toàn, nhưng cũng không nên mua đuổi. Chiến lược phù hợp là giữ tỷ trọng vừa phải, "
    "ưu tiên cổ phiếu khỏe, hạn chế margin và chờ xác nhận từ dòng tiền."
)

SAFE_INCREASE_RISK_SIGNALS: list[dict[str, str]] = [
    {"signal": "VN-Index tăng cùng thanh khoản cải thiện", "meaning": "Dòng tiền thật quay lại."},
    {"signal": "Số mã tăng lan rộng", "meaning": "Độ rộng thị trường khỏe hơn."},
    {"signal": "Ngân hàng giữ vai trò dẫn dắt", "meaning": "Chỉ số có trụ đỡ tốt hơn."},
    {"signal": "Khối ngoại giảm bán hoặc mua ròng", "meaning": "Áp lực vốn ngoại hạ nhiệt."},
    {"signal": "USD/VND ổn định", "meaning": "Rủi ro tỷ giá giảm."},
    {"signal": "Cổ phiếu vượt nền với volume tốt", "meaning": "Có điểm mua rõ hơn."},
]

SAFE_REDUCE_RISK_SIGNALS: list[dict[str, str]] = [
    {"signal": "VN-Index tăng nhưng độ rộng yếu", "action": "Không mua đuổi."},
    {"signal": "Thanh khoản giảm trong nhịp tăng", "action": "Giữ tiền mặt cao hơn."},
    {"signal": "Khối ngoại bán ròng mạnh", "action": "Giảm nhóm nhạy cảm với dòng vốn."},
    {"signal": "USD/VND tăng nhanh", "action": "Hạn chế margin."},
    {"signal": "Ngân hàng suy yếu đồng loạt", "action": "Hạ tỷ trọng cổ phiếu."},
    {"signal": "Cổ phiếu đầu cơ tăng nóng", "action": "Chốt lời từng phần, không đuổi giá."},
]

STABLE_VN_SECTOR_NAMES = (
    "Ngân hàng",
    "Dầu khí",
    "Chứng khoán",
    "Khu công nghiệp",
    "Xuất khẩu",
    "Bất động sản",
    "Thép",
    "Bán lẻ",
)

PUBLIC_JARGON_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bAI\b", ""),
    (r"\bGPT\b", ""),
    (r"\bGemini\b", ""),
    (r"(?i)\bartificial intelligence\b", ""),
    (r"(?i)\bautomation\b", ""),
    (r"(?i)\bcrawler\b", ""),
    (r"(?i)\bcrawl\b", ""),
    (r"(?i)\bpipeline\b", ""),
    (r"(?i)\bmodel\b", ""),
    (r"(?i)\bsource quality\b", ""),
    (r"(?i)\bverified links\b", ""),
    (r"(?i)\bkhông phải khuyến nghị đầu tư\b", ""),
    (r"(?i)\bdisclaimer\b", ""),
)

_GLOBAL_MACRO_KEYWORDS_RE = re.compile(
    r"fed|mỹ|my\b|usd|dxy|lợi suất|loi suat|dầu|dau|lạm phát|lam phat|trung quốc|trung quoc|"
    r"thương mại|thuong mai|địa chính trị|dia chinh tri|toàn cầu|toan cau|euro|ecb|opec|brent|wto|imf|"
    r"thế giới|the gioi|global|china|oil|inflation|rate|yield|geopolit|trade war",
    re.IGNORECASE,
)

# Tin nội địa thuần (hạ tầng địa phương, một NH, dự án đô thị) — không làm "global macro driver".
_LOCAL_ONLY_DOMESTIC_RE = re.compile(
    r"(?i)\b("
    r"cao tốc|long thành|sân bay long|tái cấu trúc ngân hàng|vietcombank|\bacb\b|\bbidv\b|\bssi\b|"
    r"vingroup|hoà phát|hòa phát|dự án bot|đường sắt đô thị|tp\.?hcm|hà nội|ha noi|"
    r"khởi động.*?dự án|tổng vốn.*?(tỷ|ty)\s*usd|cục dự trữ"
    r")\b",
)

# Risk-on item mistakenly listed under increase_risk_signals
_INCREASE_BAD_SIGNAL_RE = re.compile(
    r"(giá )?dầu.*tăng mạnh|giá vàng.*tăng mạnh|leo thang|xấu đi|bán ròng mạnh|"
    r"lạm phát.*cao hơn|lam phat.*cao hon|dự kiến.*lạm phát|du kien.*lam phat|"
    r"dữ liệu lạm phát|du lieu lam phat|"
    r"gián đoạn.*chuỗi|gian doan.*chuo|gián đoạn.*cung|tắc nghẽn.*cung|chuỗi cung ứng.*(gián|tắc|rủi ro)|"
    r"USD/VND tăng nhanh|thủng hỗ trợ|suy yếu đồng loạt|suy yeu dong loat|"
    r"rủi ro hệ thống|căng thẳng địa chính trị",
    re.IGNORECASE,
)
_INCREASE_BAD_EXCEPTION_RE = re.compile(
    r"giảm bán|giam ban|ổn định|on dinh|hạ nhiệt|ha nhiet|cải thiện|co phieu khỏe",
    re.IGNORECASE,
)

# Positive confirmation wrongly under reduce_risk_signals,
# or public investment / capex that confirms risk-on — move to increase list.
_REDUCE_GOOD_SIGNAL_RE = re.compile(
    r"tăng trưởng.*ổn định|tang truong.*on dinh|lạm phát thấp hơn|lam phat thap hon|"
    r"ngân hàng cải thiện|ngan hang cai thien|khối ngoại mua ròng|khoi ngoai mua rong|"
    r"USD/VND ổn định|thanh khoản cải thiện|thanh khoan cai thien|"
    r"đầu tư công tăng|dau tu cong tang|đầu tư công.*tốc|tăng tốc đầu tư công",
    re.IGNORECASE,
)

_SCENARIO_ACTION_PORTFOLIO_RE = re.compile(
    r"(tăng cường\s+)?nắm giữ.*(vàng|dầu|tài sản trú ẩn)|mua\s+(vàng|dầu)|"
    r"tăng cường đầu tư vào\s+(cổ phiếu|hạ tầng)",
    re.IGNORECASE,
)

_DIRECT_ASSET_PITCH_RE = re.compile(
    r"(tăng cường\s+)?nắm giữ.*(vàng|dầu thô|vàng và dầu)|"
    r"mua\s+(vàng|dầu)|khuyến nghị.*(vàng|dầu)|"
    r"ưu tiên.*(vàng|dầu)(?!\s+cao)",
    re.IGNORECASE,
)

DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET: list[dict[str, str]] = [
    {
        "title": "Lãi suất Mỹ còn cao",
        "analysis": (
            "Khi Fed chưa vội hạ lãi suất, lợi suất trái phiếu Mỹ dễ duy trì ở vùng tương đối cao. "
            "Chi phí vốn toàn cầu đắt hơn và tài sản rủi ro khó mở rộng định giá mạnh nếu không có tin tích cực rõ ràng."
        ),
        "market_impact": (
            "Định giá tài sản rủi ro toàn cầu thắt lại; thanh khoản dồn về tài sản an toàn và USD; "
            "thị trường mới nổi chịu áp lực kỳ vọng lợi suất."
        ),
    },
    {
        "title": "Đồng USD mạnh gây áp lực tỷ giá",
        "analysis": (
            "USD mạnh thường kéo chi phí nhập khẩu hàng hóa USD và làm thắt tài chính cho các DN có nợ ngoại tệ."
        ),
        "market_impact": "Hàng hóa USD, trái phiếu EM và tài sản nhạy FX chịu áp lực; vàng và tiền tệ đối trọng biến động theo thận trọng Fed.",
    },
    {
        "title": "Giá dầu là rủi ro lạm phát",
        "analysis": (
            "Dầu cao không chỉ tác động nhóm năng lượng mà lan sang vận tải, sản xuất và kỳ vọng lạm phát."
        ),
        "market_impact": (
            "Nhóm năng lượng và chuỗi chi phí đầu vào chịu áp lực; kỳ vọng lạm phát đẩy lợi suất thực và tâm lý risk-off."
        ),
    },
]

DEFAULT_SECTOR_PRIORITY_SNIPPET: list[dict[str, str]] = [
    {"sector": "Ngân hàng", "view": "Tích cực có chọn lọc", "action": "Ưu tiên mã nền tảng và room tín dụng lành mạnh."},
    {"sector": "Dầu khí", "view": "Tích cực ngắn hạn có điều kiện", "action": "Theo giá dầu; quản trị nhịp điều chỉnh."},
    {"sector": "Chứng khoán", "view": "Phụ thuộc thanh khoản", "action": "Chỉ mạnh khi dòng tiền cá nhân bền."},
    {"sector": "Khu công nghiệp", "view": "Trung tính tích cực", "action": "Chọn KCN có lấp đầy và khách ổn định."},
    {"sector": "Xuất khẩu", "view": "Trung tính", "action": "Lưu ý USD/VND và cầu bên ngoài."},
    {"sector": "Bất động sản", "view": "Thận trọng", "action": "Chỉ xem dự án có dòng tiền và pháp lý rõ."},
    {"sector": "Thép", "view": "Trung tính thận trọng", "action": "Bám giá nguyên liệu và biên."},
    {"sector": "Bán lẻ", "view": "Chọn lọc", "action": "Ưu tiên chuỗi có động lực same-store."},
]

_CANONICAL_QUICK_STATES: tuple[str, ...] = (
    "Cầm nhiều tiền mặt",
    "Đang nắm tài sản khỏe",
    "Đang lãi ngắn hạn",
    "Đang dùng margin / đòn bẩy",
    "Muốn mua mới",
    "Đang kẹt tài sản yếu",
)

_QUICK_ACTION_FALLBACKS: dict[str, str] = {
    "Cầm nhiều tiền mặt": (
        "Chuẩn bị danh mục theo 3 kịch bản; chỉ giải ngân khi VN-Index, thanh khoản và độ rộng cùng xác nhận."
    ),
    "Đang nắm tài sản khỏe": (
        "Ưu tiên giữ mã chất lượng; tăng thêm tỷ trọng chỉ khi bứt nền kèm volume; dùng chốt lời theo lớp."
    ),
    "Đang lãi ngắn hạn": (
        "Chốt lời từng phần ở kháng cự; giữ phần cốt lõi; tránh dùng margin để kéo thêm rủi ro."
    ),
    "Đang dùng margin / đòn bẩy": (
        "Ưu tiên hạ đòn bẩy khi biên an toàn thu hẹp; không mua đuổi trong nhịp nhiễu hoặc thiếu xác nhận dòng tiền."
    ),
    "Muốn mua mới": (
        "Mua có kế hoạch, phân bổ theo danh mục; chờ pull-back có cấu trúc; tránh dồn tập trung một mã."
    ),
    "Đang kẹt tài sản yếu": (
        "Cắt giảm dứt khoát phần yếu/thanh khoản kém; không trung bình giá xuống thác; tập trung vốn vào mã chất lượng."
    ),
}


def _strip_public_jargon_string(value: str) -> str:
    out = value or ""
    for pat, repl in PUBLIC_JARGON_REPLACEMENTS:
        out = re.sub(pat, repl, out, flags=0 if "?" in pat else 0)
    return re.sub(r"\s+", " ", out).strip()


def _sanitize_strings_in_brief_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return _strip_public_jargon_string(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_strings_in_brief_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_strings_in_brief_obj(v) for v in obj]
    return obj


def _allocation_guide_violates(rows: Any) -> bool:
    if not isinstance(rows, list) or len(rows) != 4:
        return True
    canon = {"thận trọng", "cân bằng", "chủ động", "rủi ro cao"}
    profiles: set[str] = set()
    for r in rows:
        if not isinstance(r, dict):
            return True
        p = str(r.get("profile", "") or "").strip().lower()
        profiles.add(p)
        profile = p
        lev = str(r.get("leverage", "") or r.get("margin", "") or "")
        lev_l = lev.lower()
        if "thận trọng" in profile or "than trong" in profile:
            if re.search(r"\d\s*%", lev):
                return True
            if re.search(
                r"\b(cao|đầy|chủ động margin|margin cao|đòn bẩy cao|kỷ luật chặt)\b",
                lev,
                re.IGNORECASE,
            ):
                return True
        if "cân bằng" in profile or "can bang" in profile:
            if re.search(r"(?:^|[^\d])(?:70|80)\s*%", lev, re.IGNORECASE):
                return True
            if re.search(r"\b(đòn bẩy cao|margin cao)\b", lev, re.IGNORECASE):
                return True
            if re.search(r"\b(margin|đòn bẩy)\b", lev, re.IGNORECASE) and "rất thấp" not in lev_l:
                return True
    if profiles != canon:
        return True
    return False


def _canonical_sort_allocation_guide(rows: list[dict[str, Any]]) -> None:
    order = {"thận trọng": 0, "cân bằng": 1, "chủ động": 2, "rủi ro cao": 3}
    rows.sort(key=lambda r: order.get(str(r.get("profile", "") or "").strip().lower(), 99))


_STRONG_GLOBAL_ANCHOR_RE = re.compile(
    r"fed|fomc|lợi suất\s*mỹ|loi suat my|treasury|kỳ hạn\s*10|us\s*yield|dxy|"
    r"brent|wti|opec|iran|dollar\s*index|trung quốc|trung quoc|wto|imf|"
    r"cầu toàn cầu|toan cau|global growth|địa chính trị.*(mỹ|my|iran)|"
    r"chính sách tiền tệ.*(mỹ|fed)",
    re.IGNORECASE,
)


def _macro_driver_is_global(row: dict[str, Any]) -> bool:
    blob = (
        f"{row.get('title', '')} {row.get('analysis', '')} "
        f"{row.get('market_impact', '')} {row.get('vietnam_impact', '')}"
    )
    if _LOCAL_ONLY_DOMESTIC_RE.search(blob) and not _STRONG_GLOBAL_ANCHOR_RE.search(blob):
        return False
    return bool(_GLOBAL_MACRO_KEYWORDS_RE.search(blob))


def _sector_in_stable_universe(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n:
        return False
    for s in STABLE_VN_SECTOR_NAMES:
        if s.lower() == n:
            return True
    return False


def sanitize_strategy_brief_snake(
    snake: dict[str, Any],
    *,
    multisector_digest: bool = False,
) -> dict[str, Any]:
    """Post-process GPT output: jargon strip, allocation/signals/global sanity (Global Market Strategy Brief v2)."""
    out = copy.deepcopy(snake)
    if not multisector_digest:
        multisector_digest = bool(out.pop("_multisector_digest", False))
    else:
        out.pop("_multisector_digest", None)
    _migrate_snake_to_global_strategy_v2(out)

    for key in (
        "title",
        "publication_intro",
        "main_thesis",
        "market_regime_score",
        "scenario_plan",
        "final_decision",
        "view_change_triggers",
    ):
        if key in out:
            out[key] = _sanitize_strings_in_brief_obj(out[key])

    for list_key in (
        "what_changed",
        "global_macro_drivers",
        "intermarket_map",
        "transmission_chains",
        "quick_actions",
        "allocation_guide",
        "increase_risk_signals",
        "reduce_risk_signals",
        "intraday_playbook",
    ):
        if list_key in out:
            out[list_key] = _sanitize_strings_in_brief_obj(out[list_key])

    pa = out.get("priority_and_avoid")
    if isinstance(pa, dict):
        out["priority_and_avoid"] = _sanitize_strings_in_brief_obj(pa)

    mt = out.get("main_thesis")
    if isinstance(mt, dict):
        ac = str(mt.get("action_conclusion", "") or "")
        if _DIRECT_ASSET_PITCH_RE.search(ac) or (
            "trú ẩn" in ac.lower() and ("vàng" in ac.lower() or "dầu" in ac.lower())
        ):
            mt["action_conclusion"] = SAFE_ACTION_CONCLUSION

    ag = out.get("allocation_guide")
    if _allocation_guide_violates(ag):
        out["allocation_guide"] = copy.deepcopy(SAFE_ALLOCATION_GUIDE_V2)
    elif isinstance(out.get("allocation_guide"), list):
        _canonical_sort_allocation_guide(out["allocation_guide"])

    inc_raw = out.get("increase_risk_signals")
    red_raw = out.get("reduce_risk_signals")
    inc = inc_raw if isinstance(inc_raw, list) else []
    red = red_raw if isinstance(red_raw, list) else []
    new_inc: list[dict[str, str]] = []
    new_red: list[dict[str, str]] = []

    for r in inc:
        if not isinstance(r, dict):
            continue
        sig = str(r.get("signal", "") or "").strip()
        meaning = str(r.get("meaning", "") or "").strip()
        if not sig:
            continue
        inc_blob = f"{sig} {meaning}"
        if (
            _INCREASE_BAD_SIGNAL_RE.search(inc_blob)
            and not _INCREASE_BAD_EXCEPTION_RE.search(inc_blob)
        ):
            new_red.append(
                {
                    "signal": sig,
                    "action": "Giữ kỷ luật vốn; không mua đuổi khi tín hiệu rủi ro chi phối.",
                }
            )
        else:
            new_inc.append({"signal": sig, "meaning": meaning or "—"})

    for r in red:
        if not isinstance(r, dict):
            continue
        sig = str(r.get("signal", "") or "").strip()
        act = str(r.get("action", "") or "").strip()
        if not sig:
            continue
        if _REDUCE_GOOD_SIGNAL_RE.search(f"{sig} {act}"):
            new_inc.append(
                {
                    "signal": sig,
                    "meaning": (
                        "Tín hiệu xác nhận dòng tiền / vĩ mô thuận lợi hơn; "
                        "có thể từng bước tăng tỷ trọng có kiểm soát."
                    ),
                }
            )
        else:
            if _DIRECT_ASSET_PITCH_RE.search(act) or (
                "vàng" in act.lower() and ("nắm giữ" in act.lower() or "mua" in act.lower())
            ):
                act = "Thận trọng; ưu tiên quản trị vốn và hạn chế đuổi giá khi biến động gia tăng."
            new_red.append({"signal": sig, "action": act or "Thận trọng; quan sát thêm."})

    def _dedupe_inc(items: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        outl: list[dict[str, str]] = []
        for it in items:
            k = (it.get("signal") or "").strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            outl.append(it)
        return outl

    def _dedupe_red(items: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        outl: list[dict[str, str]] = []
        for it in items:
            k = (it.get("signal") or "").strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            outl.append(it)
        return outl

    new_inc = _dedupe_inc(new_inc)
    new_red = _dedupe_red(new_red)
    if len(new_inc) < _LIST_MINS["increase_risk_signals"]:
        for fb in SAFE_INCREASE_RISK_SIGNALS:
            if len(new_inc) >= 6:
                break
            if fb["signal"].lower() not in {x["signal"].lower() for x in new_inc}:
                new_inc.append(dict(fb))
    if len(new_red) < _LIST_MINS["reduce_risk_signals"]:
        for fb in SAFE_REDUCE_RISK_SIGNALS:
            if len(new_red) >= 6:
                break
            if fb["signal"].lower() not in {x["signal"].lower() for x in new_red}:
                new_red.append(dict(fb))
    out["increase_risk_signals"] = new_inc[:8]
    out["reduce_risk_signals"] = new_red[:8]

    gmd = out.get("global_macro_drivers")
    if isinstance(gmd, list):
        if multisector_digest:
            kept: list[dict[str, Any]] = []
            for r in gmd:
                if not isinstance(r, dict):
                    continue
                row = dict(r)
                if not str(row.get("market_impact", "") or "").strip():
                    row["market_impact"] = str(row.get("vietnam_impact", "") or "").strip()
                row.pop("vietnam_impact", None)
                kept.append(row)
            if kept:
                out["global_macro_drivers"] = kept
        else:
            global_rows = []
            for r in gmd:
                if not isinstance(r, dict):
                    continue
                row = dict(r)
                if not str(row.get("market_impact", "") or "").strip():
                    row["market_impact"] = str(row.get("vietnam_impact", "") or "").strip()
                row.pop("vietnam_impact", None)
                if _macro_driver_is_global(row):
                    global_rows.append(row)
            if len(global_rows) < 2:
                out["global_macro_drivers"] = copy.deepcopy(DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET)
            else:
                merged = global_rows[:]
                i = 0
                while len(merged) < 3 and i < len(DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET):
                    cand = DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET[i]
                    if not any(str(c.get("title")) == str(cand.get("title")) for c in merged):
                        merged.append(copy.deepcopy(cand))
                    i += 1
                out["global_macro_drivers"] = merged[:4]

    qa = out.get("quick_actions")
    if isinstance(qa, list) and qa:
        by_lower: dict[str, str] = {}
        for r in qa:
            if not isinstance(r, dict):
                continue
            st = str(r.get("investor_state", "") or "").strip()
            if st:
                by_lower[st.lower()] = str(r.get("action", "") or "").strip()
        ordered: list[dict[str, str]] = []
        for canon in _CANONICAL_QUICK_STATES:
            act = by_lower.get(canon.lower(), "")
            if not act:
                for lk, ac in by_lower.items():
                    if lk in canon.lower() or any(
                        tok and tok in lk for tok in canon.lower().split() if len(tok) > 3
                    ):
                        act = ac
                        break
            ordered.append(
                {
                    "investor_state": canon,
                    "action": act or "Giữ kỷ luật vốn; chờ tín hiệu rõ trên VN-Index và thanh khoản.",
                }
            )
        acts_nonempty = [str(x.get("action", "") or "").strip() for x in ordered if str(x.get("action", "") or "").strip()]
        if len(acts_nonempty) >= 4 and len(set(acts_nonempty)) <= 2:
            ordered = [{"investor_state": c, "action": _QUICK_ACTION_FALLBACKS[c]} for c in _CANONICAL_QUICK_STATES]
        out["quick_actions"] = ordered[:8]

    sp_plan = out.get("scenario_plan")
    if isinstance(sp_plan, dict):
        _scenario_safe_action = {
            "base_case": (
                "Giữ tỷ trọng cân bằng theo hồ sơ rủi ro; ưu tiên chất lượng và thanh khoản; "
                "hạn chế margin khi chưa có xác nhận dòng tiền."
            ),
            "bull_case": (
                "Tăng dần tỷ trọng cổ phiếu trong danh mục khi độ rộng và thanh khoản xác nhận; "
                "tránh dồn quá tập trung một nhóm."
            ),
            "bear_case": (
                "Hạ đòn bẩy; nâng tiền mặt; chỉ giữ cổ phiếu chất lượng cao và thanh khoản tốt."
            ),
        }
        for case_key, safe_act in _scenario_safe_action.items():
            blk = sp_plan.get(case_key)
            if not isinstance(blk, dict):
                continue
            act = str(blk.get("action", "") or "").strip()
            if _SCENARIO_ACTION_PORTFOLIO_RE.search(act) or _DIRECT_ASSET_PITCH_RE.search(act):
                blk["action"] = safe_act

    mrs_n = out.get("market_regime_score")
    if isinstance(mrs_n, dict):
        _normalize_market_regime_score(mrs_n)

    fd = str(out.get("final_decision", "") or "").strip()
    if len(fd) > 520:
        out["final_decision"] = fd[:517].rstrip() + "…"

    _migrate_snake_to_global_strategy_v2(out)
    return out


sanitize_investment_brief = sanitize_strategy_brief_snake


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
            itemprop = attr_map.get("itemprop", "").lower()
            if not content:
                return

            image_props = (
                "og:image",
                "og:image:url",
                "og:image:secure_url",
                "twitter:image",
            )
            if prop in image_props and not self.image_url:
                self.image_url = content.strip()
            elif name in {"twitter:image", "twitter:image:src", "thumbnail"} and not self.image_url:
                self.image_url = content.strip()
            elif itemprop == "image" and not self.image_url:
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
            as_attr = attr_map.get("as", "").lower()
            if rel == "image_src" and href and not self.image_url:
                self.image_url = href.strip()
            if rel == "preload" and as_attr == "image" and href and not self.image_url:
                self.image_url = href.strip()


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
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(FETCH_HTML_MAX_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        extractor = MetadataExtractor()
        try:
            extractor.feed(html)
        except Exception:
            pass
        image_url = normalize_media_url(url, extractor.image_url)
        if not image_url:
            image_url = extract_image_from_html(html, url)
        return {
            "image_url": image_url,
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
        image_url = (metadata.get("image_url") or "").strip()
        if not image_url:
            blob = str(article.get("content_for_ai") or article.get("summary") or "")
            image_url = extract_image_from_plaintext(blob)
        cards.append(
            {
                "title": article.get("title", "Tin"),
                "url": url,
                "source": article.get("source", ""),
                "category": article.get("category", ""),
                "region": article.get("region", ""),
                "published_at": article.get("published_at", ""),
                "summary": summary_text,
                "image_url": image_url,
                "metadata_status": metadata.get("metadata_status", ""),
            }
        )
    return cards


def _default_market_regime_score() -> dict[str, Any]:
    return {
        "total_score": 0,
        "regime": "Trung tính",
        "items": [
            {"axis": "Lãi suất / lợi suất", "signal": "Theo dõi phản ứng lợi suất thực trong ngày", "score": 0},
            {"axis": "USD / tỷ giá", "signal": "Biến động USD ảnh hưởng risk appetite", "score": 0},
            {"axis": "Dầu / lạm phát", "signal": "Áp lực lạm phát kỳ vọng từ năng lượng", "score": 0},
            {"axis": "Thanh khoản", "signal": "Cần đối chiếu khối lượng với diễn biến giá", "score": 0},
            {"axis": "Độ rộng thị trường", "signal": "Phân hóa có thể tiếp diễn", "score": 0},
            {"axis": "Nhóm dẫn dắt", "signal": "Ưu tiên nhóm giữ nền và dòng tiền", "score": 0},
        ],
        "interpretation": (
            "Điểm tổng hợp minh họa nhịp ngày; không thay thế xác nhận trên thị trường thật."
        ),
    }


def _default_what_changed_fallback() -> list[dict[str, str]]:
    return [
        {
            "variable": "Lãi suất / lợi suất Mỹ",
            "change": "Theo dữ liệu thị trường trong ngày",
            "meaning": "Neo kỳ vọng Fed và chi phí vốn toàn cầu.",
        },
        {
            "variable": "USD / DXY",
            "change": "Theo hướng trong ngày",
            "meaning": "Ảnh hưởng tài sản nhạy FX và dòng vốn xuyên biên giới.",
        },
        {
            "variable": "Dầu / năng lượng",
            "change": "Theo áp lực lạm phát kỳ vọng",
            "meaning": "Tác động chuỗi chi phí và tâm lý risk-off.",
        },
        {
            "variable": "Cổ phiếu & thanh khoản",
            "change": "Phân hóa có thể tiếp diễn",
            "meaning": "Ưu tiên tài sản khỏe, tránh mua đuổi nhịp mỏng.",
        },
    ]


def _default_intermarket_map_fallback() -> list[dict[str, str]]:
    return [
        {"asset": "Cổ phiếu Mỹ", "state": "Theo lợi suất và định giá", "action": "Giữ tỷ trọng theo khẩu vị; tránh mua đuổi."},
        {"asset": "Cổ phiếu Việt Nam", "state": "Phân hóa", "action": "Tập trung nhóm giữ nền, có thanh khoản và dòng tiền."},
        {"asset": "Thị trường mới nổi", "state": "Nhạy USD và risk appetite", "action": "Hạn chế đòn bẩy khi chưa xác nhận dòng tiền."},
        {"asset": "Vàng", "state": "Theo USD và lợi suất thực", "action": "Có thể giữ vai trò phòng thủ vừa phải trong danh mục."},
        {"asset": "Dầu", "state": "Biến động cung cầu", "action": "Theo dõi tác động lạm phát kỳ vọng; không tập trung đơn nhất."},
        {"asset": "Trái phiếu / lợi suất", "state": "Neo theo chính sách", "action": "Ưu tiên chất lượng tín dụng và kỳ hạn phù hợp."},
        {"asset": "Crypto", "state": "Biến động cao", "action": "Giới hạn tỷ trọng; tránh đòn bẩy lớn."},
        {"asset": "Tiền mặt", "state": "Linh hoạt", "action": "Giữ buffer để chờ xác nhận đồng thuận."},
    ]


def _default_priority_and_avoid_fallback() -> dict[str, Any]:
    return {
        "prioritize": [
            {"asset": "Cổ phiếu chất lượng, dòng tiền rõ", "reason": "Giảm rủi ro đuổi nhịp mỏng."},
            {"asset": "Nhóm dẫn dắt giữ nền", "reason": "Ổn định tương đối khi phân hóa."},
            {"asset": "Tiền mặt có kế hoạch", "reason": "Giữ quyền chủ động khi tín hiệu chưa đồng thuận."},
            {"asset": "Vàng (phòng thủ vừa phải)", "reason": "Cân bằng rủi ro hệ thống và USD."},
            {"asset": "Trái phiếu chất lượng", "reason": "Neo khi risk-off."},
        ],
        "avoid_or_be_careful": [
            {"asset": "Tài sản đầu cơ tăng nóng", "reason": "Thanh khoản mỏng, dễ đảo chiều."},
            {"asset": "Đòn bẩy cao khi chưa xác nhận", "reason": "Rủi ro thanh lý trong biến động."},
            {"asset": "Crypto tỷ trọng lớn", "reason": "Biến động và thanh khoản không đồng nhất."},
            {"asset": "Tập trung một nhóm quá mức", "reason": "Giảm khả năng chịu shock."},
            {"asset": "Mua đuổi khi độ rộng yếu", "reason": "Nhịp tăng thiếu dòng tiền xác nhận."},
        ],
    }


def _default_intraday_playbook_fallback() -> list[dict[str, str]]:
    return [
        {"market_condition": "Tăng mạnh nhưng thanh khoản yếu", "action": "Không mua đuổi."},
        {"market_condition": "Tăng cùng thanh khoản và độ rộng tốt", "action": "Có thể tăng tỷ trọng từng phần có kỷ luật."},
        {"market_condition": "Giảm nhẹ với thanh khoản thấp", "action": "Quan sát; chưa cần phản ứng mạnh."},
        {"market_condition": "Giảm mạnh với thanh khoản cao", "action": "Hạ tỷ trọng; giảm đòn bẩy."},
        {"market_condition": "Đi ngang phân hóa", "action": "Giữ tài sản khỏe; loại bỏ tài sản yếu."},
        {"market_condition": "Tin tiêu cực nhưng giá không phản ánh mạnh", "action": "Theo dõi khả năng hấp thụ thông tin."},
    ]


def _default_view_change_triggers_fallback() -> dict[str, Any]:
    return {
        "more_positive_if": [
            "USD suy yếu rõ",
            "Lợi suất Mỹ hạ nhiệt",
            "Dầu ổn định",
            "Thanh khoản tăng cùng giá",
        ],
        "more_negative_if": [
            "USD tăng mạnh",
            "Lợi suất Mỹ tăng nhanh",
            "Dầu tăng sốc",
            "Chỉ số tăng nhưng độ rộng yếu",
        ],
    }


def _migrate_snake_to_global_strategy_v2(out: dict[str, Any]) -> None:
    """Chuẩn hoá brief snake_case sang Global Market Strategy Brief v2 (bổ sung field, bỏ legacy)."""
    gmd = out.get("global_macro_drivers")
    if isinstance(gmd, list):
        for d in gmd:
            if not isinstance(d, dict):
                continue
            if not str(d.get("market_impact", "") or "").strip():
                d["market_impact"] = str(d.get("vietnam_impact", "") or "").strip()
            d.pop("vietnam_impact", None)

    vt = out.get("vietnam_transmission")
    chains_from_vt: list[str] = []
    if isinstance(vt, dict):
        ch = vt.get("chains")
        if isinstance(ch, list):
            chains_from_vt = [str(x).strip() for x in ch if isinstance(x, str) and str(x).strip()]

    tc = out.get("transmission_chains")
    if not isinstance(tc, list) or len([x for x in tc if isinstance(x, str) and x.strip()]) < _LIST_MINS[
        "transmission_chains"
    ]:
        out["transmission_chains"] = chains_from_vt or [
            "Lãi suất Mỹ cao → USD mạnh → EM và tài sản rủi ro chịu áp lực định giá.",
            "Dầu biến động → lạm phát kỳ vọng → tâm lý thận trọng với tài sản rủi ro.",
            "Thanh khoản yếu trong nhịp tăng → dễ đảo chiều; ưu tiên kỷ luật vốn.",
        ]

    wc = out.get("what_changed")
    if not isinstance(wc, list) or len([x for x in wc if isinstance(x, dict)]) < _LIST_MINS["what_changed"]:
        out["what_changed"] = _default_what_changed_fallback()

    mrs = out.get("market_regime_score")
    if not isinstance(mrs, dict) or not isinstance(mrs.get("items"), list):
        out["market_regime_score"] = _default_market_regime_score()
    else:
        _n_axes = sum(
            1
            for it in mrs["items"]
            if isinstance(it, dict)
            and str(it.get("axis", "") or "").strip()
            and str(it.get("signal", "") or "").strip()
        )
        if _n_axes < _LIST_MINS["market_regime_axes"]:
            out["market_regime_score"] = _default_market_regime_score()
            mrs = out["market_regime_score"]
        mrs.setdefault("total_score", 0)
        mrs.setdefault("regime", "Trung tính")
        mrs.setdefault("interpretation", "")

    im = out.get("intermarket_map")
    if not isinstance(im, list) or len([x for x in im if isinstance(x, dict)]) < _LIST_MINS["intermarket_map"]:
        out["intermarket_map"] = _default_intermarket_map_fallback()

    pa = out.get("priority_and_avoid")
    if not isinstance(pa, dict):
        out["priority_and_avoid"] = _default_priority_and_avoid_fallback()
    else:
        if not isinstance(pa.get("prioritize"), list) or len(pa["prioritize"]) < 5:
            pa["prioritize"] = _default_priority_and_avoid_fallback()["prioritize"]
        if not isinstance(pa.get("avoid_or_be_careful"), list) or len(pa["avoid_or_be_careful"]) < 5:
            pa["avoid_or_be_careful"] = _default_priority_and_avoid_fallback()["avoid_or_be_careful"]

    ip = out.get("intraday_playbook")
    if (
        not isinstance(ip, list)
        or len([x for x in ip if isinstance(x, dict)]) < _LIST_MINS["intraday_playbook"]
    ):
        out["intraday_playbook"] = _default_intraday_playbook_fallback()

    vct = out.get("view_change_triggers")
    if not isinstance(vct, dict):
        out["view_change_triggers"] = _default_view_change_triggers_fallback()
    vct = out["view_change_triggers"]
    assert isinstance(vct, dict)
    if not isinstance(vct.get("more_positive_if"), list) or len(vct["more_positive_if"]) < 3:
        vct["more_positive_if"] = _default_view_change_triggers_fallback()["more_positive_if"]
    if not isinstance(vct.get("more_negative_if"), list) or len(vct["more_negative_if"]) < 3:
        vct["more_negative_if"] = _default_view_change_triggers_fallback()["more_negative_if"]

    fd = str(out.get("final_decision", "") or "").strip()
    if not fd:
        out["final_decision"] = str(out.get("final_takeaway", "") or "").strip() or (
            "Giữ tư thế chọn lọc; không mua đuổi; hạn chế đòn bẩy cao. "
            "Ưu tiên tài sản khỏe và tiền mặt chủ động; chỉ tăng rủi ro khi USD, lợi suất, thanh khoản và độ rộng cùng xác nhận."
        )

    ag = out.get("allocation_guide")
    if not isinstance(ag, list) or len(ag) < 4:
        out["allocation_guide"] = copy.deepcopy(SAFE_ALLOCATION_GUIDE_V2)

    out.pop("vietnam_transmission", None)
    out.pop("sector_priority", None)
    out.pop("final_takeaway", None)


def _default_strategy_snake(*, brief_date: str, generated_at: str) -> dict[str, Any]:
    """Shell Global Market Strategy Brief v2 khi thiếu dữ liệu — tone nghiên cứu, không nhắc tooling."""
    base = {
        "title": "LEON Quant Labs — Global Market Strategy Brief",
        "date": brief_date,
        "generated_at": generated_at,
        "publication_intro": {
            "headline": "Góc nhìn chiến lược thị trường toàn cầu cho nhà đầu tư Việt Nam",
            "description": (
                "LEON Quant Labs chuyển biến động vĩ mô và thanh khoản toàn cầu thành khung hành động danh mục "
                "ngắn gọn, có thể theo dõi theo ngày."
            ),
        },
        "main_thesis": {
            "regime": "Thận trọng có chọn lọc",
            "thesis": (
                "Áp lực chính đến từ lãi suất Mỹ, USD, dầu và kỳ vọng tăng trưởng. "
                "Thị trường đang ở trạng thái thận trọng có chọn lọc; cần đối chiếu dòng tiền thật."
            ),
            "action_conclusion": (
                "Chiến lược phù hợp là giữ tỷ trọng vừa phải, ưu tiên tài sản khỏe, hạn chế đòn bẩy và chỉ tăng rủi ro khi có xác nhận."
            ),
        },
        "what_changed": _default_what_changed_fallback(),
        "market_regime_score": _default_market_regime_score(),
        "global_macro_drivers": copy.deepcopy(DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET),
        "intermarket_map": _default_intermarket_map_fallback(),
        "transmission_chains": [
            "Lãi suất Mỹ cao → USD mạnh → thị trường mới nổi và tài sản rủi ro chịu áp lực định giá.",
            "Dầu biến động → lạm phát kỳ vọng → Fed thận trọng hơn → tài sản rủi ro khó tăng đồng thuận.",
            "Thanh khoản yếu trong nhịp tăng → ưu tiên kỷ luật vốn và tránh mua đuổi.",
        ],
        "quick_actions": [
            {"investor_state": s, "action": _QUICK_ACTION_FALLBACKS[s]} for s in _CANONICAL_QUICK_STATES
        ],
        "allocation_guide": copy.deepcopy(SAFE_ALLOCATION_GUIDE_V2),
        "priority_and_avoid": _default_priority_and_avoid_fallback(),
        "increase_risk_signals": copy.deepcopy(SAFE_INCREASE_RISK_SIGNALS),
        "reduce_risk_signals": copy.deepcopy(SAFE_REDUCE_RISK_SIGNALS),
        "intraday_playbook": _default_intraday_playbook_fallback(),
        "scenario_plan": {
            "base_case": {
                "title": "Kịch bản cơ sở",
                "description": "Thị trường phân hóa; vĩ mô vẫn có điểm nghẽn nhưng chưa vỡ trận.",
                "action": "Giữ tỷ trọng vừa phải; ưu tiên cổ phiếu chất lượng và quản trị margin.",
            },
            "bull_case": {
                "title": "Kịch bản tích cực",
                "description": "USD hạ nhiệt, thanh khoản cải thiện, rủi ro hệ thống không leo thang.",
                "action": "Tăng tỷ trọng từng phần theo nhịp xác nhận; giữ tiền mặt để còn quyền chủ động.",
            },
            "bear_case": {
                "title": "Kịch bản tiêu cực",
                "description": "USD mạnh, thanh khoản suy yếu, định giá tài sản rủi ro thắt lại.",
                "action": "Hạ đòn bẩy; nâng tiền mặt; chỉ giữ tài sản chất lượng cao và thanh khoản tốt.",
            },
        },
        "view_change_triggers": _default_view_change_triggers_fallback(),
        "final_decision": (
            "Trạng thái hôm nay: chọn lọc, không mua đuổi, không dùng đòn bẩy cao. "
            "Giữ tiền mặt chủ động, nắm tài sản khỏe và chỉ tăng rủi ro khi USD, lợi suất, thanh khoản và độ rộng cùng xác nhận."
        ),
    }
    return base


def _is_investment_strategy_brief(summary: dict[str, Any]) -> bool:
    mt = summary.get("main_thesis")
    pi = summary.get("publication_intro")
    return isinstance(mt, dict) and isinstance(pi, dict) and (
        bool(str(mt.get("thesis", "")).strip()) or bool(str(mt.get("regime", "")).strip())
    )


def _is_multisector_digest(summary: dict[str, Any]) -> bool:
    return bool(str(summary.get("executive_overview", "") or "").strip()) and isinstance(
        summary.get("sectors"), list
    )


def _url_hostname(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


_SOURCE_DISPLAY_BY_HOST: dict[str, str] = {
    "dantri.com.vn": "Dân trí",
    "vnexpress.net": "VnExpress",
    "tuoitre.vn": "Tuổi Trẻ",
    "thanhnien.vn": "Thanh Niên",
    "vietnamnet.vn": "VietnamNet",
    "baochinhphu.vn": "Báo Chính phủ",
    "cafef.vn": "CafeF",
    "vneconomy.vn": "VnEconomy",
    "genk.vn": "GenK",
    "plo.vn": "PLO",
    "laodong.vn": "Lao động",
    "tienphong.vn": "Tiền Phong",
    "aljazeera.com": "Al Jazeera",
    "asia.nikkei.com": "Nikkei Asia",
    "scmp.com": "SCMP",
    "theguardian.com": "The Guardian",
    "cnbc.com": "CNBC",
    "techcrunch.com": "TechCrunch",
    "theverge.com": "The Verge",
    "wired.com": "Wired",
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
}


def _source_brand_name(host: str, raw_source: str = "") -> str:
    host_key = (host or "").lower().strip()
    raw = (raw_source or "").strip()
    if raw and raw.lower() not in (host_key, f"www.{host_key}") and "." not in raw:
        return raw
    if raw and raw.lower() not in (host_key, f"www.{host_key}") and raw != host_key:
        mapped = _SOURCE_DISPLAY_BY_HOST.get(host_key, "")
        if mapped:
            return mapped
        return raw
    return _SOURCE_DISPLAY_BY_HOST.get(host_key, "")


def _link_display_label(host: str, raw_source: str = "") -> str:
    host = (host or "").strip()
    brand = _source_brand_name(host, raw_source)
    if brand and brand.lower() != host.lower():
        return f"{brand} · {host}" if host else brand
    return host or raw_source.strip() or "Nguồn"


DIGEST_FOUR_SECTORS: tuple[tuple[str, str], ...] = (
    ("finance", "Kinh tế & Tài chính"),
    ("tech", "Công nghệ & AI"),
    ("news", "Thời sự & Chính trị"),
    ("trends", "Xu hướng & Đời sống"),
)
DIGEST_SECTOR_LABEL_BY_CODE = dict(DIGEST_FOUR_SECTORS)
DIGEST_MAX_ITEMS_PER_SECTOR = 25  # parser safety only — renderer shows Gemini count
DIGEST_MAX_NOTABLE_ARTICLES = 12
DIGEST_SECTOR_SUMMARY_MAX_CHARS = 2800
_URL_MATCH_MIN_SCORE = 0.36


def _infer_digest_sector_code(name: str) -> str:
    n = (name or "").lower()
    if any(
        k in n
        for k in (
            "công nghệ",
            "cong nghe",
            "ai",
            "khoa học",
            "bán dẫn",
            "viễn thông",
            "tech",
            "chip",
            "semiconductor",
        )
    ):
        return "tech"
    if any(
        k in n
        for k in (
            "chính trị",
            "thời sự",
            "ngoại giao",
            "địa chính",
            "quốc tế",
            "news",
            "iran",
            "israel",
            "ukraine",
        )
    ):
        return "news"
    if any(
        k in n
        for k in (
            "xu hướng",
            "đời sống",
            "quan điểm",
            "góc nhìn",
            "xã hội",
            "pháp luật",
            "y tế",
            "sức khỏe",
            "môi trường",
            "thể thao",
            "văn hóa",
            "giáo dục",
            "trends",
        )
    ):
        return "trends"
    if any(
        k in n
        for k in (
            "kinh tế",
            "tài chính",
            "chứng khoán",
            "bất động",
            "tiền ảo",
            "crypto",
            "finance",
            "ngân hàng",
            "thị trường",
        )
    ):
        return "finance"
    return "trends"


def _resolve_digest_sector_code(sector: dict[str, Any]) -> str:
    code = str(sector.get("code") or "").strip().lower()
    if code in DIGEST_SECTOR_LABEL_BY_CODE:
        return code
    return _infer_digest_sector_code(str(sector.get("name") or ""))


def _normalize_vn_text(text: str) -> str:
    s = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _headline_tokens(text: str) -> set[str]:
    norm = _normalize_vn_text(text)
    raw = re.findall(r"[\w]{3,}", norm, flags=re.UNICODE)
    stop = {
        "cua",
        "va",
        "cho",
        "cac",
        "trong",
        "voi",
        "tu",
        "theo",
        "mot",
        "duoc",
        "nam",
        "ngay",
        "tin",
        "bai",
        "the",
        "and",
        "for",
        "voi",
        "cung",
        "nhung",
        "muc",
        "theo",
    }
    return {t for t in raw if t not in stop}


def _entity_hints(headline: str) -> set[str]:
    hints: set[str] = set()
    for m in re.finditer(r"\b[A-Z][a-zA-Z]{2,}\b|\b[A-Z]{2,}\b", headline):
        hints.add(m.group().lower())
    for m in re.finditer(
        r"(?i)\b(spacex|meta|nvidia|google|amd|iran|israel|ukraine|philippines|"
        r"zalando|bitcoin|pecc2|pc1|team pcp|etax|ipo|vn-index|vnindex)\b",
        headline,
    ):
        hints.add(re.sub(r"\s+", "", m.group().lower()))
    for m in re.finditer(r"\b\d[\d.,]{0,8}\b", headline):
        hints.add(m.group())
    return {h for h in hints if len(h) >= 2}


def _score_headline_to_article(headline: str, art: dict[str, Any]) -> float:
    title = str(art.get("title") or "").strip()
    if not title:
        return 0.0
    text = str(art.get("text") or "")[:1000]
    ht = _headline_tokens(headline)
    title_norm = _normalize_vn_text(title)
    blob_norm = title_norm + " " + _normalize_vn_text(text)
    at = _headline_tokens(blob_norm)
    token_sc = (len(ht & at) / max(len(ht), 1)) if ht and at else 0.0
    seq_sc = SequenceMatcher(None, _normalize_vn_text(headline), title_norm).ratio()
    hints = _entity_hints(headline)
    hint_sc = 0.0
    if hints:
        blob_l = blob_norm.lower()
        matched = sum(1 for h in hints if h in blob_l or h in title_norm)
        hint_sc = matched / len(hints)
        if matched == 0:
            return 0.0
        strong_latin = [h for h in hints if h.isascii() and len(h) >= 4]
        if strong_latin and not any(h in title_norm for h in strong_latin):
            return 0.0
    must_vn = {t for t in _headline_tokens(headline) if len(t) >= 5 and not t.isascii()}
    if must_vn:
        title_t = _headline_tokens(title)
        if len(must_vn & title_t) < min(2, len(must_vn)):
            return 0.0
    combined = min(1.0, 0.35 * token_sc + 0.4 * seq_sc + 0.25 * hint_sc)
    if seq_sc < 0.24 and token_sc < 0.42:
        return 0.0
    return combined


def _infer_article_sector_code(article: dict[str, Any]) -> str:
    blob = " ".join(
        [
            str(article.get("title") or ""),
            str(article.get("text") or "")[:1200],
            str(article.get("source") or ""),
            str(article.get("category") or ""),
        ]
    )
    return _infer_digest_sector_code(blob)


def _is_http_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def _pick_sub_topic_url(
    headline: str,
    stated: list[str],
    *,
    by_url: dict[str, dict[str, Any]],
    used_urls: set[str] | None,
    sector_code: str,
    boost_urls: list[str],
) -> str:
    """Ưu tiên URL Gemini; không bỏ link chỉ vì lệch sector trong matcher."""
    for u in stated:
        if not _is_http_url(u) or (used_urls is not None and u in used_urls):
            continue
        return u.strip()
    return _resolve_url_for_headline(
        headline,
        by_url=by_url,
        used_urls=used_urls,
        sector_code=sector_code,
        boost_urls=boost_urls,
    )


def _resolve_url_for_headline(
    headline: str,
    *,
    by_url: dict[str, dict[str, Any]],
    used_urls: set[str] | None = None,
    sector_code: str = "",
    boost_urls: list[str] | None = None,
) -> str:
    """Quét toàn bộ bài crawl, chọn URL khớp headline nhất; không gán nếu không chắc."""
    best_u = ""
    best_sc = 0.0
    boost = {str(u).strip() for u in (boost_urls or []) if str(u).strip()}
    for u, art in by_url.items():
        u = str(u or "").strip()
        if not u or (used_urls and u in used_urls):
            continue
        sc = _score_headline_to_article(headline, art)
        if not sc:
            continue
        if u in boost:
            sc = min(1.0, sc * 1.1)
        if sector_code:
            if _infer_article_sector_code(art) == sector_code:
                sc = min(1.0, sc * 1.06)
            else:
                sc *= 0.5
        if sc > best_sc:
            best_sc, best_u = sc, u
    min_sc = _URL_MATCH_MIN_SCORE
    if best_u in boost and best_sc >= 0.28:
        min_sc = 0.28
    if best_u and best_sc >= min_sc:
        return best_u
    return ""


def _links_from_urls(
    urls: list[str],
    *,
    by_url: dict[str, dict[str, Any]],
    sector_name: str,
    add_link,
    max_links: int = 1,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for u in urls[: max(1, max_links)]:
        u = str(u or "").strip()
        if not u:
            continue
        add_link(u, sector=sector_name, group=sector_name)
        art = by_url.get(u)
        host = _url_hostname(u)
        src = (str(art.get("source", "")) if art else "") or ""
        out.append(
            {
                "url": u,
                "title": (str(art.get("title", "")) if art else "") or host or u,
                "host": host,
                "source": src,
                "label": _link_display_label(host, src),
            }
        )
    return out


def _sub_topic_importance_key(row: dict[str, Any], fallback_index: int) -> tuple[int, int]:
    for field in ("importance_rank", "importance", "rank", "priority"):
        raw = row.get(field)
        if raw is None or raw == "":
            continue
        try:
            return (0, int(raw))
        except (TypeError, ValueError):
            continue
    return (1, fallback_index)


def _sort_sub_topics_by_importance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Giữ thứ tự Gemini; nếu có importance_rank thì sắp xếp 1 = quan trọng nhất."""
    indexed = [(i, r) for i, r in enumerate(rows) if isinstance(r, dict)]
    indexed.sort(key=lambda pair: _sub_topic_importance_key(pair[1], pair[0]))
    return [r for _, r in indexed]


def _sector_items_from_raw(
    sector: dict[str, Any],
    *,
    sector_code: str,
    all_articles: list[dict[str, Any]],
    by_url: dict[str, dict[str, Any]],
    sector_name: str,
    add_link,
) -> list[dict[str, Any]]:
    pool = [str(u).strip() for u in (sector.get("source_urls") or []) if str(u).strip()]

    subs = sector.get("sub_topics")
    used_urls: set[str] | None = set()
    if isinstance(subs, list) and subs:
        items: list[dict[str, Any]] = []
        for row in _sort_sub_topics_by_importance(subs):
            if not isinstance(row, dict):
                continue
            headline = str(row.get("headline") or row.get("title") or "").strip()
            if not headline:
                continue
            stated = [str(u).strip() for u in (row.get("source_urls") or []) if str(u).strip()]
            matched = _pick_sub_topic_url(
                headline,
                stated,
                by_url=by_url,
                used_urls=used_urls,
                sector_code=sector_code,
                boost_urls=stated + pool,
            )
            links = (
                _links_from_urls(
                    [matched],
                    by_url=by_url,
                    sector_name=sector_name,
                    add_link=add_link,
                )
                if matched
                else []
            )
            if matched and used_urls is not None:
                used_urls.add(matched)
            item: dict[str, Any] = {
                "headline": headline,
                "links": links,
                "importanceRank": _sub_topic_importance_key(row, len(items))[1],
            }
            for key, out_key in (
                ("priority_tier", "priorityTier"),
                ("summary_hint", "summaryHint"),
                ("reason_selected", "reasonSelected"),
            ):
                val = str(row.get(key) or "").strip()
                if val:
                    item[out_key] = val
            items.append(item)
        return items[:DIGEST_MAX_ITEMS_PER_SECTOR]

    # key_points từ Gemini: thứ tự mảng = quan trọng giảm dần (không đảo)
    points = [str(p).strip() for p in (sector.get("key_points") or []) if str(p).strip()]
    items = []
    used: set[str] = set()
    for pt in points:
        matched = _resolve_url_for_headline(
            pt,
            by_url=by_url,
            used_urls=used,
            sector_code=sector_code,
            boost_urls=pool,
        )
        links = (
            _links_from_urls(
                [matched],
                by_url=by_url,
                sector_name=sector_name,
                add_link=add_link,
            )
            if matched
            else []
        )
        if matched:
            used.add(matched)
        items.append(
            {
                "headline": pt,
                "links": links,
                "importanceRank": len(items) + 1,
            }
        )
    return items[:DIGEST_MAX_ITEMS_PER_SECTOR]


def _normalize_digest_sectors_four(
    summary: dict[str, Any],
    *,
    by_url: dict[str, dict[str, Any]],
    add_link,
    all_articles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    articles = all_articles if isinstance(all_articles, list) else []
    buckets: dict[str, dict[str, Any]] = {
        code: {"code": code, "name": label, "summary": "", "items": []}
        for code, label in DIGEST_FOUR_SECTORS
    }

    for sector in summary.get("sectors") or []:
        if not isinstance(sector, dict):
            continue
        code = _resolve_digest_sector_code(sector)
        label = (
            str(sector.get("name") or "").strip()
            or DIGEST_SECTOR_LABEL_BY_CODE[code]
        )
        summ = str(sector.get("summary") or "").strip()
        bucket = buckets[code]
        bucket["name"] = label
        if summ and not bucket["summary"]:
            bucket["summary"] = summ
        elif summ and summ not in bucket["summary"]:
            combined = f"{bucket['summary']} {summ}".strip()
            bucket["summary"] = combined[:DIGEST_SECTOR_SUMMARY_MAX_CHARS]
        bucket["items"].extend(
            _sector_items_from_raw(
                sector,
                sector_code=code,
                all_articles=articles,
                by_url=by_url,
                sector_name=label,
                add_link=add_link,
            )
        )

    out: list[dict[str, Any]] = []
    for code, label in DIGEST_FOUR_SECTORS:
        b = buckets[code]
        seen_u: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for it in b["items"]:
            links = it.get("links") if isinstance(it.get("links"), list) else []
            u = str((links[0] or {}).get("url") or "").strip() if links else ""
            if u:
                if u in seen_u:
                    continue
                seen_u.add(u)
            deduped.append(it)
        deduped.sort(key=lambda it: int(it.get("importanceRank") or 999))
        deduped = deduped[:DIGEST_MAX_ITEMS_PER_SECTOR]
        points_legacy = [
            str(p).strip()
            for p in (b.get("keyPoints") or [])
            if str(p).strip()
        ]
        out.append(
            {
                "name": b["name"] or label,
                "summary": str(b.get("summary") or "").strip(),
                "items": deduped,
                "keyPoints": [it["headline"] for it in deduped] or points_legacy,
                "links": [],
            }
        )
    return out


def build_digest_web_extras(
    summary: dict[str, Any],
    all_articles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Sectors + link index for digest-mode UI (no images)."""
    by_url: dict[str, dict[str, Any]] = {}
    for art in all_articles:
        u = str(art.get("url") or "").strip()
        if u and u not in by_url:
            by_url[u] = art

    seen: set[str] = set()
    link_index: list[dict[str, str]] = []
    sectors_out: list[dict[str, Any]] = []

    def add_link(
        url: str,
        *,
        title: str = "",
        source: str = "",
        sector: str = "",
        group: str = "",
    ) -> None:
        u = str(url or "").strip()
        if not u or u in seen:
            return
        seen.add(u)
        art = by_url.get(u)
        t = (title or (str(art.get("title", "")) if art else "") or "").strip()
        src = (source or (str(art.get("source", "")) if art else "") or "").strip()
        host = _url_hostname(u)
        link_index.append(
            {
                "url": u,
                "title": t or host or u,
                "host": host,
                "source": src,
                "label": _link_display_label(host, src),
                "sector": sector,
                "group": group or sector or "Khác",
            }
        )

    sectors_out = _normalize_digest_sectors_four(
        summary, by_url=by_url, add_link=add_link, all_articles=all_articles
    )

    for row in summary.get("notable_articles") or []:
        if not isinstance(row, dict):
            continue
        add_link(
            str(row.get("url") or ""),
            title=str(row.get("title") or ""),
            source=str(row.get("source") or ""),
            sector="Tin chọn",
            group="Tin chọn lọc",
        )

    article_links = [
        {
            "title": str(a.get("title") or "").strip() or _url_hostname(str(a.get("url") or "")),
            "url": str(a.get("url") or "").strip(),
            "source": str(a.get("source") or "").strip(),
            "publishedAt": str(a.get("published_at") or "").strip(),
            "host": _url_hostname(str(a.get("url") or "")),
        }
        for a in all_articles
        if str(a.get("url") or "").strip()
    ]

    return {
        "digestSectors": sectors_out,
        "digestLinkIndex": link_index,
        "articleLinkIndex": article_links,
    }


def _dedupe_preserve_order(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        t = str(line or "").strip()
        if not t or len(t) < 12:
            continue
        key = t.lower()[:96]
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def _prose_to_bullet_lines(text: str, *, min_len: int = 20) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    if re.search(r"(?m)^\s*[-•*]\s+", raw):
        return _dedupe_preserve_order(
            [re.sub(r"^\s*[-•*]\s+", "", ln).strip() for ln in raw.splitlines() if ln.strip()],
        )
    out: list[str] = []
    paras = re.split(r"\n\s*\n", raw) if "\n\n" in raw else [raw]
    for para in paras:
        p = re.sub(r"\s+", " ", para).strip()
        if not p:
            continue
        chunks = re.split(
            r"(?<=[.!?…])\s+(?=[\"'“‘(A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ0-9])",
            p,
        )
        if len(chunks) <= 1:
            chunks = re.split(r"(?<=[;])\s+", p)
        for c in chunks:
            c = c.strip()
            if len(c) >= min_len:
                out.append(c)
    return _dedupe_preserve_order(out) or [raw]


def _vietnam_overview_extra_bullets(overview: str) -> list[str]:
    extras: list[str] = []
    for para in re.split(r"\n\s*\n", str(overview or "").strip()):
        if re.search(
            r"việt\s*nam|vn-index|trong nước|đồng nai|hà nội|tp\.?\s*hcm|chứng khoán việt",
            para,
            re.IGNORECASE,
        ):
            extras.extend(_prose_to_bullet_lines(para))
    return extras


def _digest_multisector_to_strategy_snake(
    summary: dict[str, Any],
    *,
    brief_date: str,
    generated_at: str,
) -> dict[str, Any]:
    """Map ``gemini_digest_summary.json`` multisector schema → strategy brief snake_case."""
    out = copy.deepcopy(_default_strategy_snake(brief_date=brief_date, generated_at=generated_at))
    title = str(summary.get("title", "") or "").strip()
    if title:
        out["title"] = title

    exec_raw = summary.get("executive_overview")
    if isinstance(exec_raw, list):
        overview = "\n\n".join(str(x).strip() for x in exec_raw if str(x).strip())
    else:
        overview = str(exec_raw or "").strip()
    if overview:
        out["publication_intro"]["headline"] = title or out["publication_intro"]["headline"]
        out["publication_intro"]["description"] = overview[:1200]
        out["main_thesis"]["thesis"] = overview
        first_line = overview.split("\n", 1)[0].strip()
        if len(first_line) <= 120:
            out["main_thesis"]["regime"] = first_line
        action = overview.split("\n\n")[-1].strip() if "\n\n" in overview else overview
        if len(action) > 520:
            action = action[:517] + "…"
        out["main_thesis"]["action_conclusion"] = action

    drivers: list[dict[str, str]] = []
    for sector in summary.get("sectors") or []:
        if not isinstance(sector, dict):
            continue
        name = str(sector.get("name", "") or "").strip() or "Nhịp ngành"
        summ = str(sector.get("summary", "") or "").strip()
        points = sector.get("key_points") or []
        bullets = "\n".join(f"• {str(p).strip()}" for p in points if str(p).strip())
        analysis = "\n\n".join(x for x in (summ, bullets) if x).strip() or "—"
        urls = [str(u).strip() for u in (sector.get("source_urls") or []) if str(u).strip()]
        impact_parts = [str(p).strip() for p in points if str(p).strip()]
        market_impact = "\n".join(impact_parts[:6]) if impact_parts else summ[:500] or "—"
        drivers.append(
            {
                "title": name,
                "analysis": analysis,
                "market_impact": market_impact,
            }
        )
    if drivers:
        out["global_macro_drivers"] = drivers
    out["_multisector_digest"] = True
    out["_digest_public"] = {
        "vietnam_highlights": str(summary.get("vietnam_highlights", "") or "").strip(),
        "international_highlights": str(summary.get("international_highlights", "") or "").strip(),
        "timeline": summary.get("timeline") if isinstance(summary.get("timeline"), list) else [],
        "notable_articles": (
            summary.get("notable_articles") if isinstance(summary.get("notable_articles"), list) else []
        ),
        "gaps_and_limits": str(summary.get("gaps_and_limits", "") or "").strip(),
        "reading_time_minutes": str(summary.get("reading_time_minutes", "") or "").strip(),
        "executive_overview_bullets": (
            [str(x).strip() for x in exec_raw if str(x).strip()]
            if isinstance(exec_raw, list)
            else []
        ),
    }

    chains: list[str] = []
    for key in ("vietnam_highlights", "international_highlights"):
        val = summary.get(key)
        if isinstance(val, str) and val.strip():
            chains.append(val.strip())
        elif isinstance(val, list):
            for item in val:
                line = str(item).strip()
                if line:
                    chains.append(line)
    if len(chains) >= _LIST_MINS["transmission_chains"]:
        out["transmission_chains"] = chains[:8]

    wc_rows: list[dict[str, str]] = []
    for day in summary.get("timeline") or []:
        if not isinstance(day, dict):
            continue
        day_label = str(day.get("date", "") or "").strip() or brief_date
        for headline in (day.get("headlines") or [])[:3]:
            h = str(headline).strip()
            if not h:
                continue
            wc_rows.append(
                {
                    "variable": day_label,
                    "change": h[:280],
                    "meaning": "Sự kiện nổi bật trong cửa sổ tin 48 giờ.",
                }
            )
    if len(wc_rows) >= _LIST_MINS["what_changed"]:
        out["what_changed"] = wc_rows[:6]

    gaps = str(summary.get("gaps_and_limits", "") or "").strip()
    if gaps:
        out["final_decision"] = gaps[:520]

    _migrate_snake_to_global_strategy_v2(out)
    return out


def articles_payload_from_for_ai(path: Path) -> dict[str, Any]:
    """``news_for_ai.json`` / ``news_for_ai_clean.json`` → shape for ``build_all_article_cards``."""
    data = load_json(path)
    articles: list[dict[str, Any]] = []
    for row in data.get("articles") or []:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        text = str(row.get("text") or row.get("content_for_ai") or "").strip()
        articles.append(
            {
                "title": str(row.get("title") or "Tin").strip() or "Tin",
                "url": url,
                "source": str(row.get("source") or "").strip(),
                "category": str(row.get("category") or "").strip(),
                "region": str(row.get("region") or "").strip(),
                "published_at": str(row.get("published_at") or "").strip(),
                "summary": text[:800] if text else "",
                "content_for_ai": text,
            }
        )
    return {
        "generated_at": data.get("generated_at"),
        "count": len(articles),
        "articles": articles,
    }


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
                "vietnam_impact": vn_imp or "Ảnh hưởng qua kênh lãi suất, USD và risk appetite toàn cầu.",
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

    if _is_multisector_digest(summary):
        return _digest_multisector_to_strategy_snake(
            summary, brief_date=brief_date, generated_at=generated_at
        )
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
        ch = vt.get("chains")
        if isinstance(ch, list):
            chains_clean = [str(x).strip() for x in ch if isinstance(x, str) and str(x).strip()]
            if len(chains_clean) >= _LIST_MINS["transmission_chains"]:
                out["transmission_chains"] = chains_clean

    sp = summary.get("scenario_plan")
    if isinstance(sp, dict):
        for case in ("base_case", "bull_case", "bear_case"):
            blk = sp.get(case)
            if not isinstance(blk, dict):
                continue
            for f in ("title", "description", "action"):
                if str(blk.get(f, "")).strip():
                    out["scenario_plan"][case][f] = str(blk[f]).strip()

    if str(summary.get("final_decision", "")).strip():
        out["final_decision"] = str(summary["final_decision"]).strip()
    elif str(summary.get("final_takeaway", "")).strip():
        out["final_decision"] = str(summary["final_takeaway"]).strip()

    tc = summary.get("transmission_chains")
    if isinstance(tc, list):
        chains_clean = [str(x).strip() for x in tc if isinstance(x, str) and str(x).strip()]
        if len(chains_clean) >= _LIST_MINS["transmission_chains"]:
            out["transmission_chains"] = chains_clean

    wc = summary.get("what_changed")
    if isinstance(wc, list):
        rows_wc = []
        for r in wc:
            if not isinstance(r, dict):
                continue
            if all(str(r.get(f, "") or "").strip() for f in ("variable", "change", "meaning")):
                rows_wc.append(
                    {
                        "variable": str(r["variable"]).strip(),
                        "change": str(r["change"]).strip(),
                        "meaning": str(r["meaning"]).strip(),
                    }
                )
        if len(rows_wc) >= _LIST_MINS["what_changed"]:
            out["what_changed"] = rows_wc

    mrs = summary.get("market_regime_score")
    if isinstance(mrs, dict) and isinstance(mrs.get("items"), list):
        items = []
        for it in mrs["items"]:
            if not isinstance(it, dict):
                continue
            if all(str(it.get(f, "") or "").strip() for f in ("axis", "signal")):
                sc = it.get("score", 0)
                try:
                    score_i = int(sc)
                except (TypeError, ValueError):
                    score_i = 0
                items.append(
                    {
                        "axis": str(it["axis"]).strip(),
                        "signal": str(it["signal"]).strip(),
                        "score": score_i,
                    }
                )
        if len(items) >= _LIST_MINS["market_regime_axes"]:
            out["market_regime_score"] = {
                "total_score": int(mrs.get("total_score", 0) or 0),
                "regime": str(mrs.get("regime", "") or "").strip() or out["market_regime_score"]["regime"],
                "items": items,
                "interpretation": str(mrs.get("interpretation", "") or "").strip()
                or out["market_regime_score"]["interpretation"],
            }

    im = summary.get("intermarket_map")
    if isinstance(im, list):
        rows_im = []
        for r in im:
            if not isinstance(r, dict):
                continue
            if all(str(r.get(f, "") or "").strip() for f in ("asset", "state", "action")):
                rows_im.append(
                    {
                        "asset": str(r["asset"]).strip(),
                        "state": str(r["state"]).strip(),
                        "action": str(r["action"]).strip(),
                    }
                )
        if len(rows_im) >= _LIST_MINS["intermarket_map"]:
            out["intermarket_map"] = rows_im

    pa = summary.get("priority_and_avoid")
    if isinstance(pa, dict):
        pr = pa.get("prioritize")
        av = pa.get("avoid_or_be_careful")
        if isinstance(pr, list) and isinstance(av, list):
            pr_o = [
                {"asset": str(r["asset"]).strip(), "reason": str(r["reason"]).strip()}
                for r in pr
                if isinstance(r, dict)
                and str(r.get("asset", "") or "").strip()
                and str(r.get("reason", "") or "").strip()
            ]
            av_o = [
                {"asset": str(r["asset"]).strip(), "reason": str(r["reason"]).strip()}
                for r in av
                if isinstance(r, dict)
                and str(r.get("asset", "") or "").strip()
                and str(r.get("reason", "") or "").strip()
            ]
            if len(pr_o) >= 5 and len(av_o) >= 5:
                out["priority_and_avoid"] = {"prioritize": pr_o, "avoid_or_be_careful": av_o}

    ip = summary.get("intraday_playbook")
    if isinstance(ip, list):
        rows_ip = []
        for r in ip:
            if not isinstance(r, dict):
                continue
            if all(str(r.get(f, "") or "").strip() for f in ("market_condition", "action")):
                rows_ip.append(
                    {
                        "market_condition": str(r["market_condition"]).strip(),
                        "action": str(r["action"]).strip(),
                    }
                )
        if len(rows_ip) >= _LIST_MINS["intraday_playbook"]:
            out["intraday_playbook"] = rows_ip

    vct = summary.get("view_change_triggers")
    if isinstance(vct, dict):
        mp = vct.get("more_positive_if")
        mn = vct.get("more_negative_if")
        if isinstance(mp, list) and isinstance(mn, list):
            mp_o = [str(x).strip() for x in mp if isinstance(x, str) and str(x).strip()]
            mn_o = [str(x).strip() for x in mn if isinstance(x, str) and str(x).strip()]
            if len(mp_o) >= 3 and len(mn_o) >= 3:
                out["view_change_triggers"] = {"more_positive_if": mp_o, "more_negative_if": mn_o}

    gmd = summary.get("global_macro_drivers")
    if isinstance(gmd, list):
        rows_g = []
        for r in gmd:
            if not isinstance(r, dict):
                continue
            t = str(r.get("title", "") or "").strip()
            a = str(r.get("analysis", "") or "").strip()
            mi = str(r.get("market_impact", "") or r.get("vietnam_impact", "") or "").strip()
            if t and a and mi:
                rows_g.append({"title": t, "analysis": a, "market_impact": mi})
        if len(rows_g) >= _LIST_MINS["global_macro_drivers"]:
            out["global_macro_drivers"] = rows_g

    qa = summary.get("quick_actions")
    if isinstance(qa, list):
        rows = [
            r
            for r in qa
            if isinstance(r, dict)
            and str(r.get("investor_state", "") or "").strip()
            and str(r.get("action", "") or "").strip()
        ]
        if len(rows) >= _LIST_MINS["quick_actions"]:
            out["quick_actions"] = rows

    ag = summary.get("allocation_guide")
    if isinstance(ag, list):
        rows_a = []
        for r in ag:
            if not isinstance(r, dict):
                continue
            prof = str(r.get("profile", "") or "").strip()
            st = str(r.get("stocks", "") or "").strip()
            ca = str(r.get("cash", "") or "").strip()
            gd = str(r.get("gold_defense", "") or "").strip()
            cr = str(r.get("crypto_high_risk", "") or "").strip()
            lev = str(r.get("leverage", "") or r.get("margin", "") or "").strip()
            if prof and st and ca and lev:
                rows_a.append(
                    {
                        "profile": prof,
                        "stocks": st,
                        "cash": ca,
                        "gold_defense": gd or "—",
                        "crypto_high_risk": cr or "—",
                        "leverage": lev,
                    }
                )
        if len(rows_a) >= _LIST_MINS["allocation_guide"]:
            out["allocation_guide"] = rows_a

    for key, fields in (
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
    """Chuyển summary snake_case (final_summary) sang camelCase cho landing page (v2)."""
    pub = snake.get("publication_intro", {})
    mt = snake.get("main_thesis", {})
    sp = snake.get("scenario_plan", {})
    mrs = snake.get("market_regime_score", {})
    pa = snake.get("priority_and_avoid", {})
    vct = snake.get("view_change_triggers", {})

    mscore_items = []
    if isinstance(mrs, dict) and isinstance(mrs.get("items"), list):
        for it in mrs["items"]:
            if not isinstance(it, dict):
                continue
            try:
                sc = int(it.get("score", 0) or 0)
            except (TypeError, ValueError):
                sc = 0
            mscore_items.append(
                {
                    "axis": str(it.get("axis", "") or ""),
                    "signal": str(it.get("signal", "") or ""),
                    "score": sc,
                }
            )

    pri = pa.get("prioritize") if isinstance(pa, dict) else []
    avo = pa.get("avoid_or_be_careful") if isinstance(pa, dict) else []

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
        "whatChanged": [
            {
                "variable": str(r.get("variable", "") or ""),
                "change": str(r.get("change", "") or ""),
                "meaning": str(r.get("meaning", "") or ""),
            }
            for r in snake.get("what_changed", [])
            if isinstance(r, dict)
        ],
        "marketRegimeScore": {
            "totalScore": int(mrs.get("total_score", 0) or 0) if isinstance(mrs, dict) else 0,
            "regime": str(mrs.get("regime", "") or "") if isinstance(mrs, dict) else "",
            "items": mscore_items,
            "interpretation": str(mrs.get("interpretation", "") or "") if isinstance(mrs, dict) else "",
        },
        "globalMacroDrivers": [
            {
                "title": r.get("title", ""),
                "analysis": r.get("analysis", ""),
                "marketImpact": str(
                    r.get("market_impact", "") or r.get("vietnam_impact", "") or "",
                ),
            }
            for r in snake.get("global_macro_drivers", [])
            if isinstance(r, dict)
        ],
        "intermarketMap": [
            {
                "asset": str(r.get("asset", "") or ""),
                "state": str(r.get("state", "") or ""),
                "action": str(r.get("action", "") or ""),
            }
            for r in snake.get("intermarket_map", [])
            if isinstance(r, dict)
        ],
        "transmissionChains": [
            str(x) for x in (snake.get("transmission_chains") or []) if isinstance(x, str)
        ],
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
                "goldDefense": str(r.get("gold_defense", "") or r.get("goldDefense", "") or ""),
                "cryptoHighRisk": str(r.get("crypto_high_risk", "") or r.get("cryptoHighRisk", "") or ""),
                "leverage": str(r.get("leverage", "") or r.get("margin", "") or ""),
            }
            for r in snake.get("allocation_guide", [])
            if isinstance(r, dict)
        ],
        "priorityAndAvoid": {
            "prioritize": [
                {"asset": str(r.get("asset", "") or ""), "reason": str(r.get("reason", "") or "")}
                for r in (pri if isinstance(pri, list) else [])
                if isinstance(r, dict)
            ],
            "avoidOrBeCareful": [
                {"asset": str(r.get("asset", "") or ""), "reason": str(r.get("reason", "") or "")}
                for r in (avo if isinstance(avo, list) else [])
                if isinstance(r, dict)
            ],
        },
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
        "intradayPlaybook": [
            {
                "marketCondition": str(r.get("market_condition", "") or ""),
                "action": str(r.get("action", "") or ""),
            }
            for r in snake.get("intraday_playbook", [])
            if isinstance(r, dict)
        ],
        "scenarioPlan": _camel_case_scenario_plan(sp if isinstance(sp, dict) else {}),
        "viewChangeTriggers": {
            "morePositiveIf": [
                str(x)
                for x in (
                    (vct.get("more_positive_if") or [])
                    if isinstance(vct, dict)
                    else []
                )
                if isinstance(x, str) and x.strip()
            ],
            "moreNegativeIf": [
                str(x)
                for x in (
                    (vct.get("more_negative_if") or [])
                    if isinstance(vct, dict)
                    else []
                )
                if isinstance(x, str) and x.strip()
            ],
        },
        "finalDecision": str(snake.get("final_decision", "") or ""),
    }


def public_payload_to_snake_summary(content: dict[str, Any]) -> dict[str, Any]:
    """Từ content.json (camelCase public) suy ra object summary snake_case cho final_summary.json."""
    pub = content.get("publicationIntro") if isinstance(content.get("publicationIntro"), dict) else {}
    mt = content.get("mainThesis") if isinstance(content.get("mainThesis"), dict) else {}
    mrs = content.get("marketRegimeScore") if isinstance(content.get("marketRegimeScore"), dict) else {}
    pa = content.get("priorityAndAvoid") if isinstance(content.get("priorityAndAvoid"), dict) else {}
    sp = content.get("scenarioPlan") if isinstance(content.get("scenarioPlan"), dict) else {}
    vct = content.get("viewChangeTriggers") if isinstance(content.get("viewChangeTriggers"), dict) else {}

    mscore_items = []
    if isinstance(mrs.get("items"), list):
        for it in mrs["items"]:
            if not isinstance(it, dict):
                continue
            try:
                sc = int(it.get("score", 0) or 0)
            except (TypeError, ValueError):
                sc = 0
            mscore_items.append(
                {
                    "axis": str(it.get("axis", "") or ""),
                    "signal": str(it.get("signal", "") or ""),
                    "score": sc,
                }
            )

    pri = pa.get("prioritize") if isinstance(pa.get("prioritize"), list) else []
    avo = pa.get("avoidOrBeCareful") if isinstance(pa.get("avoidOrBeCareful"), list) else []

    def _scen_brief(case_camel: str) -> dict[str, str]:
        blk = sp.get(case_camel) if isinstance(sp.get(case_camel), dict) else {}
        return {
            "title": str(blk.get("title", "") or ""),
            "description": str(blk.get("description", "") or ""),
            "action": str(blk.get("action", "") or ""),
        }

    em = content.get("editorialMeta") if isinstance(content.get("editorialMeta"), dict) else {}
    title = str(em.get("briefTitle", "") or "").strip() or "LEON Quant Labs — Global Market Strategy Brief"
    brief_date = str(em.get("briefDate", "") or "").strip()
    if not brief_date:
        ga = str(content.get("generatedAt", "") or "")
        brief_date = ga[:10] if len(ga) >= 10 else ""

    return {
        "title": title,
        "date": brief_date,
        "generated_at": str(content.get("generatedAt", "") or ""),
        "publication_intro": {
            "headline": str(pub.get("headline", "") or ""),
            "description": str(pub.get("description", "") or ""),
        },
        "main_thesis": {
            "regime": str(mt.get("regime", "") or ""),
            "thesis": str(mt.get("thesis", "") or ""),
            "action_conclusion": str(mt.get("actionConclusion", "") or ""),
        },
        "what_changed": [
            {
                "variable": str(r.get("variable", "") or ""),
                "change": str(r.get("change", "") or ""),
                "meaning": str(r.get("meaning", "") or ""),
            }
            for r in content.get("whatChanged", [])
            if isinstance(r, dict)
        ],
        "market_regime_score": {
            "total_score": int(mrs.get("totalScore", 0) or 0),
            "regime": str(mrs.get("regime", "") or ""),
            "items": mscore_items,
            "interpretation": str(mrs.get("interpretation", "") or ""),
        },
        "global_macro_drivers": [
            {
                "title": str(r.get("title", "") or ""),
                "analysis": str(r.get("analysis", "") or ""),
                "market_impact": str(r.get("marketImpact", "") or ""),
            }
            for r in content.get("globalMacroDrivers", [])
            if isinstance(r, dict)
        ],
        "intermarket_map": [
            {
                "asset": str(r.get("asset", "") or ""),
                "state": str(r.get("state", "") or ""),
                "action": str(r.get("action", "") or ""),
            }
            for r in content.get("intermarketMap", [])
            if isinstance(r, dict)
        ],
        "transmission_chains": [
            str(x) for x in (content.get("transmissionChains") or []) if isinstance(x, str)
        ],
        "quick_actions": [
            {
                "investor_state": str(r.get("investorState", "") or ""),
                "action": str(r.get("action", "") or ""),
            }
            for r in content.get("quickActions", [])
            if isinstance(r, dict)
        ],
        "allocation_guide": [
            {
                "profile": str(r.get("profile", "") or ""),
                "stocks": str(r.get("stocks", "") or ""),
                "cash": str(r.get("cash", "") or ""),
                "gold_defense": str(r.get("goldDefense", "") or ""),
                "crypto_high_risk": str(r.get("cryptoHighRisk", "") or ""),
                "leverage": str(r.get("leverage", "") or ""),
            }
            for r in content.get("allocationGuide", [])
            if isinstance(r, dict)
        ],
        "priority_and_avoid": {
            "prioritize": [
                {"asset": str(r.get("asset", "") or ""), "reason": str(r.get("reason", "") or "")}
                for r in pri
                if isinstance(r, dict)
            ],
            "avoid_or_be_careful": [
                {"asset": str(r.get("asset", "") or ""), "reason": str(r.get("reason", "") or "")}
                for r in avo
                if isinstance(r, dict)
            ],
        },
        "increase_risk_signals": [
            {"signal": str(r.get("signal", "") or ""), "meaning": str(r.get("meaning", "") or "")}
            for r in content.get("increaseRiskSignals", [])
            if isinstance(r, dict)
        ],
        "reduce_risk_signals": [
            {"signal": str(r.get("signal", "") or ""), "action": str(r.get("action", "") or "")}
            for r in content.get("reduceRiskSignals", [])
            if isinstance(r, dict)
        ],
        "intraday_playbook": [
            {
                "market_condition": str(r.get("marketCondition", "") or ""),
                "action": str(r.get("action", "") or ""),
            }
            for r in content.get("intradayPlaybook", [])
            if isinstance(r, dict)
        ],
        "scenario_plan": {
            "base_case": _scen_brief("baseCase"),
            "bull_case": _scen_brief("bullCase"),
            "bear_case": _scen_brief("bearCase"),
        },
        "view_change_triggers": {
            "more_positive_if": [
                str(x)
                for x in (vct.get("morePositiveIf") or [])
                if isinstance(x, str) and x.strip()
            ],
            "more_negative_if": [
                str(x)
                for x in (vct.get("moreNegativeIf") or [])
                if isinstance(x, str) and x.strip()
            ],
        },
        "final_decision": str(content.get("finalDecision", "") or ""),
    }


def build_payload(
    final_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    all_articles: list[dict[str, Any]],
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

    from_digest = _is_multisector_digest(raw_summary)
    snake = coerce_summary_to_strategy_brief(
        raw_summary,
        brief_date=brief_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        generated_at=generated_at,
    )
    snake = sanitize_strategy_brief_snake(snake, multisector_digest=from_digest)
    brief = strategy_brief_to_public_json(snake)
    meta = final_payload.get("meta") if isinstance(final_payload.get("meta"), dict) else {}

    payload: dict[str, Any] = {
        "siteTitle": "LEON Quant Labs",
        "sectionLabel": (
            "Toàn cảnh tin tức 48 giờ"
            if from_digest
            else "Global Market Strategy Brief"
        ),
        **(
            {
                "digestHeroBlurb": (
                    "Trang tổng hợp tin tức thế giới và Việt Nam trong 48 giờ qua."
                ),
                "digestReportTitle": "Tổng hợp tin tức toàn cầu và Việt Nam (48 giờ)",
            }
            if from_digest
            else {}
        ),
        "generatedAt": generated_at,
        "schemaVersion": "global-market-strategy-brief-v2",
        **brief,
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
    }
    if from_digest:
        payload["briefMode"] = "multisector-digest"
        digest_pub = snake.get("_digest_public") if isinstance(snake.get("_digest_public"), dict) else {}
        if digest_pub.get("vietnam_highlights"):
            payload["digestVietnamHighlights"] = digest_pub["vietnam_highlights"]
        if digest_pub.get("international_highlights"):
            payload["digestInternationalHighlights"] = digest_pub["international_highlights"]
        if digest_pub.get("gaps_and_limits"):
            payload["digestGapsAndLimits"] = digest_pub["gaps_and_limits"]
        exec_bullets = digest_pub.get("executive_overview_bullets")
        if isinstance(exec_bullets, list) and exec_bullets:
            payload["digestExecutiveBullets"] = _dedupe_preserve_order(
                [str(x).strip() for x in exec_bullets],
            )
        else:
            overview = str((brief.get("mainThesis") or {}).get("thesis") or "").strip()
            if overview:
                payload["digestExecutiveBullets"] = _prose_to_bullet_lines(overview)
        intl_bullets = _prose_to_bullet_lines(str(digest_pub.get("international_highlights") or ""))
        if intl_bullets:
            payload["digestInternationalBullets"] = intl_bullets
        vn_bullets = _dedupe_preserve_order(
            _prose_to_bullet_lines(str(digest_pub.get("vietnam_highlights") or ""))
            + _vietnam_overview_extra_bullets(overview),
        )
        if vn_bullets:
            payload["digestVietnamBullets"] = vn_bullets
        notable = digest_pub.get("notable_articles")
        if isinstance(notable, list) and notable:
            by_url = {
                str(art.get("url") or "").strip(): art
                for art in all_articles
                if str(art.get("url") or "").strip()
            }
            notable_out: list[dict[str, str]] = []
            for a in notable:
                if not isinstance(a, dict):
                    continue
                u = str(a.get("url") or "").strip()
                art = by_url.get(u) if u else None
                img = str(art.get("image_url") or "").strip() if art else ""
                row_out: dict[str, str] = {
                    "title": str(a.get("title", "") or ""),
                    "source": str(a.get("source", "") or ""),
                    "url": u,
                    "whyNotable": str(a.get("why_notable", "") or ""),
                    "imageUrl": img,
                }
                tier = str(a.get("priority_tier") or "").strip()
                if tier:
                    row_out["priorityTier"] = tier
                notable_out.append(row_out)
            payload["digestNotableArticles"] = notable_out[:DIGEST_MAX_NOTABLE_ARTICLES]
        extras = build_digest_web_extras(raw_summary, all_articles)
        payload.update(extras)
        n_sectors = len(extras.get("digestSectors") or [])
        n_links = len(extras.get("digestLinkIndex") or [])
        print(
            f"Digest brief: {n_sectors} sector(s), {n_links} digest link(s), "
            f"{len(extras.get('articleLinkIndex') or [])} article link(s) (text-only UI)."
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build content.json from gemini_digest_summary.json + news_for_ai_clean.json.",
    )
    parser.add_argument(
        "--digest-input",
        type=Path,
        default=DEFAULT_DIGEST_FILE,
        help="gemini_digest_summary.json",
    )
    parser.add_argument(
        "--enriched-input",
        default=str(DEFAULT_ENRICHED_FILE),
        help="news_for_ai_clean.json (or news_for_ai.json)",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to content.json")
    parser.add_argument(
        "--metadata-timeout",
        type=int,
        default=10,
        help="Seconds per URL when fetching og:image/description",
    )
    parser.add_argument("--skip-images", action="store_true", help="Do not fetch og metadata (faster)")
    args = parser.parse_args()

    final_path = Path(args.digest_input)
    articles_path = Path(args.enriched_input)
    if articles_path.name.startswith("news_for_ai"):
        enriched_payload = articles_payload_from_for_ai(articles_path)
    else:
        enriched_payload = load_json(articles_path)
    final_payload = load_json(final_path)
    all_cards = build_all_article_cards(
        enriched_payload,
        not args.skip_images,
        args.metadata_timeout,
    )
    payload = build_payload(final_payload, enriched_payload, all_cards)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(all_cards)} article cards -> {args.output}")
    return 0


def rebuild_content_from_digest(
    digest_path: Path,
    articles_path: Path,
    output_path: Path,
    *,
    fetch_images: bool = True,
    metadata_timeout: int = 6,
) -> int:
    """``gemini_digest_summary.json`` + ``news_for_ai_clean.json`` → ``content.json``."""
    final_payload = load_json(digest_path)
    articles_path = articles_path.resolve()
    if articles_path.name.startswith("news_for_ai"):
        enriched_payload = articles_payload_from_for_ai(articles_path)
    else:
        enriched_payload = load_json(articles_path)
    all_cards = build_all_article_cards(
        enriched_payload,
        fetch_images,
        metadata_timeout,
    )
    payload = build_payload(final_payload, enriched_payload, all_cards)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(all_cards)


if __name__ == "__main__":
    raise SystemExit(main())
