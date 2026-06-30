from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.organization import UsageRecord


class UsageService:
    def record_usage(
        self,
        db: Session,
        *,
        workspace_id: int,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tokens: int = 0,
        requests: int = 1,
        storage_used: int = 0,
        vector_usage: int = 0,
        automation_usage: int = 0,
        workflow_usage: int = 0,
        bandwidth: int = 0,
        cpu_usage: int = 0,
        gpu_usage: int = 0,
        memory_usage: int = 0,
        response_latency_ms: int = 0,
        error_rate: int = 0,
    ) -> UsageRecord:
        # Simple operational cost model mapping:
        # 1 microcent ($0.000001) per request, 0.05 microcents per token
        estimated_cost = (requests * 1) + int(tokens * 0.05)

        rec = UsageRecord(
            workspace_id=workspace_id,
            provider=provider,
            model=model,
            tokens=tokens,
            requests=requests,
            storage_used=storage_used,
            vector_usage=vector_usage,
            automation_usage=automation_usage,
            workflow_usage=workflow_usage,
            bandwidth=bandwidth,
            cpu_usage=cpu_usage,
            gpu_usage=gpu_usage,
            memory_usage=memory_usage,
            response_latency_ms=response_latency_ms,
            error_rate=error_rate,
            estimated_cost=estimated_cost,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    def aggregate_workspace_usage(
        self, db: Session, *, workspace_id: int
    ) -> Dict[str, Any]:
        totals = (
            db.query(
                func.sum(UsageRecord.tokens).label("tokens"),
                func.sum(UsageRecord.requests).label("requests"),
                func.sum(UsageRecord.storage_used).label("storage_used"),
                func.sum(UsageRecord.vector_usage).label("vector_usage"),
                func.sum(UsageRecord.automation_usage).label("automation_usage"),
                func.sum(UsageRecord.workflow_usage).label("workflow_usage"),
                func.sum(UsageRecord.bandwidth).label("bandwidth"),
                func.sum(UsageRecord.estimated_cost).label("estimated_cost"),
                func.avg(UsageRecord.response_latency_ms).label("avg_latency"),
            )
            .filter(UsageRecord.workspace_id == workspace_id)
            .first()
        )

        return {
            "tokens": int(totals.tokens or 0),
            "requests": int(totals.requests or 0),
            "storage_used_bytes": int(totals.storage_used or 0),
            "vector_operations": int(totals.vector_usage or 0),
            "automation_executions": int(totals.automation_usage or 0),
            "workflow_executions": int(totals.workflow_usage or 0),
            "bandwidth_bytes": int(totals.bandwidth or 0),
            "estimated_cost_cents": round((totals.estimated_cost or 0) / 10000.0, 4),
            "avg_latency_ms": round(float(totals.avg_latency or 0.0), 2),
        }


usage_service = UsageService()
