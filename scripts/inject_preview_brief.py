"""Bổ sung field brief mới vào final_summary.json từ dữ liệu sẵn có (không gọi GPT) để preview UI."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
FINAL_JSON = PROJECT / "final_summary.json"


def main() -> int:
    if not FINAL_JSON.is_file():
        print("Missing final_summary.json", file=sys.stderr)
        return 1
    data = json.loads(FINAL_JSON.read_text(encoding="utf-8"))
    s = data.get("summary")
    if not isinstance(s, dict):
        print("Invalid summary", file=sys.stderr)
        return 1

    gw = str(s.get("global_watch") or "").strip()
    vw = str(s.get("vietnam_watch") or "").strip()
    if gw and not str(s.get("macro_world") or "").strip():
        s["macro_world"] = gw
    if vw and not str(s.get("vietnam_macro") or "").strip():
        s["vietnam_macro"] = vw

    s.setdefault(
        "so_what_chain",
        "Fed giữ lãi cao + dữ liệu việc làm Mỹ vượt kỳ vọng → USD/DXY củng cố → "
        "áp lực lên USD/VND và vàng (chốt lời); can thiệp JPY bình ổn ngắn hạn nhưng "
        "spread lãi suất vẫn nghiêng về USD; risk địa chính trị đẩy biến động dầu/hàng hóa.",
    )
    s.setdefault(
        "world_to_vietnam",
        "Khi USD global mạnh và risk-off, SBV có xu hướng quản lý tỷ giá linh hoạt và giữ ổn định kỳ vọng; "
        "lãi suất trong nước và thanh khoản NH vẫn là kênh truyền đầu tiên lên TTCK và tín dụng.",
    )
    s.setdefault(
        "asset_impacts",
        [
            {
                "asset": "Vàng",
                "bias": "mixed",
                "note": "Áp lực từ USD nhưng rủi ro địa chính trị vẫn hỗ trợ kênh phòng thủ ngắn hạn.",
            },
            {
                "asset": "USD / DXY",
                "bias": "bullish",
                "note": "Dữ liệu lao động mạnh hơn dự báo củng cố kịch bản Fed chậm nới.",
            },
            {
                "asset": "USD/VND",
                "bias": "bullish",
                "note": "Dollar mạnh toàn cầu thường tạo nhịp căng margin tỷ giá; theo dõi can thiệp/sẵn sàng ngoại tệ.",
            },
            {
                "asset": "TTCK VN",
                "bias": "mixed",
                "note": "Nhịp nâng hạng / tăng vốn CK tích cực trung hạn nhưng nhóm vốn hóa và nợ xấu NH phân hóa ngắn hạn.",
            },
        ],
    )
    s.setdefault(
        "macro_heat_labels",
        [
            {"label": "US yields / Fed path", "sentiment": "hot"},
            {"label": "JPY intervention", "sentiment": "warm"},
            {"label": "Oil / Hormuz risk", "sentiment": "hot"},
            {"label": "VN – bank NPL", "sentiment": "warm"},
            {"label": "VN – upgrade / margin", "sentiment": "cool"},
        ],
    )
    s.setdefault(
        "actual_vs_forecast",
        [
            {
                "indicator": "NFP Mỹ (tháng 4, khu vực tư)",
                "actual": "115k",
                "forecast": "62k",
                "actual_pct": 92,
                "forecast_pct": 50,
            }
        ],
    )
    risks = s.get("risks_to_watch")
    if isinstance(risks, list) and len(risks) > 3:
        s["risks_to_watch"] = risks[:3]

    # Mẫu layout "desk note" — pipeline GPT sẽ thay bằng output thật.
    s["title"] = "LEON Quant Labs — Daily Macro Brief"
    s["executive_summary"] = ""
    s["thirty_second_summary"] = (
        "Thị trường hôm nay bị chi phối bởi 3 biến số chính: dầu tăng vì căng thẳng Mỹ–Iran, "
        "kỳ vọng Fed hạ lãi suất bị đẩy lùi, và USD giữ sức mạnh tương đối. Brent được Reuters ghi nhận "
        "quanh vùng trên 103–105 USD/thùng sau khi tiến trình hòa đàm Mỹ–Iran bế tắc, làm dấy lên lo ngại "
        "lạm phát năng lượng kéo dài. Vàng giảm khoảng 1%, chịu áp lực từ USD mạnh và môi trường lãi suất "
        "cao lâu hơn. Tại Việt Nam, VN-Index vẫn quanh vùng cao, nhưng dòng tiền chưa lan tỏa đều; "
        "thị trường có dấu hiệu “xanh vỏ, đỏ lòng”, phụ thuộc nhiều vào nhóm vốn hóa lớn."
    )
    s["brief_stories"] = [
        {
            "headline": "Căng thẳng Mỹ–Iran đẩy dầu tăng mạnh",
            "body": (
                "Giá dầu tăng sau khi Tổng thống Donald Trump bác phản hồi của Iran đối với đề xuất "
                "hòa bình của Mỹ, khiến thị trường e ngại xung đột Trung Đông kéo dài và nguồn cung năng "
                "lượng tiếp tục bị gián đoạn. Reuters ghi nhận Brent tăng khoảng 3.6% lên 104.94 USD/thùng; "
                "Guardian ghi nhận có lúc Brent lên khoảng 105.50 USD/thùng trước khi hạ về khoảng 103.50 USD/thùng."
            ),
            "so_what": (
                "Dầu cao là biến số cực kỳ quan trọng vì nó có thể kéo lạm phát quay lại. Khi lạm phát năng "
                "lượng tăng, Fed sẽ khó hạ lãi suất sớm. Điều này thường tạo áp lực lên vàng, crypto, trái "
                "phiếu và các thị trường mới nổi."
            ),
            "assets": "Dầu, USD, vàng, trái phiếu Mỹ, chứng khoán mới nổi, Việt Nam.",
            "impact_level": "Cao",
        },
        {
            "headline": "Fed có thể giữ lãi suất cao lâu hơn",
            "body": (
                "BofA và Goldman Sachs đều lùi kỳ vọng Fed hạ lãi suất vì rủi ro lạm phát từ năng lượng và "
                "thị trường lao động Mỹ vẫn vững. BofA hiện dự báo không có đợt cắt giảm lãi suất nào trong "
                "năm 2026; Goldman lùi kỳ vọng cắt giảm từ tháng 9/2026 sang 12/2026 và 3/2027. Reuters ghi "
                "nhận số việc làm phi nông nghiệp tháng 4 tăng 115,000, gần gấp đôi kỳ vọng."
            ),
            "so_what": (
                "Khi Fed giữ lãi suất cao, dòng tiền toàn cầu thường ưu tiên USD và tài sản sinh lợi an toàn "
                "hơn. Không thuận lợi cho vàng, crypto và thị trường mới nổi. Với Việt Nam, áp lực có thể "
                "đi qua tỷ giá, dòng vốn ngoại và chi phí vốn."
            ),
            "assets": "USD, vàng, crypto, cổ phiếu tăng trưởng, VN-Index, ngân hàng.",
            "impact_level": "Cao",
        },
        {
            "headline": "USD giữ sức mạnh, gây áp lực lên tài sản rủi ro",
            "body": (
                "Reuters ghi nhận Dollar Index quanh 97.995 trong bối cảnh thận trọng vì Trung Đông và kỳ "
                "vọng Fed chưa hạ lãi suất sớm. USD mạnh khiến vàng đắt hơn với NĐT ngoài Mỹ, đồng thời tạo "
                "áp lực lên các đồng tiền thị trường mới nổi."
            ),
            "so_what": (
                "USD mạnh thường là tín hiệu phòng thủ. Với Việt Nam, theo dõi USD/VND, SBV và khối ngoại. "
                "Nếu USD tiếp tục mạnh, nhóm nhập khẩu, DN vay ngoại tệ hoặc nhóm nhạy cảm lãi suất có thể "
                "chịu áp lực."
            ),
            "assets": "USD/VND, VN-Index, ngân hàng, bất động sản, xuất nhập khẩu.",
            "impact_level": "Trung bình đến cao",
        },
        {
            "headline": "Vàng giảm dù rủi ro địa chính trị tăng",
            "body": (
                "Thông thường căng thẳng hỗ trợ vàng, nhưng hôm nay vàng giảm vì thị trường tập trung "
                "dầu cao → lạm phát cao → Fed giữ lãi suất cao. Reuters ghi nhận vàng giao ngay giảm khoảng "
                "1% về 4,667.99 USD/oz; hợp đồng tương lai Mỹ giảm 1.1% về 4,677.80 USD/oz."
            ),
            "so_what": (
                "Vàng không chỉ phụ thuộc “sợ hãi”; còn chịu ảnh hưởng mạnh từ USD, lợi suất thực và kỳ vọng "
                "lãi suất. Nếu USD và lợi suất còn mạnh, vàng có thể bị chốt lời dù rủi ro địa chính trị "
                "chưa hết."
            ),
            "assets": "Vàng, USD, trái phiếu Mỹ, cổ phiếu khai khoáng.",
            "impact_level": "Trung bình đến cao",
        },
        {
            "headline": "Việt Nam: VN-Index cao nhưng dòng tiền chưa lan tỏa",
            "body": (
                "Bàn về biên độ 1.880–1.920 và đỉnh mới quanh 1.921.29 điểm; độ rộng chưa khỏe, báo chí mô "
                "tả ‘xanh vỏ, đỏ lòng’, VIC/VHM hỗ trợ chỉ số trong khi nhiều mã chịu áp lực bán."
            ),
            "so_what": (
                "VN-Index ở vùng nhạy cảm: chỉ số có thể đẹp nhờ vốn hóa lớn, nhưng nếu dòng tiền không lan "
                "tỏa, rủi ro điều chỉnh kỹ thuật tăng. Nên xem độ rộng, thanh khoản, khối ngoại và nhóm "
                "dẫn dắt, không chỉ điểm số."
            ),
            "assets": "VN-Index, VIC, VHM, ngân hàng, chứng khoán, bất động sản.",
            "impact_level": "Trung bình",
        },
    ]
    s["asset_impact_table"] = [
        {"group": "Dầu", "impact_today": "Tích cực mạnh", "main_reason": "Căng thẳng Mỹ–Iran, rủi ro nguồn cung"},
        {"group": "USD", "impact_today": "Tích cực", "main_reason": "Fed có thể giữ lãi suất cao lâu hơn"},
        {"group": "Vàng", "impact_today": "Tiêu cực ngắn hạn", "main_reason": "USD mạnh, lãi suất cao làm vàng kém hấp dẫn"},
        {"group": "Crypto", "impact_today": "Tiêu cực nhẹ/trung bình", "main_reason": "Risk-off, lãi suất cao"},
        {"group": "Chứng khoán Mỹ", "impact_today": "Trung tính/Thận trọng", "main_reason": "AI hỗ trợ nhưng dầu & lãi suất gây áp lực"},
        {"group": "VN-Index", "impact_today": "Trung tính/Thận trọng", "main_reason": "Chỉ số cao, dòng tiền chưa lan tỏa"},
        {"group": "Ngân hàng Việt Nam", "impact_today": "Theo dõi", "main_reason": "Nhạy lãi suất, tỷ giá, dòng tiền"},
        {"group": "Bất động sản", "impact_today": "Thận trọng", "main_reason": "Chi phí vốn và tâm lý thị trường"},
    ]

    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    FINAL_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {FINAL_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
