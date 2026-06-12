# Day 12 Lab — Mission Answers

> **Student Name:** Dương Đức Cường (MSHV: 2A202600794)
> **Date:** 2026-06-12

---

## Part 1: Localhost vs Production

### Exercise 1.1: Phát hiện anti-patterns (5+ vấn đề)

Đọc file `01-localhost-vs-production/develop/app.py`, tìm được các anti-patterns sau:

1. **API key hardcode trong code** (`OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"`)
   - **Tại sao nguy hiểm:** Nếu push lên GitHub, key bị lộ công khai. Bất kỳ ai cũng có thể dùng key của bạn → mất tiền, vi phạm bảo mật. Phải dùng env vars.

2. **Database URL hardcode** (`DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`)
   - **Tại sao nguy hiểm:** Lộ username/password DB. Trong production, connection string khác hoàn toàn → code không deploy được.

3. **Debug mode bật cố định** (`DEBUG = True`)
   - **Tại sao nguy hiểm:** Debug mode trong production expose stack traces, internal errors cho attacker. Phải tắt trong production.

4. **Dùng `print()` thay vì proper logging**
   - **Tại sao nguy hiểm:** `print()` không có level (INFO/WARNING/ERROR), không có timestamp, không structured → không thể search/filter logs trong production. Phải dùng `logging` module với JSON format.

5. **Log ra secret** (`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`)
   - **Tại sao nguy hiểm:** Secret xuất hiện trong log files → ai truy cập logs cũng thấy được key.

6. **Không có health check endpoint**
   - **Tại sao nguy hiểm:** Cloud platform (Railway, Render, K8s) không biết app còn sống hay đã crash → không thể auto-restart, không biết khi nào gửi traffic.

7. **Port cứng, host là localhost**
   - **Tại sao nguy hiểm:** Cloud platforms inject PORT qua env var. Bind `localhost` thì chỉ chạy được trên máy cá nhân, container không truy cập được.

8. **Reload mode trong production** (`reload=True`)
   - **Tại sao nguy hiểm:** File watcher tiêu tốn CPU, không ổn định, có thể restart giữa lúc serve request.

### Exercise 1.3: Bảng so sánh Basic vs Advanced

| Feature | Basic (develop/) | Advanced (production/) | Tại sao quan trọng? |
|---------|-----------------|----------------------|---------------------|
| **Config** | Hardcode trong code | Env vars + `.env` file | Dễ thay đổi giữa environments (dev/staging/prod), không lộ secrets khi push code |
| **Health check** | ❌ Không có | ✅ `GET /health` | Platform biết khi nào app crash để auto-restart, load balancer biết khi nào gửi traffic |
| **Logging** | `print()` | JSON structured logging | Logs dễ parse, search, aggregate bằng ELK/CloudWatch. Có timestamp, level, context |
| **Shutdown** | Đột ngột (kill process) | Graceful (handle SIGTERM) | Hoàn thành requests đang xử lý trước khi tắt, không mất data, đóng DB connections sạch |
| **Secrets** | Hardcode + log ra | Env vars, không log | Bảo mật tối thiểu. Secrets phải là runtime config, không được nằm trong code |
| **Port/Host** | Cứng `localhost:8000` | Từ env vars | Deploy được trên bất kỳ platform nào (Railway inject PORT, K8s inject HOST) |
| **Error handling** | Không có | Try/catch + proper HTTP codes | Client biết lỗi gì để retry hoặc báo user, không crash toàn bộ app |

---

## Part 2: Docker

### Exercise 2.1: Trả lời câu hỏi Dockerfile

1. **Base image là gì?**
   - `python:3.11-slim` — đây là image chứa Python 3.11 trên Debian minimal. Dùng `slim` thay vì full image để giảm kích thước (~150MB vs ~900MB).

2. **Working directory là gì?**
   - `/app` — đây là thư mục trong container nơi code được copy vào và chạy. Giống `cd /app` trước khi chạy lệnh.

3. **Tại sao COPY requirements.txt trước?**
   - **Docker layer caching:** Docker cache mỗi layer (mỗi instruction). Nếu `requirements.txt` không đổi → Docker dùng cache cho `pip install` → build nhanh hơn rất nhiều. Nếu copy tất cả code trước thì bất kỳ thay đổi code nào cũng invalidate cache → phải install lại dependencies mỗi lần build.

