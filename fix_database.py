#!/usr/bin/env python3
"""
إصلاح قاعدة البيانات وإضافة الجداول والأعمدة المطلوبة
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def fix_database():
    """إصلاح قاعدة البيانات"""
    
    # البحث عن ملف قاعدة البيانات
    db_files = []
    for file in os.listdir('.'):
        if file.endswith('.db'):
            db_files.append(file)
    
    if not db_files:
        print("لم يتم العثور على ملف قاعدة البيانات. سيتم إنشاء قاعدة بيانات جديدة.")
        return create_new_database()
    
    db_file = db_files[0]
    print(f"تم العثور على قاعدة البيانات: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # التحقق من وجود جدول المنتجات والأعمدة الجديدة
        cursor.execute("PRAGMA table_info(product)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"أعمدة جدول المنتجات: {columns}")
        
        # إضافة أعمدة الأسعار الجديدة إذا لم تكن موجودة
        if 'wholesale_price' not in columns:
            cursor.execute("ALTER TABLE product ADD COLUMN wholesale_price REAL")
            print("✓ تم إضافة عمود wholesale_price")
            
        if 'retail_price' not in columns:
            cursor.execute("ALTER TABLE product ADD COLUMN retail_price REAL")
            print("✓ تم إضافة عمود retail_price")
        
        # تحديث الأسعار الموجودة
        cursor.execute("UPDATE product SET wholesale_price = price * 0.8, retail_price = price WHERE wholesale_price IS NULL OR retail_price IS NULL")
        print("✓ تم تحديث الأسعار الموجودة")
        
        # التحقق من وجود عمود is_system في جدول المستخدمين
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_system' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN is_system BOOLEAN DEFAULT 0")
            print("✓ تم إضافة عمود is_system")
        
        # إنشاء المستخدم الافتراضي المخفي إذا لم يكن موجود
        cursor.execute("SELECT id FROM user WHERE username = 'araby'")
        if not cursor.fetchone():
            araby_password = generate_password_hash('92321066')
            cursor.execute("""
                INSERT INTO user (username, password_hash, role, is_system) 
                VALUES ('araby', ?, 'admin', 1)
            """, (araby_password,))
            print("✓ تم إنشاء المستخدم الافتراضي المخفي: araby")
        
        # التحقق من وجود جدول المصاريف
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expense'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE expense (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description VARCHAR(500) NOT NULL,
                    amount FLOAT NOT NULL,
                    expense_type VARCHAR(50) NOT NULL,
                    expense_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    category VARCHAR(100),
                    notes TEXT,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """)
            print("✓ تم إنشاء جدول المصاريف")
        else:
            # التحقق من أعمدة جدول المصاريف
            cursor.execute("PRAGMA table_info(expense)")
            expense_columns = [col[1] for col in cursor.fetchall()]
            print(f"أعمدة جدول المصاريف: {expense_columns}")
            
            if 'created_at' not in expense_columns:
                cursor.execute("ALTER TABLE expense ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("✓ تم إضافة عمود created_at لجدول المصاريف")
        
        conn.commit()
        print("✅ تم إصلاح قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح قاعدة البيانات: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def create_new_database():
    """إنشاء قاعدة بيانات جديدة"""
    print("إنشاء قاعدة بيانات جديدة...")
    
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    try:
        # إنشاء جدول المستخدمين
        cursor.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'seller',
                is_system BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # إنشاء جدول الفئات
        cursor.execute("""
            CREATE TABLE category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ar VARCHAR(100) UNIQUE NOT NULL,
                description_ar TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # إنشاء جدول المنتجات
        cursor.execute("""
            CREATE TABLE product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ar VARCHAR(200) NOT NULL,
                description_ar TEXT,
                category_id INTEGER NOT NULL,
                wholesale_price REAL NOT NULL,
                retail_price REAL NOT NULL,
                price REAL NOT NULL,
                stock_quantity REAL NOT NULL DEFAULT 0,
                min_stock_threshold REAL DEFAULT 5,
                unit_type VARCHAR(20) DEFAULT 'كامل',
                unit_description VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES category (id)
            )
        """)
        
        # إنشاء جدول العملاء
        cursor.execute("""
            CREATE TABLE customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                phone VARCHAR(20),
                address TEXT,
                email VARCHAR(100),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # إنشاء جدول المبيعات
        cursor.execute("""
            CREATE TABLE sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_amount FLOAT NOT NULL,
                customer_id INTEGER,
                user_id INTEGER NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'paid',
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customer (id),
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        
        # إنشاء جدول عناصر المبيعات
        cursor.execute("""
            CREATE TABLE sale_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity FLOAT NOT NULL,
                unit_price FLOAT NOT NULL,
                total_price FLOAT NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sale (id),
                FOREIGN KEY (product_id) REFERENCES product (id)
            )
        """)
        
        # إنشاء جدول المدفوعات
        cursor.execute("""
            CREATE TABLE payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_method VARCHAR(50) DEFAULT 'نقدي',
                notes TEXT,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sale (id),
                FOREIGN KEY (customer_id) REFERENCES customer (id),
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        
        # إنشاء جدول المصاريف
        cursor.execute("""
            CREATE TABLE expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description VARCHAR(500) NOT NULL,
                amount FLOAT NOT NULL,
                expense_type VARCHAR(50) NOT NULL,
                expense_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                category VARCHAR(100),
                notes TEXT,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        
        # إدراج المستخدم الافتراضي
        admin_password = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO user (username, password_hash, role) 
            VALUES ('admin', ?, 'admin')
        """, (admin_password,))
        
        # إدراج المستخدم الافتراضي المخفي
        araby_password = generate_password_hash('92321066')
        cursor.execute("""
            INSERT INTO user (username, password_hash, role, is_system) 
            VALUES ('araby', ?, 'admin', 1)
        """, (araby_password,))
        
        # إدراج فئات افتراضية
        categories = [
            'كتب دينية',
            'أدب وروايات',
            'كتب علمية',
            'قصص أطفال',
            'مراجع ومعاجم',
            'كتب تاريخية',
            'أدوات مكتبية'
        ]
        
        for category in categories:
            cursor.execute("INSERT INTO category (name_ar) VALUES (?)", (category,))
        
        conn.commit()
        print("✅ تم إنشاء قاعدة بيانات جديدة بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🎉 تم الانتهاء من إصلاح قاعدة البيانات!")
        print("يمكنك الآن تشغيل التطبيق باستخدام: python app.py")
    else:
        print("\n❌ فشل في إصلاح قاعدة البيانات!") 