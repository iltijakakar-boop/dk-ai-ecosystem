from typing import List, Dict, Any
from app.config.settings import settings
from app.core.logging.logger import logger

class ContextBuilder:
    """
    Combines parsed document chunk snippets, filters duplicate entries,
    and formats them within configured token and count thresholds.
    """
    
    def build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Assembles a single formatted context block string from a list of retrieved chunks,
        ensuring size limit constraints are not exceeded.
        """
        if not chunks:
            return ""

        seen_ids = set()
        unique_chunks = []
        
        # Deduplication
        for chunk in chunks:
            cid = chunk.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                unique_chunks.append(chunk)

        # Enforce count threshold
        max_chunks = settings.MAX_CONTEXT_CHUNKS
        limited_chunks = unique_chunks[:max_chunks]

        # Enforce character/token threshold (approx 1 token = 4 characters)
        max_tokens = settings.MAX_CONTEXT_TOKENS
        max_chars = max_tokens * 4
        
        current_chars = 0
        context_parts = []

        for item in limited_chunks:
            filename = item.get("filename", "unknown")
            text = item.get("text", "")
            
            block = f"[Document: {filename}]\n{text}\n\n"
            block_len = len(block)
            
            if current_chars + block_len > max_chars:
                # Add what we can or stop
                space_left = max_chars - current_chars
                if space_left > 100:
                    truncated_block = block[:space_left] + "... [TRUNCATED]\n\n"
                    context_parts.append(truncated_block)
                logger.info("Context size threshold reached. Stopped appending chunks.")
                break
                
            context_parts.append(block)
            current_chars += block_len

        return "".join(context_parts).strip()

# Global ContextBuilder instance
context_builder = ContextBuilder()
