# scoring/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from sessions.models import Session
from .models import Score
from .services import compute_score  # or wherever compute_score lives


class SessionScoreCreateView(APIView):
    def post(self, request, session_id):
        session = Session.objects.get(id=session_id)

        # 🔒 If already scored, return existing score (IDEMPOTENT)
        existing = Score.objects.filter(session=session).first()
        if existing:
            return Response(
                {
                    "score": existing.score,
                    "severity": existing.severity,
                    "already_scored": True,
                },
                status=status.HTTP_200_OK,
            )

        answers = request.data.get("answers")
        if not answers:
            return Response(
                {"error": "answers are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = compute_score(answers)

        score = Score.objects.create(
            organization=session.organization,
            session=session,
            score=result["score"],
            severity=result["severity"],
        )

        return Response(
            {
                "score": score.score,
                "severity": score.severity,
                "already_scored": False,
            },
            status=status.HTTP_200_OK,
        )
