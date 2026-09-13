from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReportStatus, ReportUrgency


class IssueReportCreate(BaseModel):
    component_id: str | None = None
    category_code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5, max_length=5000)
    urgency: ReportUrgency = ReportUrgency.MEDIUM


class IssueReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    reporter_user_id: UUID
    reporter_name: str | None = None
    component_id: UUID | None
    category_code: str
    title: str
    description: str
    urgency: ReportUrgency
    status: ReportStatus
    review_reason: str | None
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReportRejection(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
