from typing import Any, Dict, List


class Chunker:
    """
    Splits plain text into contiguous chunks with a defined overlap.
    """

    @staticmethod
    def chunk_text(
        text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Segments the text block, returning indices, chunk contents, and token count estimates.
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be greater than zero.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "Chunk overlap must be non-negative and strictly smaller than chunk size."
            )

        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0

        if text_length == 0:
            return []

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_content = text[start:end]

            # Simple whitespace estimation (approx 1 token per word)
            token_count = len(chunk_content.split()) if chunk_content else 0

            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "text": chunk_content,
                    "token_count": token_count,
                }
            )

            chunk_index += 1
            if end == text_length:
                break

            # Shift starting index forward by difference (step size)
            start += chunk_size - chunk_overlap

        return chunks
