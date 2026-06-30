from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.studio_service import studio_service
from app.schemas.studio import WorkflowCanvasCreate
from app.services.workflow_builder_service import workflow_builder_service


def test_workflow_builder_graph_cycles_and_save(client: TestClient, db: Session):
    # Setup canvas
    canvas_payload = WorkflowCanvasCreate(
        workspace_id=1,
        name="Build Flow Canvas",
        description="Visual graph validations",
        definition={}
    )
    canvas = studio_service.create_canvas(db, canvas_payload)

    # 1. Save Graph (Valid DAG: Node A -> Node B)
    nodes = [
        {"id": "node_a", "type": "llm", "label": "Start Prompt", "position": {"x": 100, "y": 100}},
        {"id": "node_b", "type": "agent", "label": "Coding Agent", "position": {"x": 300, "y": 100}},
    ]
    edges = [
        {"id": "edge_1", "source": "node_a", "target": "node_b", "sourceHandle": "out", "targetHandle": "in"}
    ]
    workflow_builder_service.save_canvas_graph(db, canvas_id=canvas.id, nodes=nodes, edges=edges)

    # Compile should succeed
    wf = workflow_builder_service.compile_and_register_workflow(db, canvas_id=canvas.id)
    assert wf is not None
    assert "Coding Agent" in wf.definition

    # 2. Save Graph (Invalid DAG with Cycle: Node A -> Node B -> Node A)
    edges_cycle = [
        {"id": "edge_1", "source": "node_a", "target": "node_b"},
        {"id": "edge_2", "source": "node_b", "target": "node_a"},
    ]
    workflow_builder_service.save_canvas_graph(db, canvas_id=canvas.id, nodes=nodes, edges=edges_cycle)

    # Compile should fail with cycle check exception
    try:
        workflow_builder_service.compile_and_register_workflow(db, canvas_id=canvas.id)
        assert False, "Should raise cycle detection HTTP Exception."
    except Exception as e:
        assert "circular dependencies" in str(e)
