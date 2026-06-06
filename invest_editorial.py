"""Shared invest Gemini editorial rules — no BigQuery or heavy deps."""

from __future__ import annotations

INVEST_EDITORIAL_LENGTH_RULE = (
    "Không giới hạn số câu/số chữ. Độ dài phụ thuộc vào mức độ quan trọng, độ phức tạp và độ dày dữ liệu nguồn. "
    "Tin quan trọng hoặc phức tạp có thể viết dài hơn để giải thích đủ bối cảnh, chủ thể, diễn biến, tác động và biến số theo dõi. "
    "Tin nhỏ thì viết gọn. Không viết dài để lấp chỗ, không rút ngắn đến mức mất ý chính."
)
INVEST_EDITORIAL_MEMO_RULE = (
    "Cấu trúc memo phân tích (không in nhãn Fact/Context… ra output, nhưng nội dung phải cover khi nguồn hỗ trợ):\n"
    "- Fact: dữ kiện nguồn nói gì?\n"
    "- Context: bối cảnh chính sách/ngành/thị trường là gì?\n"
    "- Transmission channel: tác động đi qua kênh nào?\n"
    "- Investment implication: ý nghĩa gì với nhà đầu tư/ngành/tài sản?\n"
    "- Watch variables: cần theo dõi gì tiếp theo?\n"
    "- Uncertainty: điểm nào còn chưa rõ?"
)
INVEST_EDITORIAL_SPECIFICITY_RULE = (
    "Độ cụ thể & thực thể: không tóm tắt mơ hồ nếu nguồn có chi tiết. "
    "Ưu tiên tên đầy đủ người/tổ chức/công ty/cơ quan, chức danh, ngành/thị trường, bối cảnh, "
    "chính sách/buộc tội/quyết định/số liệu/dự án cụ thể, và vì sao quan trọng.\n"
    "Tránh khi nguồn có chi tiết hơn: \"một số lãnh đạo\" → tên/chức/đơn vị; "
    "\"cơ quan chức năng\" → tên cơ quan; \"doanh nghiệp lớn\" → tên công ty + ngành; "
    "\"FPT\" → \"công ty công nghệ FPT\" hoặc \"cổ phiếu công ty công nghệ FPT\"; "
    "\"Trump\" → \"Tổng thống Mỹ Donald Trump\" (lần đầu); "
    "\"Fed\" → \"Cục Dự trữ Liên bang Mỹ (Fed)\" (lần đầu); "
    "\"ngày hội bóng đá lớn nhất hành tinh\" → \"World Cup 2026\" nếu đúng sự kiện."
)
INVEST_EDITORIAL_TRANSMISSION_RULE = (
    "Kênh truyền tác động (investment_angle / investor_lens phải nêu kênh khi có thể): "
    "lãi suất/tỷ giá/USD; giá dầu/vàng/hàng hóa; chi phí đầu vào; tín dụng/thanh khoản; "
    "pháp lý/quản trị/điều tra; tiêu dùng/nhu cầu; chuỗi cung ứng; ngân sách/đầu tư công; "
    "định giá/tâm lý thị trường; doanh thu/biên lợi nhuận/tiến độ dự án.\n"
    "Tránh: \"Vụ việc có thể ảnh hưởng đến ngành điện.\" "
    "Tốt hơn: \"Vụ việc làm tăng rủi ro quản trị trong ngành điện; biến số cần theo dõi là phạm vi điều tra, "
    "đơn vị/dự án liên quan và khả năng tác động tới tiến độ đầu tư hoặc tâm lý thị trường đối với nhóm năng lượng.\""
)
INVEST_EDITORIAL_CAUTION_RULE = (
    "Tách bản chất và suy luận: không trình bày suy luận như sự thật. "
    "Dùng: \"có thể ảnh hưởng\", \"phụ thuộc vào\", \"cần theo dõi\", \"chưa rõ phạm vi\", "
    "\"theo nguồn công bố\", \"nếu thông tin này mở rộng sang…\".\n"
    "Không viết: \"sẽ làm cổ phiếu tăng/giảm\", \"chắc chắn tác động\", \"đây là cơ hội\", "
    "\"tín hiệu tích cực mạnh\" — trừ khi nguồn nêu rõ và vẫn viết thận trọng."
)
INVEST_EDITORIAL_RELEVANCE_RULE = (
    "Không ép góc đầu tư: tin liên quan yếu → tóm tắt trung lập, không phóng đại tác động thị trường; "
    "hạ ưu tiên nếu có thể; nói rõ tác động gián tiếp hoặc hạn chế nếu không đủ cơ sở."
)
INVEST_EDITORIAL_LEGAL_RULE = (
    "Tin điều tra/khởi tố/xét xử/phạt/kiểm tra/quản trị/vi phạm đấu thầu/ngân hàng-CK-BĐS-đầu tư công: "
    "nêu (nếu nguồn có) tên người/tổ chức, chức danh/đơn vị, nội dung cáo buộc/vi phạm, dự án/công ty/ngành liên quan, "
    "vì sao quan trọng với quản trị/rủi ro chính sách/trì hoãn dự án/tâm lý ngành. "
    "Không suy diễn có tội vượt quá wording nguồn."
)
INVEST_EDITORIAL_MARKET_RULE = (
    "Tin thị trường/cổ phiếu/tài sản/doanh nghiệp: nêu (nếu nguồn có) tên công ty/tài sản, ngành, "
    "biến động/số liệu chính, lý do nguồn đưa ra, nhóm bị ảnh hưởng, biến số theo dõi tiếp."
)
INVEST_EDITORIAL_POLICY_RULE = (
    "Tin chính sách/vĩ mô: nêu (nếu nguồn có) cơ quan ban hành, nội dung quyết định/chính sách, "
    "nhóm bị ảnh hưởng, lộ trình triển khai, kênh tác động thị trường/ngành, điểm dữ liệu/chính sách cần theo dõi tiếp."
)
INVEST_EDITORIAL_ENTITY_RULE = (
    "- Lần đầu nhắc phải xác định rõ chủ thể (xem thêm quy tắc độ cụ thể ở trên).\n"
    "- Mỗi mục quan trọng phải trả lời: Ai/cái gì? Chuyện gì đã xảy ra? "
    "Vì sao quan trọng với thị trường/ngành/chính sách/bối cảnh VN–toàn cầu? Cần theo dõi gì tiếp theo?"
)


def invest_editorial_rules_block() -> str:
    """Shared invest Gemini editorial rules — no fixed length cap; research-memo tone."""
    return "\n\n".join(
        (
            INVEST_EDITORIAL_LENGTH_RULE,
            INVEST_EDITORIAL_MEMO_RULE,
            INVEST_EDITORIAL_SPECIFICITY_RULE,
            INVEST_EDITORIAL_TRANSMISSION_RULE,
            INVEST_EDITORIAL_CAUTION_RULE,
            INVEST_EDITORIAL_RELEVANCE_RULE,
            INVEST_EDITORIAL_LEGAL_RULE,
            INVEST_EDITORIAL_MARKET_RULE,
            INVEST_EDITORIAL_POLICY_RULE,
            INVEST_EDITORIAL_ENTITY_RULE,
        )
    )
