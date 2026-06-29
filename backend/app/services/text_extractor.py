import os
from app.core.logging.logger import logger

class TextExtractor:
    """
    Service responsible for extracting plain text from PDF, DOCX, TXT, and MD files.
    """
    @staticmethod
    def extract_text(file_path: str, mime_type: str) -> str:
        """
        Extracts plain text contents of a document from file_path depending on file type/MIME.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No file found at: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Extracting text from: {file_path} ({mime_type})")

        # 1. Standard text files (TXT / Markdown)
        if ext in [".txt", ".md"] or mime_type in ["text/plain", "text/markdown"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        # 2. PDF Files (via pypdf)
        elif ext == ".pdf" or mime_type == "application/pdf":
            try:
                import pypdf
            except ImportError:
                logger.error("pypdf library not found.")
                raise ImportError("pypdf package is required to parse PDF documents.")
            
            text_blocks = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_blocks.append(page_text)
            return "\n\n".join(text_blocks)

        # 3. DOCX Microsoft Word Files (via python-docx)
        elif ext == ".docx" or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                import docx
            except ImportError:
                logger.error("python-docx library not found.")
                raise ImportError("python-docx package is required to parse DOCX documents.")
            
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)

        # Fallback raw reading
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Unsupported file format and text extraction failed: {ext} (MIME: {mime_type})")
