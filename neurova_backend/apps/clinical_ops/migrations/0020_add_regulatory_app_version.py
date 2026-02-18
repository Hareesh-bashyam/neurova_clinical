# Generated manually for regulatory compliance
# Adds app_version field to AssessmentOrder and AuditEvent models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical_ops', '0019_assessmentorder_report_failed_attempts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessmentorder',
            name='app_version',
            field=models.CharField(default='1.0', max_length=20),
        ),
        migrations.AddField(
            model_name='auditevent',
            name='app_version',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
