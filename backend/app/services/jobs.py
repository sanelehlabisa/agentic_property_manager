from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Component, IssueReport, Job, Prediction, Property, User
from app.models.enums import JobStatus, PredictionStatus, ReportStatus
from app.schemas.prediction import JobCreate
from app.services.access import require_property_manager


def create_from_report(
    session: Session, user: User, report_id: UUID, data: JobCreate
) -> Job:
    report = session.scalar(
        select(IssueReport).where(IssueReport.id == report_id).with_for_update()
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_property_manager(session, user, report.property_id)
    _ensure_unique_source(session, IssueReport, report.id)
    if report.status != ReportStatus.APPROVED:
        raise HTTPException(
            status_code=409, detail="Only an approved report can become a job"
        )

    job = _new_job(
        session,
        user,
        report.property_id,
        report.category_code,
        data,
        issue_report_id=report.id,
    )
    report.status = ReportStatus.CONVERTED_TO_JOB
    _commit_source_job(session)
    session.refresh(job)
    return job


def create_from_prediction(
    session: Session, user: User, prediction_id: UUID, data: JobCreate
) -> Job:
    prediction = session.scalar(
        select(Prediction).where(Prediction.id == prediction_id).with_for_update()
    )
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    component = session.get(Component, prediction.component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Prediction component not found")
    require_property_manager(session, user, component.property_id)
    _ensure_unique_source(session, Prediction, prediction.id)
    if prediction.status != PredictionStatus.APPROVED:
        raise HTTPException(
            status_code=409, detail="Only an approved prediction can become a job"
        )

    job = _new_job(
        session,
        user,
        component.property_id,
        component.category_code,
        data,
        prediction_id=prediction.id,
    )
    prediction.status = PredictionStatus.CONVERTED_TO_JOB
    _commit_source_job(session)
    session.refresh(job)
    return job


def list_property_jobs(
    session: Session, user: User, property_id: UUID
) -> list[tuple[Job, str]]:
    property_, _ = require_property_manager(session, user, property_id)
    jobs = list(
        session.scalars(
            select(Job)
            .where(Job.property_id == property_id)
            .order_by(Job.created_at.desc())
        )
    )
    return [(job, property_.name) for job in jobs]


def get_managed_job(session: Session, user: User, job_id: UUID) -> tuple[Job, str]:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    property_, _ = require_property_manager(session, user, job.property_id)
    return job, property_.name


def _ensure_unique_source(session: Session, source_type: type, source_id: UUID) -> None:
    field = Job.issue_report_id if source_type is IssueReport else Job.prediction_id
    if session.scalar(select(Job.id).where(field == source_id)) is not None:
        raise HTTPException(status_code=409, detail="This source already has a job")


def _new_job(
    session: Session,
    user: User,
    property_id: UUID,
    category_code: str,
    data: JobCreate,
    *,
    issue_report_id: UUID | None = None,
    prediction_id: UUID | None = None,
) -> Job:
    property_ = session.get(Property, property_id)
    if property_ is None:
        raise HTTPException(status_code=404, detail="Property not found")
    job = Job(
        property_id=property_id,
        category_code=category_code,
        issue_report_id=issue_report_id,
        prediction_id=prediction_id,
        description=data.description,
        budget=data.budget,
        public_location=f"{property_.suburb}, {property_.city}",
        status=JobStatus.OPEN,
        approved_by_user_id=user.id,
    )
    session.add(job)
    return job


def _commit_source_job(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="This source already has a job"
        ) from exc
