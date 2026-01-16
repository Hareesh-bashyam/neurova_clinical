"""
Encryption-at-rest policy:
- Database volumes encrypted via cloud provider (AWS RDS / GCP SQL)
- Object storage encrypted (S3 SSE / GCS CMEK)
- Application-level encryption hooks reserved here
"""

def encryption_policy():
    return {
        "db_encryption": "Cloud-managed AES-256",
        "object_storage": "SSE / CMEK",
        "key_rotation": "Cloud KMS",
        "application_level": "Reserved for PHI fields if mandated"
    }
