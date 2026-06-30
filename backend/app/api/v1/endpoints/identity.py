from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.identity import (
    IamIdentityProviderCreate,
    IamIdentityProviderResponse,
    IamUserSessionResponse,
    IamPasskeyCredentialCreate,
    IamPasskeyCredentialResponse,
    IamAuthorizationPolicyCreate,
    IamAuthorizationPolicyResponse,
)
from app.services.identity_service import (
    identity_provider_service,
    session_service,
    passkey_service,
    policy_engine_service,
)


router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/providers", response_model=APIResponse[IamIdentityProviderResponse])
def configure_sso_provider(
    payload: IamIdentityProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    provider = identity_provider_service.create_provider(db, workspace_id=payload.workspace_id, name=payload.name)
    return APIResponse(success=True, message="SSO Identity provider configured.", data=IamIdentityProviderResponse.model_validate(provider))


@router.get("/providers", response_model=APIResponse[List[IamIdentityProviderResponse]])
def get_sso_providers_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    providers = identity_provider_service.get_providers(db, workspace_id)
    res = [IamIdentityProviderResponse.model_validate(p) for p in providers]
    return APIResponse(success=True, data=res)


@router.get("/sessions", response_model=APIResponse[List[IamUserSessionResponse]])
def get_active_sessions_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sessions = session_service.get_sessions(db, workspace_id)
    res = [IamUserSessionResponse.model_validate(s) for s in sessions]
    return APIResponse(success=True, data=res)


@router.post("/sessions/{id}/revoke", response_model=APIResponse[IamUserSessionResponse])
def revoke_active_user_session(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = session_service.revoke_session(db, id)
    if not session:
        raise HTTPException(status_code=404, detail="Active user session not found.")
    return APIResponse(success=True, message="Active user session revoked.", data=IamUserSessionResponse.model_validate(session))


@router.post("/passkeys", response_model=APIResponse[IamPasskeyCredentialResponse])
def register_webauthn_passkey(
    payload: IamPasskeyCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pk = passkey_service.register_passkey(db, workspace_id=payload.workspace_id, user_id=payload.user_id, credential_id=payload.credential_id, public_key=payload.public_key)
    return APIResponse(success=True, message="WebAuthn passkey registered.", data=IamPasskeyCredentialResponse.model_validate(pk))


@router.post("/policies", response_model=APIResponse[IamAuthorizationPolicyResponse])
def create_conditional_access_policy(
    payload: IamAuthorizationPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    policy = policy_engine_service.create_policy(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        mfa_required=payload.mfa_required,
        device_trust_required=payload.device_trust_required
    )
    return APIResponse(success=True, message="Conditional access policy created.", data=IamAuthorizationPolicyResponse.model_validate(policy))


@router.get("/policies", response_model=APIResponse[List[IamAuthorizationPolicyResponse]])
def get_policies_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    policies = policy_engine_service.get_policies(db, workspace_id)
    res = [IamAuthorizationPolicyResponse.model_validate(p) for p in policies]
    return APIResponse(success=True, data=res)
