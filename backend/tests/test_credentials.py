from sqlalchemy.orm import Session
from app.services.credential_service import credential_service


def test_credential_encryption_and_decryption(db: Session):
    cred_dict = {"api_key": "gemini_mock_api_key_123", "client_email": "gemini@example.com"}

    # 1. Encrypt credentials
    encrypted = credential_service.encrypt_credentials(cred_dict)
    assert isinstance(encrypted, str)
    assert encrypted != "gemini_mock_api_key_123"

    # 2. Decrypt credentials
    decrypted = credential_service.decrypt_credentials(encrypted)
    assert decrypted["api_key"] == "gemini_mock_api_key_123"
    assert decrypted["client_email"] == "gemini@example.com"

    # 3. Save credential to db and get it
    credential_service.save_credential(db, workspace_id=1, connector_id=5, credential_data=cred_dict)
    loaded = credential_service.get_credential(db, workspace_id=1, connector_id=5)
    assert loaded is not None
    assert loaded["api_key"] == "gemini_mock_api_key_123"
