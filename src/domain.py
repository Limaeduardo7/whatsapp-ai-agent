from __future__ import annotations


def normalize_phone(raw: str | None) -> str | None:
    if raw is None:
        return None

    value = str(raw).strip()
    if not value:
        return None

    if any(ch.isalpha() for ch in value):
        return None

    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None

    if len(digits) == 13:
        try:
            timestamp_ms = int(digits)
            if 1500000000000 <= timestamp_ms <= 2500000000000:
                return None
        except ValueError:
            pass

    if len(set(digits)) == 1:
        return None

    if len(digits) in {10, 11} and not digits.startswith("55"):
        digits = f"55{digits}"

    if not (12 <= len(digits) <= 15):
        return None

    return digits


def mask_phone(phone: str) -> str:
    if len(phone) <= 4:
        return "***"
    return f"{phone[:4]}***{phone[-2:]}"
