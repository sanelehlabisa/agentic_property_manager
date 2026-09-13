from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, Prediction, Property, User
from app.models.enums import PredictionUrgency
from app.seed import seed_database
from app.services.predictions import calculate_predictions


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


def user_for(session: Session, email: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def auth_headers(session: Session, email: str) -> dict[str, str]:
    return {"X-User-ID": str(user_for(session, email).id)}


def demo_property(session: Session) -> Property:
    property_ = session.scalar(select(Property).where(Property.name == "Demo Home"))
    assert property_ is not None
    return property_


def create_open_job(client: TestClient, session: Session) -> dict:
    property_ = demo_property(session)
    tenant_headers = auth_headers(session, "tenant@example.com")
    manager_headers = auth_headers(session, "manager@example.com")
    report = client.post(
        f"/properties/{property_.id}/reports",
        headers=tenant_headers,
        json={
            "category_code": "plumbing",
            "title": "Burst supply pipe",
            "description": "A supply pipe is leaking behind the kitchen cabinet.",
            "urgency": "high",
        },
    ).json()
    approved = client.post(f"/reports/{report['id']}/approve", headers=manager_headers)
    assert approved.status_code == 200
    response = client.post(
        f"/jobs/from-report/{report['id']}",
        headers=manager_headers,
        json={
            "description": "Repair leaking kitchen supply pipe.",
            "budget": "2500.00",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_rule_engine_is_deterministic_and_explainable(api) -> None:
    _, session = api
    manager = user_for(session, "manager@example.com")
    property_ = demo_property(session)

    first = calculate_predictions(
        session, manager, property_.id, as_of=date(2026, 9, 13)
    )
    second = calculate_predictions(
        session, manager, property_.id, as_of=date(2026, 9, 13)
    )

    assert len(first) == 1
    prediction, component = first[0]
    assert component.name == "Main geyser"
    assert prediction.id == second[0][0].id
    assert prediction.due_date == date(2026, 9, 1)
    assert prediction.urgency == PredictionUrgency.OVERDUE
    assert prediction.estimated_cost == 1250
    assert "latest completed service" in prediction.explanation
    assert "median of 1 recent service record" in prediction.explanation
    assert session.scalar(select(func.count()).select_from(Prediction)) == 1


def test_only_management_can_view_predictions(api) -> None:
    client, session = api
    property_ = demo_property(session)

    response = client.get(
        f"/properties/{property_.id}/predictions",
        headers=auth_headers(session, "tenant@example.com"),
    )

    assert response.status_code == 403


def test_approved_report_creates_exactly_one_safe_job(api) -> None:
    client, session = api
    property_ = demo_property(session)
    tenant_headers = auth_headers(session, "tenant@example.com")
    manager_headers = auth_headers(session, "manager@example.com")
    report = client.post(
        f"/properties/{property_.id}/reports",
        headers=tenant_headers,
        json={
            "category_code": "plumbing",
            "title": "Tap will not close",
            "description": "The bathroom tap continues running when fully closed.",
            "urgency": "medium",
        },
    ).json()
    job_data = {
        "description": "Repair bathroom tap that will not close.",
        "budget": "1500.00",
    }

    unapproved = client.post(
        f"/jobs/from-report/{report['id']}",
        headers=manager_headers,
        json=job_data,
    )
    assert unapproved.status_code == 409
    client.post(f"/reports/{report['id']}/approve", headers=manager_headers)

    created = client.post(
        f"/jobs/from-report/{report['id']}",
        headers=manager_headers,
        json=job_data,
    )
    assert created.status_code == 201
    job = created.json()
    assert job["status"] == "open"
    assert job["public_location"] == "Rosebank, Johannesburg"
    assert "12 Main Road" not in str(job)

    duplicate = client.post(
        f"/jobs/from-report/{report['id']}",
        headers=manager_headers,
        json=job_data,
    )
    assert duplicate.status_code == 409


def test_prediction_can_be_approved_and_published(api) -> None:
    client, session = api
    property_ = demo_property(session)
    manager_headers = auth_headers(session, "manager@example.com")
    predictions = client.get(
        f"/properties/{property_.id}/predictions", headers=manager_headers
    ).json()
    prediction = predictions[0]

    approved = client.post(
        f"/predictions/{prediction['id']}/approve", headers=manager_headers
    )
    assert approved.status_code == 200
    created = client.post(
        f"/jobs/from-prediction/{prediction['id']}",
        headers=manager_headers,
        json={
            "description": "Complete the scheduled annual geyser service.",
            "budget": prediction["estimated_cost"],
        },
    )
    assert created.status_code == 201
    assert created.json()["prediction_id"] == prediction["id"]


def test_provider_matching_bidding_and_atomic_award(api) -> None:
    client, session = api
    job = create_open_job(client, session)
    provider_headers = auth_headers(session, "provider@example.com")
    manager_headers = auth_headers(session, "manager@example.com")

    profile = client.get("/provider/profile", headers=provider_headers)
    assert profile.status_code == 200
    services = client.put(
        "/provider/services",
        headers=provider_headers,
        json={
            "services": [
                {
                    "category_code": "plumbing",
                    "description": "Leaks, taps, drains, and geysers.",
                    "active": True,
                }
            ]
        },
    )
    assert services.status_code == 200

    matched = client.get("/provider/matched-jobs", headers=provider_headers)
    assert job["id"] in {item["id"] for item in matched.json()}
    assert "12 Main Road" not in matched.text

    first_bid = client.post(
        f"/jobs/{job['id']}/bids",
        headers=provider_headers,
        json={
            "amount": "2200.00",
            "message": "Available tomorrow with all fittings included.",
            "available_on": "2026-09-15",
        },
    )
    assert first_bid.status_code == 201
    patched = client.patch(
        f"/bids/{first_bid.json()['id']}",
        headers=provider_headers,
        json={"amount": "2100.00"},
    )
    assert patched.status_code == 200
    assert patched.json()["amount"] == "2100.00"

    second_auth = client.post(
        "/auth/email",
        json={
            "email": "second.provider@example.com",
            "name": "Second Provider",
            "role": "provider",
        },
    ).json()
    second_headers = {"X-User-ID": second_auth["token"]}
    client.put(
        "/provider/profile",
        headers=second_headers,
        json={
            "business_name": "Second Plumbing",
            "description": "A second local plumbing provider.",
            "phone": "+27 11 555 0101",
            "suburb": "Rosebank",
            "city": "Johannesburg",
            "service_radius_km": 20,
        },
    )
    client.put(
        "/provider/services",
        headers=second_headers,
        json={"services": [{"category_code": "plumbing", "active": True}]},
    )
    second_bid = client.post(
        f"/jobs/{job['id']}/bids",
        headers=second_headers,
        json={
            "amount": "2050.00",
            "message": "Can attend this week.",
            "available_on": "2026-09-16",
        },
    )
    assert second_bid.status_code == 201

    accepted = client.post(
        f"/bids/{first_bid.json()['id']}/accept", headers=manager_headers
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    bids = client.get(f"/jobs/{job['id']}/bids", headers=manager_headers).json()
    statuses = {bid["id"]: bid["status"] for bid in bids}
    assert statuses[first_bid.json()["id"]] == "accepted"
    assert statuses[second_bid.json()["id"]] == "rejected"

    awards = client.get("/provider/awards", headers=provider_headers)
    assert job["id"] in {item["id"] for item in awards.json()}
