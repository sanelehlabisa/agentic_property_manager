from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import BidStatus
from app.schemas.prediction import JobRead


class ProviderServiceWrite(BaseModel):
    category_code: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    active: bool = True


class ProviderServicesUpdate(BaseModel):
    services: list[ProviderServiceWrite] = Field(max_length=100)

    @model_validator(mode="after")
    def reject_duplicate_categories(self) -> "ProviderServicesUpdate":
        codes = [service.category_code for service in self.services]
        if len(codes) != len(set(codes)):
            raise ValueError("Each service category may appear only once")
        return self


class ProviderServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_code: str
    description: str | None
    active: bool


class ProviderProfileWrite(BaseModel):
    business_name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=5, max_length=1000)
    phone: str = Field(min_length=5, max_length=40)
    suburb: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    service_radius_km: int = Field(gt=0, le=500)


class ProviderProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    business_name: str
    description: str
    phone: str
    suburb: str
    city: str
    service_radius_km: int
    rating: Decimal
    services: list[ProviderServiceRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MatchedJobRead(JobRead):
    own_bid_id: UUID | None = None
    own_bid_status: BidStatus | None = None
    own_bid_amount: Decimal | None = None
    own_bid_message: str | None = None
    own_bid_available_on: date | None = None


class BidCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    message: str = Field(min_length=3, max_length=1000)
    available_on: date


class BidUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    message: str | None = Field(default=None, min_length=3, max_length=1000)
    available_on: date | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "BidUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one bid field is required")
        return self


class BidRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    provider_profile_id: UUID
    business_name: str | None = None
    provider_rating: Decimal | None = None
    amount: Decimal
    message: str
    available_on: date
    status: BidStatus
    created_at: datetime
    updated_at: datetime
