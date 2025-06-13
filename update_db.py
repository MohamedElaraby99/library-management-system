#!/usr/bin/env python3
"""
تحديث قاعدة البيانات لإضافة الحقول الجديدة:
- سعر الجملة وسعر البيع للمنتجات
- نموذج المصاريف
- تحسين حساب الأرباح
"""

from app import app, db
from models import Product, Sale, SaleItem, Expense
from sqlalchemy import text

def update_database():
    """تحديث قاعدة البيانات بالحقول الجديدة"""
    
    with app.app_context():
        print("بدء تحديث قاعدة البيانات...")
        
        try:
            # إضافة أعمدة جديدة لجدول المنتجات
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE product ADD COLUMN wholesale_price FLOAT"))
                    conn.commit()
                print("✓ تم إضافة عمود سعر الجملة")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("• عمود سعر الجملة موجود بالفعل")
                else:
                    print(f"خطأ في إضافة سعر الجملة: {e}")
            
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE product ADD COLUMN retail_price FLOAT"))
                    conn.commit()
                print("✓ تم إضافة عمود سعر البيع")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("• عمود سعر البيع موجود بالفعل")
                else:
                    print(f"خطأ في إضافة سعر البيع: {e}")
            
            # إنشاء جدول المصاريف إذا لم يكن موجوداً
            try:
                db.create_all()
                print("✓ تم إنشاء جداول قاعدة البيانات الجديدة")
            except Exception as e:
                print(f"خطأ في إنشاء الجداول: {e}")
            
            # تحديث المنتجات الموجودة بالأسعار الافتراضية
            products_without_prices = Product.query.filter(
                (Product.wholesale_price == None) | (Product.retail_price == None)
            ).all()
            
            if products_without_prices:
                print(f"تحديث {len(products_without_prices)} منتج بالأسعار الجديدة...")
                
                for product in products_without_prices:
                    if product.wholesale_price is None:
                        # سعر الجملة = سعر البيع - 20%
                        product.wholesale_price = product.price * 0.8
                    
                    if product.retail_price is None:
                        # سعر البيع = السعر الحالي
                        product.retail_price = product.price
                
                db.session.commit()
                print("✓ تم تحديث أسعار المنتجات")
            else:
                print("• جميع المنتجات لديها أسعار محدثة")
            
            print("✅ تم تحديث قاعدة البيانات بنجاح!")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = update_database()
    if success:
        print("\n🎉 يمكنك الآن تشغيل التطبيق بالمميزات الجديدة!")
    else:
        print("\n⚠️ يرجى مراجعة الأخطاء وإعادة المحاولة") 