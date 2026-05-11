"""Inject Macro Intelligence schema vào final_summary.json để preview UI / test validator (không gọi GPT)."""
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

    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")

    s["title"] = "LEON Quant Labs — Daily Macro Intelligence"
    s["date"] = day
    s["generated_at"] = now.isoformat()
    s["market_regime"] = {
        "regime": "Risk-off có chọn lọc — áp lực từ giá năng lượng và lãi suất thự",
        "primary_driver": "Fed giữ lãi suất đỉnh lâu hơn kỳ vọng; năng lượng toàn cầu biến động",
        "secondary_driver": "USD ổn định tương đối mạnh; rủi ro địa chính trị Trung Đông",
        "risk_tone": "Thận trọng; ưu tiên hedging thanh khoản",
        "confidence": "Medium",
        "invalidation": "Dữ liệu lạm phát Mỹ mềm đi rõ rệt + tín hiệu nới Fed sớm; dầu hạ nhiệt bền.",
    }
    s["daily_thesis"] = (
        "Trong ngày, xung đột kỳ vọng chính là giữa (i) rủi ro cung năng lượng đẩy lạm phát "
        "và (ii) thị trường vẫn định giá khả năng Fed chậm hạ lãi. Dòng vốn toàn cầu nghiêng "
        "phòng thủ; với Việt Nam, kênh USD/VND–khối ngoại–lãi suất nội địa là trọng tâm."
    )
    s["thirty_second_summary"] = (
        "Thị trường chú ý dầu và rủi ro cung sau căng thẳng Mỹ–Iran; đồng thời dữ liệu lao động Mỹ "
        "ủng hộ kịch bản Fed không vội nới. USD tương đối mạnh tạo áp lực lên vàng và tài sản rủi ro. "
        "Việt Nam: VN-Index có thể giữ nhịp nhưng độ rộng và dòng tiền bắt buộc phải theo dõi."
    )
    s["what_changed"] = (
        "Kỳ vọng đường cong Fed trong ngày dịch chuyển thận trọng hơn sau dữ liệu cứng về lao động; "
        "song song, oil curve phản ánh risk premium địa chính trị. TTCK VN phân hóa mạnh dù chỉ số đỉnh."
    )
    s["top_macro_drivers"] = [
        {
            "headline": "Năng lượng & risk premium địa chính trị",
            "fact": "Theo các bản tin trong evidence, giá dầu/Brent biến động mạnh quanh vùng được thảo luận rộng sau căng thẳng Mỹ–Iran (Reuters, Guardian được trích trong pipeline trước đó).",
            "why_it_matters": "Năng lượng là kênh truyền nhanh nhất vào lạm phát kỳ vọng và positioning risk-off.",
            "transmission_chain": ["Shock cung dầu", "Brent/rủi ro Hormuz", "Lạm phát kỳ vọng", "Fed path", "Dòng vốn"],
            "assets_affected": ["Dầu", "Lạm phát", "USD", "Vàng", "EM risk"],
            "time_horizon": "1-2 weeks",
            "confidence": {"fact": "Medium", "impact": "High"},
            "what_could_prove_this_wrong": "Đột phá ngoại giao làm dịu premium hoặc OPEC+ điều chỉnh kỳ vọng cung.",
        },
        {
            "headline": "Fed & labor market: 'higher for longer' quay lại pricing",
            "fact": "Evidence từ tin Việt Nam về USD sau bảng lương phi nông nghiệp (NFP) mạnh hơn dự báo (115k vs 62k trong các trích dẫn nội bộ pipeline).",
            "why_it_matters": "Thị trường lao động cứng củng cố Fed hawkish → real yield → áp lực vàng/tài sản dài hạn.",
            "transmission_chain": ["NFP vượt forecast", "FedSpeak/hiện trạng", "Real yields", "USD", "VN FX-sensitive"],
            "assets_affected": ["UST", "USD", "Vàng", "Growth stocks"],
            "time_horizon": "1-3 months",
            "confidence": {"fact": "Medium", "impact": "High"},
            "what_could_prove_this_wrong": "Dữ liệu CPI/PCE yếu hoặc tín hiệu slack lao động tăng trong các báo cáo tiếp theo.",
        },
        {
            "headline": "Japan FX intervention & global spillovers",
            "fact": "Tin CafeBiz/VietnamBiz trong evidence đề cập can thiệp FX Nhật (ước lượng quy mô lớn trong một ngày).",
            "why_it_matters": "Pha bình ổn FX có thể tạm thời thay đổi dòng carry, song spread lãi suất USD–JPY vẫn là trục chính.",
            "transmission_chain": ["BoJ/MoF", "USDJPY", "Risk sentiment", "Carry trades", "EM flows"],
            "assets_affected": ["JPY", "USDJPY", "Global risk"],
            "time_horizon": "1-5 days",
            "confidence": {"fact": "Medium", "impact": "Medium"},
            "what_could_prove_this_wrong": "Chính sách đồng bộ Fed–BoJ hoặc biến động thận trọng đột ngột từ thị trường.",
        },
        {
            "headline": "Vietnam: nợ xấu NH & phân hóa TTCK",
            "fact": "VietnamBiz trong evidence: nợ xấu hệ thống tăng mạnh trong Q1 và phân hóa bao phủ; song song có narrative tăng vốn/ nâng hạng CK.",
            "why_it_matters": "Chất lượng tín dụng là trần trung hạn cho margin hệ thống; TTCK có thể tách nhịp khỏi vĩ mô nếu dòng tiền chỉ tập trung bluechip.",
            "transmission_chain": ["NPL ↑", "Chi phí vốn NH", "Tín dụng", "Kỳ vọng lợi nhuận", "Breadth VN-Index"],
            "assets_affected": ["Cổ bank", "VN-Index", "Broker"],
            "time_horizon": "1-3 months",
            "confidence": {"fact": "Medium", "impact": "Medium"},
            "what_could_prove_this_wrong": "Xử lý nợ/xóa mạnh hoặc credit growth phục hồi có kiểm soát trong báo cáo quý tiếp theo.",
        },
    ]
    s["asset_impact_heatmap"] = [
        {"asset": "Dầu Brent", "direction": "Bullish", "strength": "High", "horizon": "1-2 weeks", "main_reason": "Risk premium địa chính trị + kênh lạm phát.", "watch_risk": "Đàm phán đột phá."},
        {"asset": "USD (DXY)", "direction": "Bullish", "strength": "Medium", "horizon": "1-5 days", "main_reason": "Labor cứng → Fed path thận trọng.", "watch_risk": "Dữ liệu lạm phát mềm."},
        {"asset": "Vàng", "direction": "Mixed", "strength": "Medium", "horizon": "1-5 days", "main_reason": "Risk-off vs real yield cao.", "watch_risk": "Chốt lời kỹ thuật."},
        {"asset": "UST 10Y (lợi suất)", "direction": "Bullish", "strength": "Medium", "horizon": "1-2 weeks", "main_reason": "Pricing hawkish hơn.", "watch_risk": "Flight-to-quality bid."},
        {"asset": "VN-Index", "direction": "Mixed", "strength": "Medium", "horizon": "1-5 days", "main_reason": "Phân hóa; bluechip gánh chỉ số.", "watch_risk": "Breadth yếu."},
        {"asset": "USD/VND", "direction": "Mixed", "strength": "High", "horizon": "1-2 weeks", "main_reason": "Kênh truyền trực tiếp từ USD global.", "watch_risk": "Can thiệp/ kỳ vọng SBV."},
        {"asset": "Cổ ngân hàng VN", "direction": "Mixed", "strength": "Medium", "horizon": "1-3 months", "main_reason": "NPL & chi phí vốn.", "watch_risk": "Tín hiệu xử lý nợ."},
        {"asset": "Crypto", "direction": "Bearish", "strength": "Low", "horizon": "1-5 days", "main_reason": "Liquidity tightening narrative.", "watch_risk": "Short squeeze."},
    ]
    s["vietnam_investor_lens"] = {
        "summary": (
            "Nhà đầu tư Việt Nam nên tách 3 lớp: (1) USD/VND và margin tỷ giá doanh nghiệp, "
            "(2) khối ngoại/ETF sau kỳ vọng nâng hạng, (3) chất lượng breadth nội địa."
        ),
        "channels": [
            {"channel": "USD/VND", "analysis": "Theo dõi biên độ và phát ngôn chính sách; DN XNK & nợ FX nhạy nhất."},
            {"channel": "Khối ngoại", "analysis": "Room/FTSE-MSCI narrative có thể tạo flow trung hạn nhưng phụ thuộc global risk."},
            {"channel": "Lãi suất", "analysis": "Spread global ảnh hưởng giá trị hiện tại; NH là proxy đầu tiên."},
            {"channel": "VN-Index", "analysis": "Đỉnh chỉ số không đồng nghĩa độ rộng tốt — ưu tiên chỉ báo breadth."},
            {"channel": "Nhóm ngành", "analysis": "Bank vs broker vs bất động sản phản ứng khác nhau với chi phí vốn."},
            {"channel": "Độ rộng thị trường", "analysis": "ADV declining/up ratio là tín hiệu sớm cho điều chỉnh kỹ thuật."},
            {"channel": "Thanh khoản", "analysis": "Phiên tin lớn: đặt khối lượng và biến động basis lên trên điểm số."},
        ],
    }
    s["scenario_map"] = {
        "base_case": {
            "probability": 55,
            "description": "Fed chậm nới; dầu giữ premium; VN phân hóa nhưng không vỡ thanh khoản hệ thống.",
            "signals_to_watch": ["CPI/PCE Mỹ", "Brent front", "Breadth VN"],
        },
        "bull_case": {
            "probability": 25,
            "description": "Địa chính trị hạ nhiệt + lạm phát mềm → risk-on; VN hưởng lợi ETF/upgrade narrative.",
            "signals_to_watch": ["Đàm phán Mỹ–Iran", "Soft CPI", "Net buy khối ngoại"],
        },
        "bear_case": {
            "probability": 20,
            "description": "Double shock dầu + Fed hawkish; USD spike; VN chịu áp lực FX và tâm lý margin.",
            "signals_to_watch": ["Hormuz disruption", "Dot plot cứng", "USD/VND intraday"],
        },
    }
    s["key_variables_to_watch"] = [
        {"variable": "Giá dầu giao ngay & spread Brent", "why_it_matters": "Kênh nhanh vào CPI kỳ vọng và EPS năng lượng."},
        {"variable": "Phát ngôn Fed & real yield UST", "why_it_matters": "Định giá risk assets & vàng."},
        {"variable": "USD/VND & trạng thái thanh khoản USD hệ thống", "why_it_matters": "Kênh trực tiếp cho DN và NĐT Việt Nam."},
        {"variable": "Tỷ lệ advancing/declining trên HSX/HNX", "why_it_matters": "Đo ‘sức khỏe thật’ của rally VN."},
    ]
    s["source_quality"] = {
        "sources_scanned": 0,
        "articles_selected": 0,
        "verified_links": 0,
        "coverage_note": "Demo inject — chạy finalize_summary_gpt.py để điền số liệu thực từ pipeline.",
    }
    s["final_takeaway"] = (
        "Ưu tiên quan sát **double axis**: (1) Fed/real yield vs (2) oil premium. Ở Việt Nam, đừng chỉ nhìn điểm số — "
        "breadth và USD/VND là hai chỉ báo ‘early warning’ cho nhịp điều chỉnh."
    )
    s["disclaimer"] = (
        "Nội dung chỉ phục vụ mục đích nghiên cứu và giáo dục; không phải khuyến nghị đầu tư hay dịch vụ tư vấn tài chính."
    )

    data["generated_at"] = now.isoformat()
    data["meta"] = {**(data.get("meta") if isinstance(data.get("meta"), dict) else {}), "injected_preview": True}
    FINAL_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated Macro Intelligence preview → {FINAL_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
