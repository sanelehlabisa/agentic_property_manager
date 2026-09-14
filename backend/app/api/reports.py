from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models import Job
from app.schemas.report import IssueReportCreate, IssueReportRead, ReportRejection
from app.services import reports as service

router = APIRouter(tags=["issue reports"])


def report_response(
    session: DatabaseSession, report, reporter_name: str | None = None
) -> IssueReportRead:
    job_status = session.scalar(
        select(Job.status).where(Job.issue_report_id == report.id)
    )
    return IssueReportRead.model_validate(report).model_copy(
        update={"reporter_name": reporter_name, "job_status": job_status}
    )


@router.get("/properties/{property_id}/reports", response_model=list[IssueReportRead])
def get_reports(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[IssueReportRead]:
    return [
        IssueReportRead.model_validate(report).model_copy(
            update={"reporter_name": reporter_name, "job_status": job_status}
        )
        for report, reporter_name, job_status in service.list_reports(
            session, user, property_id
        )
    ]


@router.post(
    "/properties/{property_id}/reports",
    response_model=IssueReportRead,
    status_code=status.HTTP_201_CREATED,
)
def post_report(
    property_id: UUID,
    data: IssueReportCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> IssueReportRead:
    return report_response(
        session, service.create_report(session, user, property_id, data), user.name
    )


@router.post("/reports/{report_id}/approve", response_model=IssueReportRead)
def approve_report(
    report_id: UUID, session: DatabaseSession, user: CurrentUser
) -> IssueReportRead:
    return report_response(
        session, service.review_report(session, user, report_id, approved=True)
    )


@router.post("/reports/{report_id}/reject", response_model=IssueReportRead)
def reject_report(
    report_id: UUID,
    data: ReportRejection,
    session: DatabaseSession,
    user: CurrentUser,
) -> IssueReportRead:
    return report_response(
        session,
        service.review_report(
            session, user, report_id, approved=False, reason=data.reason
        ),
    )
