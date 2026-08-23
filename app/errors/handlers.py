"""
Error Handlers
"""
from flask import render_template, request, jsonify
from app.extensions import db


def handle_404(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 404
        }), 404
    
    return render_template('errors/404.html'), 404


def handle_500(e):
    """Handle 500 errors"""
    # Log the error
    app = request.environ.get('flask.app')
    if app:
        app.logger.error(f'Server Error: {str(e)}')
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status': 500
        }), 500
    
    return render_template('errors/500.html'), 500


def handle_403(e):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status': 403
        }), 403
    
    return render_template('errors/403.html'), 403


def handle_405(e):
    """Handle 405 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'This HTTP method is not allowed for this endpoint',
            'status': 405
        }), 405
    
    return render_template('errors/405.html'), 405
