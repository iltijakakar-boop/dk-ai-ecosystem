from sqlalchemy.orm import Session
from app.services.deployment_service import deployment_service


def test_visual_builder_deployment_and_rollback(db: Session):
    # 1. Create deployment
    dep = deployment_service.create_deployment(
        db,
        workspace_id=1,
        canvas_id=10,
        version=1,
        environment="Staging",
        user_id=1,
    )
    assert dep.environment == "Staging"
    assert dep.status == "Active"

    # 2. Rollback deployment (updates status and adds logs)
    rolled_back = deployment_service.rollback_deployment(db, deployment_id=dep.id, user_id=1)
    assert rolled_back.status == "RolledBack"
