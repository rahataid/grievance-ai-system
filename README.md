# Sentiment Grievance System

A distributed, event-driven microservices system for sentiment analysis and grievance management.

## Code Structure

```
grievance-ai-system/
├── alembic.ini
├── config.py
├── docker-compose.yml
├── main.py
├── pyproject.toml
├── README.md
├── docs/                # Documentation (architecture, API, guides)
├── infra/               # Infrastructure configs (Postgres, etc.)
├── migrations/          # Alembic migration scripts
├── scripts/             # Utility scripts (API key generation, etc.)
├── services/            # All microservices
│   ├── analytics-service/
│   ├── api-gateway/
│   ├── asr-service/
│   ├── audio-service/
│   ├── auth-service/
│   ├── language-service/
│   ├── nlp-service/
│   ├── persistence-service/
│   ├── translation-service/
│   └── urgency-service/
├── shared/              # Shared code (schemas, utils, messaging)
│   ├── constants/
│   ├── database/
│   ├── messaging/
│   ├── schemas/
│   └── utils/
└── ...
```

Each microservice contains its own `app/`, `Dockerfile`, and configs.

## How to Run (Local Development)

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd grievance-ai-system
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env` (if present) and fill in required values.

3. **Start infrastructure (Postgres, RabbitMQ, etc.):**

   ```bash
   docker-compose up -d
   ```

4. **Install dependencies and activate virtual environment:**

   Sync the project dependencies using uv:

   ```bash
   uv sync
   ```

   This will create a virtual environment and install all required packages defined in `pyproject.toml`.

   ```bash
   source .venv/bin/activate
   ```

5. **Run database migrations (if needed):**

   ```bash
   alembic upgrade head
   ```

6. Export the RabbitMQ connection used by the workers:
   ```bash
   export RABBIT_URL=amqp://sentiment:password@localhost:5672/
   ```

## Run The Pipeline

Start all worker services from the repository root:

```bash
pkill -f 'app.main' || true
rm -f logs/*.log
bash scripts/run_workers.sh
```

This starts these workers in the background and writes logs to `logs/*.log`:

- `audio-service`
- `asr-service`
- `language-service`
- `translation-service`
- `nlp-service`
- `urgency-service`
- `persistence-service`

To watch the pipeline live:

To publish a test message into the first queue:

```bash
python tests/test_pipeline.py
```

## What Happens When You Run It

The current test publishes one message with routing key `audio.raw`. The workers then process it in this order:

```text
audio.raw -> audio.uploaded -> transcription.completed -> text.translated -> nlp.analyzed -> urgency.derived
```

Observed behavior with the current stub implementations:

- `audio-service` saves the incoming bytes to `services/audio-service/uploads/` and converts the file path to a `.wav` path.
- `asr-service` creates a fake transcript based on the audio path.
- `language-service` detects the transcript as English and skips translation.
- `translation-service` stays idle for this test because only non-English messages are routed there.
- `nlp-service` produces stub sentiment, emotion, and category values.
- `urgency-service` derives an urgency level from the NLP output.
- `persistence-service` prints the final payload to its log as the terminal stage.

For the current test payload, the final result is an English path with a neutral NLP result and `low` urgency.

## Example Logs

After a successful run, you should see output like this:

```text
audio-service.log        Processed audio -> uploads/<file>.wav
asr-service.log          Transcribed: Transcription of uploads/<file>.wav
language-service.log     English detected -> skipping translation
nlp-service.log          NLP done -> {'sentiment': 'neutral', 'emotion': 'calm', 'category': 'general'}
urgency-service.log      urgency: low
persistence-service.log  persisted: test-001
```

## Stop The Pipeline

Stop the worker processes:

```bash
pkill -f 'app.main'
```

Stop infrastructure:

```bash
docker-compose down
```

## Production

- Use `deployments/k8s/` for Kubernetes
- See `docs/` for architecture and scaling

## API Key Authentication

- See `docs/api-key-auth.md` for full design and integration details
- Generate keys: `./scripts/generate_api_key.sh <identifier> [expires_days]`
- Protect FastAPI routes: add `Depends(verify_api_key)`
- The API gateway also enforces API key checks in middleware for protected routes

---

## Running the API Gateway

The API Gateway is a FastAPI app located at `services/api-gateway/`.

### Prerequisites

Make sure you have a virtual environment with dependencies installed (see **Local Setup** above). The gateway only needs `fastapi`, `uvicorn`, and `python-multipart`:

```bash
uv pip install --python .venv/bin/python fastapi uvicorn python-multipart
```

### Start the server

**Option A — from the repo root** (recommended, no `cd` needed):

```bash
source .venv/bin/activate
PYTHONPATH=services/api-gateway:. uvicorn app.main:app --app-dir services/api-gateway --reload --port 8000
```

This repo-root command needs both import roots:

- `services/api-gateway` so `app.main` resolves
- `.` so shared modules like `shared.database.models` and `services.auth_service` resolve

Without the extra `PYTHONPATH`, `uvicorn --app-dir` adds only `services/api-gateway` to Python's import path, which causes `ModuleNotFoundError: No module named 'shared'`.

**Option B — from inside the service directory**:

```bash
source .venv/bin/activate
cd services/api-gateway
PYTHONPATH=../.. uvicorn app.main:app --reload --port 8000
```

**Option C — use the repo launcher**:

```bash
source .venv/bin/activate
.venv/bin/python main.py
```

**Option C — start workers + API together** (single command):

```bash
source .venv/bin/activate
bash scripts/run_api_with_workers.sh
```

This starts all worker consumers (`audio-service`, `asr-service`, `language-service`, `translation-service`, `nlp-service`, `urgency-service`, `persistence-service`) and then runs the API Gateway.

> **Stop behavior:** `Ctrl+C` stops only FastAPI. Workers are background processes; stop them with:
>
> ```bash
> pkill -f 'app.main'
> ```

> **Note:** Do not use `services.api_gateway.app.main` — the directory name contains a hyphen which Python cannot import as a module. Use one of the startup options above.

The server will be available at **http://localhost:8000**.

### Interactive API docs

| URL                                | Description                              |
| ---------------------------------- | ---------------------------------------- |
| http://localhost:8000/docs         | Swagger UI (try endpoints interactively) |
| http://localhost:8000/redoc        | ReDoc documentation                      |
| http://localhost:8000/openapi.json | Raw OpenAPI schema                       |

### Available endpoints

| Method   | Path                | Description                         |
| -------- | ------------------- | ----------------------------------- |
| `POST`   | `/auth/register`    | Register a new application          |
| `POST`   | `/auth/login`       | Login and receive a JWT token       |
| `POST`   | `/auth/api-key`     | Generate an API key from a JWT      |
| `DELETE` | `/auth/api-key`     | Revoke the active API key           |
| `GET`    | `/auth/verify`      | Verify an API key                   |
| `POST`   | `/audio`            | Upload an audio file for processing |
| `GET`    | `/audio/{audio_id}` | Poll processing status and results  |
| `GET`    | `/health`           | Health check                        |

### Auth rules

- Public routes: `/health`, `/docs`, `/openapi.json`, `/redoc`, `/auth/register`, `/auth/login`
- JWT bearer token routes: `POST /auth/api-key`, `DELETE /auth/api-key`
- API key routes: `GET /auth/verify`, `POST /audio`, `GET /audio/{audio_id}`
- Protected requests are enforced at the API gateway middleware layer, and the audio routes also declare API key security in OpenAPI so Swagger shows lock icons

### Quick smoke test with curl

```bash
# Register an app
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"my_app","email":"test@example.com"}'

# Login and capture JWT
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
   -d '{"email":"test@example.com"}')

JWT_TOKEN=$(printf '%s' "$LOGIN_RESPONSE" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

# Generate an API key from the JWT
API_KEY_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/api-key \
   -H "Authorization: Bearer $JWT_TOKEN")

API_KEY=$(printf '%s' "$API_KEY_RESPONSE" | sed -n 's/.*"api_key":"\([^"]*\)".*/\1/p')

# Verify the API key
curl -s http://localhost:8000/auth/verify \
   -H "X-API-Key: $API_KEY"

# Upload audio with the API key
curl -s -X POST http://localhost:8000/audio \
   -H "X-API-Key: $API_KEY" \
  -F "file=@/path/to/audio.wav"

# Poll status
curl -s http://localhost:8000/audio/<audio_id> \
   -H "X-API-Key: $API_KEY"

# Revoke the API key
curl -s -X DELETE http://localhost:8000/auth/api-key \
   -H "Authorization: Bearer $JWT_TOKEN"
```

Auth flow summary:

- Use `/auth/register` to create an app record.
- Use `/auth/login` to get a JWT bearer token.
- Use that JWT only for `/auth/api-key` create and revoke operations.
- Use the API key in `X-API-Key` for protected routes such as `/audio` and `/auth/verify`.
