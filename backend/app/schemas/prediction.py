from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobStatus, PredictionStatus, PredictionUrgency


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    component_id: UUID
    component_name: str = ""
    category_code: str = ""
    due_date: date
    estimated_cost: Decimal
    urgency: PredictionUrgency
    explanation: str
    status: PredictionStatus
    created_at: datetime
    updated_at: datetime


class JobCreate(BaseModel):
    description: str = Field(min_length=5, max_length=5000)
    budget: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    property_name: str | None = None
    category_code: str
    issue_report_id: UUID | None
    prediction_id: UUID | None
    description: str
    budget: Decimal
    public_location: str
    status: JobStatus
    approved_by_user_id: UUID
    approved_at: datetime
    created_at: datetime
    updated_at: datetime
