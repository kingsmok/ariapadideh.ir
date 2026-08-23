"""
Blog Routes
"""
from flask import render_template, request
from flask_login import current_user
from app.blueprints.blog import blog_bp
from app.models import Post, Comment, Category
from app.extensions import db


# Blog routes are included in public routes with /blog prefix
# This file can add additional blog-specific routes if needed
