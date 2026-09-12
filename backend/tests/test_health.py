from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.main import app


class HealthySession:
    def execute(self, statement):
        return None


class UnavailableSession:
    def execute(self, statement):
        raise SQLAlchemyError("database unavailable")


def override_healthy_db() -> Generator[HealthySession, None, None]:
    yield HealthySession()


def override_unavailable_db() -> Generator[UnavailableSession, None, None]:
    yield UnavailableSession()


def test_health_reports_api_and_database_ready() -> None:
    app.dependency_overrides[get_db] = override_healthy_db

    try:
        with TestClient(app) as client:
            response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert response.headers["X-Request-ID"]


def test_health_reports_database_failure() -> None:
    app.dependency_overrides[get_db] = override_unavailable_db

    try:
        with TestClient(app) as client:
            response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "service_unavailable", "message": "Database unavailable"}
    }


def test_cors_allows_configured_frontend() -> None:
    app.dependency_overrides[get_db] = override_healthy_db

    try:
        with TestClient(app) as client:
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
