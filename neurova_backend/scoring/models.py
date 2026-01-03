from django.db import models
from sessions.models import Session


class Score(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)

    score = models.IntegerField()
    severity = models.CharField(max_length=32)

    breakdown = models.JSONField()   # stores answers

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Score(session={self.session_id}, score={self.score})"
