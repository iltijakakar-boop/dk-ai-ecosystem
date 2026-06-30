import json
from typing import Any, Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.marketplace import (
    MarketplaceCategory,
    MarketplaceItem,
    MarketplaceVersion,
    MarketplacePublisher,
    MarketplaceDependency,
)


class MarketplaceService:
    def create_category(
        self, db: Session, *, name: str, slug: str, description: Optional[str] = None
    ) -> MarketplaceCategory:
        cat = MarketplaceCategory(name=name, slug=slug, description=description)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    def create_publisher(
        self, db: Session, *, name: str, support_email: str, description: Optional[str] = None, website: Optional[str] = None, user_id: Optional[int] = None
    ) -> MarketplacePublisher:
        pub = MarketplacePublisher(
            name=name,
            support_email=support_email,
            description=description,
            website=website,
            user_id=user_id,
        )
        db.add(pub)
        db.commit()
        db.refresh(pub)
        return pub

    def publish_item(
        self,
        db: Session,
        *,
        name: str,
        slug: str,
        item_type: str,
        author: str,
        version_str: str,
        description: Optional[str] = None,
        price: float = 0.0,
        manifest_data: Optional[Dict[str, Any]] = None,
        category_slug: Optional[str] = None,
        publisher_id: Optional[int] = None,
        dependencies: Optional[List[Dict[str, Any]]] = None,
    ) -> MarketplaceItem:
        """
        Publishes a new marketplace item, registering its initial version and dependencies list.
        """
        # Resolve category
        cat_id = None
        if category_slug:
            cat = db.query(MarketplaceCategory).filter(MarketplaceCategory.slug == category_slug).first()
            if cat:
                cat_id = cat.id

        # Check existing item
        item = db.query(MarketplaceItem).filter(MarketplaceItem.slug == slug).first()
        if not item:
            item = MarketplaceItem(
                slug=slug,
                name=name,
                description=description,
                item_type=item_type,
                author=author,
                price=price,
                publisher_id=publisher_id,
                category_id=cat_id,
            )
            db.add(item)
            db.commit()
            db.refresh(item)

        # Register version
        ver = MarketplaceVersion(
            item_id=item.id,
            version_str=version_str,
            manifest_data=json.dumps(manifest_data or {}),
        )
        db.add(ver)
        db.commit()
        db.refresh(ver)

        # Register dependencies
        if dependencies:
            for dep in dependencies:
                db_dep = MarketplaceDependency(
                    version_id=ver.id,
                    dependency_item_name=dep.get("name", ""),
                    min_version=dep.get("min_version"),
                    max_version=dep.get("max_version"),
                )
                db.add(db_dep)
            db.commit()

        return item

    def search_items(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        item_type: Optional[str] = None,
        category_slug: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[MarketplaceItem]:
        """
        Filters catalog items based on search query, categories, and type.
        """
        q = db.query(MarketplaceItem).filter(MarketplaceItem.active == True)

        if item_type:
            q = q.filter(MarketplaceItem.item_type == item_type)

        if category_slug:
            q = q.join(MarketplaceCategory).filter(MarketplaceCategory.slug == category_slug)

        if query:
            q = q.filter(
                or_(
                    MarketplaceItem.name.ilike(f"%{query}%"),
                    MarketplaceItem.description.ilike(f"%{query}%"),
                )
            )

        return q.limit(limit).offset(offset).all()


marketplace_service = MarketplaceService()
