from sqlalchemy.orm import Session
from app.services.pipeline_service import pipeline_service


def test_visual_pipeline_lifecycle(db: Session):
    # 1. Create pipeline definition
    pipeline = pipeline_service.create_pipeline(
        db,
        workspace_id=1,
        name="Vector indexing flow",
        description="Extracts data and uploads to SQLite Vector index",
        type="RAG",
        definition={"source": "file_reader", "destination": "vector_store"},
    )
    assert pipeline.name == "Vector indexing flow"
    assert pipeline.type == "RAG"

    # 2. Update pipeline (creates version 2 snapshot)
    updated = pipeline_service.update_pipeline(
        db,
        pipeline_id=pipeline.id,
        definition={"source": "file_reader", "chunker": "token_chunker", "destination": "vector_store"},
    )
    assert "token_chunker" in updated.definition
