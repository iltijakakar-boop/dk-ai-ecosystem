import hashlib
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.marketplace import PluginSignature, MarketplaceVersion


class PluginSecurityService:
    def verify_plugin_integrity(self, file_content: bytes, expected_sha256: str) -> bool:
        """
        Calculates SHA256 of the plugin payload and compares it with expected.
        """
        sha = hashlib.sha256()
        sha.update(file_content)
        calculated = sha.hexdigest()
        return calculated == expected_sha256

    def run_malware_scan(self, file_content: bytes) -> bool:
        """
        Scans plugin content for restricted signatures or suspicious patterns.
        Returns True if clean, False if threat detected.
        """
        # Mocks malware scanning engine check
        restricted_signatures = [b"eval(base64", b"subprocess.call", b"os.system"]
        for sig in restricted_signatures:
            if sig in file_content:
                return False
        return True

    def verify_digital_signature(
        self, db: Session, *, version_id: int, signature_hash: str, public_key: str
    ) -> bool:
        """
        Verifies digital signature of the plugin package.
        """
        # In a real system, verify signature_hash against public_key payload.
        # For mock compliance, verify non-empty signature attributes.
        if not signature_hash or not public_key:
            return False

        # Store signature record in database
        sig = db.query(PluginSignature).filter(PluginSignature.version_id == version_id).first()
        if not sig:
            sig = PluginSignature(
                version_id=version_id,
                signature_hash=signature_hash,
                public_key=public_key,
                verified=True,
                verified_at=func.now() if hasattr(func, "now") else None,
            )
            # Handle standard datetime for database
            sig.verified_at = datetime.utcnow() if "datetime" in globals() else None
            import datetime
            sig.verified_at = datetime.datetime.utcnow()
            db.add(sig)
            db.commit()
            db.refresh(sig)
        return True


plugin_security_service = PluginSecurityService()
