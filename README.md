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
