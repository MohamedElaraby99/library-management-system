#!/usr/bin/env python3
"""
إنشاء قاعدة البيانات بشكل مبسط
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# نماذج البيانات المحدثة
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='seller')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def is_admin(self):
        return self.role == 'admin'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    description_ar = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # الأسعار الجديدة
    wholesale_price = db.Column(db.Float, nullable=False, default=0.0)  # سعر الجملة
    retail_price = db.Column(db.Float, nullable=False, default=0.0)     # سعر البيع
    price = db.Column(db.Float, nullable=False, default=0.0)            # للتوافق مع الكود القديم
    
    stock_quantity = db.Column(db.Float, nullable=False, default=0)
    min_stock_threshold = db.Column(db.Float, default=10)
    unit_type = db.Column(db.String(20), default='كلي')
    unit_description = db.Column(db.String(50), default='قطعة')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sales = db.relationship('Sale', backref='customer', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    payment_type = db.Column(db.String(20), default='cash')
    payment_status = db.Column(db.String(20), default='paid')
    notes = db.Column(db.Text)
    
    sale_items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='sale', lazy=True, cascade='all, delete-orphan')

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='sale_items')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), default='نقدي')
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref='payments', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)
    expense_type = db.Column(db.String(50), nullable=False)  # 'salary', 'rent', 'utilities', 'other'
    category = db.Column(db.String(100))  # فئة فرعية اختيارية
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref='expenses', lazy=True)

def create_database():
    """إنشاء قاعدة البيانات والبيانات الأولية"""
    
    with app.app_context():
        print("إنشاء قاعدة البيانات...")
        
        # حذف الجداول الموجودة وإنشاءها من جديد
        db.drop_all()
        db.create_all()
        print("✅ تم إنشاء قاعدة البيانات!")
        
        # إنشاء المستخدمين
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        seller = User(username='seller', role='seller')
        seller.set_password('seller123')
        db.session.add(seller)
        
        # إنشاء الفئات
        categories = [
            Category(name_ar='كتب أدبية وروايات', description_ar='الروايات والقصص والشعر'),
            Category(name_ar='كتب علمية وتقنية', description_ar='الكتب العلمية والتقنية'),
            Category(name_ar='كتب دراسية ومناهج', description_ar='المناهج الدراسية'),
            Category(name_ar='أقلام حبر وجاف', description_ar='أقلام الحبر بألوان مختلفة'),
            Category(name_ar='أقلام رصاص وملونة', description_ar='أقلام الرصاص والتلوين'),
            Category(name_ar='كشاكيل ودفاتر', description_ar='الكشاكيل والدفاتر'),
            Category(name_ar='محايات وبراية', description_ar='المحايات وبرايات الأقلام'),
            Category(name_ar='مجلدات وحافظات', description_ar='مجلدات حفظ الأوراق'),
            Category(name_ar='أدوات هندسية', description_ar='أدوات القياس الهندسية'),
            Category(name_ar='أدوات مكتبية', description_ar='أدوات مكتبية متنوعة'),
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()  # حفظ الفئات أولاً للحصول على IDs
        
        # إنشاء المنتجات
        products = [
            Product(name_ar='رواية مئة عام من العزلة', category_id=1, wholesale_price=65.00, retail_price=85.00, price=85.00, stock_quantity=25, min_stock_threshold=5),
            Product(name_ar='كتاب البرمجة بالبايثون', category_id=2, wholesale_price=95.00, retail_price=120.00, price=120.00, stock_quantity=15, min_stock_threshold=3),
            Product(name_ar='منهج الرياضيات - ثانوي', category_id=3, wholesale_price=42.00, retail_price=55.00, price=55.00, stock_quantity=50, min_stock_threshold=15),
            Product(name_ar='قلم حبر جاف أزرق', category_id=4, wholesale_price=2.50, retail_price=3.50, price=3.50, stock_quantity=200, min_stock_threshold=50, unit_type='جزئي', unit_description='قلم'),
            Product(name_ar='قلم رصاص HB', category_id=5, wholesale_price=1.50, retail_price=2.00, price=2.00, stock_quantity=250, min_stock_threshold=60, unit_type='جزئي', unit_description='قلم'),
            Product(name_ar='كشكول 100 ورقة', category_id=6, wholesale_price=12.00, retail_price=15.00, price=15.00, stock_quantity=120, min_stock_threshold=30),
            Product(name_ar='محاية بيضاء', category_id=7, wholesale_price=1.80, retail_price=2.50, price=2.50, stock_quantity=300, min_stock_threshold=75, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='مجلد بلاستيكي A4', category_id=8, wholesale_price=9.00, retail_price=12.00, price=12.00, stock_quantity=80, min_stock_threshold=20),
            Product(name_ar='مسطرة 30 سم', category_id=9, wholesale_price=6.00, retail_price=8.00, price=8.00, stock_quantity=120, min_stock_threshold=30, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='دباسة صغيرة', category_id=10, wholesale_price=11.00, retail_price=15.00, price=15.00, stock_quantity=60, min_stock_threshold=15),
        ]
        
        for product in products:
            db.session.add(product)
        
        # إنشاء العملاء
        customers = [
            Customer(name='أحمد محمد علي', phone='01234567890', address='القاهرة - مصر الجديدة'),
            Customer(name='فاطمة أحمد حسن', phone='01098765432', address='الجيزة - الدقي'),
            Customer(name='محمد حسن إبراهيم', phone='01555666777', address='الإسكندرية - سيدي جابر'),
        ]
        
        for customer in customers:
            db.session.add(customer)
        
        db.session.commit()
        print("✅ تم إنشاء البيانات التجريبية!")
        print("\n🎉 قاعدة البيانات جاهزة!")
        print("اسم المستخدم: admin")
        print("كلمة المرور: admin123")

if __name__ == '__main__':
    create_database() 