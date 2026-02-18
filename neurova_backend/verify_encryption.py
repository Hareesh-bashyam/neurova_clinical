"""
Quick Encryption Verification Script

Run this script to verify that the encryption utilities are working correctly.
This is a simple smoke test before running the full test suite.

Usage:
    python verify_encryption.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.crypto_utils import encrypt_data, decrypt_data


def test_basic_encryption():
    """Test basic encryption and decryption"""
    print("Testing basic encryption...")
    
    original_data = {
        "patient_name": "John Doe",
        "age": 35,
        "test_id": 12345
    }
    
    print(f"Original data: {original_data}")
    
    # Encrypt
    encrypted = encrypt_data(original_data)
    print(f"Encrypted (first 50 chars): {encrypted[:50]}...")
    
    # Decrypt
    decrypted = decrypt_data(encrypted)
    print(f"Decrypted data: {decrypted}")
    
    # Verify
    if decrypted == original_data:
        print("✅ Basic encryption test PASSED")
        return True
    else:
        print("❌ Basic encryption test FAILED")
        return False


def test_iv_randomness():
    """Test that IV is random"""
    print("\nTesting IV randomness...")
    
    data = {"test": "value"}
    
    encrypted1 = encrypt_data(data)
    encrypted2 = encrypt_data(data)
    
    if encrypted1 != encrypted2:
        print("✅ IV randomness test PASSED (different ciphertexts)")
        return True
    else:
        print("❌ IV randomness test FAILED (same ciphertext)")
        return False


def test_real_world_payload():
    """Test with real API payload"""
    print("\nTesting real-world API payload...")
    
    patient_payload = {
        "org_id": "550e8400-e29b-41d4-a716-446655440000",
        "full_name": "Jane Smith",
        "age": 42,
        "sex": "FEMALE",
        "phone": "9876543210",
        "email": "jane.smith@example.com"
    }
    
    print(f"Patient payload: {patient_payload}")
    
    encrypted = encrypt_data(patient_payload)
    decrypted = decrypt_data(encrypted)
    
    if decrypted == patient_payload:
        print("✅ Real-world payload test PASSED")
        return True
    else:
        print("❌ Real-world payload test FAILED")
        return False


def test_error_handling():
    """Test error handling for invalid data"""
    print("\nTesting error handling...")
    
    try:
        decrypt_data("invalid-encrypted-data")
        print("❌ Error handling test FAILED (should have raised exception)")
        return False
    except Exception as e:
        print(f"✅ Error handling test PASSED (caught exception: {type(e).__name__})")
        return True


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("ENCRYPTION VERIFICATION SCRIPT")
    print("=" * 60)
    
    results = []
    
    results.append(test_basic_encryption())
    results.append(test_iv_randomness())
    results.append(test_real_world_payload())
    results.append(test_error_handling())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Encryption is working correctly!")
        print("\nNext steps:")
        print("1. Install pycryptodome: pip install pycryptodome")
        print("2. Run full test suite: pytest tests/unit/test_encryption.py -v")
        print("3. Update integration tests to use encryption")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Please check the errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
