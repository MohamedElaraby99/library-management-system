from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='seller')  # 'admin' or 'seller'
    is_system = db.Column(db.Boolean, default=False, comment='مستخدم النظام المخفي')  # للمستخدم الافتراضي المخفي
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    description_ar = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    wholesale_price = db.Column(db.Float, nullable=False, comment='سعر الجملة')
    retail_price = db.Column(db.Float, nullable=False, comment='سعر البيع')
    price = db.Column(db.Float, nullable=True)
    stock_quantity = db.Column(db.Float, nullable=False, default=0)
    min_stock_threshold = db.Column(db.Float, nullable=False, default=10)
    unit_type = db.Column(db.String(50), nullable=False, default='كامل')  # 'كامل' or 'جزئي'
    unit_description = db.Column(db.String(100))  # وصف الوحدة مثل "صفحة" أو "فصل"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    
    @property
    def profit_margin(self):
        """هامش الربح للوحدة الواحدة"""
        return self.retail_price - self.wholesale_price
    
    @property
    def profit_percentage(self):
        """نسبة الربح"""
        if self.wholesale_price > 0:
            return ((self.retail_price - self.wholesale_price) / self.wholesale_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_threshold
    
    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0
    
    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return 'نفد المخزون'
        elif self.is_low_stock:
            return 'مخزون منخفض'
        else:
            return 'متوفر'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='customer', lazy=True)
    
    @property
    def total_debt(self):
        """إجمالي الدين المستحق على العميل"""
        total_sales = sum(sale.total_amount for sale in self.sales if sale.payment_status != 'paid')
        total_payments = sum(payment.amount for sale in self.sales for payment in sale.payments)
        return max(0, total_sales - total_payments)
    
    @property
    def total_sales_amount(self):
        """إجمالي مبلغ المبيعات للعميل"""
        return sum(sale.total_amount for sale in self.sales)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='paid')  # 'paid', 'partial', 'unpaid'
    payment_type = db.Column(db.String(20), nullable=False, default='cash')  # 'cash', 'credit'
    notes = db.Column(db.Text)
    
    # Relationships
    sale_items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    @property
    def paid_amount(self):
        """المبلغ المدفوع من إجمالي البيع"""
        if self.payment_type == 'cash':
            return self.total_amount
        return sum(payment.amount for payment in self.payments)
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return max(0, self.total_amount - self.paid_amount)
    
    @property
    def is_fully_paid(self):
        """هل تم دفع المبلغ كاملاً"""
        return self.remaining_amount == 0
    
    @property
    def total_profit(self):
        """إجمالي ربح البيع"""
        profit = 0
        for item in self.sale_items:
            if item.product:
                # الربح = (سعر البيع - سعر الجملة) × الكمية
                profit += (item.unit_price - item.product.wholesale_price) * item.quantity
        return profit
    
    @property
    def cost_amount(self):
        """إجمالي تكلفة البيع (بسعر الجملة)"""
        cost = 0
        for item in self.sale_items:
            if item.product:
                cost += item.product.wholesale_price * item.quantity
        return cost

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False, default='نقدي')  # نقدي، تحويل، إلخ
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # من سجل الدفعة
    
    # Relationships
    user = db.relationship('User', backref='payments', lazy=True)

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.quantity and self.unit_price:
            self.total_price = self.quantity * self.unit_price

# نموذج جديد للمصاريف
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False, comment='وصف المصروف')
    amount = db.Column(db.Float, nullable=False, comment='المبلغ')
    expense_type = db.Column(db.String(50), nullable=False, comment='نوع المصروف')  # 'salary', 'rent', 'utilities', 'other'
    expense_date = db.Column(db.DateTime, default=datetime.utcnow, comment='تاريخ المصروف')
    category = db.Column(db.String(100), comment='فئة المصروف')
    notes = db.Column(db.Text, comment='ملاحظات')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='المستخدم الذي سجل المصروف')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='expenses', lazy=True)
    
    @property
    def expense_type_ar(self):
        """ترجمة نوع المصروف للعربية"""
        types = {
            'salary': 'راتب',
            'rent': 'إيجار',
            'utilities': 'خدمات (كهرباء، ماء، هاتف)',
            'marketing': 'تسويق وإعلان',
            'maintenance': 'صيانة',
            'supplies': 'مستلزمات مكتبية',
            'transportation': 'مواصلات',
            'other': 'أخرى'
        }
        return types.get(self.expense_type, self.expense_type) 