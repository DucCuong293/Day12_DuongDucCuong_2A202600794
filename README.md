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

Bài làm hoàn thiện nằm hoàn toàn trong thư mục **[06-lab-complete/](file:///e:/VinUni/Lab/Day%2012%20%E2%80%94%20Deployment%20%C4%90%C6%B0a%20Agent%20L%C3%AAn%20Cloud/day12_ha-tang-cloud_va_deployment/06-lab-complete/)**:

```
day12_ha-tang-cloud_va_deployment/
├── 06-lab-complete/                  # Thư mục bài làm chính thức hoàn chỉnh
│   ├── app/                          # Mã nguồn ứng dụng AI Agent (FastAPI)
│   │   ├── main.py                   # Điểm khởi chạy chính & routing
│   │   ├── config.py                 # 12-Factor App config (Pydantic settings)
│   │   ├── auth.py                   # API Key Auth (hmac constant-time compare)
│   │   ├── storage.py                # Redis client & conversation history
│   │   ├── rate_limiter.py           # Sliding Window Rate Limiter (Sorted Set)
│   │   ├── cost_guard.py             # Monthly Cost protection ($10/month limit)
│   │   ├── schemas.py                # Pydantic request/response models
│   │   └── logging_config.py         # Structured JSON logging
│   ├── utils/
│   │   └── mock_llm.py               # Mock LLM engine (không tốn phí API key)
│   ├── tests/                        # Thư mục unit tests (Fakeredis)
│   │   ├── conftest.py               # Thiết lập client fixtures
│   │   └── test_app.py               # 18 test cases đã PASSED
│   ├── screenshots/                  # Minh chứng chạy thực tế
│   │   ├── dashboard.png             # Railway Dashboard
│   │   ├── running.png               # Active Deploy Logs
│   │   └── test.png                  # Terminal curl test
│   ├── Dockerfile                    # Docker Multi-stage, non-root, slim (<200MB)
│   ├── docker-compose.yml            # Stack: 3 Agent + Redis + Nginx Load Balancer
│   ├── nginx.conf                    # Cấu hình reverse proxy & load balancing
│   ├── requirements.txt              # Thư viện phụ thuộc
│   ├── .env.example                  # Template cấu hình môi trường
│   ├── .dockerignore                 # Danh sách bỏ qua khi build Docker
│   ├── railway.toml                  # Cấu hình deploy Railway
│   ├── render.yaml                   # Cấu hình Render Blueprint
│   ├── check_production_ready.py     # Script kiểm tra chất lượng (100% Passed)
│   ├── MISSION_ANSWERS.md            # Giải thích câu hỏi lý thuyết bài tập
│   ├── DEPLOYMENT.md                 # Hướng dẫn chi tiết triển khai & test commands
│   └── DAY12_FULL_REPORT.md          # Báo cáo kỹ thuật chi tiết (Tiếng Việt)
│
├── screenshots/                      # Thư mục lưu ảnh minh chứng (Root)
└── DAY12_DELIVERY_CHECKLIST.md       # Checklist kiểm tra tự đánh giá nộp bài
```

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
