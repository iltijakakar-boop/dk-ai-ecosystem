import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.identity_models import (
    IamIdentityProvider,
    IamUserSession,
    IamPasskeyCredential,
    IamAuthorizationPolicy,
    IamIdentityAudit,
)


class IdentityProviderService:
    def create_provider(self, db: Session, *, workspace_id: int, name: str) -> IamIdentityProvider:
        provider = IamIdentityProvider(workspace_id=workspace_id, name=name, enabled=True)
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return provider

    def get_providers(self, db: Session, workspace_id: int) -> List[IamIdentityProvider]:
        return db.query(IamIdentityProvider).filter(IamIdentityProvider.workspace_id == workspace_id).all()


class SessionService:
    def create_session(self, db: Session, *, workspace_id: int, user_id: int) -> IamUserSession:
        token = f"session_{uuid.uuid4()}"
        session = IamUserSession(
            workspace_id=workspace_id,
            user_id=user_id,
            session_token=token,
            active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_sessions(self, db: Session, workspace_id: int) -> List[IamUserSession]:
        return db.query(IamUserSession).filter(IamUserSession.workspace_id == workspace_id, IamUserSession.active == True).all()

    def revoke_session(self, db: Session, session_id: int) -> IamUserSession:
        session = db.query(IamUserSession).filter(IamUserSession.id == session_id).first()
        if not session:
            return None
        session.active = False
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


class PasskeyService:
    def register_passkey(self, db: Session, *, workspace_id: int, user_id: int, credential_id: str, public_key: str) -> IamPasskeyCredential:
        pk = IamPasskeyCredential(
            workspace_id=workspace_id,
            user_id=user_id,
            credential_id=credential_id,
            public_key=public_key
        )
        db.add(pk)
        db.commit()
        db.refresh(pk)
        return pk

    def get_passkeys(self, db: Session, workspace_id: int, user_id: int) -> List[IamPasskeyCredential]:
        return db.query(IamPasskeyCredential).filter(IamPasskeyCredential.workspace_id == workspace_id, IamPasskeyCredential.user_id == user_id).all()


class PolicyEngineService:
    def create_policy(self, db: Session, *, workspace_id: int, name: str, mfa_required: bool, device_trust_required: bool) -> IamAuthorizationPolicy:
        policy = IamAuthorizationPolicy(
            workspace_id=workspace_id,
            name=name,
            mfa_required=mfa_required,
            device_trust_required=device_trust_required
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def get_policies(self, db: Session, workspace_id: int) -> List[IamAuthorizationPolicy]:
        return db.query(IamAuthorizationPolicy).filter(IamAuthorizationPolicy.workspace_id == workspace_id).all()


identity_provider_service = IdentityProviderService()
session_service = SessionService()
passkey_service = PasskeyService()
policy_engine_service = PolicyEngineService()
