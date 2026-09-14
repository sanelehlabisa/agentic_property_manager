from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.models import (
    Base,
    Component,
    MaintenanceRecord,
    MaintenanceRule,
    Property,
    PropertyAccess,
    ProviderProfile,
    ProviderService,
    ServiceCategory,
    User,
)
from app.seed import seed_database
from app.seed.reset import reset_demo_database

EXPECTED_TABLES = {
    "bids",
    "components",
    "issue_reports",
    "jobs",
    "maintenance_records",
    "maintenance_rules",
    "predictions",
    "properties",
    "property_access",
    "provider_profiles",
    "provider_services",
    "service_categories",
    "users",
}


def count(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_schema_contains_all_foundation_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES


def test_seed_is_complete_and_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_database(session)
        seed_database(session)

        assert count(session, ServiceCategory) == 7
        assert count(session, MaintenanceRule) == 7
        assert count(session, User) == 5
        assert count(session, Property) == 1
        assert count(session, PropertyAccess) == 3
        assert count(session, Component) == 1
        assert count(session, MaintenanceRecord) == 1
        assert count(session, ProviderProfile) == 2
        assert count(session, ProviderService) == 2


def test_startup_seed_preserves_provider_edits() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_database(session)
        provider = session.scalar(
            select(User).where(User.email == "provider@example.com")
        )
        assert provider is not None
        profile = session.scalar(
            select(ProviderProfile).where(ProviderProfile.user_id == provider.id)
        )
        assert profile is not None
        service = session.scalar(
            select(ProviderService).where(
                ProviderService.provider_profile_id == profile.id
            )
        )
        assert service is not None

        profile.business_name = "Provider-edited name"
        service.active = False
        session.commit()

        seed_database(session)
        session.refresh(profile)
        session.refresh(service)

        assert profile.business_name == "Provider-edited name"
        assert service.active is False


def test_demo_reset_removes_runtime_data_and_restores_seed() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        session.add(
            User(
                email="runtime.user@example.com",
                name="Runtime User",
                role="tenant",
            )
        )
        session.commit()

        reset_demo_database(session)

        assert count(session, User) == 5
        assert (
            session.scalar(select(User).where(User.email == "runtime.user@example.com"))
            is None
        )
        assert count(session, Property) == 1
        assert count(session, Component) == 1
        assert count(session, ProviderProfile) == 2
