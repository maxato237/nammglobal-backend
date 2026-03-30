from flask import jsonify
from datetime import date
import uuid, re

def success(data=None, message="OK", status=200):
    body = {"success": True, "message": message}
    if data is not None: body["data"] = data
    return jsonify(body), status

def created(data=None, message="Créé avec succès"):
    return success(data=data, message=message, status=201)

def error(message="Erreur", status=400, errors=None):
    body = {"success": False, "message": message}
    if errors: body["errors"] = errors
    return jsonify(body), status

def not_found(msg="Ressource introuvable"): return error(msg, 404)
def forbidden(msg="Accès refusé"):          return error(msg, 403)
def server_error(msg="Erreur serveur"):     return error(msg, 500)

def generate_uuid(): return str(uuid.uuid4())

def validate_password(p):
    if len(p)<6: return False,"Le mot de passe doit contenir au moins 6 caractères."
    return True,""

def parse_date(s):
    if not s: return None
    try: return date.fromisoformat(s)
    except: return None
