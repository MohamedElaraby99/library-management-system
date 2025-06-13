#!/usr/bin/env python3
"""
سكريبت إعداد النشر لنظام إدارة المكتبة
يجب تشغيله مرة واحدة فقط بعد رفع المشروع إلى PythonAnywhere
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Category

def create_database():
    """إنشاء قاعدة البيانات والجداول"""
    with app.app_context():
        print("🔧 إنشاء قاعدة البيانات...")
        
        # إنشاء جميع الجداول
        db.create_all()
        print("✅ تم إنشاء جميع الجداول بنجاح")

def create_default_users():
    """إنشاء المستخدمين الافتراضيين"""
    with app.app_context():
        print("👥 إنشاء المستخدمين الافتراضيين...")
        
        # التحقق من عدم وجود مستخدمين مسبقاً
        if User.query.first():
            print("⚠️  المستخدمون موجودون مسبقاً، تم تخطي هذه الخطوة")
            return
        
        # مستخدم البائع
        seller = User(
            username='seller',
            email='seller@library.com',
            is_admin=False,
            created_at=datetime.utcnow()
        )
        seller.set_password('seller123')
        
        # مستخدم الإدارة
        araby = User(
            username='araby',
            email='araby@library.com',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        araby.set_password('92321066')
        
        db.session.add(seller)
        db.session.add(araby)
        db.session.commit()
        
        print("✅ تم إنشاء المستخدمين:")
        print("   - seller (كلمة المرور: seller123)")
        print("   - araby (كلمة المرور: 92321066)")

def create_default_categories():
    """إنشاء الفئات الافتراضية"""
    with app.app_context():
        print("📚 إنشاء الفئات الافتراضية...")
        
        # التحقق من عدم وجود فئات مسبقاً
        if Category.query.first():
            print("⚠️  الفئات موجودة مسبقاً، تم تخطي هذه الخطوة")
            return
        
        default_categories = [
            'كتب عامة',
            'روايات',
            'كتب دينية',
            'كتب علمية',
            'كتب تاريخ',
            'كتب أطفال',
            'قواميس ومعاجم',
            'مجلات',
            'كتب طبخ',
            'كتب رياضة'
        ]
        
        for cat_name in default_categories:
            category = Category(
                name=cat_name,
                description=f'فئة {cat_name}',
                created_at=datetime.utcnow()
            )
            db.session.add(category)
        
        db.session.commit()
        print(f"✅ تم إنشاء {len(default_categories)} فئة افتراضية")

def setup_production_config():
    """إعداد التكوين للنشر"""
    print("⚙️  إعداد التكوين للنشر...")
    
    # التحقق من متغيرات البيئة المهمة
    if not os.environ.get('SECRET_KEY'):
        print("⚠️  تحذير: لم يتم تعيين SECRET_KEY في متغيرات البيئة")
        print("   يرجى تعيين مفتاح سري قوي في ملف wsgi.py")
    
    if not os.environ.get('DATABASE_URL'):
        print("⚠️  تحذير: لم يتم تعيين DATABASE_URL في متغيرات البيئة")
        print("   سيتم استخدام قاعدة البيانات الافتراضية")
    
    print("✅ تم فحص التكوين")

def main():
    """الدالة الرئيسية لإعداد النشر"""
    print("🚀 بدء إعداد نظام إدارة المكتبة للنشر")
    print("=" * 50)
    
    try:
        # إعداد التكوين
        setup_production_config()
        
        # إنشاء قاعدة البيانات
        create_database()
        
        # إنشاء المستخدمين الافتراضيين
        create_default_users()
        
        # إنشاء الفئات الافتراضية
        create_default_categories()
        
        print("=" * 50)
        print("✅ تم إعداد النظام بنجاح!")
        print("\n📋 معلومات الدخول:")
        print("   🔐 مدير النظام: araby / 92321066")
        print("   🛒 البائع: seller / seller123")
        print("\n🌐 يمكنك الآن الوصول إلى النظام من خلال الرابط الخاص بك")
        
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الإعداد: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 