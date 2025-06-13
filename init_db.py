#!/usr/bin/env python3
"""
إنشاء قاعدة البيانات بالهيكل المحدث
"""

from app import app, db
from models import User, Category, Product, Sale, SaleItem, Customer, Payment, Expense

def init_database():
    """إنشاء قاعدة البيانات"""
    
    with app.app_context():
        print("إنشاء قاعدة البيانات...")
        
        try:
            # إنشاء جميع الجداول
            db.create_all()
            print("✅ تم إنشاء قاعدة البيانات بنجاح!")
            
            # إنشاء البيانات الأولية
            print("إنشاء البيانات الأولية...")
            
            # إنشاء المستخدمين
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                print("✓ تم إنشاء مستخدم المدير")
            
            seller = User.query.filter_by(username='seller').first()
            if not seller:
                seller = User(username='seller', role='seller')
                seller.set_password('seller123')
                db.session.add(seller)
                print("✓ تم إنشاء مستخدم البائع")
            
            # إنشاء فئات أساسية
            if Category.query.count() == 0:
                categories = [
                    Category(name_ar='كتب أدبية وروايات', description_ar='الروايات والقصص والشعر والأدب العربي والعالمي'),
                    Category(name_ar='كتب علمية وتقنية', description_ar='الكتب العلمية والتقنية والهندسية والطبية'),
                    Category(name_ar='كتب دراسية ومناهج', description_ar='المناهج الدراسية والكتب الجامعية والمدرسية'),
                    Category(name_ar='أقلام حبر وجاف', description_ar='أقلام الحبر الجاف والسائل بألوان مختلفة'),
                    Category(name_ar='أقلام رصاص وملونة', description_ar='أقلام الرصاص العادية والملونة وأقلام التلوين'),
                    Category(name_ar='كشاكيل ودفاتر خانات', description_ar='الكشاكيل المخططة والمربعة وذات الخانات'),
                    Category(name_ar='دفاتر مسطرة وسادة', description_ar='الدفاتر المسطرة والسادة للكتابة'),
                    Category(name_ar='محايات وبراية', description_ar='المحايات البيضاء والملونة وبرايات الأقلام'),
                    Category(name_ar='مجلدات وحافظات', description_ar='المجلدات البلاستيكية والكرتونية لحفظ الأوراق'),
                    Category(name_ar='أدوات هندسية ورياضية', description_ar='المساطر والزوايا وأدوات القياس الهندسية'),
                ]
                
                for category in categories:
                    db.session.add(category)
                print("✓ تم إنشاء الفئات الأساسية")
            
            # إنشاء منتجات تجريبية
            if Product.query.count() == 0:
                products = [
                    Product(name_ar='رواية مئة عام من العزلة', category_id=1, wholesale_price=65.00, retail_price=85.00, price=85.00, stock_quantity=25, min_stock_threshold=5, description_ar='رواية للكاتب غابرييل غارسيا ماركيز'),
                    Product(name_ar='كتاب البرمجة بالبايثون', category_id=2, wholesale_price=95.00, retail_price=120.00, price=120.00, stock_quantity=15, min_stock_threshold=3, description_ar='دليل شامل لتعلم البرمجة'),
                    Product(name_ar='منهج الرياضيات - الصف الثالث الثانوي', category_id=3, wholesale_price=42.00, retail_price=55.00, price=55.00, stock_quantity=50, min_stock_threshold=15, description_ar='منهج وزارة التربية والتعليم'),
                    Product(name_ar='قلم حبر جاف أزرق', category_id=4, wholesale_price=2.50, retail_price=3.50, price=3.50, stock_quantity=200, min_stock_threshold=50, unit_type='جزئي', unit_description='قلم', description_ar='قلم حبر جاف لون أزرق'),
                    Product(name_ar='قلم رصاص HB', category_id=5, wholesale_price=1.50, retail_price=2.00, price=2.00, stock_quantity=250, min_stock_threshold=60, unit_type='جزئي', unit_description='قلم'),
                    Product(name_ar='كشكول 100 ورقة مخطط', category_id=6, wholesale_price=12.00, retail_price=15.00, price=15.00, stock_quantity=120, min_stock_threshold=30, description_ar='كشكول مخطط للكتابة'),
                    Product(name_ar='دفتر 48 ورقة سادة', category_id=7, wholesale_price=6.00, retail_price=8.00, price=8.00, stock_quantity=200, min_stock_threshold=50, description_ar='دفتر سادة للكتابة الحرة'),
                    Product(name_ar='محاية بيضاء كبيرة', category_id=8, wholesale_price=1.80, retail_price=2.50, price=2.50, stock_quantity=300, min_stock_threshold=75, unit_type='جزئي', unit_description='قطعة'),
                    Product(name_ar='مجلد بلاستيكي A4', category_id=9, wholesale_price=9.00, retail_price=12.00, price=12.00, stock_quantity=80, min_stock_threshold=20, description_ar='مجلد شفاف لحفظ الأوراق'),
                    Product(name_ar='مسطرة 30 سم شفافة', category_id=10, wholesale_price=6.00, retail_price=8.00, price=8.00, stock_quantity=120, min_stock_threshold=30, unit_type='جزئي', unit_description='قطعة'),
                ]
                
                for product in products:
                    db.session.add(product)
                print("✓ تم إنشاء المنتجات التجريبية")
            
            # إنشاء عملاء تجريبيين
            if Customer.query.count() == 0:
                customers = [
                    Customer(name='أحمد محمد علي', phone='01234567890', address='القاهرة - مصر الجديدة', notes='عميل دائم'),
                    Customer(name='فاطمة أحمد حسن', phone='01098765432', address='الجيزة - الدقي'),
                    Customer(name='محمد حسن إبراهيم', phone='01555666777', address='الإسكندرية - سيدي جابر', notes='عميل مميز'),
                    Customer(name='سارة علي محمود', phone='01122334455', address='القاهرة - المعادي'),
                    Customer(name='عمر خالد أحمد', phone='01199887766', address='الجيزة - المهندسين', notes='عميل جديد'),
                ]
                
                for customer in customers:
                    db.session.add(customer)
                print("✓ تم إنشاء العملاء التجريبيين")
            
            db.session.commit()
            print("✅ تم حفظ جميع البيانات!")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = init_database()
    if success:
        print("\n🎉 قاعدة البيانات جاهزة للاستخدام!")
        print("اسم المستخدم: admin")
        print("كلمة المرور: admin123")
    else:
        print("\n⚠️ يرجى مراجعة الأخطاء وإعادة المحاولة") 