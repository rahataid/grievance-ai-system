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

6. **Start microservices:**
   - Each service can be started individually. For example:
     ```bash
     cd services/api-gateway/app
     uvicorn main:app --reload
     ```
   - Repeat for other services (see their respective README/config).

7. **(Optional) Generate API keys:**

   ```bash
   ./scripts/generate_api_key.sh <identifier> [expires_days]
   ```

8. **Access API docs:**
   - Most FastAPI services expose Swagger UI at `/docs` (e.g., http://localhost:8000/docs)

See the `docs/` folder for more details on architecture, API, and advanced deployment.

## Production

- Use `deployments/k8s/` for Kubernetes
- See `docs/` for architecture and scaling

## API Key Authentication

- See `docs/api-key-auth.md` for full design and integration details
- Generate keys: `./scripts/generate_api_key.sh <identifier> [expires_days]`
- Protect FastAPI routes: add `Depends(verify_api_key)`
