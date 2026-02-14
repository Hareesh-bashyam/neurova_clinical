import hashlib
import secrets
from django.db import models
from django.utils import timezone


class PublicAccessToken(models.Model):

    order = models.ForeignKey(
        "clinical_ops.AssessmentOrder",
        on_delete=models.CASCADE,
        related_name="secure_tokens"
    )
    token_hash = models.CharField(max_length=64, unique=True)

    expires_at = models.DateTimeField()

    # Security Controls
    is_used = models.BooleanField(default=False)
    failed_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    # Binding
    bound_ip = models.GenericIPAddressField(null=True, blank=True)
    bound_user_agent = models.TextField(blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------
    # Utilities
    # ---------------------

    @staticmethod
    def generate_raw_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(raw_token: str):
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def is_expired(self):
        return timezone.now() > self.expires_at
