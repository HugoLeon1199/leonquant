# Hướng dẫn nhận báo giá khách hàng qua Google Sheet

Làm theo đúng 8 bước dưới đây (khoảng 5 phút, không cần biết code). Sau khi xong, mỗi khi có khách điền form trên web, thông tin sẽ **tự động** xuất hiện thành 1 dòng mới trong Google Sheet của anh.

## Bước 1: Tạo Google Sheet
- Mở https://sheets.google.com
- Bấm **Blank spreadsheet** (bảng tính trống)
- Đặt tên file (ví dụ: "Khách hàng OMODA JAECOO Hà Tĩnh")

## Bước 2: Đặt tên cột
Ở hàng đầu tiên (hàng 1), gõ đúng theo thứ tự vào các ô A1, B1, C1, D1, E1:

```
Thời gian | Họ tên | SĐT | Xe quan tâm | Ghi chú
```

## Bước 3: Mở Apps Script
- Trên thanh menu, bấm **Extensions** (Tiện ích mở rộng) → **Apps Script**
- Một tab mới sẽ mở ra với ô code trống

## Bước 4: Dán code
- Xóa hết chữ có sẵn trong ô code (thường là `function myFunction() {}`)
- Dán đoạn code này vào:

```javascript
function doPost(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = JSON.parse(e.postData.contents);
  sheet.appendRow([
    new Date(),
    data.name || "",
    data.phone || "",
    data.model || "",
    data.message || ""
  ]);
  return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

## Bước 5: Lưu
- Bấm biểu tượng **💾 (Save)** ở góc trên, hoặc Ctrl+S
- Nếu Google hỏi đặt tên project, gõ tên gì cũng được (ví dụ "LeadForm")

## Bước 6: Deploy (xuất bản)
- Bấm nút xanh **Deploy** ở góc trên phải → chọn **New deployment**
- Bấm vào biểu tượng ⚙️ cạnh chữ "Select type" → chọn **Web app**

## Bước 7: Cấp quyền truy cập
- Ở mục **Who has access** (Ai có quyền truy cập), chọn **Anyone** (Bất kỳ ai)
- ⚠️ Bắt buộc chọn "Anyone" — nếu không chọn, web sẽ không gửi được dữ liệu vào Sheet
- Bấm **Deploy**
- Google sẽ hiện màn hình xin cấp quyền — bấm **Authorize access**, chọn tài khoản Google của anh, bấm **Allow** (Cho phép). Nếu Google cảnh báo "unsafe", bấm **Advanced** → **Go to [tên project] (unsafe)** — đây là bình thường vì code do chính mình tạo, không phải của bên thứ ba.

## Bước 8: Copy link và gửi lại
- Sau khi deploy xong, Google hiện ra 1 đường link dạng:
  ```
  https://script.google.com/macros/s/AKfycb...................../exec
  ```
- Copy **toàn bộ link đó**, gửi lại cho người đang làm web giúp anh.

---

**Sau khi có link này, mọi lượt khách bấm "Nhận báo giá" trên web sẽ tự động thêm 1 dòng mới vào Google Sheet của anh — anh chỉ cần mở Sheet lên là thấy danh sách khách hàng, không cần làm gì thêm.**
