import os
from alembic.config import Config
from alembic import command

def run_migrations() -> None:
    # Run database migrations programmatically using Alembic config
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
