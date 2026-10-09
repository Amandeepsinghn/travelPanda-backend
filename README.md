# travelPanda-backend

FastAPI backend with async SQLAlchemy and JWT auth.

## Setup

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Auth

- `POST /api/v1/auth/register` — `{ "email", "first_name", "last_name", "password" }`
- `POST /api/v1/auth/login` — `{ "email", "password" }` → bearer token
- `GET /api/v1/auth/me` — `Authorization: Bearer <token>`

## Catalog (public read)

- `GET /api/v1/destinations`
- `GET /api/v1/destinations/{slug}`
- `GET /api/v1/packages?destination_slug=goa`
- `GET /api/v1/packages/{slug}` — itinerary, hotels, media
- `GET /api/v1/hotels?city=Goa`
- `GET /api/v1/hotels/{slug}`

## Catalog admin (`role=admin` bearer)

- `POST/PATCH /api/v1/destinations`
- `POST/PATCH /api/v1/packages`
- `POST/PATCH /api/v1/hotels`

## Comments

- `GET /api/v1/packages/{slug}/comments`
- `POST /api/v1/packages/{slug}/comments` — bearer, `{ "body", "rating?" }`
- `GET /api/v1/hotels/{slug}/comments`
- `POST /api/v1/hotels/{slug}/comments` — bearer, `{ "body", "rating?" }`
- `DELETE /api/v1/comments/{id}` — owner or admin
