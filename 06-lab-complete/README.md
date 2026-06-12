# 🚀 Production AI Agent — Day 12 Lab Complete

> Production-ready AI Agent với FastAPI, Redis, Docker, Nginx Load Balancer.

---

## ⚡ Quick Start

### Cách 1: Chạy local bằng Python

```bash
cd 06-lab-complete

# 1. Tạo virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy và cấu hình env
cp .env.example .env.local

# 4. Chạy Redis (cần Docker hoặc Redis server local)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 5. Chạy app
python -m app.main
```

App sẽ chạy tại `http://localhost:8000`.

### Cách 2: Chạy bằng Docker Compose (Recommended)

```bash
cd 06-lab-complete

# Build và chạy toàn bộ stack (agent + redis + nginx)
docker compose up --build

# App chạy tại http://localhost (port 80 qua Nginx)
```

### Cách 3: Scale 3 Instances

```bash
# Chạy 3 agent instances + Redis + Nginx LB
docker compose up --build --scale agent=3

# Verify load balancing
for i in $(seq 1 5); do
  curl -s http://localhost/health | python -m json.tool
done
# Header X-Served-By sẽ thay đổi → chứng tỏ load balancing hoạt động
```

---

## 🧪 Test Endpoints

### Health Check (không cần auth)
```bash
curl http://localhost/health
# → {"status":"ok","version":"1.0.0",...}
```

### Readiness Check
```bash
curl http://localhost/ready
# → {"ready":true,"redis":"connected"}
```

### Gửi câu hỏi (cần API key)
```bash
curl -X POST http://localhost/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "question": "What is Docker?"}'
```

### Xem conversation history
```bash
curl http://localhost/users/user1/history \
  -H "X-API-Key: dev-key-change-me-in-production"
```

### Test authentication (sẽ bị reject)
```bash
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
# → 401 Unauthorized
```

### Test rate limit
```bash
# Gửi 15 requests liên tục → request 11+ sẽ bị 429
for i in $(seq 1 15); do echo "Request $i:"; curl -s -w "\n" \
  -X POST http://localhost/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"rate_test\", \"question\": \"test $i\"}"; done
```

---

## 🏗 Architecture

```
Client → Nginx (port 80) → Agent ×N (port 8000) → Redis (port 6379)
```

| Component | Vai trò |
|-----------|---------|
| **Nginx** | Load balancer, reverse proxy, round-robin |
| **Agent** | FastAPI app, stateless, scale horizontally |
| **Redis** | Shared state: conversations, rate limits, budgets |

---

## 📁 File Structure

```
06-lab-complete/
├── app/
│   ├── __init__.py          # Package init
│   ├── main.py              # FastAPI app, routing, middleware
│   ├── config.py            # Env-based settings (pydantic-settings)
│   ├── auth.py              # API key authentication
│   ├── storage.py           # Redis client, conversation history
│   ├── rate_limiter.py      # Sliding window rate limiter
│   ├── cost_guard.py        # Monthly budget per user
│   ├── schemas.py           # Pydantic request/response models
│   └── logging_config.py    # Structured JSON logging
├── utils/
│   └── mock_llm.py          # Mock LLM (không cần API key)
├── tests/
│   ├── conftest.py          # Fixtures với fakeredis
│   └── test_app.py          # 15+ test cases
├── Dockerfile               # Multi-stage, non-root, <500MB
├── docker-compose.yml       # Agent + Redis + Nginx
├── nginx.conf               # Load balancer config
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker build exclusions
├── railway.toml             # Railway deploy config
├── render.yaml              # Render deploy config
├── check_production_ready.py # Readiness checker
├── MISSION_ANSWERS.md       # Câu trả lời exercises
├── DEPLOYMENT.md            # Hướng dẫn deploy
├── DAY12_FULL_REPORT.md     # Báo cáo chi tiết
└── README.md                # File này
```

---

## 🚢 Deploy lên Cloud

### Railway
```bash
npm i -g @railway/cli
railway login
railway init
railway add --plugin redis
railway variables set AGENT_API_KEY=your-secret-key
railway variables set ENVIRONMENT=production
railway up
railway domain
```

### Render
1. Push code lên GitHub
2. Vào render.com → New → Blueprint
3. Connect repo → Render đọc `render.yaml` tự động
4. Kiểm tra env vars → Deploy

Chi tiết xem [DEPLOYMENT.md](DEPLOYMENT.md).

---

## ✅ Chạy Tests

```bash
# Unit tests (dùng fakeredis, không cần Redis server)
python -X utf8 -m pytest tests/ -v

# Production readiness checker
python -X utf8 check_production_ready.py

# Compile check
python -m py_compile app/main.py
```

---

## 🔒 Security Features

- API Key authentication (`X-API-Key` header)
- Rate limiting: 10 req/min per user (Redis sorted set)
- Cost guard: $10/month per user budget
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- No hardcoded secrets
- CORS configurable from env
- Docs disabled in production
- Non-root Docker user
