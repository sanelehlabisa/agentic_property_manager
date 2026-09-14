import argparse
import logging

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Bid,
    Component,
    IssueReport,
    Job,
    MaintenanceRecord,
    MaintenanceRule,
    Prediction,
    Property,
    PropertyAccess,
    ProviderProfile,
    ProviderService,
    ServiceCategory,
    User,
)
from app.seed.data import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESET_ORDER = (
    Bid,
    Job,
    Prediction,
    IssueReport,
    MaintenanceRecord,
    ProviderService,
    ProviderProfile,
    Component,
    PropertyAccess,
    MaintenanceRule,
    ServiceCategory,
    Property,
    User,
)


def reset_demo_database(session: Session) -> None:
    try:
        for model in RESET_ORDER:
            session.execute(delete(model))
        session.flush()
        seed_database(session)
    except Exception:
        session.rollback()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete application data and recreate the development demo seed."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help=(
            "Confirm that all application data in the configured database "
            "may be deleted."
        ),
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error(
            "--confirm is required because this command deletes application data"
        )

    with SessionLocal() as session:
        reset_demo_database(session)
    logger.info("Development demo database reset complete")


if __name__ == "__main__":
    main()
