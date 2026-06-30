from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class DevOpsRepository(Base):
    __tablename__ = "devops_repositories"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)


class DevOpsGitProvider(Base):
    __tablename__ = "devops_git_providers"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)  # github, gitlab


class DevOpsBranch(Base):
    __tablename__ = "devops_branches"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("devops_repositories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class DevOpsCommit(Base):
    __tablename__ = "devops_commits"
    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("devops_branches.id", ondelete="CASCADE"), nullable=False)
    sha = Column(String, nullable=False)
    message = Column(String, nullable=False)


class DevOpsPullRequest(Base):
    __tablename__ = "devops_pull_requests"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("devops_repositories.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    source_branch = Column(String, nullable=False)
    target_branch = Column(String, nullable=False)
    merged = Column(Boolean, default=False, nullable=False)


class DevOpsPipeline(Base):
    __tablename__ = "devops_pipelines"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DevOpsPipelineRun(Base):
    __tablename__ = "devops_pipeline_runs"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("devops_pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    created_at = Column(DateTime, default=func.now(), nullable=False)


class DevOpsPipelineStage(Base):
    __tablename__ = "devops_pipeline_stages"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("devops_pipeline_runs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # build, test, deploy
    status = Column(String, default="pending", nullable=False)


class DevOpsBuild(Base):
    __tablename__ = "devops_builds"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    commit_sha = Column(String, nullable=False)
    status = Column(String, nullable=False)


class DevOpsArtifact(Base):
    __tablename__ = "devops_artifacts"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DevOpsArtifactVersion(Base):
    __tablename__ = "devops_artifact_versions"
    id = Column(Integer, primary_key=True, index=True)
    artifact_id = Column(Integer, ForeignKey("devops_artifacts.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)


class DevOpsContainerImage(Base):
    __tablename__ = "devops_container_images"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    digest = Column(String, nullable=False)


class DevOpsContainerRegistry(Base):
    __tablename__ = "devops_container_registries"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    url = Column(String, nullable=False)


class DevOpsRelease(Base):
    __tablename__ = "devops_releases"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    version = Column(String, nullable=False)  # v1.0.0
    status = Column(String, default="active", nullable=False)


class DevOpsReleaseNote(Base):
    __tablename__ = "devops_release_notes"
    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("devops_releases.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)


class DevOpsDeployment(Base):
    __tablename__ = "devops_deployments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    release_id = Column(Integer, ForeignKey("devops_releases.id", ondelete="CASCADE"), nullable=False)
    environment = Column(String, nullable=False)  # production, staging
    status = Column(String, default="deploying", nullable=False)


class DevOpsDeploymentEnvironment(Base):
    __tablename__ = "devops_deployment_environments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DevOpsApprovalRequest(Base):
    __tablename__ = "devops_approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    deployment_id = Column(Integer, ForeignKey("devops_deployments.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, approved, rejected


class DevOpsApprovalHistory(Base):
    __tablename__ = "devops_approval_history"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("devops_approval_requests.id", ondelete="CASCADE"), nullable=False)
    approver = Column(String, nullable=False)
    action = Column(String, nullable=False)


class DevOpsRollback(Base):
    __tablename__ = "devops_rollbacks"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    deployment_id = Column(Integer, ForeignKey("devops_deployments.id", ondelete="CASCADE"), nullable=False)
    target_release_id = Column(Integer, ForeignKey("devops_releases.id", ondelete="CASCADE"), nullable=False)


class DevOpsInfrastructureTemplate(Base):
    __tablename__ = "devops_iac_templates"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DevOpsTerraformState(Base):
    __tablename__ = "devops_terraform_states"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("devops_iac_templates.id", ondelete="CASCADE"), nullable=False)
    state_file_json = Column(Text, nullable=False)


class DevOpsGitOpsRepository(Base):
    __tablename__ = "devops_gitops_repositories"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    sync_status = Column(String, default="synced", nullable=False)


class DevOpsSecretReference(Base):
    __tablename__ = "devops_secret_references"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    secret_path = Column(String, nullable=False)


class DevOpsDeploymentPolicy(Base):
    __tablename__ = "devops_deployment_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    policy_name = Column(String, nullable=False)


class DevOpsChangeRequest(Base):
    __tablename__ = "devops_change_requests"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="draft", nullable=False)
