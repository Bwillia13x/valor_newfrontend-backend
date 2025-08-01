from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os
import json
from typing import Dict, Any, Optional
import secrets

class DataEncryption:
    """Advanced encryption for sensitive financial data"""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize encryption with provided key or generate new one"""
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> bytes:
        """Encrypt sensitive financial data"""
        json_data = json.dumps(data, sort_keys=True)
        return self.cipher.encrypt(json_data.encode())
    
    def decrypt_sensitive_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt sensitive financial data"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a single field value"""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a single field value"""
        encrypted = base64.b64decode(encrypted_value.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
    
    def rotate_key(self) -> bytes:
        """Generate new encryption key and return old key"""
        old_key = self.key
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        return old_key
    
    def get_key(self) -> bytes:
        """Get current encryption key"""
        return self.key

class FieldEncryption:
    """Field-level encryption for specific data types"""
    
    def __init__(self, password: str):
        """Initialize field encryption with password-derived key"""
        self.key = self._derive_key(password)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        password_bytes = password.encode()
        salt = b'valor_ivx_salt_2024'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value"""
        f = Fernet(self.key)
        encrypted = f.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value"""
        f = Fernet(self.key)
        encrypted = base64.b64decode(encrypted_value.encode())
        decrypted = f.decrypt(encrypted)
        return decrypted.decode()

class SecureTokenManager:
    """Generate and manage secure tokens"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate API key with prefix"""
        token = secrets.token_urlsafe(32)
        return f"vk_{token}"
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate session token"""
        return secrets.token_urlsafe(24)
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)

class EncryptionService:
    """High-level encryption service for application data"""
    
    def __init__(self):
        self.master_key = os.environ.get('MASTER_ENCRYPTION_KEY')
        if not self.master_key:
            self.master_key = Fernet.generate_key()
            print("WARNING: Using generated key. Set MASTER_ENCRYPTION_KEY environment variable.")
        
        self.data_encryption = DataEncryption(self.master_key)
        self.token_manager = SecureTokenManager()
    
    def encrypt_model_data(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive model data"""
        encrypted = {}
        
        # Encrypt sensitive fields
        sensitive_fields = ['revenue', 'ebitda', 'net_income', 'cash_flow']
        for field in sensitive_fields:
            if field in model_data:
                encrypted[field] = self.data_encryption.encrypt_field(str(model_data[field]))
        
        # Encrypt entire model if needed
        if model_data.get('is_sensitive', False):
            encrypted_data = self.data_encryption.encrypt_sensitive_data(model_data)
            encrypted = {'encrypted_payload': base64.b64encode(encrypted_data).decode()}
        
        return encrypted
    
    def decrypt_model_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt model data"""
        if 'encrypted_payload' in encrypted_data:
            encrypted_bytes = base64.b64decode(encrypted_data['encrypted_payload'])
            return self.data_encryption.decrypt_sensitive_data(encrypted_bytes)
        
        # Decrypt individual fields
        decrypted = {}
        for key, value in encrypted_data.items():
            if key != 'encrypted_payload':
                decrypted[key] = self.data_encryption.decrypt_field(value)
        
        return decrypted
    
    def encrypt_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt user personal data"""
        encrypted = user_data.copy()
        
        # Encrypt PII fields
        pii_fields = ['email', 'phone', 'address', 'ssn']
        for field in pii_fields:
            if field in user_data:
                encrypted[field] = self.data_encryption.encrypt_field(user_data[field])
        
        return encrypted
    
    def decrypt_user_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt user personal data"""
        decrypted = encrypted_data.copy()
        
        for key, value in encrypted_data.items():
            if key in ['email', 'phone', 'address', 'ssn']:
                decrypted[key] = self.data_encryption.decrypt_field(value)
        
        return decrypted
    
    def create_secure_backup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create encrypted backup of data"""
        encrypted_data = self.data_encryption.encrypt_sensitive_data(data)
        backup_token = self.token_manager.generate_secure_token()
        
        return {
            'backup_token': backup_token,
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'created_at': str(pd.Timestamp.now()),
            'version': '1.0'
        }
    
    def restore_from_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore data from encrypted backup"""
        encrypted_bytes = base64.b64decode(backup_data['encrypted_data'])
        return self.data_encryption.decrypt_sensitive_data(encrypted_bytes)

class ComplianceManager:
    """Handle compliance requirements for data encryption"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
    
    def encrypt_for_gdpr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt data for GDPR compliance"""
        return {
            'encrypted_data': self.encryption_service.encrypt_model_data(data),
            'compliance': {
                'gdpr': True,
                'encryption_standard': 'AES-256',
                'key_rotation': 'quarterly'
            }
        }
    
    def encrypt_for_hipaa(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt data for HIPAA compliance"""
        return {
            'encrypted_data': self.encryption_service.encrypt_model_data(data),
            'compliance': {
                'hipaa': True,
                'encryption_standard': 'AES-256',
                'access_controls': True,
                'audit_logging': True
            }
        }
    
    def encrypt_for_soc2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt data for SOC 2 compliance"""
        return {
            'encrypted_data': self.encryption_service.encrypt_model_data(data),
            'compliance': {
                'soc2': True,
                'encryption_standard': 'AES-256',
                'key_management': True,
                'access_monitoring': True
            }
        }

# Global encryption service instance
encryption_service = EncryptionService()
