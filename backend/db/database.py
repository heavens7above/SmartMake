from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from ..utils.config import config
from .models import Base
from ..utils.logger import logger

# Create engine
# handling potential sqlite fallback or postgres specific args could go here
if not config.DATABASE_URL:
    logger.error("DATABASE_URL is missing. Please set it in .env.")
    raise ValueError("DATABASE_URL is missing.")

# Postgres-specific args for Supabase (and general production)
connect_args = {"sslmode": "require"} if "postgresql" in config.DATABASE_URL else {}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
