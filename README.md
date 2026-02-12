# Prueba FastAPI

## Project structure

```
src/app/
├── main.py          # FastAPI app entry
├── api/             # Routers / controllers
├── services/        # Business logic
├── repositories/    # DB access
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic DTOs
├── db/              # Engine, session, base
└── core/            # Settings, logging, security
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (or pip)
- Docker & Docker Compose (for PostgreSQL)
