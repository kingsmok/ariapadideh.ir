#!/bin/bash
# Flask Pro - Quick Setup Script
# Run this in your project directory

# 1. Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip and install all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create instance and logs folder
mkdir -p instance logs

# 5. Initialize database
flask --app run init-db

# 6. Create admin user
flask --app run create-admin

# 7. Seed initial data
flask --app run seed-data

echo "Setup complete! Run 'python run.py' to start the server."
