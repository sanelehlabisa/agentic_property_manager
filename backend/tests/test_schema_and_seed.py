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
        assert count(session, User) == 4
        assert count(session, Property) == 1
        assert count(session, PropertyAccess) == 3
        assert count(session, Component) == 1
        assert count(session, MaintenanceRecord) == 1
        assert count(session, ProviderProfile) == 1
        assert count(session, ProviderService) == 1
