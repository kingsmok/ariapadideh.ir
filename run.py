#!/usr/bin/env python
"""
Rahsa Dev Enterprise Application Runner
"""
import os
import sys

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

# Schema management:
#   production/staging → Alembic migrations only (`flask db upgrade`)
#   development        → `flask init-db` (create_all convenience) or migrations
# An implicit create_all at boot is intentionally NOT done here: it races
# with migration history and can silently diverge the schema.

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.debug
    )
