from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from backend.database.database import engine

# -----------------------------------------------------------------------
# Session Factory
# -----------------------------------------------------------------------
# autocommit=False: Transactions must be explicitly committed, giving
#   callers full control over transaction boundaries.
# autoflush=False: Avoids implicit flushes before queries, preventing
#   unintended partial writes from being emitted mid-transaction.
# future=True: Opts into SQLAlchemy 2.0-style session behavior.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session scoped to a single request.

    Intended for use as a FastAPI dependency via `Depends(get_db)`. The
    session is created lazily per-request and guaranteed to close after
    the request completes, even if an exception is raised.

    Yields:
        An active SQLAlchemy `Session` bound to the application engine.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()