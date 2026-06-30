from sqlalchemy.orm import Session
from app.models.mcp_models import ToolUsageStatistics


class AnalyticsService:
    def record_tool_call(
        self, db: Session, *, workspace_id: int, tool_name: str, duration_ms: float, is_error: bool = False
    ) -> ToolUsageStatistics:
        stats = (
            db.query(ToolUsageStatistics)
            .filter(
                ToolUsageStatistics.workspace_id == workspace_id,
                ToolUsageStatistics.tool_name == tool_name,
            )
            .first()
        )
        if not stats:
            stats = ToolUsageStatistics(
                workspace_id=workspace_id,
                tool_name=tool_name,
                calls_count=1,
                errors_count=1 if is_error else 0,
                total_duration_ms=duration_ms,
            )
            db.add(stats)
        else:
            stats.calls_count += 1
            if is_error:
                stats.errors_count += 1
            stats.total_duration_ms += duration_ms
        db.commit()
        db.refresh(stats)
        return stats

    def get_tool_statistics(self, db: Session, *, workspace_id: int) -> list:
        return db.query(ToolUsageStatistics).filter(ToolUsageStatistics.workspace_id == workspace_id).all()


analytics_service = AnalyticsService()
