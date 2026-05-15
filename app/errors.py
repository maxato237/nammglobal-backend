from flask import jsonify


class APIException(Exception):
    """Exception métier avec code HTTP et message JSON structuré."""

    def __init__(self, message: str, status_code: int = 400, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors

    def to_response(self):
        body = {"success": False, "message": self.message}
        if self.errors:
            body["errors"] = self.errors
        return jsonify(body), self.status_code


def register_error_handlers(app):
    @app.errorhandler(APIException)
    def handle_api_exception(e):
        return e.to_response()

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": "Requête invalide."}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "message": "Authentification requise."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"success": False, "message": "Accès refusé."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Route introuvable."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Méthode non autorisée."}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"success": False, "message": "Données invalides.", "errors": str(e)}), 422

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({"success": False, "message": "Trop de requêtes. Réessayez plus tard."}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Erreur serveur interne."}), 500
