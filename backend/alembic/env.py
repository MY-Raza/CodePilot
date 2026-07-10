import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# -----------------------------------------------------------------------
# Path Setup
# -----------------------------------------------------------------------
# Ensure the project root (the parent of the `backend` package) is on
# sys.path so `import backend...` resolves correctly regardless of the
# working directory Alembic is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import get_settings  # noqa: E402
from backend.database.models import Base  # noqa: E402

# -----------------------------------------------------------------------
# Alembic Config Object
# -----------------------------------------------------------------------
# Provides access to the values within alembic.ini.
config = context.config

# Inject the real database URL from application settings at runtime,
# overriding the intentionally blank `sqlalchemy.url` in alembic.ini.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure Python logging per alembic.ini, if a config file is present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata used by `--autogenerate` to diff models against the
# live database schema.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping the Engine creation,
    we don't even need a DBAPI to be available. Calls to
    `context.execute()` emit the given string to the script output.

    Useful for generating raw SQL scripts without a live database
    connection (e.g. `alembic upgrade head --sql`).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the migration
    context, executing migrations directly against the live database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # Detects column server_default changes during autogenerate;
            # disabled by default in Alembic since it can be noisy, but
            # useful given our mixins rely on server_default extensively.
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()