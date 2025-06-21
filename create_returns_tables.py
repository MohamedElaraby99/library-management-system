#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# تأكد من إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# إنشاء تطبيق Flask مؤقت
app = Flask(__name__)

# تحديد قاعدة البيانات المطلوبة - المسار المطلق
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'library_dev.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إنشاء كائن db مستقل
db = SQLAlchemy()
db.init_app(app)

def create_returns_tables():
    """إنشاء جداول المرتجعات والجداول المفقودة"""
    
    with app.app_context():
        print(f"🔧 بدء إنشاء جداول المرتجعات في {db_path}...")
        
        # تأكد من وجود مجلد instance
        instance_dir = os.path.join(basedir, 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            print(f"✅ تم إنشاء مجلد: {instance_dir}")
        
        try:
            # استيراد النماذج بعد إنشاء السياق
            from models import User, Category, Customer, Product, Sale, SaleItem, Return, ReturnItem, Expense, Payment, ShoppingList
            
            # إنشاء جميع الجداول
            db.create_all()
            
            # التحقق من إنشاء الجداول
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print("✅ تم إنشاء الجداول بنجاح!")
            
            # فحص الجداول المطلوبة
            required_tables = ['return_transaction', 'return_item', 'category', 'customer']
            missing_tables = []
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ جدول {table} تم إنشاؤه")
                else:
                    print(f"❌ فشل في إنشاء جدول {table}")
                    missing_tables.append(table)
            
            print("\n📋 الجداول الموجودة في قاعدة البيانات:")
            for table in sorted(existing_tables):
                print(f"  - {table}")
            
            if missing_tables:
                print(f"\n⚠️  جداول مفقودة: {', '.join(missing_tables)}")
                return False
            
            print("\n🚀 يمكنك الآن:")
            print("  1. تشغيل التطبيق: python app.py")
            print("  2. الذهاب إلى صفحة المبيعات وإنشاء مرتجع جديد")
            print("  3. عرض جميع المرتجعات من قائمة المبيعات")
            print("  4. معالجة المرتجعات (للمديرين)")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True

if __name__ == '__main__':
    success = create_returns_tables()
    sys.exit(0 if success else 1) 