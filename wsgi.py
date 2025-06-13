#!/usr/bin/python3

import sys
import os
from dotenv import load_dotenv

# إضافة مسار المشروع
path = '/home/system99/library-management-system'
if path not in sys.path:
    sys.path.append(path)

# تحميل متغيرات البيئة
load_dotenv(os.path.join(path, '.env'))

# Set environment variables for production
os.environ['FLASK_CONFIG'] = 'production'
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'your-production-secret-key-here'  # Change this to a strong secret key
os.environ['DATABASE_URL'] = 'sqlite:////home/system99/library-system/library.db'  # Updated for your PythonAnywhere username

from app import app as application

if __name__ == "__main__":
    application.run() 