4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `ENTRYPOINT` — lệnh cố định, không thể override bằng `docker run` args. Phù hợp khi container luôn chạy một chương trình cụ thể.
   - `CMD` — lệnh mặc định, CÓ THỂ override khi `docker run`. Linh hoạt hơn cho debugging (có thể chạy `docker run myimage bash` để debug).
   - Trong lab ta dùng `CMD` vì linh hoạt hơn cho development.

### Exercise 2.3: So sánh image size (Multi-stage build)

- **Basic Dockerfile (single-stage):** ~400-500 MB
  - Chứa gcc, build tools, source code, cache pip
- **Advanced Dockerfile (multi-stage):** ~150-200 MB
  - Stage 1 (builder): install dependencies với gcc
  - Stage 2 (runtime): chỉ copy compiled packages từ builder, không có gcc, không build tools
- **Giảm được:** ~50-60% kích thước

**Tại sao quan trọng:**
- Image nhỏ hơn → deploy nhanh hơn (pull image nhanh)
- Ít packages → ít attack surface → bảo mật hơn
- Tiết kiệm storage trên registry
- Cold start nhanh hơn trên serverless platforms

### Exercise 2.4: Architecture diagram

```
┌──────────────┐
│    Client     │  (browser, curl, Postman)
└──────┬───────┘
       │ HTTP request (port 80)
       ▼
┌──────────────┐
│  Nginx (LB)  │  Load Balancer — phân tán traffic
│   port 80    │  round-robin giữa các agent instances
└──────┬───────┘
       │
       ├─────────────┬──────────────┐
       ▼             ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Agent 1  │  │ Agent 2  │  │ Agent 3  │
│ :8000    │  │ :8000    │  │ :8000    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
             ┌──────────┐
             │  Redis   │  Shared state store
             │  :6379   │  (sessions, rate limit, budget)
             └──────────┘
```

**Communication flow:**
1. Client → Nginx (port 80): HTTP request
2. Nginx → Agent (port 8000): proxy_pass round-robin
3. Agent → Redis (port 6379): lưu/đọc conversation, rate limit, budget
4. Tất cả services trên cùng Docker network `agent_net`

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Quy trình deploy Railway:**
1. `npm i -g @railway/cli` — cài CLI
2. `railway login` — đăng nhập
3. `railway init` — tạo project
4. Set env vars: `PORT`, `AGENT_API_KEY`, `REDIS_URL`
5. `railway up` — deploy
6. `railway domain` — lấy public URL

**Trạng thái:** Đã deploy thành công lên Railway! Public URL: https://agent-production-262b.up.railway.app

### Exercise 3.2: So sánh railway.toml vs render.yaml

| Tiêu chí | railway.toml (Railway) | render.yaml (Render) |
|----------|----------------------|---------------------|
| **Format** | TOML | YAML |
| **Build config** | `builder = "DOCKERFILE"` | `runtime: docker` |
| **Health check** | `healthcheckPath` | `healthCheckPath` |
| **Env vars** | Set qua CLI/dashboard | Khai báo trong file, hỗ trợ `generateValue` |
| **Redis** | Thêm Redis plugin riêng | Khai báo service type redis trong cùng file |
| **Auto deploy** | Mặc định khi push | `autoDeploy: true` |
| **Start command** | Trong file `startCommand` | Dùng CMD trong Dockerfile |

**Nhận xét:** Render cho phép khai báo infra (Redis) cùng file → dễ reproduce. Railway đơn giản hơn nhưng phải config Redis riêng qua dashboard.

### Exercise 3.3: GCP Cloud Run CI/CD (Optional)

Cloud Run CI/CD pipeline gồm:
- `cloudbuild.yaml`: định nghĩa build steps (docker build → push → deploy)
- `service.yaml`: cấu hình Cloud Run service (CPU, memory, min/max instances, env vars)
- Trigger: GitHub push → Cloud Build → auto deploy lên Cloud Run
- Ưu điểm: pay-per-request, auto-scale to zero, phù hợp production thật

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

- **API key được check ở đâu?** Trong `app/auth.py`, function `verify_api_key()`. FastAPI dependency injection tự động extract header `X-API-Key` và gọi hàm verify trước khi vào handler.
- **Điều gì xảy ra nếu sai key?** HTTP 401 Unauthorized với message "Invalid API key."
- **Làm sao rotate key?** Thay giá trị `AGENT_API_KEY` trong env vars → restart app. Không cần sửa code. Nếu dùng Railway: `railway variables set AGENT_API_KEY=new-key-here`.

**Tại sao quan trọng:** Public URL = ai cũng gọi được API. Không có auth → attacker spam requests → hết budget OpenAI, lộ data users.

### Exercise 4.3: Rate limiting

