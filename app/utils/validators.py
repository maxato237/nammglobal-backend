import re


def validate_phone(phone: str) -> tuple[bool, str]:
    """Valide un numéro international (ex: +237612345678)."""
    if not phone:
        return False, "Le numéro de téléphone est requis."
    cleaned = re.sub(r"\s+", "", phone)
    if not re.match(r"^\+?\d{8,15}$", cleaned):
        return False, "Format de numéro invalide. Utilisez le format international (+237...)."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Min 8 chars, 1 chiffre, 1 caractère spécial."""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, ""


def validate_country_code(code: str) -> bool:
    """Valide un code pays ISO2."""
    return bool(code) and len(code) == 2 and code.isalpha()


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(email) and bool(re.match(pattern, email))
