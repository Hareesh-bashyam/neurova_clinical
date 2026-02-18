from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Inspect ID 59 using raw SQL directly'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            print("--- Inspecting ID 59 directly ---")
            try:
                cursor.execute("SELECT id, public_token, created_at FROM clinical_ops_assessmentorder WHERE id = 59")
                row = cursor.fetchone()
                if row:
                    print(f"ID: {row[0]}")
                    print(f"Public Token: {row[1]}")
                    print(f"Created At: {row[2]}")
                else:
                    print("ID 59 not found in DB.")
            except Exception as e:
                print(f"Error querying table: {e}")
