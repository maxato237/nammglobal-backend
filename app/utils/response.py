from flask import jsonify


def api_response(success: bool, message: str, data=None, errors=None, status_code: int = 200):
    """Format de réponse standardisé pour toute l'API."""
    body = {"success": success, "message": message}
    if data is not None:
        body["data"] = data
    if errors is not None:
        body["errors"] = errors
    return jsonify(body), status_code


def ok(data=None, message: str = "OK") -> tuple:
    return api_response(True, message, data=data, status_code=200)


def created(data=None, message: str = "Créé avec succès.") -> tuple:
    return api_response(True, message, data=data, status_code=201)


def bad_request(message: str = "Requête invalide.", errors=None) -> tuple:
    return api_response(False, message, errors=errors, status_code=400)


def unauthorized(message: str = "Authentification requise.") -> tuple:
    return api_response(False, message, status_code=401)


def forbidden(message: str = "Accès refusé.") -> tuple:
    return api_response(False, message, status_code=403)


def not_found(message: str = "Ressource introuvable.") -> tuple:
    return api_response(False, message, status_code=404)


def conflict(message: str = "Conflit de données.") -> tuple:
    return api_response(False, message, status_code=409)


def server_error(message: str = "Erreur serveur interne.") -> tuple:
    return api_response(False, message, status_code=500)
