from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.api.jobs import job_response
from app.schemas.marketplace import (
    MatchedJobRead,
    ProviderProfileRead,
    ProviderProfileWrite,
    ProviderServiceRead,
    ProviderServicesUpdate,
)
from app.schemas.prediction import JobRead
from app.services import marketplace as service

router = APIRouter(prefix="/provider", tags=["provider marketplace"])


def profile_response(session, profile, services=None) -> ProviderProfileRead:
    next_services = services or service.list_provider_services(session, profile.id)
    return ProviderProfileRead.model_validate(profile).model_copy(
        update={
            "services": [
                ProviderServiceRead.model_validate(item) for item in next_services
            ]
        }
    )


@router.get("/profile", response_model=ProviderProfileRead)
def get_profile(session: DatabaseSession, user: CurrentUser) -> ProviderProfileRead:
    profile = service.get_provider_profile(session, user)
    assert profile is not None
    return profile_response(session, profile)


@router.put("/profile", response_model=ProviderProfileRead)
def put_profile(
    data: ProviderProfileWrite,
    session: DatabaseSession,
    user: CurrentUser,
) -> ProviderProfileRead:
    return profile_response(
        session, service.upsert_provider_profile(session, user, data)
    )


@router.put("/services", response_model=ProviderProfileRead)
def put_services(
    data: ProviderServicesUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> ProviderProfileRead:
    profile, services = service.update_provider_services(session, user, data)
    return profile_response(session, profile, services)


@router.get("/matched-jobs", response_model=list[MatchedJobRead])
def get_matched_jobs(
    session: DatabaseSession, user: CurrentUser
) -> list[MatchedJobRead]:
    return [
        MatchedJobRead.model_validate(job).model_copy(
            update={
                "own_bid_id": bid.id if bid else None,
                "own_bid_status": bid.status if bid else None,
                "own_bid_amount": bid.amount if bid else None,
                "own_bid_message": bid.message if bid else None,
                "own_bid_available_on": bid.available_on if bid else None,
            }
        )
        for job, bid in service.matched_jobs(session, user)
    ]


@router.get("/awards", response_model=list[JobRead])
def get_awards(session: DatabaseSession, user: CurrentUser) -> list[JobRead]:
    return [job_response(job) for job in service.awarded_jobs(session, user)]
