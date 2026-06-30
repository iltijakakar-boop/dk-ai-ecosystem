from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class IamIdentityProvider(Base):
    __tablename__ = "iam_identity_providers"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)  # okta, google, saml
    enabled = Column(Boolean, default=True, nullable=False)


class IamFederatedIdentity(Base):
    __tablename__ = "iam_federated_identities"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("iam_identity_providers.id", ondelete="CASCADE"), nullable=False)
    external_user_id = Column(String, nullable=False)


class IamOrganizationIdentity(Base):
    __tablename__ = "iam_org_identities"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, index=True, nullable=False)
    identity_provider_id = Column(Integer, ForeignKey("iam_identity_providers.id", ondelete="CASCADE"), nullable=False)


class IamWorkspaceIdentity(Base):
    __tablename__ = "iam_workspace_identities"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    identity_provider_id = Column(Integer, ForeignKey("iam_identity_providers.id", ondelete="CASCADE"), nullable=False)


class IamUserSession(Base):
    __tablename__ = "iam_user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class IamSessionHistory(Base):
    __tablename__ = "iam_session_history"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("iam_user_sessions.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # created, revoked


class IamSessionDevice(Base):
    __tablename__ = "iam_session_devices"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("iam_user_sessions.id", ondelete="CASCADE"), nullable=False)
    device_fingerprint = Column(String, nullable=False)


class IamTrustedDevice(Base):
    __tablename__ = "iam_trusted_devices"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    device_fingerprint = Column(String, nullable=False)


class IamLoginHistory(Base):
    __tablename__ = "iam_login_history"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    ip_address = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class IamAuthenticationAttempt(Base):
    __tablename__ = "iam_auth_attempts"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    username = Column(String, nullable=False)
    success = Column(Boolean, default=False, nullable=False)


class IamRefreshToken(Base):
    __tablename__ = "iam_refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("iam_user_sessions.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)


class IamAccessToken(Base):
    __tablename__ = "iam_access_tokens"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("iam_user_sessions.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)


class IamOAuthClient(Base):
    __tablename__ = "iam_oauth_clients"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    client_id = Column(String, unique=True, nullable=False)
    client_secret = Column(String, nullable=False)


class IamOAuthScope(Base):
    __tablename__ = "iam_oauth_scopes"
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, unique=True, nullable=False)


class IamOAuthConsent(Base):
    __tablename__ = "iam_oauth_consents"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("iam_oauth_clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)


class IamAuthorizationPolicy(Base):
    __tablename__ = "iam_auth_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    mfa_required = Column(Boolean, default=False, nullable=False)
    device_trust_required = Column(Boolean, default=False, nullable=False)


class IamPolicyRule(Base):
    __tablename__ = "iam_policy_rules"
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("iam_auth_policies.id", ondelete="CASCADE"), nullable=False)
    rule_expression = Column(String, nullable=False)


class IamPermissionAssignment(Base):
    __tablename__ = "iam_permission_assignments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    role = Column(String, nullable=False)
    permission = Column(String, nullable=False)


class IamPermissionGroup(Base):
    __tablename__ = "iam_permission_groups"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class IamRoleHierarchy(Base):
    __tablename__ = "iam_role_hierarchy"
    id = Column(Integer, primary_key=True, index=True)
    parent_role = Column(String, nullable=False)
    child_role = Column(String, nullable=False)


class IamServiceIdentity(Base):
    __tablename__ = "iam_service_identities"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    service_name = Column(String, nullable=False)


class IamMachineIdentity(Base):
    __tablename__ = "iam_machine_identities"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    machine_uuid = Column(String, nullable=False)


class IamAPIClient(Base):
    __tablename__ = "iam_api_clients"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class IamAPISecret(Base):
    __tablename__ = "iam_api_secrets"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("iam_api_clients.id", ondelete="CASCADE"), nullable=False)
    secret_hash = Column(String, nullable=False)


class IamPasskeyCredential(Base):
    __tablename__ = "iam_passkey_credentials"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    credential_id = Column(String, unique=True, nullable=False)
    public_key = Column(Text, nullable=False)


class IamMFADevice(Base):
    __tablename__ = "iam_mfa_devices"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    device_type = Column(String, nullable=False)  # totp, sms
    secret = Column(String, nullable=False)


class IamBackupCode(Base):
    __tablename__ = "iam_backup_codes"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("iam_mfa_devices.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)


class IamSecurityChallenge(Base):
    __tablename__ = "iam_security_challenges"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    challenge_type = Column(String, nullable=False)


class IamRiskScore(Base):
    __tablename__ = "iam_risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    score = Column(Float, default=0.0, nullable=False)


class IamAccessDecision(Base):
    __tablename__ = "iam_access_decisions"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    decision = Column(String, nullable=False)  # allow, deny


class IamIdentityAudit(Base):
    __tablename__ = "iam_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
