# 🎯 HỆ THỐNG TRÍCH XUẤT & PHÂN LOẠI KHÁCH HÀNG TIỀM NĂNG FACEBOOK (AI LEAD EXTRACTOR)

> **Giải quyết triệt để bài toán:** Không cần copy-paste thủ công vào ChatGPT/Gemini mỗi lần xuất file. Chỉ cần kéo thả file cào từ Facebook -> Bấm 1 nút -> Hệ thống tự động phân loại, lọc sạch rác & xuất Excel chuẩn CRM!

---

## 🚀 1. Khởi động hệ thống (1 Click)
- Nhấp đúp chuột vào file: **`Chay_He_Thong.bat`**
- Trình duyệt sẽ tự động mở giao diện ứng dụng tại: `http://localhost:8501`

---

## ⚡ 2. Cách lấy API Key AI Miễn Phí (Google Gemini)
Hệ thống hỗ trợ Google Gemini (Khuyên dùng vì tốc độ cực nhanh và **hoàn toàn miễn phí**):
1. Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Đăng nhập tài khoản Google của bạn -> Bấm nút **Create API key**.
3. Copy API Key đó, dán vào ô **Gemini API Key** trên cột bên trái (Sidebar) của phần mềm.
4. Bấm **Lưu Cấu Hình Này** (chỉ cần làm 1 lần duy nhất, hệ thống sẽ tự nhớ cho các lần sau).

*(Nếu không có API Key, phần mềm vẫn có chế độ **Offline** chạy bằng bộ lọc từ điển và regex nội bộ).*

---

## 📋 3. Quy trình từ Nick Clone đến Nick Chính (A: 3k, B: 4k Friends)

### Bước 1: Quét thử trên nick Clone (50 - 100 Friends)
1. Đăng nhập nick Clone trên một profile trình duyệt Chrome riêng (tránh dính cookie nick chính).
2. Cài tiện ích miễn phí **Instant Data Scraper** trên Chrome Web Store.
3. Vào link: `https://www.facebook.com/me/friends`
4. Bấm icon con Pokemon đỏ của Instant Data Scraper.
5. Cài đặt tốc độ an toàn:
   - **Min delay:** `2.5s`
   - **Max delay:** `4.0s`
6. Bấm **Start Crawling** -> Sau khi cuộn hết bạn bè, bấm nút **XLSX** hoặc **CSV** để tải file về máy.

### Bước 2: Nạp file vào Hệ Thống Tự Động & Khử Trùng Lặp
- Khi quét tài khoản lớn (3k - 4k friends), bạn quét chia nhỏ thành nhiều file (ví dụ quét theo chữ A, B, C...).
- Bạn **KHÔNG CẦN** phải copy gộp file hay bấm Remove Duplicates trong Excel một cách thủ công!
- **Chỉ cần kéo thả tất cả các file cùng lúc vào phần mềm:**
  - Hệ thống tự động gộp tất cả các file lại.
  - Chuẩn hóa URL Facebook (xóa các mã tracking như `?fref=ts`, `?mibextid=...`).
  - **Tự động xóa 100% dòng trùng lặp** dựa trên Link Profile duy nhất.
  - Hiển thị bảng thống kê: Đã gộp bao nhiêu file, xóa bao nhiêu dòng trùng, còn lại bao nhiêu người bạn duy nhất.
- Bấm **🚀 BẮT ĐẦU XỬ LÝ & BÓC TÁCH DỮ LIỆU** -> AI chỉ cần phân tích tệp sạch, không tốn token thừa!

### Bước 3: Xem Kết Quả & Xuất File Chuẩn CRM
1. Chuyển sang **Tab 2: Bảng Kết Quả & Xuất File**:
   - Xem thống kê số lượng: C-Level, Quản lý, Hợp lệ, Rác đã loại bỏ.
   - Dùng bộ lọc nhanh: Lọc chỉ lấy C-Level / Chủ DN, lọc bỏ nick ảo/rác.
   - Bấm trực tiếp vào link Facebook để mở profile khách hàng.
2. Bấm **📥 Tải File Excel Chuẩn CRM (.xlsx)**:
   - File đã được tô màu phân tầng khách hàng.
   - Có link click trực tiếp.
   - Sẵn sàng bàn giao cho Sales chăm sóc hoặc import vào HubSpot, Lark Base, Notion, v.v.

---

## 🛡️ 4. Bí quyết An Toàn khi nhân rộng sang Nick Chính A (3k) & B (4k)
Khi tài khoản clone chạy mượt mà, áp dụng sang A và B với các lưu ý sống còn sau:
- **Không cào dồn dập 1 lần hết 3.000 bạn bè:** Hãy chia nhỏ mỗi phiên khoảng **800 - 1.000 người** (tương đương 10 - 15 phút cuộn). Sau đó bấm Stop và xuất file. Nghỉ 20 - 30 phút hoặc cào vào buổi khác.
- **Tăng nhẹ Delay:** Đặt **Min delay: 3.0s** và **Max delay: 5.0s** để Facebook không phát hiện bot.
- **Chi phí AI:** 3.000 bạn bè chia lô 25 người = ~120 requests. Với hạn mức Free của Gemini (15 RPM), xử lý 3.000 bạn bè chỉ mất khoảng 8-10 phút với chi phí **0 ĐỒNG**!
