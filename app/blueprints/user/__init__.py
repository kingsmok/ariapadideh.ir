"""
User Blueprint
"""
from flask import Blueprint

user_bp = Blueprint('user', __name__)

from app.blueprints.user import routes
