import logging

from app.core.database import SessionLocal
from app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    with SessionLocal() as session:
        seed_database(session)
    logger.info("Database seed complete")


if __name__ == "__main__":
    main()
