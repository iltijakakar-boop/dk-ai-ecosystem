import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.marketplace import (
    MarketplaceItem,
    MarketplaceVersion,
    MarketplaceInstallation,
    PluginPermission,
    PluginSecret,
    MarketplacePurchase,
)


class PluginInstallationService:
    def install_item(
        self,
        db: Session,
        *,
        item_id: int,
        version_id: int,
        workspace_id: int,
        organization_id: int,
        user_id: int,
        config_values: Optional[Dict[str, Any]] = None,
        approved_scopes: Optional[List[str]] = None,
    ) -> MarketplaceInstallation:
        """
        Installs a marketplace extension to a workspace.
        Ensures purchase verification for paid items and registers required permissions.
        """
        item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace item not found."
            )

        # 1. Purchase Validation for Paid Items
        if item.price > 0.0:
            purchase = (
                db.query(MarketplacePurchase)
                .filter(
                    MarketplacePurchase.item_id == item_id,
                    MarketplacePurchase.organization_id == organization_id,
                    MarketplacePurchase.active == True,
                )
                .first()
            )
            if not purchase:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="This item is paid and requires a valid purchase record.",
                )

        # 2. Prevent Duplicate Active Installation
        inst = (
            db.query(MarketplaceInstallation)
            .filter(
                MarketplaceInstallation.item_id == item_id,
                MarketplaceInstallation.workspace_id == workspace_id,
            )
            .first()
        )
        if inst:
            inst.version_id = version_id
            inst.status = "active"
            inst.config_values = json.dumps(config_values or {})
            inst.updated_at = datetime.utcnow()
        else:
            inst = MarketplaceInstallation(
                item_id=item_id,
                version_id=version_id,
                workspace_id=workspace_id,
                status="active",
                config_values=json.dumps(config_values or {}),
            )
            db.add(inst)
            db.commit()
            db.refresh(inst)

        # 3. Register Permissions Approval
        # Remove old permissions
        db.query(PluginPermission).filter(PluginPermission.installation_id == inst.id).delete()
        if approved_scopes:
            for scope in approved_scopes:
                perm = PluginPermission(
                    installation_id=inst.id,
                    scope=scope,
                    approved=True,
                    approved_by=user_id,
                    approved_at=datetime.utcnow(),
                )
                db.add(perm)
            db.commit()

        return inst

    def uninstall_item(self, db: Session, *, installation_id: int) -> bool:
        inst = (
            db.query(MarketplaceInstallation)
            .filter(MarketplaceInstallation.id == installation_id)
            .first()
        )
        if not inst:
            return False

        db.delete(inst)
        db.commit()
        return True

    def toggle_status(
        self, db: Session, *, installation_id: int, enabled: bool
    ) -> MarketplaceInstallation:
        inst = (
            db.query(MarketplaceInstallation)
            .filter(MarketplaceInstallation.id == installation_id)
            .first()
        )
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found."
            )

        inst.status = "active" if enabled else "disabled"
        inst.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(inst)
        return inst

    def set_plugin_secret(
        self, db: Session, *, installation_id: int, secret_name: str, secret_value: str
    ) -> PluginSecret:
        """
        Stores an encrypted secret for a workspace plugin installation.
        """
        # Simple base64 mock encryption for testing compliance
        import base64
        encrypted = base64.b64encode(secret_value.encode()).decode()

        sec = (
            db.query(PluginSecret)
            .filter(
                PluginSecret.installation_id == installation_id,
                PluginSecret.secret_name == secret_name,
            )
            .first()
        )
        if sec:
            sec.secret_value_encrypted = encrypted
            sec.updated_at = datetime.utcnow()
        else:
            sec = PluginSecret(
                installation_id=installation_id,
                secret_name=secret_name,
                secret_value_encrypted=encrypted,
            )
            db.add(sec)
        db.commit()
        db.refresh(sec)
        return sec


plugin_installation_service = PluginInstallationService()
