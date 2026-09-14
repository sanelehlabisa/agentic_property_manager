from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, IssueReport, Job, User
from app.models.enums import JobStatus, PropertyAccessRole, ReportStatus, UserRole
from app.schemas.report import IssueReportCreate
from app.services.access import get_accessible_property, require_property_manager
from app.services.properties import validate_category


def list_reports(
    session: Session, user: User, property_id: UUID
) -> list[tuple[IssueReport, str, JobStatus | None]]:
    _, membership = get_accessible_property(session, user, property_id)
    query = (
        select(IssueReport, User.name, Job.status)
        .join(User, User.id == IssueReport.reporter_user_id)
        .outerjoin(Job, Job.issue_report_id == IssueReport.id)
        .where(IssueReport.property_id == property_id)
        .order_by(IssueReport.created_at.desc())
    )
    if membership.access_role == PropertyAccessRole.TENANT:
        query = query.where(IssueReport.reporter_user_id == user.id)
    return list(session.execute(query).all())


def create_report(
    session: Session,
    user: User,
    property_id: UUID,
    data: IssueReportCreate,
) -> IssueReport:
    if user.role == UserRole.PROVIDER:
        raise HTTPException(
            status_code=403, detail="Providers cannot report property issues"
        )
    get_accessible_property(session, user, property_id)
    validate_category(session, data.category_code)

    component_id: UUID | None = None
    if data.component_id:
        try:
            component_id = UUID(data.component_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid component ID") from exc
        component = session.get(Component, component_id)
        if component is None or component.property_id != property_id:
            raise HTTPException(
                status_code=422, detail="Component is not on this property"
            )

    report = IssueReport(
        property_id=property_id,
        reporter_user_id=user.id,
        component_id=component_id,
        category_code=data.category_code,
        title=data.title,
        description=data.description,
        urgency=data.urgency,
        status=ReportStatus.PENDING_APPROVAL,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def review_report(
    session: Session,
    user: User,
    report_id: UUID,
    approved: bool,
    reason: str | None = None,
) -> IssueReport:
    report = session.scalar(
        select(IssueReport).where(IssueReport.id == report_id).with_for_update()
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_property_manager(session, user, report.property_id)
    if report.status != ReportStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail="Report has already been reviewed")

    report.status = ReportStatus.APPROVED if approved else ReportStatus.REJECTED
    report.review_reason = reason
    report.reviewed_by_user_id = user.id
    report.reviewed_at = datetime.now(UTC)
    session.commit()
    session.refresh(report)
    return report
