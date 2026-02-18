"""
Unit Tests for Encryption Utilities

Tests the AES-256-CBC encryption and decryption functions to ensure:
- Correct encryption/decryption round-trips
- IV randomness (different ciphertexts for same plaintext)
- Error handling for invalid/corrupted data
- Edge cases (empty data, large payloads, special characters)
- Security properties (key validation, padding)
"""

import pytest
import os
import json
from unittest.mock import patch

from common.crypto_utils import encrypt_data, decrypt_data, is_encrypted_format


class TestEncryptionRoundTrip:
    """Test basic encryption and decryption functionality"""
    
    def test_simple_dict_encryption(self):
        """Test encryption and decryption of simple dictionary"""
        original_data = {"name": "John Doe", "age": 35}
        
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original_data
    
    def test_complex_nested_dict(self):
        """Test encryption of nested dictionary structures"""
        original_data = {
            "patient": {
                "name": "Jane Smith",
                "age": 42,
                "contact": {
                    "email": "jane@example.com",
                    "phone": "1234567890"
                }
            },
            "orders": [1, 2, 3],
            "metadata": {
                "created_at": "2026-02-16",
                "status": "active"
            }
        }
        
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original_data
    
    def test_empty_dict(self):
        """Test encryption of empty dictionary"""
        original_data = {}
        
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original_data
    
    def test_unicode_and_special_characters(self):
        """Test encryption with unicode and special characters"""
        original_data = {
            "name": "José García",
            "description": "Test with émojis 🔒🔐 and symbols: @#$%^&*()",
            "unicode": "中文字符",
            "newlines": "Line 1\nLine 2\nLine 3"
        }
        
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original_data


class TestIVRandomness:
    """Test that IV is random and different for each encryption"""
    
    def test_same_data_different_ciphertext(self):
        """Encrypting same data twice should produce different ciphertexts"""
        data = {"test": "value"}
        
        encrypted1 = encrypt_data(data)
        encrypted2 = encrypt_data(data)
        
        # Ciphertexts should be different due to random IV
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same data
        assert decrypt_data(encrypted1) == data
        assert decrypt_data(encrypted2) == data
    
    def test_iv_uniqueness_multiple_encryptions(self):
        """Test IV uniqueness across multiple encryptions"""
        data = {"patient_id": 123}
        ciphertexts = set()
        
        # Encrypt same data 100 times
        for _ in range(100):
            encrypted = encrypt_data(data)
            ciphertexts.add(encrypted)
        
        # All ciphertexts should be unique
        assert len(ciphertexts) == 100


class TestErrorHandling:
    """Test error handling for invalid inputs"""
    
    def test_decrypt_invalid_base64(self):
        """Test decryption with invalid base64 string"""
        with pytest.raises(Exception):
            decrypt_data("not-valid-base64!!!")
    
    def test_decrypt_malformed_data(self):
        """Test decryption with malformed encrypted data"""
        import base64
        malformed = base64.b64encode(b"malformed:data").decode()
        
        with pytest.raises(Exception):
            decrypt_data(malformed)
    
    def test_decrypt_missing_iv_separator(self):
        """Test decryption with missing IV separator"""
        import base64
        # Create base64 without ':' separator
        malformed = base64.b64encode(b"noSeparatorHere").decode()
        
        with pytest.raises(ValueError, match="missing IV separator"):
            decrypt_data(malformed)
    
    def test_decrypt_corrupted_ciphertext(self):
        """Test decryption with corrupted ciphertext"""
        # Encrypt valid data
        original = {"test": "data"}
        encrypted = encrypt_data(original)
        
        # Corrupt the ciphertext by modifying a character
        corrupted = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(Exception):
            decrypt_data(corrupted)
    
    def test_encrypt_non_serializable_data(self):
        """Test encryption with non-JSON-serializable data"""
        # Functions are not JSON serializable
        non_serializable = {"func": lambda x: x}
        
        with pytest.raises(ValueError, match="serialization failed"):
            encrypt_data(non_serializable)


class TestDataTypes:
    """Test encryption with various data types"""
    
    def test_list_values(self):
        """Test encryption with list values"""
        data = {
            "answers": [1, 2, 3, 4, 5],
            "names": ["Alice", "Bob", "Charlie"]
        }
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data
    
    def test_boolean_values(self):
        """Test encryption with boolean values"""
        data = {
            "is_active": True,
            "is_deleted": False,
            "has_consent": True
        }
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data
    
    def test_null_values(self):
        """Test encryption with null values"""
        data = {
            "optional_field": None,
            "required_field": "value"
        }
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data
    
    def test_numeric_values(self):
        """Test encryption with various numeric types"""
        data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -100,
            "zero": 0
        }
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data


