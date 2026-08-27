# [NEW_PROJECT_NAME]

ML-powered transaction fraud detection backend built with FastAPI, PostgreSQL, Redis, and scikit-learn.

The system evaluates transactions using real-time behavioral features and a trained machine-learning model, then classifies them as:

- SAFE
- REVIEW
- BLOCK

It also demonstrates authentication, authorization, idempotency, database migrations, Redis feature storage, and automated testing.

## Architecture

Client
  |
  v
FastAPI
  |
  +-- Authentication --> PostgreSQL
  |
  +-- Transactions
         |
         +--> Redis Velocity Features
         |
         +--> Redis Device/IP Features
         |
         +--> ML Fraud Model
                    |
                    +--> SAFE
                    +--> REVIEW
                    +--> BLOCK
         |
         v
     PostgreSQL

## Features

### Authentication

- User signup and login
- bcrypt password hashing
- JWT access tokens
- Short-lived access tokens
- Secure refresh tokens
- Refresh-token rotation
- Refresh-token revocation
- Logout
- Logout from all sessions
- Password change
- Protected user profile
- Role-based authorization

### Transaction Processing

- Authenticated transaction creation
- Transaction persistence with PostgreSQL
- Transaction history
- Pagination
- Status filtering
- Transaction ownership enforcement
- Individual transaction lookup
- Risk information persistence

### Fraud Detection

The fraud engine uses:

- Transaction count in the last 1 minute
- Transaction count in the last 5 minutes
- Transaction amount in the last 5 minutes
- New device detection
- New IP detection
- Current transaction amount

The ML model produces a fraud probability which is mapped to:

SAFE     < 0.30

REVIEW   0.30 - < 0.70

BLOCK    >= 0.70

### Redis Feature Store

Redis stores derived behavioral features including:

- Transaction velocity
- Rolling transaction amounts
- Known devices
- Known IP addresses
- Refresh tokens

Redis is treated as a derived feature store rather than the source of truth for transactions.

### Idempotency

Transaction creation requires an `Idempotency-Key`.

The system:

- Prevents duplicate processing of the same request
- Returns the existing transaction for a valid retry
- Returns `409 Conflict` when an idempotency key is reused for different transaction data
- Uses a database uniqueness constraint for additional protection against concurrent requests

### Admin Review

Administrators can:

- View all transactions
- Filter transactions by status
- Approve REVIEW transactions
- Reject REVIEW transactions

Customers cannot access admin endpoints.

## API

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a user |
| POST | `/auth/login` | Authenticate a user |
| POST | `/auth/refresh` | Rotate refresh token |
| POST | `/auth/logout` | Revoke refresh token |
| GET | `/auth/me` | Get current user |
| POST | `/auth/change-password` | Change password |
| POST | `/auth/logout-all` | Revoke all user sessions |

### Transactions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/transactions/` | Create and evaluate transaction |
| GET | `/transactions/` | Get user's transactions |
| GET | `/transactions/{transaction_id}` | Get a transaction |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/transactions` | View all transactions |
| POST | `/admin/transactions/{transaction_id}/approve` | Approve REVIEW transaction |
| POST | `/admin/transactions/{transaction_id}/reject` | Reject REVIEW transaction |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API and ML model health |

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## ML Pipeline

The model development pipeline is located in `data/`.

```text
transactions.csv
      |
      v
generate_dataset.py
      |
      v
split_dataset.py
      |
      +--> train.csv
      +--> validation.csv
      +--> test.csv
      |
      v
train_model.py
      |
      v
fraud_model.joblib
scaler.joblib
      |
      +--> evaluate_model.py
      |
      +--> optimize_threshold.py

Tech Stack
Python
FastAPI
Uvicorn
PostgreSQL
SQLAlchemy
Alembic
Redis
Pydantic
pydantic-settings
JWT
python-jose
bcrypt
pandas
NumPy
scikit-learn
joblib
pytest
Docker / Docker Compose

[NEW_PROJECT_NAME]/
|
+-- app/
|   +-- api/
|   |   +-- admin.py
|   |   +-- transactions.py
|   |
|   +-- auth/
|   |   +-- dependencies.py
|   |   +-- router.py
|   |   +-- security.py
|   |
|   +-- models/
|   |   +-- transaction.py
|   |   +-- user.py
|   |
|   +-- schemas/
|   |   +-- auth.py
|   |   +-- risk.py
|   |   +-- transaction.py
|   |
|   +-- services/
|       +-- identity_features.py
|       +-- ml_model.py
|       +-- risk_engine.py
|       +-- velocity.py
|
+-- alembic/
|   +-- versions/
|   +-- env.py
|
+-- data/
|   +-- models/
|   |   +-- fraud_model.joblib
|   |   +-- scaler.joblib
|   |
|   +-- generate_dataset.py
|   +-- split_dataset.py
|   +-- train_model.py
|   +-- evaluate_model.py
|   +-- optimize_threshold.py
|   +-- transactions.csv
|   +-- train.csv
|   +-- validation.csv
|   +-- test.csv
|
+-- tests/
|   +-- test_auth.py
|   +-- test_refresh_tokens.py
|   +-- test_transactions.py
|   +-- test_api_transactions.py
|   +-- test_idempotency.py
|   +-- test_ml_model.py
|   +-- test_feature_cache_failure.py
|
+-- alembic.ini
+-- docker-compose.yml
+-- requirements.txt
+-- .gitignore

Setup
Requirements
Python 3.13
Docker Desktop
Git

git clone <(https://github.com/shudhanshu2708/Vendly)>
cd [NEW_PROJECT_NAME]
