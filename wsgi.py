"""Entrypoint Gunicorn pour la production.
Usage : gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
"""
from app import create_app

app = create_app()
