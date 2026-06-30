import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class MarketplaceCategory(Base):
    __tablename__ = "marketplace_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    items = relationship("MarketplaceItem", back_populates="category")


class MarketplacePublisher(Base):
    __tablename__ = "marketplace_publishers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    support_email = Column(String, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, index=True, nullable=True)  # Publisher owner
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    items = relationship("MarketplaceItem", back_populates="publisher")
    revenues = relationship("MarketplaceRevenue", back_populates="publisher")


class MarketplaceItem(Base):
    __tablename__ = "marketplace_items"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(String, index=True, nullable=False)  # plugin, workflow, agent_template, prompt_pack, knowledge_pack, tool
    author = Column(String, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    publisher_id = Column(Integer, ForeignKey("marketplace_publishers.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("marketplace_categories.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    category = relationship("MarketplaceCategory", back_populates="items")
    publisher = relationship("MarketplacePublisher", back_populates="items")
    versions = relationship("MarketplaceVersion", back_populates="item", cascade="all, delete-orphan")
    installations = relationship("MarketplaceInstallation", back_populates="item")
    purchases = relationship("MarketplacePurchase", back_populates="item")
    reviews = relationship("MarketplaceReview", back_populates="item")
    downloads = relationship("MarketplaceDownload", back_populates="item")
    wishlists = relationship("MarketplaceWishlist", back_populates="item")


class MarketplaceVersion(Base):
    __tablename__ = "marketplace_versions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    version_str = Column(String, nullable=False)
    changelog = Column(Text, nullable=True)
    manifest_data = Column(Text, nullable=True)  # Manifest JSON string
    download_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="versions")
    dependencies = relationship("MarketplaceDependency", back_populates="version", cascade="all, delete-orphan")
    signature = relationship("PluginSignature", uselist=False, back_populates="version", cascade="all, delete-orphan")


class MarketplaceDependency(Base):
    __tablename__ = "marketplace_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("marketplace_versions.id"), nullable=False)
    dependency_item_name = Column(String, nullable=False)
    min_version = Column(String, nullable=True)
    max_version = Column(String, nullable=True)

    # Relationships
    version = relationship("MarketplaceVersion", back_populates="dependencies")


class MarketplaceInstallation(Base):
    __tablename__ = "marketplace_installations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("marketplace_versions.id"), nullable=False)
    workspace_id = Column(Integer, index=True, nullable=False)
    status = Column(String, default="active", nullable=False)  # active, disabled
    config_values = Column(Text, default="{}", nullable=False)  # JSON config overrides
    installed_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="installations")
    permissions = relationship("PluginPermission", back_populates="installation", cascade="all, delete-orphan")
    secrets = relationship("PluginSecret", back_populates="installation", cascade="all, delete-orphan")
    logs = relationship("PluginLog", back_populates="installation", cascade="all, delete-orphan")
    execution_history = relationship("PluginExecutionHistory", back_populates="installation", cascade="all, delete-orphan")
    crash_reports = relationship("PluginCrashReport", back_populates="installation", cascade="all, delete-orphan")


class MarketplacePurchase(Base):
    __tablename__ = "marketplace_purchases"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("marketplace_versions.id"), nullable=False)
    organization_id = Column(Integer, index=True, nullable=False)
    purchased_by = Column(Integer, nullable=False)  # User ID
    amount_paid = Column(Float, default=0.0, nullable=False)
    billing_cycle = Column(String, default="one_time", nullable=False)  # one_time, monthly, yearly
    active = Column(Boolean, default=True, nullable=False)
    purchased_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="purchases")
    licenses = relationship("MarketplaceLicense", back_populates="purchase", cascade="all, delete-orphan")
    revenues = relationship("MarketplaceRevenue", back_populates="purchase", cascade="all, delete-orphan")


class MarketplaceReview(Base):
    __tablename__ = "marketplace_reviews"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="reviews")


class MarketplaceDownload(Base):
    __tablename__ = "marketplace_downloads"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("marketplace_versions.id"), nullable=False)
    workspace_id = Column(Integer, index=True, nullable=True)
    user_id = Column(Integer, nullable=True)
    downloaded_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="downloads")


