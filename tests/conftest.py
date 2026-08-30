import pytest
import redis

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.security import (
    create_access_token,
    hash_password,
)
from app.database import Base, get_db
from app.main import app
from app.models.transaction import Transaction
from app.models.user import User

TEST_REDIS_URL = "redis://localhost:6380/15"

test_redis = redis.Redis.from_url(
    TEST_REDIS_URL,
    decode_responses=False,
)

TEST_DATABASE_URL = (
    "postgresql://fraud_user:fraud_pass"
    "@localhost:5433/fraud_spike_detector"
)

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)
@pytest.fixture(autouse=True)
def isolate_redis():
    import app.redis_client as redis_module
    import app.services.velocity as velocity_module
    import app.services.identity_features as identity_module
    import app.auth.security as security_module

    original_client = redis_module.redis_client
    original_velocity_client = velocity_module.redis_client
    original_identity_client = identity_module.redis_client
    original_security_client = security_module.redis_client

    redis_module.redis_client = test_redis
    velocity_module.redis_client = test_redis
    identity_module.redis_client = test_redis
    security_module.redis_client = test_redis

    test_redis.flushdb()

    yield

    test_redis.flushdb()

    redis_module.redis_client = original_client
    velocity_module.redis_client = original_velocity_client
    identity_module.redis_client = original_identity_client
    security_module.redis_client = original_security_client

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        test_user = User(
            id=8,
            email = "test-user@vendlyexample.com",
            password_hash=hash_password("test-password"),
            role="customer",
        )

        db.add(test_user)
        db.commit()

    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()

    try:
        test_user = (
            db.query(User)
            .filter(User.id == 8)
            .first()
        )

        if test_user:
            test_user.password_hash = hash_password(
                "test-password"
            )
            db.commit()

        yield db

    finally:
        db.rollback()

        db.query(Transaction).delete()
        db.commit()

        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(
        data={"sub": "test-user@vendlyexample.com"}
    )

    with TestClient(app) as test_client:
        test_client.headers.update({
            "Authorization": f"Bearer {access_token}"
        })

        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(db_session):
    admin_user = (
        db_session.query(User)
        .filter(User.email == "admin@vendlyexample.com")
        .first()
    )

    if admin_user is None:
        admin_user = User(
            email="admin@vendlyexample.com",
            password_hash="unused-test-hash",
            role="admin",
        )

        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(
        data={"sub": admin_user.email}
    )

    with TestClient(app) as test_client:
        test_client.headers.update({
            "Authorization": f"Bearer {access_token}"
        })

        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def unauthenticated_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def seed_velocity():
    def _seed(
        user_id: int,
        transactions: list[tuple[str, float]],
    ):
        import time

        key = f"user:{user_id}:velocity"
        amount_key = f"{key}:amounts"

        now = time.time()

        for transaction_id, amount in transactions:
            test_redis.zadd(
                key,
                {transaction_id: now},
            )

            test_redis.hset(
                amount_key,
                transaction_id,
                amount,
            )

    return _seed