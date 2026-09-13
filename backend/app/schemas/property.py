from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import ComponentCondition, PropertyAccessRole


class PropertyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    address_line_1: str = Field(min_length=3, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    suburb: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)


class PropertyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address_line_1: str | None = Field(default=None, min_length=3, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    suburb: str | None = Field(default=None, min_length=2, max_length=120)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address_line_1: str
    address_line_2: str | None
    suburb: str
    city: str
    postal_code: str | None
    access_role: PropertyAccessRole | None = None
    created_at: datetime
    updated_at: datetime


class PropertyAccessCreate(BaseModel):
    email: EmailStr
    access_role: PropertyAccessRole


class PropertyAccessRead(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    name: str
    access_role: PropertyAccessRole


class ServiceCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str


class ComponentCreate(BaseModel):
    category_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    installed_on: date | None = None
    condition: ComponentCondition = ComponentCondition.UNKNOWN


class ComponentUpdate(BaseModel):
    category_code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    installed_on: date | None = None
    condition: ComponentCondition | None = None


class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    category_code: str
    name: str
    installed_on: date | None
    condition: ComponentCondition
    created_at: datetime
    updated_at: datetime


class MaintenanceRecordCreate(BaseModel):
    completed_on: date
    cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    provider_name: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=5000)


class MaintenanceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    component_id: UUID
    completed_on: date
    cost: Decimal
    provider_name: str | None
    notes: str | None
    created_at: datetime


class ImportPreviewRequest(BaseModel):
    csv_text: str = Field(min_length=1)


class ImportPreviewRow(BaseModel):
    row_number: int
    completed_on: date | None
    cost: Decimal | None
    description: str
    category_code: str | None
    component_id: str | None
    component_name: str | None
    errors: list[str]


class ImportPreviewResponse(BaseModel):
    rows: list[ImportPreviewRow]
    valid_count: int
    error_count: int


class ImportConfirmRow(BaseModel):
    completed_on: date
    cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    component_id: str
    provider_name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=5000)


class ImportConfirmRequest(BaseModel):
    rows: list[ImportConfirmRow] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def reject_duplicate_rows(self) -> "ImportConfirmRequest":
        keys = [
            (row.component_id, row.completed_on, row.cost, row.description)
            for row in self.rows
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("Import contains duplicate rows")
        return self