- **Algorithm:** Sliding window dùng Redis Sorted Set
  - Mỗi request thêm entry (score = timestamp) vào sorted set
  - Trước khi check: `ZREMRANGEBYSCORE` xóa entries cũ hơn 60s
  - `ZCARD` đếm entries còn lại → nếu >= limit thì reject
- **Limit:** 10 requests/minute per user (configurable qua `RATE_LIMIT_PER_MINUTE`)
- **Bypass cho admin:** Có thể implement bằng cách check user_id trong whitelist hoặc thêm role-based check. Hiện tại chưa implement admin bypass.

**Tại sao sliding window tốt hơn fixed window:** Fixed window có edge case "burst at boundary" — 10 requests cuối window + 10 requests đầu window mới = 20 requests trong 60s thực tế. Sliding window không có vấn đề này.

### Exercise 4.4: Cost guard implementation

```python
# app/cost_guard.py — logic chính:

def check_budget(user_id: str, estimated_cost: float):
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(redis.get(key) or 0)
    if current + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(402, "Monthly budget exceeded")

    redis.incrbyfloat(key, estimated_cost)
    redis.expire(key, 32 * 24 * 3600)  # 32 days TTL
```

**Giải thích approach:**
- Mỗi user có key riêng theo tháng: `budget:user123:2026-06`
- Dùng `INCRBYFLOAT` (atomic operation) để tránh race condition
- TTL 32 ngày → tự cleanup sau khi qua tháng
- Check TRƯỚC khi gọi LLM để tránh tốn cost khi đã vượt budget
- Trả HTTP 402 (Payment Required) khi vượt budget

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks implementation

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    return {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "redis_status": "connected" if storage.redis_healthy() else "disconnected",
    }

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
    if not storage.redis_healthy():
        raise HTTPException(503, "Not ready: Redis unavailable")
    return {"ready": True, "redis": "connected"}
```

**Sự khác biệt:**
- **Health (liveness):** "App còn chạy không?" → nếu fail, platform restart container
- **Ready (readiness):** "App có thể nhận request không?" → nếu fail, load balancer ngừng gửi traffic nhưng KHÔNG restart

### Exercise 5.2: Graceful shutdown

Sử dụng FastAPI lifespan + SIGTERM handler:

```python
@asynccontextmanager
async def lifespan(app):
    # Startup
    storage.init_redis()
    yield
    # Shutdown — đóng Redis connections sạch sẽ
    storage.close_redis()

signal.signal(signal.SIGTERM, lambda s, f: logger.info("SIGTERM received"))
```

**Tại sao quan trọng:**
1. Hoàn thành requests đang xử lý (không trả 502 cho client)
2. Đóng Redis/DB connections sạch (tránh connection leak)
3. Flush logs (không mất log entries)
4. Container orchestrator gửi SIGTERM → chờ grace period → SIGKILL

### Exercise 5.3: Stateless design

**Anti-pattern (stateful):**
```python
# ❌ State trong memory — mất khi restart, không share giữa instances
conversation_history = {}
rate_windows = defaultdict(deque)
daily_cost = 0.0
```

**Correct (stateless):**
```python
# ✅ Tất cả state trong Redis — share giữa instances, persist qua restart
storage.save_message(user_id, "user", question)  # Redis RPUSH
check_rate_limit(user_id)  # Redis SORTED SET
check_budget(user_id, cost)  # Redis INCRBYFLOAT
```

**Tại sao stateless quan trọng khi scale:**
- Instance 1 nhận request → lưu conversation trong memory
- Instance 2 nhận request tiếp → KHÔNG có conversation! Bug!
- Với Redis: bất kỳ instance nào cũng đọc/ghi cùng Redis → consistent

### Exercise 5.4: Load balanced stack

```bash
docker compose up --scale agent=3
```

Kết quả:
- 3 agent instances được start
- Nginx phân tán requests round-robin
- Header `X-Served-By` cho thấy mỗi request được xử lý bởi instance khác nhau
- Nếu 1 instance die → Nginx tự chuyển traffic sang instances còn lại

### Exercise 5.5: Test stateless

Quy trình test:
1. Gửi request tạo conversation → response chứa `served_by: instance-1`
2. Kill instance-1: `docker compose kill -s TERM agent-1`
3. Gửi request tiếp → response chứa `served_by: instance-2`
4. Conversation history vẫn còn (vì lưu trong Redis, không trong memory)

Đây là bằng chứng stateless design hoạt động: bất kỳ instance nào cũng serve được request mà không mất context.
