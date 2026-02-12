# Prueba FastAPI

REST API for patient management with:
- full patient CRUD
- document photo upload/download
- paginated listing
- background confirmation email sending

Main stack: `Python 3.13`, `FastAPI`, `SQLAlchemy async + asyncpg`, `Alembic`, `uv`, `Docker/Compose`, local file storage, and SMTP Sandbox (Mailtrap) with noop fallback.

## Table of contents

- [1) Project overview](#1-project-overview)
- [2) Prerequisites](#2-prerequisites)
- [3) Local quickstart](#3-local-quickstart)
- [4) Docker quickstart](#4-docker-quickstart)
- [5) Configuration (environment variables)](#5-configuration-environment-variables)
- [6) Database and migrations (Alembic)](#6-database-and-migrations-alembic)
- [7) Document uploads](#7-document-uploads)
- [8) Emails with Mailtrap Sandbox](#8-emails-with-mailtrap-sandbox)
- [9) Testing](#9-testing)
- [10) Linting, formatting, and pre-commit](#10-linting-formatting-and-pre-commit)
- [11) CI (GitHub Actions)](#11-ci-github-actions)
- [12) Repository layout](#12-repository-layout)
- [13) Makefile quick reference](#13-makefile-quick-reference)

## 1) Project overview

### What the API does

Main endpoints under `/patients`:
- `POST /patients`: create patient (multipart/form-data with document file).
- `GET /patients`: list patients with pagination (`page`, `size`).
- `GET /patients/{patient_id}`: get patient by ID.
- `GET /patients/{patient_id}/document-photo`: return document photo binary.
- `PUT /patients/{patient_id}`: full replacement (optionally replaces document).
- `PATCH /patients/{patient_id}`: partial update.
- `DELETE /patients/{patient_id}`: delete patient and associated file.

### Key technical decisions

- Async API with FastAPI.
- Async persistence with SQLAlchemy + asyncpg.
- Migrations with Alembic.
- Uploads stored in local filesystem (`UPLOADS_DIR`) and metadata in DB.
- Notification layer with SMTP (Mailtrap Sandbox) or `NoopNotificationClient` if credentials are missing.
- Async tests with pytest + httpx AsyncClient + testcontainers.

## 2) Prerequisites

- Python `3.13+`
- [uv (Astral)](https://docs.astral.sh/uv/getting-started/installation/)
- Docker + Docker Compose

## 3) Local quickstart

### 1. Clone and enter the repository

```bash
git clone <REPOSITORY_URL> <directory>
cd <directory>
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if you need to change credentials/host/ports.

### 3. Install dependencies with `uv`

Canonical command from this repository:

```bash
make install
```

Note: `uv` creates/uses `.venv` and runs tools with `uv run ...`.

### 4. Start only the database (development)

```bash
make dev
```

### 5. Apply migrations

```bash
make deploy-migrations
```

### 6. Start the API with hot reload

```bash
make api
```

API available at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 4) Docker quickstart

This repository already defines API + Postgres in `docker-compose.yml`, and the API is built from `Dockerfile`.

```bash
cp .env.example .env
make prod
```

View logs:

```bash
make logs
```

Notes:
- API runs on `http://localhost:${PORT:-8000}`.
- In container startup, it automatically runs: `alembic upgrade head && uvicorn ...`.
- The `uploads_data` volume persists uploaded files.

## 5) Configuration (environment variables)

Relevant variables:

| Variable | Required | Example / Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/prueba` | Async DB URL for SQLAlchemy/asyncpg. |
| `APP_ENV` | No | `development` | Application environment. |
| `LOG_LEVEL` | No | `INFO` | Log level. |
| `UPLOADS_DIR` | No | `data/uploads` | Local directory for uploaded files. |
| `MAIL_HOST` | No | `sandbox.smtp.mailtrap.io` | SMTP host (Mailtrap Sandbox). |
| `MAIL_PORT` | No | `587` | SMTP port. |
| `MAIL_USERNAME` | No | `your_mailtrap_username` | SMTP username. |
| `MAIL_PASSWORD` | No | `your_mailtrap_password` | SMTP password. |
| `MAIL_FROM_EMAIL` | No | `noreply@prueba-fastapi.com` | Sender email. |
| `MAIL_FROM_NAME` | No | `Patient Registry` | Sender display name. |
| `POSTGRES_USER` | For Docker Compose | `postgres` | Postgres user in Compose. |
| `POSTGRES_PASSWORD` | For Docker Compose | `postgres` | Postgres password in Compose. |
| `POSTGRES_DB` | For Docker Compose | `prueba` | Database name in Compose. |
| `PORT` | No (Docker Compose) | `8000` | Host port exposed for API. |

If SMTP variables are missing, the app falls back to `NoopNotificationClient` (no real email sent).

## 6) Database and migrations (Alembic)

### Main commands

Create migration:

```bash
make create-migration message="description"
```

Apply migrations:

```bash
make deploy-migrations
```

Rollback last migration:

```bash
make rollback-migrations
```

### Local vs Docker

- Local: use `make deploy-migrations` with `.env` and `DATABASE_URL`.
- Docker (`docker-compose.yml`): API already runs `alembic upgrade head` at startup.
- Manual inside container (if needed):

```bash
docker compose exec api alembic upgrade head
```

## 7) Document uploads

### Request format

`POST /patients` requires `multipart/form-data`:
- `full_name` (string)
- `email` (valid email)
- `phone_number` (international format)
- `document_photo` (file `jpg/jpeg/png`, max `5MB`)

### Storage behavior

- Physical file: saved in `UPLOADS_DIR` with UUID filename (no extension).
- Metadata in DB: `files` table (original filename, storage_path, content type, size, timestamps).
- Relation to patient: patients.document_file_id.
- Binary download: `GET /patients/{id}/document-photo`.

## 8) Emails with Mailtrap Sandbox

This integration uses Mailtrap Sandbox SMTP for email testing. It does not deliver to real inboxes on the internet; emails are captured in your Mailtrap inbox.

### Where to find credentials in Mailtrap

1. Sign in to Mailtrap.
2. Go to `Email Testing`.
3. Open or create an Inbox.
4. Open `SMTP settings`.
5. Copy `Host`, `Port`, `Username`, and `Password`.

### Enable it locally

1. Fill `.env` with: `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM_EMAIL`, `MAIL_FROM_NAME`.
2. Restart the API.
3. Create a patient (`POST /patients`).
4. Verify the message in Mailtrap inbox.

If SMTP configuration is incomplete, the app keeps running and uses noop client logging only.

## 9) Testing

Run full test suite:

```bash
make test
```

Or directly:

```bash
uv run pytest
```

Coverage:

```bash
make test-cov
```

`term-missing` shows uncovered lines, and `html` report is generated in `htmlcov/`.

To reproduce CI condition (minimum 80%):

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Important notes:
- Tests use `testcontainers` with PostgreSQL: Docker must be running.
- Coverage config is in `pyproject.toml` (`[tool.coverage.*]`), not in `.coveragerc`.

## 10) Linting, formatting, and pre-commit

Integrated command:

```bash
make lint
```

Includes:
- `ruff check .`
- `ruff format --check .`
- `ty check .`

Pre-commit:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Configured hooks:
- Ruff lint
- Type check (`ty`)
- Tests (`make test`)

## 11) CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml`

Runs on `push` and `pull_request` to `main` and executes:
- dependency install with `uv sync --all-extras --dev`
- `ruff check .`
- `ty check`
- `pytest` with coverage and `--cov-fail-under=80`

## 12) Repository layout

```text
app/
  api/             # FastAPI routers
  services/        # Business logic (patients, storage, notifications)
  repositories/    # Data access layer
  models/          # SQLAlchemy models
  schemas/         # Pydantic DTOs
  db/              # Async engine and session
  core/            # Settings, exceptions, logging, constants
migrations/        # Alembic env + versions
tests/             # Async API/service tests
```

Dependency injection:
- `app/dependencies.py` defines providers (`PatientService`, `NotificationClient`, etc.).
- Tests override dependencies with `app.dependency_overrides` (e.g. `get_session` and `get_notification_client`) to isolate infrastructure and control behavior.

## 13) Makefile quick reference

Available targets in this repository:

```bash
make help
make api
make prod
make logs
make dev
make install
make test
make test-cov
make lint
make create-migration message="description"
make deploy-migrations
make rollback-migrations
make clean
```

