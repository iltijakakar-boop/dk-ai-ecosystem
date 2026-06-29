import os
import sqlite3

from app.config.settings import settings
from app.core.logging import logger


def run_migrations() -> None:
    if settings.DATABASE_URL.startswith("sqlite"):
        logger.info("SQLite database detected. Running custom schema migrations...")

        # Parse database path
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")

        # Connect directly via sqlite3 driver
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()

            # Inspect table columns on the 'users' table
            cursor.execute("PRAGMA table_info(users);")
            columns = [row[1] for row in cursor.fetchall()]

            # Add columns if not already present
            if "is_deleted" not in columns:
                logger.info("Adding column 'is_deleted' to users table.")
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL;"
                )

            if "deleted_at" not in columns:
                logger.info("Adding column 'deleted_at' to users table.")
                cursor.execute("ALTER TABLE users ADD COLUMN deleted_at DATETIME;")

            if "deleted_by" not in columns:
                logger.info("Adding column 'deleted_by' to users table.")
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN deleted_by INTEGER REFERENCES users(id);"
                )

            conn.commit()
            logger.info("SQLite schema migrations applied successfully.")
        except Exception as e:
            logger.error(f"Failed to apply SQLite schema migrations: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()
    else:
        logger.info("PostgreSQL/Other database detected. Running Alembic migrations...")
        from alembic import command
        from alembic.config import Config

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
