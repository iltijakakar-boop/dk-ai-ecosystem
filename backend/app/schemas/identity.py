from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class IamIdentityProviderCreate(BaseModel):
    workspace_id: int
    name: str


class IamIdentityProviderResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    enabled: bool

    class Config:
        from_attributes = True


class IamUserSessionResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    session_token: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IamPasskeyCredentialCreate(BaseModel):
    workspace_id: int
    user_id: int
    credential_id: str
    public_key: str


class IamPasskeyCredentialResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    credential_id: str

    class Config:
        from_attributes = True


class IamAuthorizationPolicyCreate(BaseModel):
    workspace_id: int
    name: str
    mfa_required: bool
    device_trust_required: bool


class IamAuthorizationPolicyResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    mfa_required: bool
    device_trust_required: bool

    class Config:
        from_attributes = True
