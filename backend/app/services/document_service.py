import hashlib
import os
import uuid
from typing import Optional, Tuple

from app.config.settings import settings
from app.core.logging.logger import logger


class DocumentService:
    """
    Coordinates file storage operations, extension validation, size checks, and SHA-256 integrity hashing.
    """

    def __init__(self):
        # Resolve target storage path relative to workspace root (data/documents)
        self.storage_path = os.path.abspath(settings.DOCUMENT_STORAGE_PATH)
        os.makedirs(self.storage_path, exist_ok=True)

    def calculate_sha256(self, file_content: bytes) -> str:
        """
        Computes SHA-256 checksum of raw binary content for duplicate check.
        """
        return hashlib.sha256(file_content).hexdigest()

    def validate_file(
        self, filename: str, file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates file size limits and extensions.
        """
        # 1. Size Validation
        max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return (
                False,
                f"File exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE_MB}MB.",
            )

        # 2. Extension Validation
        ext = os.path.splitext(filename)[1].lower().strip(".")
        if ext not in settings.ALLOWED_DOCUMENT_TYPES:
            return (
                False,
                f"Unsupported file type '{ext}'. Allowed types: {settings.ALLOWED_DOCUMENT_TYPES}.",
            )

        return True, None

    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Saves file content to disk under a unique UUID name while maintaining extension type.
        Returns the saved unique filename.
        """
        ext = os.path.splitext(original_filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        target_path = os.path.join(self.storage_path, unique_name)

        # Verify no path traversals
        if not os.path.abspath(target_path).startswith(self.storage_path):
            raise PermissionError("Access denied: path points outside storage bounds.")

        logger.info(f"Saving uploaded file: {original_filename} -> {unique_name}")
        with open(target_path, "wb") as f:
            f.write(file_content)

        return unique_name

    def delete_file(self, filename: str) -> bool:
        """
        Removes file from disk storage.
        """
        target_path = os.path.join(self.storage_path, filename)
        if not os.path.abspath(target_path).startswith(self.storage_path):
            logger.warning(
                f"Path traversal attempt prevented during file deletion: {filename}"
            )
            return False

        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                logger.info(f"Deleted file from storage: {filename}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete file {filename}: {e}")
                return False
        logger.warning(f"File to delete not found on disk: {filename}")
        return False


# Global DocumentService instance
document_service = DocumentService()
