from .db.database import init_db
from .utils.logger import logger

if __name__ == "__main__":
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e
