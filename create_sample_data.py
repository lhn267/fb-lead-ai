import pandas as pd
import openpyxl

data = [
    {
        "link": "https://www.facebook.com/dung.techviet",
        "name": "Nguyễn Văn Dũng",
        "text": "CEO & Founder tại TechViet Solutions · 24 bạn chung · Sống tại Hà Nội"
    },
    {
        "link": "https://www.facebook.com/phuong.tran.cmo",
        "name": "Trần Thị Mai Phương",
        "text": "Giám đốc Marketing (CMO) tại Vingroup · 15 bạn chung"
    },
    {
        "link": "https://www.facebook.com/long.le.fnb",
        "name": "Lê Hoàng Long",
        "text": "Chủ chuỗi Cà phê The Bean & Đồng sáng lập The Bean Roastery · 45 bạn chung"
    },
    {
        "link": "https://www.facebook.com/anh.pt.bds",
        "name": "Phạm Tuấn Anh",
        "text": "Trưởng phòng Kinh doanh Bất động sản tại Đất Xanh Miền Bắc · 8 bạn chung"
    },
    {
        "link": "https://www.facebook.com/khang.troll",
        "name": "Ngô Minh Khang",
        "text": "Làm việc tại Viện chém gió quốc tế · Ăn bám gia đình · 12 bạn chung"
    },
    {
        "link": "https://www.facebook.com/ngoc.sungroup",
        "name": "Hoàng Bảo Ngọc",
        "text": "Giám đốc Dự án Nghỉ dưỡng tại Sun Group · 60 bạn chung"
    },
    {
        "link": "https://www.facebook.com/thang.fpt",
        "name": "Vũ Đức Thắng",
        "text": "Senior Solution Architect tại FPT Software · 12 bạn chung"
    },
    {
        "link": "https://www.facebook.com/huong.boutique",
        "name": "Đỗ Thu Hương",
        "text": "Chủ sáng lập thương hiệu Thời trang Hương Boutique · Sống tại TP.HCM"
    },
    {
        "link": "https://www.facebook.com/huy.troll2",
        "name": "Bùi Quang Huy",
        "text": "Chủ tịch hội độc thân vui vẻ tại Ở nhà chơi game · 3 bạn chung"
    },
    {
        "link": "https://www.facebook.com/bao.ssi",
        "name": "Đinh Quốc Bảo",
        "text": "Trưởng bộ phận Quản lý Danh mục Đầu tư tại SSI Securities · 31 bạn chung"
    },
    {
        "link": "https://www.facebook.com/tuan.maianh",
        "name": "Mai Anh Tuấn",
        "text": "18 bạn chung · Sống tại Đà Nẵng"
    },
    {
        "link": "https://www.facebook.com/ha.shopee",
        "name": "Lý Thanh Hà",
        "text": "Head of Talent Acquisition (Trưởng phòng Tuyển dụng) tại Shopee Vietnam"
    },
    {
        "link": "https://www.facebook.com/quang.vietcom",
        "name": "Phan Minh Quang",
        "text": "Phó Giám đốc Khối Khách hàng Doanh nghiệp lớn tại Vietcombank"
    },
    {
        "link": "https://www.facebook.com/linh.spa",
        "name": "Võ Thùy Linh",
        "text": "Founder & Master Trainer tại Linh Academy & Spa · 28 bạn chung"
    },
    {
        "link": "https://www.facebook.com/nam.funny",
        "name": "Trịnh Hoài Nam",
        "text": "Làm việc tại Thất nghiệp · Đại học Bôn Ba"
    },
    {
        "link": "https://www.facebook.com/an.bds",
        "name": "Trương Quốc An",
        "text": "Tổng Giám Đốc tại Công ty CP Đầu tư & Xây dựng An Thịnh Phát"
    },
    {
        "link": "https://www.facebook.com/thao.agency",
        "name": "Đặng Phương Thảo",
        "text": "Managing Director tại DigiMedia Marketing Agency · 52 bạn chung"
    },
    {
        "link": "https://www.facebook.com/binh.logistic",
        "name": "Nguyễn Thanh Bình",
        "text": "Giám đốc Chi nhánh Hải Phòng tại Viettel Post · 19 bạn chung"
    },
    {
        "link": "https://www.facebook.com/trang.freelance",
        "name": "Cao Thu Trang",
        "text": "Freelance UI/UX Designer & Content Creator · Sống tại Hà Nội"
    },
    {
        "link": "https://www.facebook.com/duc.student",
        "name": "Lê Huỳnh Đức",
        "text": "Sinh viên năm 3 tại Trường Đại học Kinh tế Quốc dân (NEU)"
    }
]

df = pd.DataFrame(data)
df.to_excel("sample_test_data.xlsx", index=False)
df.to_csv("sample_test_data.csv", index=False, encoding="utf-8-sig")
print("Saved sample_test_data.xlsx and sample_test_data.csv successfully!")
