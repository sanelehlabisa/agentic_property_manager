from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Bid,
    Job,
    Property,
    ProviderProfile,
    ProviderService,
    User,
)
from app.models.enums import BidStatus, JobStatus, UserRole
from app.schemas.marketplace import (
    BidCreate,
    BidUpdate,
    ProviderProfileWrite,
    ProviderServicesUpdate,
)
from app.services.access import require_account_role, require_property_manager
from app.services.properties import validate_category


def get_provider_profile(
    session: Session, user: User, *, required: bool = True
) -> ProviderProfile | None:
    require_account_role(user, {UserRole.PROVIDER})
    profile = session.scalar(
        select(ProviderProfile).where(ProviderProfile.user_id == user.id)
    )
    if profile is None and required:
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return profile


def upsert_provider_profile(
    session: Session, user: User, data: ProviderProfileWrite
) -> ProviderProfile:
    profile = get_provider_profile(session, user, required=False)
    if profile is None:
        profile = ProviderProfile(user_id=user.id, rating=Decimal("0"))
        session.add(profile)
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


def list_provider_services(session: Session, profile_id: UUID) -> list[ProviderService]:
    return list(
        session.scalars(
            select(ProviderService)
            .where(ProviderService.provider_profile_id == profile_id)
            .order_by(ProviderService.category_code)
        )
    )


def update_provider_services(
    session: Session, user: User, data: ProviderServicesUpdate
) -> tuple[ProviderProfile, list[ProviderService]]:
    profile = get_provider_profile(session, user)
    assert profile is not None
    requested_codes = {item.category_code for item in data.services}
    existing = {
        service.category_code: service
        for service in list_provider_services(session, profile.id)
    }

    for item in data.services:
        validate_category(session, item.category_code)
        service = existing.get(item.category_code)
        if service is None:
            service = ProviderService(
                provider_profile_id=profile.id,
                category_code=item.category_code,
            )
            session.add(service)
        service.description = item.description
        service.active = item.active

    for code, service in existing.items():
        if code not in requested_codes:
            service.active = False

    session.commit()
    return profile, list_provider_services(session, profile.id)


def matched_jobs(session: Session, user: User) -> list[tuple[Job, Bid | None]]:
    profile = get_provider_profile(session, user)
    assert profile is not None
    active_categories = select(ProviderService.category_code).where(
        ProviderService.provider_profile_id == profile.id,
        ProviderService.active.is_(True),
    )
    jobs = list(
        session.scalars(
            select(Job)
            .join(Property, Property.id == Job.property_id)
            .where(
                Job.status == JobStatus.OPEN,
                Job.category_code.in_(active_categories),
                func.lower(Property.city) == profile.city.lower(),
            )
            .order_by(Job.created_at.desc())
        )
    )
    results = []
    for job in jobs:
        bid = session.scalar(
            select(Bid).where(
                Bid.job_id == job.id,
                Bid.provider_profile_id == profile.id,
            )
        )
        results.append((job, bid))
    return results


def awarded_jobs(session: Session, user: User) -> list[Job]:
    profile = get_provider_profile(session, user)
    assert profile is not None
    return list(
        session.scalars(
            select(Job)
            .join(Bid, Bid.job_id == Job.id)
            .where(
                Bid.provider_profile_id == profile.id,
                Bid.status == BidStatus.ACCEPTED,
                Job.status.in_(
                    [JobStatus.AWARDED, JobStatus.IN_PROGRESS, JobStatus.COMPLETED]
                ),
            )
            .order_by(Job.updated_at.desc())
        )
    )


def create_bid(
    session: Session, user: User, job_id: UUID, data: BidCreate
) -> tuple[Bid, ProviderProfile]:
    profile = _require_job_match(session, user, job_id)
    existing = session.scalar(
        select(Bid).where(
            Bid.job_id == job_id,
            Bid.provider_profile_id == profile.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="You already have a bid for this job"
        )
    bid = Bid(
        job_id=job_id,
        provider_profile_id=profile.id,
        amount=data.amount,
        message=data.message,
        available_on=data.available_on,
        status=BidStatus.SUBMITTED,
    )
    session.add(bid)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="You already have a bid for this job"
        ) from exc
    session.refresh(bid)
    return bid, profile


def update_bid(
    session: Session, user: User, bid_id: UUID, data: BidUpdate
) -> tuple[Bid, ProviderProfile]:
    profile = get_provider_profile(session, user)
    assert profile is not None
    bid = session.scalar(select(Bid).where(Bid.id == bid_id).with_for_update())
    if bid is None or bid.provider_profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Bid not found")
    job = session.get(Job, bid.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.OPEN or bid.status != BidStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="This bid can no longer be updated")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bid, field, value)
    session.commit()
    session.refresh(bid)
    return bid, profile


def withdraw_bid(session: Session, user: User, bid_id: UUID) -> None:
    profile = get_provider_profile(session, user)
    assert profile is not None
    bid = session.scalar(select(Bid).where(Bid.id == bid_id).with_for_update())
    if bid is None or bid.provider_profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Bid not found")
    job = session.get(Job, bid.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.OPEN or bid.status != BidStatus.SUBMITTED:
        raise HTTPException(
            status_code=409, detail="This bid can no longer be withdrawn"
        )
    bid.status = BidStatus.WITHDRAWN
    session.commit()


def list_job_bids(
    session: Session, user: User, job_id: UUID
) -> list[tuple[Bid, ProviderProfile]]:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    require_property_manager(session, user, job.property_id)
    return list(
        session.execute(
            select(Bid, ProviderProfile)
            .join(ProviderProfile, ProviderProfile.id == Bid.provider_profile_id)
            .where(Bid.job_id == job_id)
            .order_by(Bid.amount, Bid.created_at)
        ).all()
    )


def accept_bid(
    session: Session, user: User, bid_id: UUID
) -> tuple[Bid, ProviderProfile]:
    bid = session.scalar(select(Bid).where(Bid.id == bid_id).with_for_update())
    if bid is None:
        raise HTTPException(status_code=404, detail="Bid not found")
    job = session.scalar(select(Job).where(Job.id == bid.job_id).with_for_update())
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    require_property_manager(session, user, job.property_id)
    if job.status != JobStatus.OPEN or bid.status != BidStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="This bid cannot be accepted")

    competing_bids = list(
        session.scalars(select(Bid).where(Bid.job_id == job.id).with_for_update())
    )
    for candidate in competing_bids:
        if candidate.id == bid.id:
            candidate.status = BidStatus.ACCEPTED
        elif candidate.status == BidStatus.SUBMITTED:
            candidate.status = BidStatus.REJECTED
    job.status = JobStatus.AWARDED
    session.commit()
    session.refresh(bid)
    profile = session.get(ProviderProfile, bid.provider_profile_id)
    assert profile is not None
    return bid, profile


def _require_job_match(session: Session, user: User, job_id: UUID) -> ProviderProfile:
    profile = get_provider_profile(session, user)
    assert profile is not None
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.OPEN:
        raise HTTPException(status_code=409, detail="Job is not open for bids")
    property_ = session.get(Property, job.property_id)
    service = session.scalar(
        select(ProviderService).where(
            ProviderService.provider_profile_id == profile.id,
            ProviderService.category_code == job.category_code,
            ProviderService.active.is_(True),
        )
    )
    if (
        property_ is None
        or service is None
        or property_.city.casefold() != profile.city.casefold()
    ):
        raise HTTPException(status_code=403, detail="Job does not match your services")
    return profile
