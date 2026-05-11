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
        "lãi suất trong nước và thanh khoản NH vẫn là kênh truyền đầu tiên lên TTCK và tín dụt.",
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

    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    FINAL_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {FINAL_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
