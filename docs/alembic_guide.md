## Alembic & Project Change Log

This document summarizes the key changes and migrations made in the repository.

### 2026-05-04: Added New Tables & Schema Changes

- **New Tables Added:**
  - `apps` table:
    - Fields: `id` (UUID, PK), `name`, `email`, `is_verified`.
  - `audios` table:
    - Fields: `id` (UUID, PK), `app_name` (FK to `apps.name`), `url`, `status`, `current_stage`.
  - `categories` table:
    - Fields: `id` (PK), `app_name` (FK to `apps.name`), `categories` (JSON).

- **Schema Changes:**
  - `api_keys` table:
    - Added: `app_id` (String).
    - Removed: `tenant_id`, `user_id`.
  - `grievances` table:
    - Added: `audio_id` (UUID, FK to `audios.id`).

---

### 2026-05-01: Initial Migration & Project Structure

- **Alembic Migration Setup:**
  - Alembic was configured for database migrations.
  - `alembic.ini` and `migrations/` directory added.
  - `migrations/env.py` set up for async migrations using SQLAlchemy and Pydantic settings.
  - Models imported from `shared/database/models.py`.

- **Initial Migration Script:**
  - Created `api_keys` table:
    - Fields: `id`, `identifier`, `api_key_hash`, `is_active`, `expires_on`, `created_at`, `last_used_at`, `user_id`, `tenant_id`, `scopes`, `rate_limit`.
  - Created `grievances` table:
    - Fields: `id`, `beneficiary_id`, `confidence`, `transcript`, `language`, `grievance_detected`, `category`, `sentiment`, `urgency`, `severity_score`, `recommended_action`, `keywords`, `created_at`, `updated_at`, `api_key_id` (FK to `api_keys`).

---

For more details, see the main [README.md](../README.md) and other docs in this folder.
