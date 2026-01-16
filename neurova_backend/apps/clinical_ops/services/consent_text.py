CONSENT_TEXTS = {
    ("V1", "en"): """CONSENT FOR PSYCHIATRIC ASSESSMENT (DIGITAL)

By proceeding, I confirm:
1) I consent to the collection and processing of my responses to standardized mental health questionnaires.
2) I understand this produces a standardized assessment summary report. It is NOT a standalone medical diagnosis.
3) I consent to sharing the report with the healthcare provider / facility conducting this assessment.
4) In case I report self-harm thoughts, the facility may initiate safety escalation as per their protocol.
5) I can request deletion where legally applicable, subject to clinical/legal retention requirements.

I confirm I have read and understood this consent.
""",
}

def get_consent_text(version: str = "V1", lang: str = "en") -> str:
    return CONSENT_TEXTS.get((version, lang), CONSENT_TEXTS[("V1", "en")])


