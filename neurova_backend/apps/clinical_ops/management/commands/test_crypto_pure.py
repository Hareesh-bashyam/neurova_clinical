import os
import sys
import django
from django.conf import settings

# Configure minimal settings for Django if needed by imports
if not settings.configured:
    settings.configure(DEBUG=True, SECRET_KEY='secret')
    django.setup()

try:
    from common.crypto_utils import encrypt_data, decrypt_data
    
    print("--- Testing Encryption ---")
    data = {"test": "value", "nested": {"a": 1}}
    
    try:
        encrypted = encrypt_data(data)
        print(f"Encryption Success: {encrypted[:20]}...")
    except Exception as e:
        print(f"Encryption FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("--- Testing Decryption ---")
    try:
        decrypted = decrypt_data(encrypted)
        print(f"Decryption Success: {decrypted}")
        assert decrypted == data
    except Exception as e:
        print(f"Decryption FAILED: {e}")
        sys.exit(1)

except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure pycryptodome is installed.")
except Exception as e:
    print(f"Unexpected Error: {e}")
