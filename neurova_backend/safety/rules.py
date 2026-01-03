def detect_flags(test_code: str, answers: dict) -> list:
    flags = []

    if test_code.upper() == "PHQ9":
        item9 = answers.get("item_9") or answers.get("q9") or answers.get("9")
        if item9 is not None and int(item9) >= 1:
            flags.append({
                "flag_type": "SELF_HARM",
                "level": "CRITICAL",
                "details": {
                    "message": "Patient reported thoughts of self-harm on PHQ-9 item 9.",
                    "tele_manas": "14416"
                }
            })

    return flags
