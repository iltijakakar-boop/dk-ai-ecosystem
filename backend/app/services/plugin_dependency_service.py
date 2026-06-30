from typing import List, Dict, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.marketplace import MarketplaceItem, MarketplaceVersion, MarketplaceDependency


class PluginDependencyService:
    def resolve_dependencies(
        self, db: Session, *, version_id: int
    ) -> List[str]:
        """
        Recursively resolves all dependency item names for a given marketplace version.
        Returns a sorted list of dependency item names to install.
        Raises HTTPException if a circular dependency is detected.
        """
        resolved: List[str] = []
        visited: Set[str] = set()
        temp_marked: Set[str] = set()

        def visit(vid: int, item_name: str):
            if item_name in temp_marked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Circular dependency detected containing: {item_name}",
                )
            if item_name not in visited:
                temp_marked.add(item_name)
                # Query dependencies for this version
                deps = (
                    db.query(MarketplaceDependency)
                    .filter(MarketplaceDependency.version_id == vid)
                    .all()
                )
                for dep in deps:
                    # Find item ID for dependency
                    dep_item = (
                        db.query(MarketplaceItem)
                        .filter(MarketplaceItem.name == dep.dependency_item_name)
                        .first()
                    )
                    if dep_item:
                        # Find latest active version of dependency
                        latest_ver = (
                            db.query(MarketplaceVersion)
                            .filter(MarketplaceVersion.item_id == dep_item.id)
                            .order_by(MarketplaceVersion.id.desc())
                            .first()
                        )
                        if latest_ver:
                            visit(latest_ver.id, dep.dependency_item_name)

                temp_marked.remove(item_name)
                visited.add(item_name)
                resolved.append(item_name)

        # Get the starting version item name
        start_ver = db.query(MarketplaceVersion).filter(MarketplaceVersion.id == version_id).first()
        if start_ver:
            visit(version_id, start_ver.item.name)

        return resolved


plugin_dependency_service = PluginDependencyService()
