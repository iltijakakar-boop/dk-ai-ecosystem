import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.studio_models import WorkflowCanvas, WorkflowNode, WorkflowEdge, WorkflowVariable, WorkflowParameter, WorkflowOutput, WorkflowTrigger, WorkflowSchedule
from app.models.workflow_model import Workflow
from app.services.workspace_service import workspace_service


class WorkflowBuilderService:
    def save_canvas_graph(
        self, db: Session, *, canvas_id: int, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> WorkflowCanvas:
        canvas = db.query(WorkflowCanvas).filter(WorkflowCanvas.id == canvas_id).first()
        if not canvas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas not found.")

        # Clean old graph
        db.query(WorkflowNode).filter(WorkflowNode.canvas_id == canvas_id).delete()
        db.query(WorkflowEdge).filter(WorkflowEdge.canvas_id == canvas_id).delete()

        # Save new nodes
        for node in nodes:
            db_node = WorkflowNode(
                canvas_id=canvas_id,
                node_id=node.get("id"),
                type=node.get("type", "llm"),
                label=node.get("label", "Node"),
                config_data=json.dumps(node.get("config", {})),
                pos_x=node.get("position", {}).get("x", 0.0),
                pos_y=node.get("position", {}).get("y", 0.0),
            )
            db.add(db_node)

        # Save new edges
        for edge in edges:
            db_edge = WorkflowEdge(
                canvas_id=canvas_id,
                edge_id=edge.get("id"),
                source_node=edge.get("source"),
                target_node=edge.get("target"),
                source_handle=edge.get("sourceHandle"),
                target_handle=edge.get("targetHandle"),
            )
            db.add(db_edge)

        canvas.definition = json.dumps({"nodes": nodes, "edges": edges})
        db.commit()
        db.refresh(canvas)
        return canvas

    def check_circular_dependencies(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> bool:
        # Simple DFS cycle detection
        adj = {n.node_id: [] for n in nodes}
        for e in edges:
            if e.source_node in adj:
                adj[e.source_node].append(e.target_node)

        visited = {}  # 0: unvisited, 1: visiting, 2: visited
        for node_id in adj:
            visited[node_id] = 0

        def dfs(u):
            visited[u] = 1
            for v in adj[u]:
                if v not in visited:
                    continue
                if visited[v] == 1:
                    return True
                if visited[v] == 0:
                    if dfs(v):
                        return True
            visited[u] = 2
            return False

        for node_id in adj:
            if visited[node_id] == 0:
                if dfs(node_id):
                    return True
        return False

    def compile_and_register_workflow(self, db: Session, *, canvas_id: int) -> Workflow:
        canvas = db.query(WorkflowCanvas).filter(WorkflowCanvas.id == canvas_id).first()
        if not canvas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas not found.")

        # Check quota limits
        workspace_service.check_quota(db, workspace_id=canvas.workspace_id, resource_type="workflows")

        nodes = db.query(WorkflowNode).filter(WorkflowNode.canvas_id == canvas_id).all()
        edges = db.query(WorkflowEdge).filter(WorkflowEdge.canvas_id == canvas_id).all()

        # Validation: check cycle
        if self.check_circular_dependencies(nodes, edges):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Validation Failed: Visual workflow contains circular dependencies.",
            )

        # Topological sorting to construct steps order
        adj = {n.node_id: [] for n in nodes}
        in_degree = {n.node_id: 0 for n in nodes}
        node_map = {n.node_id: n for n in nodes}

        for e in edges:
            if e.source_node in adj:
                adj[e.source_node].append(e.target_node)
            if e.target_node in in_degree:
                in_degree[e.target_node] += 1

        queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
        sorted_steps = []

        while queue:
            u = queue.pop(0)
            node = node_map[u]
            sorted_steps.append({
                "name": node.label,
                "required_capability": node.type,
                "input": json.loads(node.config_data or "{}"),
            })
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Build runtime definition
        workflow_def = {"steps": sorted_steps}

        # Create or update visual deployed version
        wf = Workflow(
            workflow_id=f"studio_ws_{canvas.workspace_id}_canvas_{canvas.id}",
            version=canvas.version,
            is_active=True,
            is_template=False,
            name=canvas.name,
            description=canvas.description,
            definition=json.dumps(workflow_def),
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)

        # Increment canvas version draft
        canvas.version += 1
        db.commit()

        return wf

    def add_variable(
        self, db: Session, *, canvas_id: int, name: str, var_type: str, default_value: Optional[str] = None, description: Optional[str] = None
    ) -> WorkflowVariable:
        var = WorkflowVariable(
            canvas_id=canvas_id,
            name=name,
            type=var_type,
            default_value=default_value,
            description=description,
        )
        db.add(var)
        db.commit()
        db.refresh(var)
        return var

    def get_variables(self, db: Session, *, canvas_id: int) -> List[WorkflowVariable]:
        return db.query(WorkflowVariable).filter(WorkflowVariable.canvas_id == canvas_id).all()


workflow_builder_service = WorkflowBuilderService()
