# Vendly

A production-grade e-commerce backend built with FastAPI, PostgreSQL, and Redis — focused on demonstrating real-world backend engineering practices around authentication, security, and clean API design.

> **Status:** Auth module in progress. Core e-commerce features (products, cart, orders, payments) are planned next.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (via SQLAlchemy ORM)
- **Cache / Token Store:** Redis
- **Auth:** JWT (access + refresh tokens) via `python-jose`
- **Password Hashing:** `bcrypt` (direct, not via `passlib` — see Notes)
- **Config Management:** `pydantic-settings`
- **Containerization:** Docker (Postgres + Redis run as containers locally)

## Features Implemented

### Auth Module

| Route | Method | Status | Description |
|---|---|---|---|
| `/auth/signup` | POST | ✅ Done | Registers a new user, hashes password with bcrypt, returns access + refresh tokens |
| `/auth/login` | POST | ✅ Done | Verifies credentials, returns access + refresh tokens |
| `/auth/refresh` | POST | ✅ Done | Verifies refresh token against Redis, **rotates** it (old token is invalidated), returns a new access + refresh token pair |
| `/auth/logout` | POST | 🔲 Pending | Will revoke the refresh token from Redis |
| `/auth/me` | GET | 🔲 Pending | Will return current authenticated user's info (protected route) |
| `/auth/change-password` | POST | 🔲 Pending | Optional — change password for logged-in user |
| `/auth/logout-all` | POST | 🔲 Pending | Optional — revoke all active sessions for a user |

### Security Design Choices

- **Password hashing:** Passwords are hashed with `bcrypt` before storage — never stored in plain text.
- **JWT access tokens:** Short-lived (15 min default), stateless, signed with a secret key.
- **Refresh token rotation:** Refresh tokens are random, cryptographically secure strings (`secrets.token_urlsafe`) stored in Redis with an expiry (7 days default). Each refresh token can be used **exactly once** — using it issues a new refresh token and immediately invalidates the old one. This limits the damage if a refresh token is ever leaked.
- **Role-based structure:** `User` model includes a `role` field (`customer` / `admin`) via a Python enum, enforced at the DB level.

## Project Structure

```
vendly/
├── app/
│   ├── main.py                 # App entrypoint, router mounting, table creation
│   ├── config.py               # Environment-based settings (pydantic-settings)
│   ├── database.py              # SQLAlchemy engine, session, Base
│   ├── redis_client.py         # Redis connection client
│   ├── models/
│   │   └── user.py             # User table definition
│   ├── schemas/
│   │   └── auth.py             # Pydantic request/response schemas
│   └── auth/
│       ├── security.py         # Password hashing, JWT creation, refresh token storage
│       ├── dependencies.py     # get_current_user (JWT verification dependency)
│       └── router.py           # Auth route handlers
├── requirements.txt
├── docker-compose.yml           # (planned)
├── .env.example
└── .gitignore
```

## Setup

### Prerequisites
- Python 3.13
- Docker Desktop (for Postgres + Redis containers)

### 1. Clone and set up virtual environment
```bash
git clone <repo-url>
cd vendly
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
```

### 2. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Start Postgres and Redis (Docker)
```bash
docker run --name vendly-postgres -e POSTGRES_USER=vendly_user -e POSTGRES_PASSWORD=vendly_pass -e POSTGRES_DB=vendly -p 5433:5432 -d postgres

docker run --name vendly-redis -p 6380:6379 -d redis
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in real values:
```
DATABASE_URL=postgresql://vendly_user:vendly_pass@localhost:5433/vendly
JWT_SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6380/0
```

### 5. Run the server
```bash
python -m uvicorn app.main:app --reload
```

API docs available at: `http://127.0.0.1:8000/docs`

## Notes / Known Gotchas

- **`passlib` was dropped** in favor of calling `bcrypt` directly, due to a compatibility bug between `passlib`'s bcrypt backend detection and newer `bcrypt` (4.1+) releases.
- Docker containers do **not** auto-restart after a system reboot by default. Run `docker start vendly-postgres vendly-redis` (or set a restart policy) after restarting your machine.
- Always activate the virtual environment before installing packages or running the server — mixing a global Python install with the project's venv is a common source of `ModuleNotFoundError`.

## Roadmap

- [ ] Finish remaining auth routes (`/logout`, `/me`, `/change-password`, `/logout-all`)
- [ ] Products module (CRUD, categories, search/filter)
- [ ] Cart module (Redis-backed)
- [ ] Orders module (status transitions, order history)
- [ ] Mock payment flow with idempotency handling
- [ ] Dockerize the full app (`docker-compose.yml`)
- [ ] Deploy (Railway / Render)
