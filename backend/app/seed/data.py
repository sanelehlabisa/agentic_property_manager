from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
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
from app.models.enums import ComponentCondition, PropertyAccessRole, UserRole

CATEGORIES = (
    ("plumbing", "Plumbing", "Pipes, taps, drains, geysers, and water systems."),
    ("electrical", "Electrical", "Wiring, distribution, lighting, and power."),
    ("hvac", "HVAC", "Heating, ventilation, and air-conditioning systems."),
    ("roofing", "Roofing", "Roof surfaces, flashing, gutters, and drainage."),
    ("cleaning", "Cleaning", "Routine and specialist property cleaning."),
    ("gardening", "Gardening", "Garden, lawn, and outdoor maintenance."),
    ("handyman", "Handyman", "General repairs and small maintenance jobs."),
)

RULES = (
    ("plumbing", 12, 30, "1250.00", "Annual plumbing and geyser inspection."),
    ("electrical", 24, 60, "1800.00", "Two-year electrical safety inspection."),
    ("hvac", 6, 30, "950.00", "Six-month HVAC clean and service."),
    ("roofing", 12, 45, "1500.00", "Annual roof and gutter inspection."),
    ("cleaning", 1, 7, "650.00", "Monthly deep-clean planning rule."),
    ("gardening", 1, 7, "500.00", "Monthly garden maintenance planning rule."),
    ("handyman", 6, 30, "800.00", "Six-month general condition inspection."),
)

DEMO_USERS = (
    ("owner@example.com", "Demo Homeowner", UserRole.HOMEOWNER),
    ("manager@example.com", "Demo Manager", UserRole.MANAGER),
    ("tenant@example.com", "Demo Tenant", UserRole.TENANT),
    ("provider@example.com", "Demo Provider", UserRole.PROVIDER),
    ("provider2@example.com", "Second Demo Provider", UserRole.PROVIDER),
)


def seed_database(session: Session) -> None:
    try:
        _seed_categories_and_rules(session)
        users = _seed_users(session)
        property_ = _seed_property(session)
        _seed_property_access(session, property_, users)
        _seed_component_history(session, property_)
        _seed_provider(
            session,
            users["provider@example.com"],
            business_name="Demo Plumbing Services",
            description="Local plumbing and geyser maintenance provider.",
            phone="+27 11 555 0100",
            suburb="Rosebank",
            rating=Decimal("4.60"),
        )
        _seed_provider(
            session,
            users["provider2@example.com"],
            business_name="Jozi Rapid Repairs",
            description="Residential plumbing repairs across Johannesburg.",
            phone="+27 11 555 0110",
            suburb="Sandton",
            rating=Decimal("4.35"),
        )
        session.commit()
    except Exception:
        session.rollback()
        raise


def _seed_categories_and_rules(session: Session) -> None:
    for code, name, description in CATEGORIES:
        category = session.get(ServiceCategory, code)
        if category is None:
            category = ServiceCategory(code=code, name=name, description=description)
            session.add(category)
        else:
            category.name = name
            category.description = description
            category.active = True

    session.flush()

    for category_code, interval, warning, cost, description in RULES:
        rule = session.scalar(
            select(MaintenanceRule).where(
                MaintenanceRule.category_code == category_code
            )
        )
        if rule is None:
            rule = MaintenanceRule(category_code=category_code)
            session.add(rule)
        rule.interval_months = interval
        rule.warning_days = warning
        rule.default_cost = Decimal(cost)
        rule.description = description
        rule.active = True


def _seed_users(session: Session) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, name, role in DEMO_USERS:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, name=name, role=role)
            session.add(user)
            session.flush()
        users[email] = user
    return users


def _seed_property(session: Session) -> Property:
    property_ = session.scalar(select(Property).where(Property.name == "Demo Home"))
    if property_ is None:
        property_ = Property(
            name="Demo Home",
            address_line_1="12 Main Road",
            suburb="Rosebank",
            city="Johannesburg",
            postal_code="2196",
        )
        session.add(property_)
        session.flush()
    return property_


def _seed_property_access(
    session: Session, property_: Property, users: dict[str, User]
) -> None:
    access = (
        (users["owner@example.com"], PropertyAccessRole.OWNER),
        (users["manager@example.com"], PropertyAccessRole.MANAGER),
        (users["tenant@example.com"], PropertyAccessRole.TENANT),
    )
    for user, access_role in access:
        membership = session.scalar(
            select(PropertyAccess).where(
                PropertyAccess.property_id == property_.id,
                PropertyAccess.user_id == user.id,
            )
        )
        if membership is None:
            session.add(
                PropertyAccess(
                    property_id=property_.id,
                    user_id=user.id,
                    access_role=access_role,
                )
            )


def _seed_component_history(session: Session, property_: Property) -> None:
    component = session.scalar(
        select(Component).where(
            Component.property_id == property_.id,
            Component.name == "Main geyser",
        )
    )
    if component is None:
        component = Component(
            property_id=property_.id,
            category_code="plumbing",
            name="Main geyser",
            installed_on=date(2022, 9, 1),
            condition=ComponentCondition.FAIR,
        )
        session.add(component)
        session.flush()

    existing_record = session.scalar(
        select(MaintenanceRecord).where(
            MaintenanceRecord.component_id == component.id,
            MaintenanceRecord.completed_on == date(2025, 9, 1),
        )
    )
    if existing_record is None:
        session.add(
            MaintenanceRecord(
                component_id=component.id,
                completed_on=date(2025, 9, 1),
                cost=Decimal("1250.00"),
                provider_name="Demo Plumbing Services",
                notes="Annual geyser inspection and valve replacement.",
            )
        )


def _seed_provider(
    session: Session,
    user: User,
    *,
    business_name: str,
    description: str,
    phone: str,
    suburb: str,
    rating: Decimal,
) -> None:
    profile = session.scalar(
        select(ProviderProfile).where(ProviderProfile.user_id == user.id)
    )
    if profile is None:
        profile = ProviderProfile(
            user_id=user.id,
            business_name=business_name,
            description=description,
            phone=phone,
            suburb=suburb,
            city="Johannesburg",
            service_radius_km=25,
            rating=rating,
        )
        session.add(profile)
        session.flush()
    service = session.scalar(
        select(ProviderService).where(
            ProviderService.provider_profile_id == profile.id,
            ProviderService.category_code == "plumbing",
        )
    )
    if service is None:
        session.add(
            ProviderService(
                provider_profile_id=profile.id,
                category_code="plumbing",
                description=description,
                active=True,
            )
        )
