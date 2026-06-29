import os
import pickle
import time
from datetime import datetime, timezone

from app.config.settings import settings
from app.core.logging.logger import logger
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.monitoring_model import ExecutionMetric
from app.models.vector_embedding import VectorEmbedding
from app.services.chunker import Chunker
from app.services.document_service import document_service
from app.services.embedding_service import embedding_service
from app.services.text_extractor import TextExtractor


class IndexingService:
    """
    Coordinates document text extraction, chunking, embedding lookup/cache-reuse,
    batch embedding generation, incremental reindexing, and performance monitoring.
    """

    def index_document_in_background(self, document_id: int) -> None:
        """
        Ingestion pipeline run in the background.
        """
        db = SessionLocal()
        start_time_total = time.perf_counter()

        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(
                f"Ingestion failed: Document ID {document_id} not found in DB."
            )
            db.close()
            return

        doc.processing_status = "processing"
        db.commit()

        try:
            # 1. Text Extraction
            file_path = os.path.join(document_service.storage_path, doc.filename)

            start_extract = time.perf_counter()
            text = TextExtractor.extract_text(file_path, doc.mime_type)
            duration_extract = (time.perf_counter() - start_extract) * 1000.0
            self._log_performance_metric(db, "indexing:extraction", duration_extract)

            # 2. Chunking
            start_chunk = time.perf_counter()
            raw_chunks = Chunker.chunk_text(
                text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            duration_chunk = (time.perf_counter() - start_chunk) * 1000.0
            self._log_performance_metric(db, "indexing:chunking", duration_chunk)

            # 3. Processing and Embedding Cache lookup
            start_embed = time.perf_counter()

            chunks_to_create = []
            texts_to_embed = []

            for index, rc in enumerate(raw_chunks):
                chunk_text = rc["text"]
                token_count = rc["token_count"]

                # Check Embedding Cache: see if this exact text exists in ANY chunk in
                # database
                cached_chunk = (
                    db.query(DocumentChunk)
                    .filter(DocumentChunk.text == chunk_text)
                    .first()
                )
                if cached_chunk and cached_chunk.embedding:
                    # Reuse cached vector
                    cached_vector = cached_chunk.embedding.embedding_data
                    dimension = cached_chunk.embedding.vector_dimension

                    new_chunk = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=index,
                        text=chunk_text,
                        token_count=token_count,
                    )
                    db.add(new_chunk)
                    db.flush()  # populated chunk_id

                    new_emb = VectorEmbedding(
                        chunk_id=new_chunk.id,
                        embedding_provider=settings.EMBEDDING_PROVIDER,
                        embedding_model=settings.EMBEDDING_MODEL,
                        vector_dimension=dimension,
                        embedding_data=cached_vector,
                    )
                    db.add(new_emb)
                    logger.info(
                        f"Embedding Cache Hit: Reusing cached vector for chunk {index}."
                    )
                else:
                    # Needs new embedding
                    new_chunk = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=index,
                        text=chunk_text,
                        token_count=token_count,
                    )
                    db.add(new_chunk)
                    db.flush()

                    chunks_to_create.append(new_chunk)
                    texts_to_embed.append(chunk_text)

            # Generate missing embeddings in batches with retries
            if texts_to_embed:
                logger.info(
                    f"Generating embeddings for {len(texts_to_embed)} new chunks in batches..."
                )
                generated_vectors = embedding_service.get_embeddings_with_retry(
                    texts_to_embed
                )

                for idx, chunk_obj in enumerate(chunks_to_create):
                    vector = generated_vectors[idx]
                    serialized_vector = pickle.dumps(vector)

                    emb_obj = VectorEmbedding(
                        chunk_id=chunk_obj.id,
                        embedding_provider=settings.EMBEDDING_PROVIDER,
                        embedding_model=settings.EMBEDDING_MODEL,
                        vector_dimension=len(vector),
                        embedding_data=serialized_vector,
                    )
                    db.add(emb_obj)

            duration_embed = (time.perf_counter() - start_embed) * 1000.0
            self._log_performance_metric(db, "indexing:embedding", duration_embed)

            # Save state
            doc.chunk_count = len(raw_chunks)
            doc.processing_status = "indexed"
            db.commit()

            duration_total = (time.perf_counter() - start_time_total) * 1000.0
            self._log_performance_metric(db, "indexing:total", duration_total)
            logger.info(
                f"Indexing completed successfully for Document: {doc.original_filename} (ID: {doc.id})"
            )

        except Exception:
            db.rollback()
            logger.exception(
                f"Ingestion pipeline failed for Document ID {document_id}:"
            )
            doc.processing_status = "failed"
            db.commit()
        finally:
            db.close()

    def reindex_document(self, document_id: int) -> None:
        """
        Executes incremental reindexing: keeps unchanged chunks and their vectors,
        generates vectors for modified chunks, and removes old obsolete chunks.
        """
        db = SessionLocal()
        start_time = time.perf_counter()

        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Reindexing failed: Document ID {document_id} not found.")
            db.close()
            return

        doc.processing_status = "processing"
        db.commit()

        try:
            file_path = os.path.join(document_service.storage_path, doc.filename)
            text = TextExtractor.extract_text(file_path, doc.mime_type)

            # Generate new chunks
            new_chunks_data = Chunker.chunk_text(
                text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            # Load old chunks for this document
            old_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == doc.id)
                .all()
            )
            old_chunks_by_text = {c.text: c for c in old_chunks}

            new_chunks_to_save = []
            obsolete_chunk_ids = set(c.id for c in old_chunks)

            for idx, nc in enumerate(new_chunks_data):
                chunk_text = nc["text"]
                token_count = nc["token_count"]

                if chunk_text in old_chunks_by_text:
                    # Incremental match: Keep old chunk, update its index
                    existing_chunk = old_chunks_by_text[chunk_text]
                    existing_chunk.chunk_index = idx
                    # Do not delete this chunk
                    obsolete_chunk_ids.discard(existing_chunk.id)
                    logger.info(
                        f"Incremental match: Keeping unchanged chunk at new index {idx}."
                    )
                else:
                    # Generate or fetch embedding
                    new_chunks_to_save.append((idx, chunk_text, token_count))

            # Delete obsolete chunks
            if obsolete_chunk_ids:
                for obsolete_id in obsolete_chunk_ids:
                    chunk_obj = (
                        db.query(DocumentChunk)
                        .filter(DocumentChunk.id == obsolete_id)
                        .first()
                    )
                    if chunk_obj:
                        db.query(VectorEmbedding).filter(
                            VectorEmbedding.chunk_id == chunk_obj.id
                        ).delete()
                        db.delete(chunk_obj)
                logger.info(
                    f"Incremental purge: Deleted {len(obsolete_chunk_ids)} obsolete chunks."
                )

            # Process new chunks
            texts_to_embed = [item[1] for item in new_chunks_to_save]
            if texts_to_embed:
                # 1. Lookup cache
                final_texts_to_embed = []
                temp_saved_chunks = []

                for idx, chunk_text, token_count in new_chunks_to_save:
                    cached_chunk = (
                        db.query(DocumentChunk)
                        .filter(DocumentChunk.text == chunk_text)
                        .first()
                    )
                    if cached_chunk and cached_chunk.embedding:
                        cached_vector = cached_chunk.embedding.embedding_data
                        dimension = cached_chunk.embedding.vector_dimension

                        nc_obj = DocumentChunk(
                            document_id=doc.id,
                            chunk_index=idx,
                            text=chunk_text,
                            token_count=token_count,
                        )
                        db.add(nc_obj)
                        db.flush()

                        new_emb = VectorEmbedding(
                            chunk_id=nc_obj.id,
                            embedding_provider=settings.EMBEDDING_PROVIDER,
                            embedding_model=settings.EMBEDDING_MODEL,
                            vector_dimension=dimension,
                            embedding_data=cached_vector,
                        )
                        db.add(new_emb)
                    else:
                        nc_obj = DocumentChunk(
                            document_id=doc.id,
                            chunk_index=idx,
                            text=chunk_text,
                            token_count=token_count,
                        )
                        db.add(nc_obj)
                        db.flush()

                        final_texts_to_embed.append(chunk_text)
                        temp_saved_chunks.append(nc_obj)

                # 2. Embed remainder
                if final_texts_to_embed:
                    logger.info(
                        f"Incremental Embed: generating vectors for {len(final_texts_to_embed)} new blocks."
                    )
                    vectors = embedding_service.get_embeddings_with_retry(
                        final_texts_to_embed
                    )
                    for i, chunk_obj in enumerate(temp_saved_chunks):
                        vector = vectors[i]
                        serialized = pickle.dumps(vector)
                        emb = VectorEmbedding(
                            chunk_id=chunk_obj.id,
                            embedding_provider=settings.EMBEDDING_PROVIDER,
                            embedding_model=settings.EMBEDDING_MODEL,
                            vector_dimension=len(vector),
                            embedding_data=serialized,
                        )
                        db.add(emb)

            # Update Document stats
            doc.chunk_count = len(new_chunks_data)
            doc.processing_status = "indexed"
            db.commit()

            duration = (time.perf_counter() - start_time) * 1000.0
            self._log_performance_metric(db, "indexing:reindex", duration)
            logger.info(f"Reindexing completed for document {doc.original_filename}.")

        except Exception:
            db.rollback()
            logger.exception(
                f"Incremental reindexing failed for Document ID {document_id}:"
            )
            doc.processing_status = "failed"
            db.commit()
        finally:
            db.close()

    def _log_performance_metric(self, db, component: str, duration_ms: float) -> None:
        """
        Saves indexing durations into the Sprint 007.5 monitoring table.
        """
        try:
            metric = ExecutionMetric(
                component=component,
                execution_time=duration_ms,
                success=True,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(metric)
            db.commit()
        except Exception as err:
            logger.warning(f"Failed to record indexing performance metric: {err}")


# Global IndexingService instance
indexing_service = IndexingService()
