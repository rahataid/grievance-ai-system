# Sentiment Grievance System

A distributed, event-driven microservices system for sentiment analysis and grievance management.

## Structure
- **services/**: All microservices (API gateway, NLP, audio, etc.)
- **shared/**: Shared code (schemas, utils, messaging, etc.)
- **infra/**: Infrastructure configs (RabbitMQ, Redis, Postgres, monitoring)
- **deployments/**: Kubernetes manifests, HPA, configmaps, secrets
- **docker/**: Dockerfiles, compose files
- **scripts/**: Utility scripts (seed, replay, load gen, etc.)
- **tests/**: Unit, integration, load tests
- **docs/**: Architecture, API, event flow, scaling

## Local Setup
1. Copy `.env.example` to `.env`.
2. Create a virtual environment with `uv`:
   ```bash
   uv venv .venv --python 3.11
   source .venv/bin/activate
   ```
3. Install the packages currently used by the workers and test script:
   ```bash
   uv pip install --python .venv/bin/python aio-pika fastapi sqlalchemy alembic psycopg2-binary uvicorn pytest
   ```
4. Start infrastructure:
   ```bash
   docker-compose up -d rabbitmq redis postgres postgres-migrations
   ```
5. Export the RabbitMQ connection used by the workers:
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
uvicorn app.main:app --app-dir services/api-gateway --reload --port 8000
```

**Option B — from inside the service directory**:

```bash
source .venv/bin/activate
cd services/api-gateway
uvicorn app.main:app --reload --port 8000
```

> **Note:** Do not use `services.api_gateway.app.main` — the directory name contains a hyphen which Python cannot import as a module. Always use one of the two options above.

The server will be available at **http://localhost:8000**.

### Interactive API docs

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (try endpoints interactively) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/openapi.json | Raw OpenAPI schema |

### Available endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register a new application |
| `POST` | `/auth/login` | Login and receive a JWT token |
| `GET` | `/auth/verify` | Verify an API key or JWT token |
| `POST` | `/auth/api-key` | Generate a new API key |
| `POST` | `/audio` | Upload an audio file for processing |
| `GET` | `/audio/{audio_id}` | Poll processing status and results |
| `GET` | `/health` | Health check |

### Quick smoke test with curl

```bash
# Register
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"my_app","email":"test@example.com"}'

# Login
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Upload audio (requires X-API-Key or Authorization header)
curl -s -X POST http://localhost:8000/audio \
  -H "X-API-Key: my_key" \
  -F "file=@/path/to/audio.wav"

# Poll status
curl -s http://localhost:8000/audio/<audio_id> \
  -H "X-API-Key: my_key"
```
