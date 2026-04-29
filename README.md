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

## Quick Start
1. Copy `.env.example` to `.env` and fill in values
2. `docker-compose up -d` to start core infra
3. Deploy services from `services/`

## Production
- Use `deployments/k8s/` for Kubernetes
- See `docs/` for architecture and scaling

## API Key Authentication
- See `docs/api-key-auth.md` for full design and integration details
- Generate keys: `./scripts/generate_api_key.sh <identifier> [expires_days]`
- Protect FastAPI routes: add `Depends(verify_api_key)`
