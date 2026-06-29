from typing import Any, Dict

from app.db.session import SessionLocal
from app.models.tool_model import Plugin as DBPlugin


def get_plugin_metrics() -> Dict[str, Any]:
    """
    Queries the database plugins table to count active, disabled, and failed plugins.
    """
    db = SessionLocal()
    try:
        total = db.query(DBPlugin).count()
        active = db.query(DBPlugin).filter(DBPlugin.status == "active").count()
        disabled = db.query(DBPlugin).filter(DBPlugin.status == "disabled").count()
        failed = db.query(DBPlugin).filter(DBPlugin.status == "error").count()

        return {
            "installed_plugins": total,
            "active_plugins": active,
            "disabled_plugins": disabled,
            "failed_plugins": failed,
        }
    except Exception:
        return {
            "installed_plugins": 0,
            "active_plugins": 0,
            "disabled_plugins": 0,
            "failed_plugins": 0,
        }
    finally:
        db.close()
