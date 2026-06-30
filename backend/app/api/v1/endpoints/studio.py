from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.studio import (
    AgentStudioProjectCreate,
    AgentStudioProjectResponse,
    WorkflowCanvasCreate,
    WorkflowCanvasResponse,
    WorkflowNodeResponse,
    WorkflowEdgeResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
    AgentTemplateCreate,
    AgentTemplateResponse,
    PipelineCreate,
    PipelineResponse,
    DeploymentCreate,
    DeploymentResponse,
    ExecutionSessionCreate,
    ExecutionSessionResponse,
    DebugSessionResponse,
)
from app.services.studio_service import studio_service
from app.services.workflow_builder_service import workflow_builder_service
from app.services.agent_builder_service import agent_builder_service
from app.services.prompt_studio_service import prompt_studio_service
from app.services.pipeline_service import pipeline_service
from app.services.deployment_service import deployment_service
from app.services.debugger_service import debugger_service
from app.services.execution_service import execution_service


router = APIRouter(prefix="/studio", tags=["studio"])


# --- Request Payloads ---
class SaveGraphPayload(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class StepExecutionPayload(BaseModel):
    node_id: str
    node_type: str
    status: str
    output_data: Dict[str, Any]
    variables_delta: Dict[str, Any]


class PromptComparePayload(BaseModel):
    prompt_id: int
    version_a: int
    version_b: int
    test_inputs: Dict[str, Any]


# --- Studio Projects ---
@router.post("/projects", response_model=APIResponse[AgentStudioProjectResponse])
def create_studio_project(
    payload: AgentStudioProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proj = studio_service.create_project(db, payload)
    return APIResponse(success=True, message="Studio Project created successfully.", data=AgentStudioProjectResponse.model_validate(proj))


@router.get("/projects", response_model=APIResponse[List[AgentStudioProjectResponse]])
def list_studio_projects(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    projects = studio_service.get_projects(db, workspace_id)
    res = [AgentStudioProjectResponse.model_validate(p) for p in projects]
    return APIResponse(success=True, data=res)


# --- Workflow Canvases ---
@router.post("/canvas", response_model=APIResponse[WorkflowCanvasResponse])
def create_canvas_draft(
    payload: WorkflowCanvasCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    canvas = studio_service.create_canvas(db, payload)
    return APIResponse(success=True, message="Canvas created successfully.", data=WorkflowCanvasResponse.model_validate(canvas))


@router.get("/canvas", response_model=APIResponse[List[WorkflowCanvasResponse]])
def list_canvas_drafts(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    canvases = studio_service.get_canvases(db, workspace_id)
    res = [WorkflowCanvasResponse.model_validate(c) for c in canvases]
    return APIResponse(success=True, data=res)


@router.get("/canvas/{id}", response_model=APIResponse[WorkflowCanvasResponse])
def get_canvas_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    canvas = studio_service.get_canvas(db, id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found.")
    return APIResponse(success=True, data=WorkflowCanvasResponse.model_validate(canvas))


@router.put("/canvas/{id}/graph", response_model=APIResponse[WorkflowCanvasResponse])
def save_canvas_nodes_and_edges(
    id: int,
    payload: SaveGraphPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    canvas = workflow_builder_service.save_canvas_graph(
        db, canvas_id=id, nodes=payload.nodes, edges=payload.edges
    )
    return APIResponse(success=True, message="Graph layout saved successfully.", data=WorkflowCanvasResponse.model_validate(canvas))


@router.post("/canvas/{id}/deploy", response_model=APIResponse)
def deploy_canvas_to_runtime(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # 1. Compile flowchart to runtime Workflow template
    wf = workflow_builder_service.compile_and_register_workflow(db, canvas_id=id)

    # 2. Register Active Deployment
    canvas = studio_service.get_canvas(db, id)
    dep = deployment_service.create_deployment(
        db,
        workspace_id=canvas.workspace_id,
        canvas_id=id,
        version=wf.version,
        environment="Production",
        user_id=current_user.id,
    )

    return APIResponse(
        success=True,
        message="Workflow compiled and deployed to Production successfully.",
        data={"workflow_id": wf.workflow_id, "deployment_id": dep.id, "version": wf.version},
    )


# --- Debugger ---
@router.post("/canvas/{id}/test", response_model=APIResponse[DebugSessionResponse])
def trigger_debug_test_session(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    canvas = studio_service.get_canvas(db, id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found.")

    # Create root execution log session
    exec_session = execution_service.create_session(
        db, workspace_id=canvas.workspace_id, entity_type="workflow", entity_id=id
    )

    # Initialize Debug Session
    debug_sess = debugger_service.create_debug_session(
        db, workspace_id=canvas.workspace_id, execution_session_id=exec_session.id
    )

    return APIResponse(
        success=True,
        message="Debug session started successfully.",
        data=DebugSessionResponse.model_validate(debug_sess),
    )


@router.get("/debug/{session_id}", response_model=APIResponse[DebugSessionResponse])
def get_debug_session_details(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sess = debugger_service.get_debug_session(db, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Debug session not found.")
    return APIResponse(success=True, data=DebugSessionResponse.model_validate(sess))


@router.post("/debug/{session_id}/step", response_model=APIResponse[DebugSessionResponse])
def record_debug_node_step_execution(
    session_id: int,
    payload: StepExecutionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sess = debugger_service.record_step_execution(
        db,
        session_id=session_id,
        node_id=payload.node_id,
        node_type=payload.node_type,
        status_str=payload.status,
        output_data=payload.output_data,
        variables_delta=payload.variables_delta,
    )
    return APIResponse(success=True, message="Step executed successfully.", data=DebugSessionResponse.model_validate(sess))


# --- Prompts ---
@router.post("/prompts", response_model=APIResponse[PromptTemplateResponse])
def create_prompt_template(
    payload: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    prompt = prompt_studio_service.create_prompt(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        template_text=payload.template_text,
        variables=payload.variables,
    )
    return APIResponse(success=True, message="Prompt template created.", data=PromptTemplateResponse.model_validate(prompt))


@router.post("/prompts/compare", response_model=APIResponse)
def compare_prompt_versions(
    payload: PromptComparePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    res = prompt_studio_service.compare_prompts(
        db,
        prompt_id=payload.prompt_id,
        version_a=payload.version_a,
        version_b=payload.version_b,
        test_inputs=payload.test_inputs,
    )
    return APIResponse(success=True, data=res)
