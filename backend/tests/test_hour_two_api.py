from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, Property, User
from app.seed import seed_database


@pytest.fixture
def api() -> Generator[tuple[TestClient, Session], None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    seed_database(session)

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


def token_for(session: Session, email: str) -> str:
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    return str(user.id)


def auth_headers(session: Session, email: str) -> dict[str, str]:
    return {"X-User-ID": token_for(session, email)}


def demo_property(session: Session) -> Property:
    property_ = session.scalar(select(Property).where(Property.name == "Demo Home"))
    assert property_ is not None
    return property_


def test_email_authentication_supports_first_time_onboarding(api) -> None:
    client, _ = api

    lookup = client.post("/auth/email", json={"email": "new.owner@example.com"})
    assert lookup.status_code == 200
    assert lookup.json() == {
        "requires_onboarding": True,
        "token": None,
        "user": None,
    }

    onboarding = client.post(
        "/auth/email",
        json={
            "email": "new.owner@example.com",
            "name": "New Owner",
            "role": "homeowner",
        },
    )
    assert onboarding.status_code == 200
    assert onboarding.json()["requires_onboarding"] is False
    assert onboarding.json()["user"]["role"] == "homeowner"
    assert onboarding.json()["token"]


def test_tenant_report_requires_manager_approval(api) -> None:
    client, session = api
    property_ = demo_property(session)
    tenant_headers = auth_headers(session, "tenant@example.com")
    manager_headers = auth_headers(session, "manager@example.com")

    created = client.post(
        f"/properties/{property_.id}/reports",
        headers=tenant_headers,
        json={
            "category_code": "plumbing",
            "title": "Kitchen tap is leaking",
            "description": "Water keeps dripping under the kitchen sink.",
            "urgency": "high",
        },
    )
    assert created.status_code == 201
    report = created.json()
    assert report["status"] == "pending_approval"

    forbidden = client.post(f"/reports/{report['id']}/approve", headers=tenant_headers)
    assert forbidden.status_code == 403

    approved = client.post(f"/reports/{report['id']}/approve", headers=manager_headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_by_user_id"] == manager_headers["X-User-ID"]


def test_owner_can_create_property_component_and_history(api) -> None:
    client, session = api
    owner_headers = auth_headers(session, "owner@example.com")

    property_response = client.post(
        "/properties",
        headers=owner_headers,
        json={
            "name": "Test Apartment",
            "address_line_1": "1 Test Street",
            "suburb": "Parktown",
            "city": "Johannesburg",
            "postal_code": "2001",
        },
    )
    assert property_response.status_code == 201
    property_ = property_response.json()
    assert property_["access_role"] == "owner"

    component_response = client.post(
        f"/properties/{property_['id']}/components",
        headers=owner_headers,
        json={
            "category_code": "electrical",
            "name": "Distribution board",
            "installed_on": "2022-02-01",
            "condition": "good",
        },
    )
    assert component_response.status_code == 201
    component = component_response.json()

    history_response = client.post(
        f"/components/{component['id']}/maintenance-records",
        headers=owner_headers,
        json={
            "completed_on": "2026-01-15",
            "cost": "875.50",
            "provider_name": "Safe Spark",
            "notes": "Safety inspection",
        },
    )
    assert history_response.status_code == 201
    assert history_response.json()["cost"] == "875.50"


def test_property_access_does_not_leak_across_memberships(api) -> None:
    client, session = api
    owner_headers = auth_headers(session, "owner@example.com")
    tenant_headers = auth_headers(session, "tenant@example.com")

    created = client.post(
        "/properties",
        headers=owner_headers,
        json={
            "name": "Owner-only Property",
            "address_line_1": "99 Private Road",
            "suburb": "Parkview",
            "city": "Johannesburg",
        },
    )
    assert created.status_code == 201

    hidden = client.get(f"/properties/{created.json()['id']}", headers=tenant_headers)
    assert hidden.status_code == 404

    visible_properties = client.get("/properties", headers=tenant_headers)
    assert visible_properties.status_code == 200
    assert created.json()["id"] not in {
        property_["id"] for property_ in visible_properties.json()
    }


def test_csv_preview_uses_predefined_aliases(api) -> None:
    client, session = api
    property_ = demo_property(session)
    manager_headers = auth_headers(session, "manager@example.com")

    response = client.post(
        f"/properties/{property_.id}/maintenance-imports/preview",
        headers=manager_headers,
        json={
            "csv_text": (
                "date,description,amount,component\n"
                "2026-02-01,Annual geyser service,1350.00,Main geyser"
            )
        },
    )

    assert response.status_code == 200
    preview = response.json()
    assert preview["valid_count"] == 1
    assert preview["rows"][0]["category_code"] == "plumbing"
    assert preview["rows"][0]["errors"] == []