class TestLargePayloads:
    """Test encryption with large data payloads"""
    
    def test_large_string(self):
        """Test encryption with large string value"""
        large_text = "A" * 10000  # 10KB string
        data = {"large_field": large_text}
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data
    
    def test_large_list(self):
        """Test encryption with large list"""
        large_list = list(range(1000))
        data = {"numbers": large_list}
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == data
    
    def test_deeply_nested_structure(self):
        """Test encryption with deeply nested structure"""
        # Create nested structure
        nested = {"level": 0}
        current = nested
        for i in range(1, 20):
            current["nested"] = {"level": i}
            current = current["nested"]
        
        encrypted = encrypt_data(nested)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == nested


class TestIsEncryptedFormat:
    """Test the is_encrypted_format helper function"""
    
    def test_encrypted_format_detected(self):
        """Test detection of encrypted format"""
        data = {"encrypted_data": "some_encrypted_string"}
        assert is_encrypted_format(data) is True
    
    def test_non_encrypted_format(self):
        """Test detection of non-encrypted format"""
        data = {"data": "some_data"}
        assert is_encrypted_format(data) is False
    
    def test_empty_dict(self):
        """Test empty dictionary"""
        assert is_encrypted_format({}) is False
    
    def test_non_dict_input(self):
        """Test non-dictionary input"""
        assert is_encrypted_format("string") is False
        assert is_encrypted_format(None) is False
        assert is_encrypted_format([]) is False


class TestSecurityProperties:
    """Test security-related properties"""
    
    def test_encrypted_output_is_base64(self):
        """Test that encrypted output is valid base64"""
        import base64
        data = {"test": "value"}
        
        encrypted = encrypt_data(data)
        
        # Should not raise exception
        try:
            base64.b64decode(encrypted)
        except Exception:
            pytest.fail("Encrypted output is not valid base64")
    
    def test_encrypted_output_length(self):
        """Test that encrypted output has reasonable length"""
        data = {"test": "value"}
        
        encrypted = encrypt_data(data)
        
        # Encrypted output should be longer than original due to IV and padding
        original_json = json.dumps(data)
        assert len(encrypted) > len(original_json)
    
    def test_different_keys_produce_different_results(self):
        """Test that different encryption keys produce different results"""
        data = {"test": "value"}
        
        # Encrypt with current key
        encrypted1 = encrypt_data(data)
        
        # Temporarily change the key
        from common import crypto_utils
        original_key = crypto_utils.ENCRYPTION_KEY
        crypto_utils.ENCRYPTION_KEY = b'different-key-32-bytes-long!'
        
        try:
            encrypted2 = encrypt_data(data)
            
            # Encrypted values should be different
            assert encrypted1 != encrypted2
            
            # Decryption with wrong key should fail
            with pytest.raises(Exception):
                decrypt_data(encrypted1)
        finally:
            # Restore original key
            crypto_utils.ENCRYPTION_KEY = original_key


class TestRealWorldScenarios:
    """Test real-world API payload scenarios"""
    
    def test_patient_creation_payload(self):
        """Test encryption of patient creation payload"""
        payload = {
            "org_id": "550e8400-e29b-41d4-a716-446655440000",
            "full_name": "John Doe",
            "age": 35,
            "sex": "MALE",
            "phone": "1234567890",
            "email": "john.doe@example.com"
        }
        
        encrypted = encrypt_data(payload)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == payload
    
    def test_order_creation_payload(self):
        """Test encryption of order creation payload"""
        payload = {
            "org_id": "550e8400-e29b-41d4-a716-446655440000",
            "patient_id": 123,
            "battery_code": "PHQ9_GAD7",
            "battery_version": "1.0",
            "encounter_type": "OPD",
            "referring_unit": "Psychiatry",
            "administration_mode": "KIOSK",
            "verified_by_staff": True
        }
        
        encrypted = encrypt_data(payload)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == payload
    
    def test_assessment_submission_payload(self):
        """Test encryption of assessment submission payload"""
        payload = {
            "answers": [
                {"question_id": "Q1", "answer": 2},
                {"question_id": "Q2", "answer": 3},
                {"question_id": "Q3", "answer": 1}
            ],
            "duration_seconds": 180
        }
        
        encrypted = encrypt_data(payload)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == payload
    
    def test_consent_submission_payload(self):
        """Test encryption of consent submission payload"""
        payload = {
            "consent_version": "V1",
            "consent_language": "en",
            "consent_given_by": "SELF",
            "guardian_name": None,
            "allow_patient_copy": True
        }
        
        encrypted = encrypt_data(payload)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == payload
