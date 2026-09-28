# 🚀 HƯỚNG DẪN ĐƯA HỆ THỐNG LÊN CLOUD ĐỂ NHIỀU NGƯỜI CÙNG TRUY CẬP

Tài liệu này hướng dẫn chi tiết từng bước để đưa hệ thống phân loại bạn bè Facebook lên Cloud, giúp toàn bộ nhân viên, team sales hoặc đồng nghiệp của bạn có thể truy cập qua một đường link web (`https://...`) trên máy tính hoặc điện thoại mà không cần cài đặt Python.

---

## 🌟 PHƯƠNG ÁN 1: STREAMLIT COMMUNITY CLOUD (KHUYÊN DÙNG NHẤT)

> **Ưu điểm vượt trội:**
> - **100% Miễn phí vĩnh viễn**, chính chủ từ Streamlit.
> - **Thời gian triển khai:** Chỉ mất đúng **3 - 5 phút**.
> - Hỗ trợ kho lưu trữ **Private (Riêng tư)** trên GitHub, người ngoài không thấy mã nguồn.
> - Có sẵn tên miền bảo mật HTTPS: `https://ten-ung-dung-cua-ban.streamlit.app`.
> - **Cách ly phiên (Multi-user safe):** Mỗi người dùng mở web sẽ có phiên làm việc riêng biệt, không ai thấy file hay dữ liệu của ai.
> - Cài sẵn **API Key trong Cloud Secrets** để toàn bộ nhân viên vào là dùng được ngay, không cần từng người phải tự đi lấy API Key.

---

### BƯỚC 1: ĐƯA MÃ NGUỒN LÊN GITHUB (PRIVATE)

