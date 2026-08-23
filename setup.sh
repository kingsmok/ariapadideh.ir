# Flask Pro - Quick Setup Script
# Run this in your project directory

# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
# source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Create instance folder
mkdir instance

# 5. Initialize database
flask --app run init-db

# 6. Create admin user
flask --app run create-admin

# 7. Seed initial data
flask --app run seed-data

# 8. Run the application
python run.py
