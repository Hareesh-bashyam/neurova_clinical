from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from apps.clinical_ops.models_public_token import PublicAccessToken
from apps.clinical_ops.audit.logger import log_event

MAX_FAILED_ATTEMPTS = 5
TOKEN_EXPIRY_MINUTES = 60 * 24  # Ultra short expiry


def validate_and_rotate_url_token(raw_token, request):

    token_hash = PublicAccessToken.hash_token(raw_token)

    try:
        token_obj = PublicAccessToken.objects.select_related("order").get(
            token_hash=token_hash
        )
    except PublicAccessToken.DoesNotExist:
        raise PermissionDenied("Invalid token")

    # Locked?
    if token_obj.is_locked:
        raise PermissionDenied("Token locked")

    # Expired?
    if token_obj.is_expired():
        raise PermissionDenied("Token expired")

    # Already used?
    if token_obj.is_used:
        raise PermissionDenied("Token already used")

    current_ip = request.META.get("REMOTE_ADDR")
    current_ua = request.META.get("HTTP_USER_AGENT")

    # IP Binding Check
    if token_obj.bound_ip and token_obj.bound_ip != current_ip:
        token_obj.failed_attempts += 1
        token_obj.save(update_fields=["failed_attempts"])
        raise PermissionDenied("IP mismatch")

    # Device Binding Check
    if token_obj.bound_user_agent and token_obj.bound_user_agent != current_ua:
        token_obj.failed_attempts += 1
        token_obj.save(update_fields=["failed_attempts"])
        raise PermissionDenied("Device mismatch")

    # Bind on first use
    if not token_obj.bound_ip:
        token_obj.bound_ip = current_ip

    if not token_obj.bound_user_agent:
        token_obj.bound_user_agent = current_ua

    token_obj.save(update_fields=["bound_ip", "bound_user_agent"])

    # ------------------------------
    # MARK OLD TOKEN AS USED
    # ------------------------------
    token_obj.is_used = True
    token_obj.last_used_at = timezone.now()
    token_obj.save(update_fields=["is_used", "last_used_at"])

    # ------------------------------
    # CREATE NEW TOKEN ROW
    # ------------------------------
    new_raw_token = PublicAccessToken.generate_raw_token()

    PublicAccessToken.objects.create(
        order=token_obj.order,
        token_hash=PublicAccessToken.hash_token(new_raw_token),
        expires_at=timezone.now() + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        bound_ip=current_ip,
        bound_user_agent=current_ua,
        failed_attempts=0,
        is_used=False
    )

    # Audit Log
    log_event(
        org=token_obj.order.org,
        event_type="PUBLIC_TOKEN_ROTATED",
        entity_type="AssessmentOrder",
        entity_id=token_obj.order.id,
        actor_role="PublicUser",
        details={"ip": current_ip},
        request=request,
        severity="SECURITY"
    )

    return token_obj.order, new_raw_token
