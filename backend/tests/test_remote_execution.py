from sqlalchemy.orm import Session
from app.services.remote_execution_service import remote_execution_service


def test_remote_execution_endpoints(db: Session):
    # 1. Register remote endpoint
    endpoint = remote_execution_service.register_remote_endpoint(
        db,
        workspace_id=1,
        url="https://remote-mcp-server.local/api",
        auth_header="Bearer token_xyz"
    )
    assert endpoint.url == "https://remote-mcp-server.local/api"

    # 2. Trigger execution
    res = remote_execution_service.execute_remote_tool(
        db,
        workspace_id=1,
        endpoint_id=endpoint.id,
        tool_name="get_remote_logs",
        arguments={"lines": 50}
    )
    assert res is not None
    assert res["status"] == "success"
    assert "echo_args" in res
