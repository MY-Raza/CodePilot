from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from backend.core.config import get_settings

settings = get_settings()

# -----------------------------------------------------------------------
# Engine Configuration
# -----------------------------------------------------------------------
# pool_size: Number of persistent connections kept open in the pool.
# max_overflow: Additional connections allowed beyond pool_size under
#   burst load, closed once no longer needed.
# pool_timeout: Seconds to wait for a connection from the pool before
#   raising a TimeoutError.
# pool_recycle: Seconds after which a connection is recycled, preventing
#   the use of connections dropped by the database server or a
#   load balancer (e.g. common with managed Postgres providers).
# pool_pre_ping: Issues a lightweight "SELECT 1" before checkout to
#   detect and transparently replace stale/dead connections.
# future=True: Opts into SQLAlchemy 2.0-style engine/connection behavior.
engine: Engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    future=True,
    echo=settings.debug,
)