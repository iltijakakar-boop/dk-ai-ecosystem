import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.marketplace import (
    MarketplaceItem,
    MarketplaceVersion,
    MarketplacePurchase,
    MarketplaceLicense,
    MarketplaceRevenue,
    MarketplacePublisher,
)


class MarketplacePaymentService:
    def purchase_item(
        self,
        db: Session,
        *,
        item_id: int,
        version_id: int,
        organization_id: int,
        user_id: int,
        discount_code: Optional[str] = None,
        billing_cycle: str = "one_time",
    ) -> MarketplacePurchase:
        """
        Creates a purchase record for paid marketplace items.
        Applies discount codes, generates licenses, and distributes revenue split.
        """
        item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace item not found."
            )

        # Calculate final price
        original_price = item.price
        final_price = original_price
        if discount_code == "ENTERPRISE20":
            final_price = original_price * 0.8  # 20% discount

        # 1. Register Purchase
        purchase = MarketplacePurchase(
            item_id=item_id,
            version_id=version_id,
            organization_id=organization_id,
            purchased_by=user_id,
            amount_paid=final_price,
            billing_cycle=billing_cycle,
            active=True,
        )
        db.add(purchase)
        db.commit()
        db.refresh(purchase)

        # 2. Generate License Key
        license_key = f"lic_{uuid.uuid4().hex[:16]}"
        lic = MarketplaceLicense(
            purchase_id=purchase.id,
            license_key=license_key,
            status="active",
            expires_at=datetime.utcnow() + timedelta(days=365) if billing_cycle == "yearly" else None,
        )
        db.add(lic)

        # 3. Distribute Revenue Splits (70% Publisher, 30% Platform)
        if final_price > 0.0 and item.publisher_id:
            pub_share = final_price * 0.70
            plat_share = final_price * 0.30
            rev = MarketplaceRevenue(
                purchase_id=purchase.id,
                publisher_id=item.publisher_id,
                total_amount=final_price,
                publisher_share=pub_share,
                platform_share=plat_share,
                payout_status="pending",
            )
            db.add(rev)

        db.commit()
        return purchase

    def verify_license(self, db: Session, *, license_key: str) -> bool:
        lic = db.query(MarketplaceLicense).filter(MarketplaceLicense.license_key == license_key).first()
        if not lic or lic.status != "active":
            return False
        if lic.expires_at and lic.expires_at < datetime.utcnow():
            lic.status = "expired"
            db.commit()
            return False
        return True


marketplace_payment_service = MarketplacePaymentService()
