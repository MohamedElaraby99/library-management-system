#!/usr/bin/python3.10

"""
WSGI configuration for PythonAnywhere deployment
This file is used by PythonAnywhere to serve the Flask application
"""

import sys
import os

# Add your project directory to the sys.path
# Change 'yourusername' to your actual PythonAnywhere username
project_home = '/home/yourusername/library-management-system'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variable for configuration
os.environ['FLASK_CONFIG'] = 'pythonanywhere'

# Import your Flask application
from app import app as application

# Initialize the application for production
if __name__ == "__main__":
    # This won't be called in production, but useful for testing
    application.run(debug=False) 