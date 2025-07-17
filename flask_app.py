#!/usr/bin/python3.10

# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It has been auto-generated for your Flask project

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/SkillSwap'  # Replace 'yourusername' with your PythonAnywhere username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables for PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'true'

# Database configuration - Set these in your PythonAnywhere environment
# os.environ['MYSQL_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
# os.environ['MYSQL_USER'] = 'yourusername'
# os.environ['MYSQL_PASSWORD'] = 'your-mysql-password'
# os.environ['MYSQL_DATABASE'] = 'yourusername$skillswaps'

# Secret key for sessions
os.environ['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure secret key

from app import app as application

if __name__ == "__main__":
    application.run()
