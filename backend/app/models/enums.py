from enum import StrEnum


class UserRole(StrEnum):
    HOMEOWNER = "homeowner"
    MANAGER = "manager"
    TENANT = "tenant"
    PROVIDER = "provider"


class PropertyAccessRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    TENANT = "tenant"


class ComponentCondition(StrEnum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class ReportUrgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ReportStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED_TO_JOB = "converted_to_job"


class PredictionUrgency(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    UPCOMING = "upcoming"


class PredictionStatus(StrEnum):
    ACTIVE = "active"
    APPROVED = "approved"
    DISMISSED = "dismissed"
    CONVERTED_TO_JOB = "converted_to_job"


class JobStatus(StrEnum):
    OPEN = "open"
    AWARDED = "awarded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatus(StrEnum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"
