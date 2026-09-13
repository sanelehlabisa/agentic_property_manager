"""Create the initial property management schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "homeowner",
                "manager",
                "tenant",
                "provider",
                name="user_role",
                native_enum=False,
            ),
            nullable=False,
        ),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("address_line_1", sa.String(length=200), nullable=False),
        sa.Column("address_line_2", sa.String(length=200), nullable=True),
        sa.Column("suburb", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_properties")),
    )
    op.create_index("ix_properties_suburb", "properties", ["suburb"])
    op.create_index("ix_properties_city", "properties", ["city"])

    op.create_table(
        "service_categories",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_service_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_service_categories_name")),
    )

    op.create_table(
        "property_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "access_role",
            sa.Enum(
                "owner",
                "manager",
                "tenant",
                name="property_access_role",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_property_access_property_id_properties"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_property_access_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_property_access")),
        sa.UniqueConstraint("property_id", "user_id", name="uq_property_access_member"),
    )
    op.create_index(
        "ix_property_access_property_id", "property_access", ["property_id"]
    )
    op.create_index("ix_property_access_user_id", "property_access", ["user_id"])

    op.create_table(
        "components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("installed_on", sa.Date(), nullable=True),
        sa.Column(
            "condition",
            sa.Enum(
                "new",
                "good",
                "fair",
                "poor",
                "unknown",
                name="component_condition",
                native_enum=False,
            ),
            nullable=False,
        ),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["service_categories.code"],
            name=op.f("fk_components_category_code_service_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_components_property_id_properties"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_components")),
    )
    op.create_index("ix_components_property_id", "components", ["property_id"])
    op.create_index("ix_components_category_code", "components", ["category_code"])

    op.create_table(
        "maintenance_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("interval_months", sa.Integer(), nullable=False),
        sa.Column("warning_days", sa.Integer(), nullable=False),
        sa.Column("default_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "default_cost >= 0",
            name=op.f("ck_maintenance_rules_nonnegative_default_cost"),
        ),
        sa.CheckConstraint(
            "interval_months > 0",
            name=op.f("ck_maintenance_rules_positive_interval_months"),
        ),
        sa.CheckConstraint(
            "warning_days >= 0",
            name=op.f("ck_maintenance_rules_nonnegative_warning_days"),
        ),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["service_categories.code"],
            name=op.f("fk_maintenance_rules_category_code_service_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_rules")),
        sa.UniqueConstraint("category_code", name="uq_maintenance_rule_category"),
    )
    op.create_index(
        "ix_maintenance_rules_category_code", "maintenance_rules", ["category_code"]
    )

    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("suburb", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("service_radius_km", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "rating >= 0 AND rating <= 5",
            name=op.f("ck_provider_profiles_valid_provider_rating"),
        ),
        sa.CheckConstraint(
            "service_radius_km > 0",
            name=op.f("ck_provider_profiles_positive_service_radius"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_provider_profiles_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_provider_profiles_user_id")),
    )
    op.create_index("ix_provider_profiles_suburb", "provider_profiles", ["suburb"])
    op.create_index("ix_provider_profiles_city", "provider_profiles", ["city"])

    op.create_table(
        "issue_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_user_id", sa.Uuid(), nullable=False),
        sa.Column("component_id", sa.Uuid(), nullable=True),
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "urgency",
            sa.Enum(
                "low",
                "medium",
                "high",
                "emergency",
                name="report_urgency",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending_approval",
                "approved",
                "rejected",
                "converted_to_job",
                name="report_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("review_reason", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["service_categories.code"],
            name=op.f("fk_issue_reports_category_code_service_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name=op.f("fk_issue_reports_component_id_components"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_issue_reports_property_id_properties"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_user_id"],
            ["users.id"],
            name=op.f("fk_issue_reports_reporter_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f("fk_issue_reports_reviewed_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_issue_reports")),
    )
    op.create_index("ix_issue_reports_property_id", "issue_reports", ["property_id"])
    op.create_index(
        "ix_issue_reports_reporter_user_id", "issue_reports", ["reporter_user_id"]
    )
    op.create_index("ix_issue_reports_component_id", "issue_reports", ["component_id"])
    op.create_index(
        "ix_issue_reports_category_code", "issue_reports", ["category_code"]
    )
    op.create_index("ix_issue_reports_status", "issue_reports", ["status"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("component_id", sa.Uuid(), nullable=False),
        sa.Column("completed_on", sa.Date(), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("provider_name", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "cost >= 0",
            name=op.f("ck_maintenance_records_nonnegative_maintenance_cost"),
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name=op.f("fk_maintenance_records_component_id_components"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_records")),
    )
    op.create_index(
        "ix_maintenance_records_component_id",
        "maintenance_records",
        ["component_id"],
    )
    op.create_index(
        "ix_maintenance_records_completed_on",
        "maintenance_records",
        ["completed_on"],
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("component_id", sa.Uuid(), nullable=False),
        sa.Column("maintenance_rule_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "urgency",
            sa.Enum(
                "overdue",
                "due_soon",
                "upcoming",
                name="prediction_urgency",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("explanation", sa.String(length=500), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "approved",
                "dismissed",
                "converted_to_job",
                name="prediction_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint(
            "estimated_cost >= 0",
            name=op.f("ck_predictions_nonnegative_estimated_cost"),
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name=op.f("fk_predictions_component_id_components"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_rule_id"],
            ["maintenance_rules.id"],
            name=op.f("fk_predictions_maintenance_rule_id_maintenance_rules"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
    )
    op.create_index("ix_predictions_component_id", "predictions", ["component_id"])
    op.create_index(
        "ix_predictions_maintenance_rule_id", "predictions", ["maintenance_rule_id"]
    )
    op.create_index("ix_predictions_due_date", "predictions", ["due_date"])
    op.create_index("ix_predictions_status", "predictions", ["status"])

    op.create_table(
        "provider_services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_profile_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["service_categories.code"],
            name=op.f("fk_provider_services_category_code_service_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_profile_id"],
            ["provider_profiles.id"],
            name=op.f("fk_provider_services_provider_profile_id_provider_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_services")),
        sa.UniqueConstraint(
            "provider_profile_id",
            "category_code",
            name="uq_provider_service_category",
        ),
    )
    op.create_index(
        "ix_provider_services_provider_profile_id",
        "provider_services",
        ["provider_profile_id"],
    )
    op.create_index(
        "ix_provider_services_category_code",
        "provider_services",
        ["category_code"],
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("issue_report_id", sa.Uuid(), nullable=True),
        sa.Column("prediction_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("budget", sa.Numeric(12, 2), nullable=False),
        sa.Column("public_location", sa.String(length=250), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "awarded",
                "in_progress",
                "completed",
                "cancelled",
                name="job_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint(
            "((issue_report_id IS NOT NULL AND prediction_id IS NULL) OR "
            "(issue_report_id IS NULL AND prediction_id IS NOT NULL))",
            name=op.f("ck_jobs_exactly_one_job_source"),
        ),
        sa.CheckConstraint("budget >= 0", name=op.f("ck_jobs_nonnegative_job_budget")),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            name=op.f("fk_jobs_approved_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["service_categories.code"],
            name=op.f("fk_jobs_category_code_service_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["issue_report_id"],
            ["issue_reports.id"],
            name=op.f("fk_jobs_issue_report_id_issue_reports"),
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"],
            ["predictions.id"],
            name=op.f("fk_jobs_prediction_id_predictions"),
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_jobs_property_id_properties"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("issue_report_id", name=op.f("uq_jobs_issue_report_id")),
        sa.UniqueConstraint("prediction_id", name=op.f("uq_jobs_prediction_id")),
    )
    op.create_index("ix_jobs_property_id", "jobs", ["property_id"])
    op.create_index("ix_jobs_category_code", "jobs", ["category_code"])
    op.create_index("ix_jobs_public_location", "jobs", ["public_location"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "bids",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("provider_profile_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("available_on", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "submitted",
                "accepted",
                "withdrawn",
                "rejected",
                name="bid_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint("amount > 0", name=op.f("ck_bids_positive_bid_amount")),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_bids_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["provider_profile_id"],
            ["provider_profiles.id"],
            name=op.f("fk_bids_provider_profile_id_provider_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bids")),
        sa.UniqueConstraint(
            "job_id", "provider_profile_id", name="uq_bid_provider_job"
        ),
    )
    op.create_index("ix_bids_job_id", "bids", ["job_id"])
    op.create_index("ix_bids_provider_profile_id", "bids", ["provider_profile_id"])
    op.create_index("ix_bids_status", "bids", ["status"])


def downgrade() -> None:
    op.drop_table("bids")
    op.drop_table("jobs")
    op.drop_table("provider_services")
    op.drop_table("predictions")
    op.drop_table("maintenance_records")
    op.drop_table("issue_reports")
    op.drop_table("provider_profiles")
    op.drop_table("maintenance_rules")
    op.drop_table("components")
    op.drop_table("property_access")
    op.drop_table("service_categories")
    op.drop_table("properties")
    op.drop_table("users")
