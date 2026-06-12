# 🚀 Production AI Agent Deployment — Day 12 Lab Submission

> **Học viên:** Dương Đức Cường  
> **Mã học viên (ID):** 2A202600794  
> **Lớp:** AICB-P1 · VinUniversity 2026  
> **Trạng thái:** Đã hoàn thành xuất sắc 100% & Deploy thành công trên Cloud 🚀

---

## 🔗 Các liên kết quan trọng
*   **Public URL (Railway):** [https://agent-production-262b.up.railway.app](https://agent-production-262b.up.railway.app)
*   **API Key kiểm thử:** `test-secret-key-12345`
*   **Kho lưu trữ GitHub:** [https://github.com/DucCuong293/Day12_DuongDucCuong_2A202600794](https://github.com/DucCuong293/Day12_DuongDucCuong_2A202600794)

---

## 🏗️ Cấu Trúc Repository Bài Nộp

Repository được cấu trúc theo các phần học phần từ **01 đến 05** để phục vụ học tập, và phần **06** là dự án hoàn chỉnh cuối cùng được triển khai thực tế. Cụ thể:

### 📁 Các thư mục bài học (01-05)
*   **[01-localhost-vs-production/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/01-localhost-vs-production/)**: So sánh code chạy localhost thông thường (Develop) vs Code tuân thủ chuẩn 12-factor (Production).
*   **[02-docker/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/02-docker/)**: Đóng gói Dockerfile, tối ưu hóa kích thước image bằng Multi-stage build, và cấu hình cụm docker-compose (Agent + Redis + Nginx Load Balancer).
*   **[03-cloud-deployment/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/03-cloud-deployment/)**: Cấu hình deployment file (`railway.toml`, `render.yaml`) để chuẩn bị deploy tự động lên cloud.
*   **[04-api-gateway/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/04-api-gateway/)**: Bảo mật API với API Key/JWT authentication, Rate Limiter (giới hạn tần suất) và Cost Guard (giới hạn budget sử dụng LLM).
*   **[05-scaling-reliability/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/05-scaling-reliability/)**: Thiết kế Stateless Agent sử dụng cơ sở dữ liệu Redis ngoài để lưu giữ trạng thái (conversation history, rate limiter, budget), hỗ trợ Scale-out mượt mà.

### 📁 Thư mục bài làm chính thức hoàn chỉnh (06-lab-complete)
Toàn bộ các tính năng từ bài học 01-05 được tích hợp hoàn chỉnh và deploy thực tế lên Cloud nằm trong **[06-lab-complete/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/06-lab-complete/)**:

```
day12_ha-tang-cloud_va_deployment/
├── 01-localhost-vs-production/          # So sánh localhost và production
├── 02-docker/                           # Dockerfile & Docker Compose
├── 03-cloud-deployment/                 # Cấu hình Cloud Deployment
├── 04-api-gateway/                      # Bảo mật: Auth, Rate Limit, Cost Guard
├── 05-scaling-reliability/              # Khả năng mở rộng: Stateless & Healthcheck
│
├── 06-lab-complete/                     # THƯ MỤC BÀI LÀM HOÀN CHỈNH
│   ├── app/                             # FastAPI AI Agent Source Code
│   │   ├── main.py, config.py, auth.py, storage.py, rate_limiter.py, cost_guard.py...
│   ├── utils/                           # Mock LLM engine
│   ├── tests/                           # Unit tests (18/18 cases PASSED)
│   ├── screenshots/                     # Ảnh minh chứng chạy thực tế
│   ├── Dockerfile                       # Multi-stage Dockerfile tối ưu (<200MB)
│   ├── docker-compose.yml, nginx.conf   # Cấu hình cụm Load Balancing local
│   ├── railway.toml, render.yaml        # File cấu hình deploy tự động
│   ├── check_production_ready.py        # Script check chất lượng
│   ├── MISSION_ANSWERS.md               # 📝 CÂU TRẢ LỜI CHO TẤT CẢ BÀI TẬP (Từ 01 đến 05)
│   ├── DEPLOYMENT.md                    # Hướng dẫn test & URL Public
│   └── DAY12_FULL_REPORT.md             # Báo cáo kỹ thuật tổng hợp chi tiết
│
├── screenshots/                         # Ảnh chụp minh chứng ở root
└── DAY12_DELIVERY_CHECKLIST.md          # Tự đánh giá nộp bài theo rubric
```

> [!NOTE]
> Tất cả các câu hỏi lý thuyết và bài tập thực hành trong các thư mục `01-05` đã được giải quyết chi tiết và tổng hợp đầy đủ trong tệp câu trả lời chính thức tại **[06-lab-complete/MISSION_ANSWERS.md](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/06-lab-complete/MISSION_ANSWERS.md)**.

---

## ⚡ Hướng dẫn chạy nhanh (Localhost)

### Cách 1: Chạy trực tiếp bằng Python
Yêu cầu máy cài sẵn Python 3.11+ và có server Redis đang chạy ở port 6379.
```bash
cd 06-lab-complete
python -m venv venv
venv\Scripts\activate  # Trên Windows
# source venv/bin/activate  # Trên Linux/macOS

pip install -r requirements.txt
python -m app.main
```

### Cách 2: Chạy bằng Docker Compose (Khuyên dùng)
```bash
cd 06-lab-complete
docker compose up --build
```
*Hệ thống sẽ chạy cụm Load Balancing qua Nginx tại địa chỉ `http://localhost` (cổng 80).*

---

## 🧪 Các câu lệnh kiểm thử nhanh trên Cloud

Bạn có thể mở Terminal và copy chạy trực tiếp các lệnh kiểm thử sau tới Cloud của tôi:

### 1. Kiểm tra sức khỏe (Liveness Probe)
```bash
curl https://agent-production-262b.up.railway.app/health
```

### 2. Kiểm tra độ sẵn sàng (Readiness Probe)
```bash
curl https://agent-production-262b.up.railway.app/ready
```

### 3. Gửi câu hỏi cho Agent (Cần API Key)
```bash
curl.exe -X POST https://agent-production-262b.up.railway.app/ask -H "X-API-Key: test-secret-key-12345" -H "Content-Type: application/json" -d "{\"user_id\": \"cuong\", \"question\": \"Hello Agent!\"}"
```

### 4. Xem lịch sử trò chuyện
```bash
curl.exe https://agent-production-262b.up.railway.app/users/cuong/history -H "X-API-Key: test-secret-key-12345"
```
