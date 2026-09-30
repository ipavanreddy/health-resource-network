from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import settings

# Tests never call real Google APIs, even if keys are present in .env.
settings.force_demo_mode = True

from app.main import app  # noqa: E402
from app.store import reset_store  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
DHO = {"X-Role": "district_health_officer"}


@pytest.fixture
def store():
    return reset_store(datetime.now(IST).replace(microsecond=0))


@pytest.fixture
def client(store):
    return TestClient(app)