1. Truy cập [github.com](https://github.com/) và đăng nhập tài khoản của bạn (nếu chưa có thì đăng ký miễn phí).
2. Bấm vào biểu tượng dấu **`+`** ở góc phải trên -> Chọn **New repository**.
3. Điền thông tin:
   - **Repository name:** ví dụ `fb-lead-extractor`
   - Chọn chế độ: **Private** (để giữ kín mã nguồn và cấu hình công ty).
   - Không cần tích chọn Add README (vì trong thư mục đã có sẵn).
   - Bấm **Create repository**.
4. Mở cửa sổ dòng lệnh PowerShell ngay tại thư mục dự án (`c:\Users\User\GCW\Project\Data\Quet BB FB`) và chạy các lệnh sau (thay thế URL git bằng link repo của bạn):

```bash
# Khởi tạo git riêng cho dự án
git init -b main

# Thêm tất cả file (file .gitignore đã bảo vệ an toàn các key và data cá nhân)
git add .

# Tạo commit đầu tiên
git commit -m "Deploy AI FB Lead Extractor to Cloud"

# Liên kết với repo GitHub của bạn
git remote add origin https://github.com/TÊN_GITHUB_CỦA_BẠN/fb-lead-extractor.git

# Đẩy code lên GitHub
git push -u origin main
```

*(Mẹo: Nếu bạn quen dùng phần mềm đồ họa, bạn có thể tải **GitHub Desktop**, chọn Add Local Repository rồi bấm Publish Repository sang Private là xong).*

---

### BƯỚC 2: DEPLOY LÊN STREAMLIT COMMUNITY CLOUD

1. Truy cập: **[share.streamlit.io](https://share.streamlit.io)**
2. Đăng nhập bằng tài khoản **GitHub** vừa tạo ở bước 1.
3. Bấm nút **Create app** (hoặc **New app**).
4. Điền các trường:
   - **Repository:** Chọn repo vừa tạo (ví dụ `TÊN_GITHUB_CỦA_BẠN/fb-lead-extractor`).
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** Bạn có thể tùy chỉnh tên miền ngắn gọn, ví dụ: `fb-leads-crm` -> Đường link web sẽ là: `https://fb-leads-crm.streamlit.app`.
5. **CẤU HÌNH API KEY BẢO MẬT (Quan trọng):**
   - Trước khi bấm Deploy, bấm vào dòng chữ **Advanced settings...**
   - Tại mục **Secrets**, copy nội dung sau dán vào:
   ```toml
   GEMINI_API_KEY = "AIzaSy..." # Thay bằng Gemini API Key của bạn
   TARGET_CRITERIA = "Ưu tiên tìm kiếm: Chủ doanh nghiệp, C-Level (CEO, Founder, Giám đốc), Trưởng phòng kinh doanh/Marketing. Loại bỏ các chức danh đùa cợt hoặc không có công việc rõ ràng."
   ```
   - Bấm **Save**.
6. Bấm nút **Deploy!**

---

### BƯỚC 3: SỬ DỤNG VÀ CHIA SẺ CHO NHIỀU NGƯỜI DÙNG

- Chờ khoảng 1 - 2 phút để hệ thống tự động cài đặt thư viện (`streamlit`, `pandas`, `openpyxl`, `requests`).
- Khi màn hình hiện giao diện phần mềm:
  - Bạn chỉ cần **copy đường link web** (ví dụ `https://fb-leads-crm.streamlit.app`) gửi cho nhân viên, cộng sự hoặc team sales.
  - Mọi người chỉ việc mở link trên trình duyệt Chrome/Cốc Cốc/Safari, kéo thả file cào danh sách bạn bè vào và bấm nút xử lý.
  - Hệ thống đã nhận diện sẵn `GEMINI_API_KEY` từ Cloud Secrets nên mọi người không cần phải nhập key nữa!

---

## 🛡️ PHƯƠNG ÁN 2: TRIỂN KHAI LÊN VPS / SERVER NỘI BỘ (DOCKER)

Nếu công ty bạn có server riêng (VPS Ubuntu, DigitalOcean, Vietnix, CloudFly) và yêu cầu dữ liệu tuyệt đối không qua bên thứ 3:

Dự án đã tạo sẵn file [`Dockerfile`](file:///c:/Users/User/GCW/Project/Data/Quet%20BB%20FB/Dockerfile). Bạn chỉ cần thực hiện 2 lệnh:

```bash
# 1. Build image Docker
docker build -t fb-lead-extractor .

# 2. Chạy container ở cổng 8501
docker run -d --name fb-lead-app -p 8501:8501 --restart always fb-lead-extractor
```

Sau đó trỏ tên miền công ty (hoặc IP server) qua Nginx Reverse Proxy là toàn bộ mạng nội bộ hoặc internet có thể truy cập 24/7.

---

## 🔒 CHECKLIST AN TOÀN DỮ LIỆU KHI CHẠY MULTI-USER TRÊN CLOUD

Hệ thống đã được lập trình sẵn các tiêu chuẩn cao nhất cho môi trường nhiều người dùng đồng thời:

- [x] **File `.gitignore` chuẩn:** Ngăn chặn tuyệt đối việc vô tình đưa file `config.json` hay danh sách khách hàng thật lên GitHub.
- [x] **In-Memory Excel Generation:** Quá trình xuất và tải file Excel chuẩn CRM được thực hiện trực tiếp trong bộ nhớ RAM (`io.BytesIO`), không ghi đè file dùng chung trên ổ đĩa server. Hai người tải cùng lúc sẽ không bao giờ bị đè dữ liệu lên nhau.
- [x] **Cách ly Session State:** Dữ liệu tải lên của mỗi nhân viên nằm trong bộ nhớ riêng của phiên duyệt web đó, người khác vào web sẽ thấy màn hình làm việc trống của riêng mình.
- [x] **Hạn mức tải file lớn:** Cấu hình sẵn `maxUploadSize = 200MB` trong `.streamlit/config.toml` cho phép tải cùng lúc hàng chục file Excel nặng mà không bị ngắt kết nối.
