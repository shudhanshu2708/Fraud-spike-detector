# Fraud-spike Detector

**ML-powered transaction fraud detection backend built with FastAPI, PostgreSQL, Redis, and scikit-learn.**

Fraud-spike Detector evaluates authenticated transactions using real-time behavioral features and a trained machine-learning model. Each transaction receives a fraud probability and is converted into an operational decision:

* 🟢 **SAFE** — low-risk transaction
* 🟡 **REVIEW** — suspicious transaction requiring human/admin review
* 🔴 **BLOCK** — high-risk transaction rejected before persistence

The project demonstrates how an ML fraud model can be integrated into a payment-style backend while maintaining **real-time behavioral context, explainability, reliability, idempotency, authentication, authorization, and automated testing**.

**Repository:** [github.com/shudhanshu2708/Fraud-spike-detector](https://github.com/shudhanshu2708/Fraud-spike-detector?utm_source=chatgpt.com)

---

## Problem

Transaction fraud is rarely identifiable from transaction amount alone.

Suspicious behavior can emerge from combinations of signals such as:

* Sudden transaction spikes
* High transaction frequency
* Unusual short-window transaction volume
* Unusual accumulated transaction value
* Previously unseen devices
* Previously unseen IP addresses
* Account-takeover-like behavior

A practical fraud system therefore needs both **transaction-level features** and **recent behavioral context**.

---

## Solution

Fraud-spike Detector combines:

1. **Machine learning** for fraud probability estimation
2. **Redis** for low-latency behavioral features
3. **PostgreSQL** for durable transaction persistence
4. **Validation-optimized thresholding** for fraud blocking
5. **Human-readable behavioral explanations**
6. **SAFE / REVIEW / BLOCK** risk decisioning
7. **Idempotency** for safe transaction retries
8. **Rate limiting** for transaction protection
9. **Authentication and role-based authorization**
10. **Automated testing** across the backend

---

# Architecture

```text
                         Client
                           |
                           v
                       FastAPI
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
   Authentication     Transactions      Admin Review
          |                |
          v                v
     PostgreSQL       Feature Retrieval
                           |
                    +------+------+
                    |             |
                    v             v
              Redis Velocity   Redis Identity
                    |             |
                    +------+------+
                           |
                           v
                    Feature Vector
                           |
                           v
                   ML Fraud Model
                           |
                           v
                  Fraud Probability
                           |
                           v
                  Risk Decision Engine
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           SAFE          REVIEW        BLOCK
             |             |             |
             v             v             X
        PostgreSQL     PostgreSQL     No persistence
```

---

# Transaction Risk Pipeline

Every transaction follows this flow:

```text
Request
   |
   v
Authentication
   |
   v
Rate-limit check
   |
   v
Idempotency check
   |
   v
Read Redis behavioral features
   |
   v
Check device/IP history
   |
   v
Generate ML fraud probability
   |
   v
Apply risk thresholds
   |
   +---- SAFE ------> Persist as APPROVED
   |
   +---- REVIEW ----> Persist as REVIEW
   |
   +---- BLOCK -----> Reject before persistence
```

---

# AI / ML Design

The fraud model is a **Logistic Regression classifier** trained using synthetic transaction data.

The model uses six features:

| Feature           | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `amount`          | Current transaction amount                               |
| `transactions_1m` | Transactions during the previous minute                  |
| `transactions_5m` | Transactions during the previous five minutes            |
| `amount_5m`       | Total transaction value during the previous five minutes |
| `new_device`      | Whether the device has not previously been seen          |
| `new_ip`          | Whether the IP address has not previously been seen      |

The training pipeline uses:

* `StandardScaler`
* Logistic Regression
* `class_weight="balanced"`
* Separate training, validation, and test datasets
* Validation-based threshold optimization
* Held-out test evaluation

### Why these features?

The model is intentionally designed around **behavior rather than only transaction amount**.

The synthetic dataset contains:

* Normal transactions
* Legitimate high-value transactions
* Legitimate new-device activity
* Velocity-based fraud
* Account takeover patterns
* Low-and-slow fraud

This prevents the model from simply learning:

> High amount = fraud

or:

> High velocity = fraud

---

# Risk Decisioning

The ML model produces a fraud probability between `0` and `1`.

The live application uses:

```text
SAFE
probability < 0.30

REVIEW
0.30 <= probability < block_threshold

BLOCK
probability >= block_threshold
```

The `0.30` SAFE boundary is a business-policy threshold.

The **BLOCK threshold is not hardcoded in the application**.

It is generated by `optimize_threshold.py`, stored in:

```text
data/models/thresholds.joblib
```

and loaded dynamically by:

```text
app/services/ml_model.py
```

The same optimized threshold is also used by `evaluate_model.py` for test-set evaluation.

This keeps the deployed decision logic aligned with the evaluated model configuration.

---

# Explainability

The ML probability is the primary risk signal.

The system also generates human-readable behavioral reasons, including:

```text
high_transaction_velocity_1m
high_transaction_velocity_5m
high_amount_velocity_5m
high_transaction_amount
new_device
new_ip
```

Example:

```json
{
  "risk_score": 0.8748,
  "decision": "BLOCK",
  "reasons": [
    "high_amount_velocity_5m",
    "new_device",
    "new_ip"
  ]
}
```

This separates three concepts:

```text
ML model
    ↓
"What is the estimated fraud probability?"

Risk signals
    ↓
"Which observable behaviors look unusual?"

Decision engine
    ↓
"What should the system do?"
```

The behavioral reasons are **not presented as formal ML feature attribution**. They are supporting explanations generated from observable transaction signals.

---

# Redis Feature Store

Redis provides low-latency derived behavioral features.

### Transaction velocity

```text
user:{user_id}:velocity
user:{user_id}:velocity:amounts
```

These support:

* 1-minute transaction count
* 5-minute transaction count
* 5-minute accumulated amount

### Identity history

Redis also stores previously observed:

* Devices
* IP addresses

### Refresh tokens

Refresh-token state is stored in Redis as part of the authentication system.

Redis is treated as a **derived feature store**, not the source of truth for transactions.

PostgreSQL remains responsible for durable transaction persistence.

---

# Reliability & Failure Handling

The system deliberately separates **durable state** from **derived feature state**.

### PostgreSQL

PostgreSQL is the source of truth for:

* Users
* Transactions
* Transaction status
* Risk information

### Redis

Redis stores derived behavioral features.

After an allowed transaction has been persisted, Redis feature updates are performed separately.

If a Redis update fails, the already-persisted transaction is not invalidated.

The API reports the feature-cache update status:

```json
{
  "feature_cache": {
    "velocity_updated": true,
    "identity_updated": true
  }
}
```

### Fraud feature retrieval failure

If the required Redis fraud features cannot be retrieved before the risk decision, the API returns:

```text
503 Service Unavailable
```

rather than silently making a fraud decision from incomplete behavioral data.

---

# Idempotency

Transaction creation requires an:

```text
Idempotency-Key
```

The system:

* Prevents duplicate processing of retried requests
* Returns the existing transaction for a valid retry
* Rejects reuse of an idempotency key with different transaction data
* Returns `409 Conflict` for conflicting reuse
* Uses a database uniqueness constraint as an additional concurrency safeguard

This protects transaction processing against client retries and network-level duplicate requests.

---

# Authentication & Authorization

The backend supports:

* User signup
* Login
* bcrypt password hashing
* JWT access tokens
* Short-lived access tokens
* Refresh tokens
* Refresh-token rotation
* Refresh-token revocation
* Logout
* Logout from all sessions
* Password changes
* Protected user profile
* Role-based authorization
* Customer/admin separation
* Transaction ownership enforcement

---

# Rate Limiting

Authenticated transaction creation is protected by rate limiting.

The transaction API currently limits a user to:

```text
30 requests / 60 seconds
```

The rate limiter prevents a single authenticated user from overwhelming the transaction-processing endpoint.

---

# Admin Review

Transactions classified as `REVIEW` can be handled by an administrator.

Administrators can:

* View transactions across users
* Filter transactions by status
* Approve `REVIEW` transactions
* Reject `REVIEW` transactions

Customers cannot perform administrative review actions.

This creates a human-in-the-loop path for transactions that are suspicious but do not meet the blocking threshold.

---

# Request Tracing & Observability

Every HTTP request receives a unique request ID.

The middleware:

* Generates a UUID request ID
* Stores it in request state
* Returns it through the `X-Request-ID` response header
* Logs request method
* Logs request path
* Logs response status
* Logs request duration

Example:

```text
request_id=<id>
method=POST
path=/transactions/
status=201
duration_ms=<value>
```

The ML model is loaded during application startup, and the `/health` endpoint reports whether the model is loaded.

---

# ML Data Pipeline

The complete model-development pipeline is:

```text
generate_dataset.py
        |
        v
transactions.csv
        |
        v
split_dataset.py
        |
        +---- train.csv
        +---- validation.csv
        +---- test.csv
        |
        v
train_model.py
        |
        +---- fraud_model.joblib
        +---- scaler.joblib
        |
        +---- optimize_threshold.py
        |             |
        |             v
        |       thresholds.joblib
        |
        v
evaluate_model.py
```

### Dataset generation

The synthetic dataset intentionally contains multiple behavioral patterns:

* Normal transactions
* Legitimate high-value transactions
* Legitimate new-device transactions
* Velocity fraud
* Account takeover
* Low-and-slow fraud

### Dataset split

The data is split into:

```text
70% training
15% validation
15% test
```

with stratification by fraud label.

### Threshold optimization

`optimize_threshold.py` evaluates thresholds from `0.10` to `0.90` and selects the threshold with the highest validation-set F1 score.

The resulting configuration is stored in:

```text
data/models/thresholds.joblib
```

---

# Evaluation Results

The model was evaluated on a **held-out test set**.

Current evaluation:

| Metric              |      Result |
| ------------------- | ----------: |
| ROC-AUC             |  **0.9670** |
| PR-AUC              |  **0.9338** |
| Precision           |  **0.8813** |
| Recall              |  **0.8155** |
| F1-score            |  **0.8471** |
| False-positive rate | **3.6622%** |

### Confusion Matrix

|                   | Predicted Legitimate | Predicted Fraud |
| ----------------- | -------------------: | --------------: |
| Actual Legitimate |                5,419 |             206 |
| Actual Fraud      |                  346 |           1,529 |

### False-positive exposure

```text
False-positive count:                    206
False-positive rate:                     3.6622%
Legitimate value incorrectly flagged:    ₹263,559.27
Average false-positive amount:           ₹1,279.41
Median false-positive amount:            ₹763.42
```

The ₹263,559.27 figure represents **legitimate transaction value flagged by the model in the synthetic test dataset**.

It is reported as false-positive exposure and **not as actual business loss**.

---

# API

## Authentication

| Method | Endpoint                | Description              |
| ------ | ----------------------- | ------------------------ |
| POST   | `/auth/signup`          | Register a user          |
| POST   | `/auth/login`           | Authenticate a user      |
| POST   | `/auth/refresh`         | Rotate refresh token     |
| POST   | `/auth/logout`          | Revoke refresh token     |
| GET    | `/auth/me`              | Get current user         |
| POST   | `/auth/change-password` | Change password          |
| POST   | `/auth/logout-all`      | Revoke all user sessions |

## Transactions

| Method | Endpoint                         | Description                     |
| ------ | -------------------------------- | ------------------------------- |
| POST   | `/transactions/`                 | Create and evaluate transaction |
| GET    | `/transactions/`                 | Get user's transactions         |
| GET    | `/transactions/{transaction_id}` | Get a transaction               |

## Admin

| Method | Endpoint                                       | Description                |
| ------ | ---------------------------------------------- | -------------------------- |
| GET    | `/admin/transactions`                          | View all transactions      |
| POST   | `/admin/transactions/{transaction_id}/approve` | Approve REVIEW transaction |
| POST   | `/admin/transactions/{transaction_id}/reject`  | Reject REVIEW transaction  |

## Health

| Method | Endpoint  | Description             |
| ------ | --------- | ----------------------- |
| GET    | `/health` | API and ML model health |

### Interactive API documentation

After starting the application:

```text
http://127.0.0.1:8000/docs
```

FastAPI provides interactive Swagger documentation at this endpoint.

---

# Tech Stack

### Backend

* Python 3.13
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* Alembic

### Machine Learning

* pandas
* NumPy
* scikit-learn
* joblib

### Infrastructure

* PostgreSQL 16
* Redis 7
* Docker
* Docker Compose

### Security & Testing

* JWT
* python-jose
* bcrypt
* pytest

---

# Project Structure

```text
Fraud-spike-detector/
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
|       +-- rate_limiting.py
|       +-- risk_engine.py
|       +-- velocity.py
|   |
|   +-- config.py
|   +-- database.py
|   +-- main.py
|   +-- redis_client.py
|
+-- alembic/
|   +-- versions/
|   +-- env.py
|
+-- data/
|   +-- models/
|   |   +-- fraud_model.joblib
|   |   +-- scaler.joblib
|   |   +-- thresholds.joblib
|   |
|   +-- generate_dataset.py
|   +-- split_dataset.py
|   +-- train_model.py
|   +-- optimize_threshold.py
|   +-- evaluate_model.py
|   +-- transactions.csv
|   +-- train.csv
|   +-- validation.csv
|   +-- test.csv
|
+-- tests/
|   +-- conftest.py
|   +-- test_auth.py
|   +-- test_refresh_tokens.py
|   +-- test_transactions.py
|   +-- test_api_transactions.py
|   +-- test_idempotency.py
|   +-- test_ml_model.py
|   +-- test_feature_cache_failure.py
|   +-- test_rate_limiting.py
|
+-- alembic.ini
+-- docker-compose.yml
+-- requirements.txt
+-- README.md
```

---

# Local Setup

## Requirements

* Python 3.13
* Docker Desktop
* Git

## Clone

```bash
git clone https://github.com/shudhanshu2708/Fraud-spike-detector.git
cd Fraud-spike-detector
```

## Create virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install dependencies

```powershell
pip install -r requirements.txt
```

## Environment configuration

Create a `.env` file.

Example local database configuration:

```env
DATABASE_URL=postgresql://fraud_user:fraud_pass@localhost:5433/fraud_spike_detector
```

Do not commit real credentials or secrets to Git.

---

# Start Infrastructure

Start PostgreSQL and Redis:

```powershell
docker compose up -d
```

The local services are exposed on:

```text
PostgreSQL → localhost:5433
Redis      → localhost:6380
```

Check containers:

```powershell
docker compose ps
```

---

# Database Migration

Run:

```powershell
alembic upgrade head
```

---

# Run the API

```powershell
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
http://127.0.0.1:8000/health
```

Expected health response:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

# Running Tests

Run the complete test suite:

```powershell
python -m pytest
```

Current result:

```text
49 passed
```

The test suite covers:

* Authentication
* Refresh tokens
* Transaction creation
* Transaction retrieval
* Authorization
* Transaction ownership
* Idempotency
* ML model behavior
* Risk decisions
* Redis feature-cache failures
* Rate limiting
* Admin transaction operations
* Pagination
* Status filtering

---

# Limitations

This project is a **fraud-detection prototype**, not a production payment fraud engine.

### Synthetic training data

The model is trained and evaluated using generated transaction data rather than real payment data.

Therefore, the reported metrics should not be interpreted as production fraud-detection performance.

### Limited feature set

The current model uses six features.

A production implementation could incorporate additional signals such as:

* Merchant history
* User transaction history
* Geographic consistency
* Payment instrument behavior
* Device fingerprinting
* Historical fraud patterns
* Chargeback information
* Network relationships

### Model explainability

The current explanation layer provides behavioral risk signals but does not implement formal SHAP or LIME attribution.

### Threshold optimization

The blocking threshold is optimized using validation-set F1 score.

A production payment system would normally incorporate business costs associated with:

* False positives
* False negatives
* Manual review
* Fraud losses
* Customer friction

---

# Design Principles

### ML estimates risk; application logic makes the decision

The ML model produces the fraud probability.

The application applies business-policy thresholds to determine SAFE, REVIEW, or BLOCK.

### Redis is derived state

Redis provides low-latency behavioral context but is not the durable transaction source of truth.

### High transaction value does not automatically mean fraud

The training dataset explicitly contains legitimate high-value transactions.

### Fraud is not synonymous with velocity

The training dataset includes low-and-slow fraud patterns.

### Suspicious does not always mean block

The REVIEW state provides a human-in-the-loop path for uncertain transactions.

### Durable state and derived state are separated

Transactions are persisted in PostgreSQL independently from Redis feature updates.

---

# Buildathon Summary

Fraud-spike Detector demonstrates an end-to-end transaction fraud-risk system rather than a standalone ML classifier.

The system combines:

```text
FastAPI
   +
Authentication & Authorization
   +
PostgreSQL
   +
Redis
   +
Real-time Behavioral Features
   +
Machine Learning
   +
Validation-Optimized Thresholding
   +
Risk Explanations
   +
Idempotency
   +
Rate Limiting
   +
Admin Review
   +
Automated Testing
```

### Current verification

```text
49 automated tests passing

ROC-AUC: 0.9670
PR-AUC:  0.9338
F1-score: 0.8471
```

The project is intentionally presented as a prototype using synthetic data, with the architecture focused on demonstrating **real-time fraud-risk scoring, operational decisioning, reliability, and explainability**.
