from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.marketplace import BidCreate, BidRead, BidUpdate
from app.schemas.prediction import JobCreate, JobRead
from app.services import jobs as job_service
from app.services import marketplace as marketplace_service

router = APIRouter(tags=["jobs and bids"])


def job_response(job, property_name: str | None = None) -> JobRead:
    return JobRead.model_validate(job).model_copy(
        update={"property_name": property_name}
    )


def bid_response(bid, business_name=None, rating=None) -> BidRead:
    return BidRead.model_validate(bid).model_copy(
        update={"business_name": business_name, "provider_rating": rating}
    )


@router.post(
    "/jobs/from-report/{report_id}",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
)
def post_job_from_report(
    report_id: UUID,
    data: JobCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> JobRead:
    return job_response(job_service.create_from_report(session, user, report_id, data))


@router.post(
    "/jobs/from-prediction/{prediction_id}",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
)
def post_job_from_prediction(
    prediction_id: UUID,
    data: JobCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> JobRead:
    return job_response(
        job_service.create_from_prediction(session, user, prediction_id, data)
    )


@router.get("/properties/{property_id}/jobs", response_model=list[JobRead])
def get_property_jobs(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[JobRead]:
    return [
        job_response(job, property_name)
        for job, property_name in job_service.list_property_jobs(
            session, user, property_id
        )
    ]


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: UUID, session: DatabaseSession, user: CurrentUser) -> JobRead:
    job, property_name = job_service.get_managed_job(session, user, job_id)
    return job_response(job, property_name)


@router.post(
    "/jobs/{job_id}/bids",
    response_model=BidRead,
    status_code=status.HTTP_201_CREATED,
)
def post_bid(
    job_id: UUID,
    data: BidCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> BidRead:
    bid, profile = marketplace_service.create_bid(session, user, job_id, data)
    return bid_response(bid, profile.business_name, profile.rating)


@router.patch("/bids/{bid_id}", response_model=BidRead)
def patch_bid(
    bid_id: UUID,
    data: BidUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> BidRead:
    bid, profile = marketplace_service.update_bid(session, user, bid_id, data)
    return bid_response(bid, profile.business_name, profile.rating)


@router.delete("/bids/{bid_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bid(bid_id: UUID, session: DatabaseSession, user: CurrentUser) -> Response:
    marketplace_service.withdraw_bid(session, user, bid_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/jobs/{job_id}/bids", response_model=list[BidRead])
def get_bids(
    job_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[BidRead]:
    return [
        bid_response(bid, profile.business_name, profile.rating)
        for bid, profile in marketplace_service.list_job_bids(session, user, job_id)
    ]


@router.post("/bids/{bid_id}/accept", response_model=BidRead)
def accept_bid(bid_id: UUID, session: DatabaseSession, user: CurrentUser) -> BidRead:
    bid, profile = marketplace_service.accept_bid(session, user, bid_id)
    return bid_response(bid, profile.business_name, profile.rating)
