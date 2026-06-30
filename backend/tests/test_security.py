from sqlalchemy.orm import Session
from app.services.tool_permission_service import tool_permission_service


def test_tool_security_scopes_and_workspace_isolation(db: Session):
    # 1. Grant tool permission scopes
    tool_permission_service.grant_permission(
        db,
        workspace_id=1,
        tool_name="delete_database_records",
        allowed_scopes=["admin.full", "developer"]
    )

    # 2. Verify allowed scope permission
    allowed = tool_permission_service.verify_tool_permission(
        db,
        workspace_id=1,
        tool_name="delete_database_records",
        required_scope="developer"
    )
    assert allowed is True

    # 3. Verify denied scope permission
    denied = tool_permission_service.verify_tool_permission(
        db,
        workspace_id=1,
        tool_name="delete_database_records",
        required_scope="viewer"
    )
    assert denied is False

    # 4. Verify workspace isolation (Should return false for same tool in Workspace 2)
    isolated = tool_permission_service.verify_tool_permission(
        db,
        workspace_id=2,
        tool_name="delete_database_records",
        required_scope="developer"
    )
    assert isolated is False
