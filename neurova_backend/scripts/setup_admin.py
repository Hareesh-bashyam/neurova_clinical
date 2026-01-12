
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neurova_backend.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Organization, UserProfile

def setup():
    username = "admin"
    password = "Hareesh"
    
    # 1. Ensure User
    if not User.objects.filter(username=username).exists():
        print(f"Creating user {username}...")
        user = User.objects.create_superuser(username, "admin@test.com", password)
    else:
        print(f"User {username} exists.")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()

    # 2. Ensure Organization
    org, created = Organization.objects.get_or_create(
        name="Dev Organization",
        defaults={"code": "DEV_ORG"}
    )
    if created:
        print("Created Dev Organization.")

    # 3. Ensure Profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "organization": org,
            "role": "ORG_ADMIN"
        }
    )
    
    if not created:
        print("Updating existing profile...")
        profile.organization = org
        profile.role = "ORG_ADMIN"
        profile.save()
    
    print(f"✅ Setup complete. {username} is now ORG_ADMIN of {org.name}")

if __name__ == "__main__":
    setup()