class MarketplaceCollection(Base):
    __tablename__ = "marketplace_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class MarketplaceWishlist(Base):
    __tablename__ = "marketplace_wishlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    item = relationship("MarketplaceItem", back_populates="wishlists")


class MarketplaceLicense(Base):
    __tablename__ = "marketplace_licenses"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("marketplace_purchases.id"), nullable=False)
    license_key = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="active", nullable=False)  # active, expired, suspended
    trial_expires_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    purchase = relationship("MarketplacePurchase", back_populates="licenses")


class MarketplaceRevenue(Base):
    __tablename__ = "marketplace_revenues"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("marketplace_purchases.id"), nullable=False)
    publisher_id = Column(Integer, ForeignKey("marketplace_publishers.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    publisher_share = Column(Float, nullable=False)
    platform_share = Column(Float, nullable=False)
    payout_status = Column(String, default="pending", nullable=False)  # pending, completed
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    purchase = relationship("MarketplacePurchase", back_populates="revenues")
    publisher = relationship("MarketplacePublisher", back_populates="revenues")


class MarketplaceAnalytics(Base):
    __tablename__ = "marketplace_analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True, default=datetime.utcnow, nullable=False)
    item_id = Column(Integer, ForeignKey("marketplace_items.id"), nullable=False)
    downloads_count = Column(Integer, default=0, nullable=False)
    active_installs_count = Column(Integer, default=0, nullable=False)
    revenue_amount = Column(Float, default=0.0, nullable=False)
    crash_count = Column(Integer, default=0, nullable=False)


class PluginPermission(Base):
    __tablename__ = "plugin_permissions"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_installations.id"), nullable=False)
    scope = Column(String, nullable=False)  # e.g., agent.read, storage.write
    approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, nullable=True)  # User ID
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    installation = relationship("MarketplaceInstallation", back_populates="permissions")


class PluginSignature(Base):
    __tablename__ = "plugin_signatures"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("marketplace_versions.id"), nullable=False)
    signature_hash = Column(String, nullable=False)
    public_key = Column(Text, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    version = relationship("MarketplaceVersion", back_populates="signature")


class PluginSecret(Base):
    __tablename__ = "plugin_secrets"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_installations.id"), nullable=False)
    secret_name = Column(String, nullable=False)
    secret_value_encrypted = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    installation = relationship("MarketplaceInstallation", back_populates="secrets")


class PluginLog(Base):
    __tablename__ = "plugin_logs"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_installations.id"), nullable=False)
    log_level = Column(String, default="INFO", nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    installation = relationship("MarketplaceInstallation", back_populates="logs")


class PluginExecutionHistory(Base):
    __tablename__ = "plugin_execution_history"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_installations.id"), nullable=False)
    function_name = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=False)
    cpu_usage_pct = Column(Float, default=0.0, nullable=False)
    memory_usage_mb = Column(Float, default=0.0, nullable=False)
    status = Column(String, nullable=False)  # success, error
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    installation = relationship("MarketplaceInstallation", back_populates="execution_history")


class PluginCrashReport(Base):
    __tablename__ = "plugin_crash_reports"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_installations.id"), nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=False)
    occurrence_time = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    installation = relationship("MarketplaceInstallation", back_populates="crash_reports")


# Logic subclasses / Helper models mapping properties
class WorkflowTemplate:
    def __init__(self, name: str, description: str, definition: Dict[str, Any]):
        self.name = name
        self.description = description
        self.definition = definition


class AgentTemplate:
    def __init__(self, name: str, description: str, system_prompt: str, tools: List[str]):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools


class PromptTemplate:
    def __init__(self, name: str, prompt_text: str, variables: List[str]):
        self.name = name
        self.prompt_text = prompt_text
        self.variables = variables


class KnowledgePack:
    def __init__(self, name: str, description: str, documents: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.documents = documents


class ToolPackage:
    def __init__(self, name: str, description: str, tools_code: str):
        self.name = name
        self.description = description
        self.tools_code = tools_code


class UIExtension:
    def __init__(self, name: str, component_name: str, assets_urls: List[str]):
        self.name = name
        self.component_name = component_name
        self.assets_urls = assets_urls
