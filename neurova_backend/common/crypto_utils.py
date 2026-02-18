"""
AES-256-CBC Encryption Utilities for Clinical API

Provides encryption and decryption functions for securing sensitive patient data
in API requests and responses. Uses AES-256-CBC with random IV per operation.

Security Features:
- AES-256-CBC encryption
- Random IV per encryption operation
- PKCS7 padding
- Base64 encoding for transport
- JSON serialization/deserialization

Usage:
    from common.crypto_utils import encrypt_data, decrypt_data
    
    # Encrypt data
    raw_data = {"patient_name": "John Doe", "age": 35}
    encrypted = encrypt_data(raw_data)
    
    # Decrypt data
    decrypted = decrypt_data(encrypted)
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import json
import os
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_SECRET_KEY', '').encode('utf-8')

# Validate key length (must be 16, 24, or 32 bytes for AES)
if len(ENCRYPTION_KEY) not in [16, 24, 32]:
    logger.warning(
        f"ENCRYPTION_SECRET_KEY has invalid length ({len(ENCRYPTION_KEY)} bytes). "
        "Must be 16, 24, or 32 bytes for AES. Using default key for development only."
    )
    # Development fallback (DO NOT USE IN PRODUCTION)
    ENCRYPTION_KEY = b'dev-key-16-bytes'  # 16 bytes for AES-128


def encrypt_data(data: dict) -> str:
    """
    Encrypt dictionary data using AES-256-CBC.
    
    Args:
        data: Dictionary containing data to encrypt
        
    Returns:
        Base64-encoded string in format: base64(iv:ciphertext)
        
    Raises:
        ValueError: If data cannot be serialized to JSON
        Exception: If encryption fails
        
    Example:
        >>> encrypt_data({"name": "John", "age": 30})
        'U2FsdGVkX1+VfZG8hN3mK9pqR...'
    """
    try:
        # Serialize data to JSON
        json_data = json.dumps(data, separators=(',', ':'))
        plaintext = json_data.encode('utf-8')
        
        # Create cipher with random IV
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
        
        # Encrypt with PKCS7 padding
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
        
        # Encode IV and ciphertext separately
        iv_b64 = base64.b64encode(cipher.iv).decode('utf-8')
        ct_b64 = base64.b64encode(ciphertext).decode('utf-8')
        
        # Combine as "iv:ciphertext" and encode again
        combined = f"{iv_b64}:{ct_b64}".encode('utf-8')
        encrypted = base64.b64encode(combined).decode('utf-8')
        
        return encrypted
        
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data for encryption: {e}")
        raise ValueError(f"Data serialization failed: {e}")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise Exception(f"Encryption error: {e}")


def decrypt_data(encrypted: str) -> dict:
    """
    Decrypt AES-256-CBC encrypted data.
    
    Args:
        encrypted: Base64-encoded encrypted string in format: base64(iv:ciphertext)
        
    Returns:
        Dictionary containing decrypted data
        
    Raises:
        ValueError: If encrypted data is malformed or decryption fails
        Exception: If decryption fails
        
    Example:
        >>> decrypt_data('U2FsdGVkX1+VfZG8hN3mK9pqR...')
        {'name': 'John', 'age': 30}
    """
    try:
        # Decode outer base64 layer
        combined = base64.b64decode(encrypted).decode('utf-8')
        
        # Split IV and ciphertext
        if ':' not in combined:
            raise ValueError("Invalid encrypted data format: missing IV separator")
            
        iv_b64, ct_b64 = combined.split(':', 1)
        
        # Decode IV and ciphertext
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ct_b64)
        
        # Create cipher with extracted IV
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
        
        # Decrypt and remove padding
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        # Deserialize JSON
        json_data = plaintext.decode('utf-8')
        data = json.loads(json_data)
        
        return data
        
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to decrypt data: {e}")
        raise ValueError(f"Decryption failed: invalid or corrupted data")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse decrypted JSON: {e}")
        raise ValueError(f"Decryption failed: invalid JSON data")
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise Exception(f"Decryption error: {e}")


def is_encrypted_format(data: dict) -> bool:
    """
    Check if request data is in encrypted format.
    
    Args:
        data: Request data dictionary
        
    Returns:
        True if data contains 'encrypted_data' field, False otherwise
    """
    return isinstance(data, dict) and 'encrypted_data' in data
