from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
import json
import os

from config import config
from models import db, User, Category, Product, Sale, SaleItem, Customer, Payment, Expense
from forms import LoginForm, UserForm, CategoryForm, ProductForm, SaleForm, SaleItemForm, StockUpdateForm, CustomerForm, PaymentForm, ExpenseForm

app = Flask(__name__)

# Load configuration based on environment
config_name = os.environ.get('FLASK_CONFIG') or 'default'
app.config.from_object(config[config_name])

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

def format_currency(amount):
    """Format currency for Egyptian Pounds"""
    return f"{amount:.2f} ج.م"

def format_date(date):
    """تنسيق التاريخ بالعربية"""
    months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 
              'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    return f"{date.day} {months[date.month-1]} {date.year}"

# Template filters
app.jinja_env.filters['currency'] = format_currency
app.jinja_env.filters['arabic_date'] = format_date

@app.context_processor
def inject_debt_stats():
    """إضافة إحصائيات الديون إلى جميع القوالب"""
    if current_user.is_authenticated:
        try:
            # إحصائيات الديون
            # حساب إجمالي المبيعات الآجلة (غير المدفوعة بالكامل)
            unpaid_sales_total = db.session.query(func.sum(Sale.total_amount)).filter(
                Sale.payment_status != 'paid'
            ).scalar() or 0
            
            # حساب إجمالي الدفعات للمبيعات الآجلة
            total_payments = db.session.query(func.sum(Payment.amount)).join(Sale).filter(
                Sale.payment_status != 'paid'
            ).scalar() or 0
            
            # إجمالي الديون = إجمالي المبيعات الآجلة - إجمالي الدفعات
            total_debt = max(0, unpaid_sales_total - total_payments)
            
            customers_with_debt = Customer.query.filter(Customer.id.in_(
                db.session.query(Sale.customer_id).filter(Sale.payment_status != 'paid').distinct()
            )).count()
            return dict(global_total_debt=total_debt, global_customers_with_debt=customers_with_debt)
        except:
            return dict(global_total_debt=0, global_customers_with_debt=0)
    return dict(global_total_debt=0, global_customers_with_debt=0)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # تصفية اسم المستخدم من المسافات
        username = form.username.data.strip()
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(form.password.data):
            # تسجيل الدخول مع خيار التذكر
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock_quantity <= Product.min_stock_threshold).count()
    out_of_stock_products = Product.query.filter(Product.stock_quantity <= 0).count()
    total_categories = Category.query.count()
    
    # Sales statistics
    today = datetime.now().date()
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
    today_revenue = sum(sale.total_amount for sale in today_sales)
    
    # This month sales
    month_start = datetime.now().replace(day=1).date()
    month_sales = Sale.query.filter(func.date(Sale.sale_date) >= month_start).all()
    month_revenue = sum(sale.total_amount for sale in month_sales)
    
    # حساب أرباح ومصاريف الشهر الحالي
    month_profit = sum(sale.total_profit for sale in month_sales)
    month_cost = sum(sale.cost_amount for sale in month_sales)
    
    # مصاريف الشهر الحالي
    month_expenses = Expense.query.filter(func.date(Expense.expense_date) >= month_start).all()
    month_total_expenses = sum(expense.amount for expense in month_expenses)
    
    # صافي ربح الشهر
    month_net_profit = month_profit - month_total_expenses
    
    # إحصائيات اليوم
    today_profit = sum(sale.total_profit for sale in today_sales)
    today_expenses = Expense.query.filter(func.date(Expense.expense_date) == today).all()
    today_total_expenses = sum(expense.amount for expense in today_expenses)
    today_net_profit = today_profit - today_total_expenses
    
    # Recent sales
    recent_sales = Sale.query.order_by(desc(Sale.sale_date)).limit(5).all()
    
    # Low stock alerts
    low_stock_alerts = Product.query.filter(Product.stock_quantity <= Product.min_stock_threshold).all()
    
    # Top selling products (this month)
    top_products = db.session.query(
        Product.name_ar,
        func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.sale_date) >= month_start
    ).group_by(Product.id).order_by(desc('total_sold')).limit(5).all()
    
    # إحصائيات الديون
    # حساب إجمالي المبيعات الآجلة (غير المدفوعة بالكامل)
    unpaid_sales_total = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.payment_status != 'paid'
    ).scalar() or 0
    
    # حساب إجمالي الدفعات للمبيعات الآجلة
    total_payments = db.session.query(func.sum(Payment.amount)).join(Sale).filter(
        Sale.payment_status != 'paid'
    ).scalar() or 0
    
    # إجمالي الديون = إجمالي المبيعات الآجلة - إجمالي الدفعات
    total_debt = max(0, unpaid_sales_total - total_payments)
    
    customers_with_debt = Customer.query.filter(Customer.id.in_(
        db.session.query(Sale.customer_id).filter(Sale.payment_status != 'paid').distinct()
    )).count()
    
    return render_template('dashboard.html', 
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products,
                         total_categories=total_categories,
                         today_revenue=today_revenue,
                         month_revenue=month_revenue,
                         # إحصائيات الأرباح والمصاريف
                         month_profit=month_profit,
                         month_cost=month_cost,
                         month_total_expenses=month_total_expenses,
                         month_net_profit=month_net_profit,
                         today_profit=today_profit,
                         today_expenses=today_total_expenses,  # Fixed: added missing today_expenses
                         today_total_expenses=today_total_expenses,
                         today_net_profit=today_net_profit,
                         recent_sales=recent_sales,
                         low_stock_alerts=low_stock_alerts,
                         top_products=top_products,
                         total_debt=total_debt,
                         customers_with_debt=customers_with_debt)

@app.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category', 0, type=int)
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name_ar.contains(search))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.order_by(desc(Product.created_at)).paginate(
        page=page, per_page=10, error_out=False)
    
    categories = Category.query.all()
    return render_template('products/list.html', products=products, categories=categories)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('products'))
    
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name_ar=form.name_ar.data,
            description_ar=form.description_ar.data,
            category_id=form.category_id.data,
            wholesale_price=form.wholesale_price.data,
            retail_price=form.retail_price.data,
            price=form.retail_price.data,  # للتوافق مع الكود القديم
            stock_quantity=form.stock_quantity.data,
            min_stock_threshold=form.min_stock_threshold.data,
            unit_type=form.unit_type.data,
            unit_description=form.unit_description.data
        )
        db.session.add(product)
        db.session.commit()
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('products'))
    
    return render_template('products/form.html', form=form, title='إضافة منتج جديد')

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('products'))
    
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        form.populate_obj(product)
        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('products'))
    
    return render_template('products/form.html', form=form, title='تعديل المنتج')

@app.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لحذف المنتجات', 'error')
        return redirect(url_for('products'))
    
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('products'))

@app.route('/categories')
@login_required
def categories():
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.order_by(Category.name_ar).all()
    return render_template('categories/list.html', categories=categories)

@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('categories'))
    
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name_ar=form.name_ar.data,
            description_ar=form.description_ar.data
        )
        db.session.add(category)
        db.session.commit()
        flash('تم إضافة الفئة بنجاح', 'success')
        return redirect(url_for('categories'))
    
    return render_template('categories/form.html', form=form, title='إضافة فئة جديدة')

@app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('categories'))
    
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('تم تحديث الفئة بنجاح', 'success')
        return redirect(url_for('categories'))
    
    return render_template('categories/form.html', form=form, title='تعديل الفئة')

@app.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """حذف فئة"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لحذف الفئات', 'error')
        return redirect(url_for('categories'))
    
    category = Category.query.get_or_404(id)
    
    # التحقق من عدم وجود منتجات في الفئة
    if category.products:
        flash('لا يمكن حذف فئة تحتوي على منتجات', 'error')
        return redirect(url_for('categories'))
    
    category_name = category.name_ar
    db.session.delete(category)
    db.session.commit()
    flash(f'تم حذف الفئة "{category_name}" بنجاح', 'success')
    return redirect(url_for('categories'))

# User management routes
@app.route('/users')
@login_required
def users():
    """عرض قائمة المستخدمين"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى إدارة المستخدمين', 'error')
        return redirect(url_for('dashboard'))
    
    # إخفاء مستخدمي النظام من القائمة
    users = User.query.filter_by(is_system=False).order_by(User.created_at.desc()).all()
    return render_template('users/list.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """إضافة مستخدم جديد"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لإضافة المستخدمين', 'error')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'تم إضافة المستخدم "{user.username}" بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة المستخدم', 'error')
    
    return render_template('users/add.html', form=form)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    """تعديل مستخدم"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لتعديل المستخدمين', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    
    # منع تعديل مستخدم النظام
    if user.is_system:
        flash('لا يمكن تعديل مستخدم النظام', 'error')
        return redirect(url_for('users'))
    
    # منع تعديل نفس المستخدم
    if user.id == current_user.id:
        flash('لا يمكنك تعديل حسابك الشخصي من هنا', 'error')
        return redirect(url_for('users'))
    
    form = UserForm(original_username=user.username, is_edit=True)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        
        # تحديث كلمة المرور إذا تم إدخال واحدة جديدة
        if form.password.data:
            user.set_password(form.password.data)
        
        try:
            db.session.commit()
            flash(f'تم تحديث بيانات المستخدم "{user.username}" بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث المستخدم', 'error')
    
    # ملء النموذج بالبيانات الحالية
    if request.method == 'GET':
        form.username.data = user.username
        form.role.data = user.role
        form.password.data = ''  # لا نعرض كلمة المرور
    
    return render_template('users/edit.html', form=form, user=user)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    """حذف مستخدم"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لحذف المستخدمين', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    
    # منع حذف مستخدم النظام
    if user.is_system:
        flash('لا يمكن حذف مستخدم النظام', 'error')
        return redirect(url_for('users'))
    
    # منع حذف نفس المستخدم
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الشخصي', 'error')
        return redirect(url_for('users'))
    
    # التحقق من وجود مبيعات للمستخدم
    if user.sales:
        flash('لا يمكن حذف مستخدم لديه مبيعات مسجلة', 'error')
        return redirect(url_for('users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'تم حذف المستخدم "{username}" بنجاح', 'success')
    return redirect(url_for('users'))

# Customer management routes
@app.route('/customers')
@login_required
def customers():
    """عرض قائمة العملاء"""
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """إضافة عميل جديد"""
    if request.method == 'POST':
        # Check if it's a JSON request (for quick add from sales page)
        if request.is_json:
            data = request.get_json()
            customer = Customer(
                name=data['name'],
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                notes=data.get('notes', '')
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify({'success': True, 'customer_id': customer.id})
        
        # Regular form submission
        form = CustomerForm()
        if form.validate_on_submit():
            customer = Customer(
                name=form.name.data,
                phone=form.phone.data,
                address=form.address.data,
                notes=form.notes.data
            )
            db.session.add(customer)
            db.session.commit()
            flash(f'تم إضافة العميل "{customer.name}" بنجاح', 'success')
            return redirect(url_for('customers'))
        return render_template('customers/form.html', form=form, title='إضافة عميل جديد')
    
    # GET request
    form = CustomerForm()
    return render_template('customers/form.html', form=form, title='إضافة عميل جديد')

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    """تعديل بيانات عميل"""
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        customer.notes = form.notes.data
        db.session.commit()
        flash(f'تم تحديث بيانات العميل "{customer.name}" بنجاح', 'success')
        return redirect(url_for('customers'))
    return render_template('customers/form.html', form=form, title='تعديل بيانات العميل', customer=customer)

@app.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    """حذف عميل"""
    customer = Customer.query.get_or_404(id)
    
    # Check if customer has any sales
    if customer.sales:
        flash('لا يمكن حذف العميل لأن لديه مبيعات مسجلة', 'error')
        return redirect(url_for('customers'))
    
    customer_name = customer.name
    db.session.delete(customer)
    db.session.commit()
    flash(f'تم حذف العميل "{customer_name}" بنجاح', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/<int:id>/account')
@login_required
def customer_account(id):
    """عرض حساب العميل والديون"""
    customer = Customer.query.get_or_404(id)
    sales = Sale.query.filter_by(customer_id=id).order_by(desc(Sale.sale_date)).all()
    return render_template('customers/account.html', customer=customer, sales=sales)

@app.route('/customers/<int:customer_id>/sales/<int:sale_id>/payment', methods=['GET', 'POST'])
@login_required
def add_payment(customer_id, sale_id):
    """إضافة دفعة لمبيعة"""
    customer = Customer.query.get_or_404(customer_id)
    sale = Sale.query.get_or_404(sale_id)
    
    if sale.customer_id != customer_id:
        flash('خطأ في بيانات العميل أو المبيعة', 'error')
        return redirect(url_for('customers'))
    
    if sale.is_fully_paid:
        flash('هذه المبيعة مدفوعة بالكامل', 'info')
        return redirect(url_for('customer_account', id=customer_id))
    
    form = PaymentForm()
    if form.validate_on_submit():
        # التأكد من أن المبلغ لا يتجاوز المتبقي
        remaining = sale.remaining_amount
        if form.amount.data > remaining:
            flash(f'المبلغ المدخل أكبر من المتبقي ({remaining:.2f} ج.م)', 'error')
        else:
            payment = Payment(
                sale_id=sale_id,
                amount=form.amount.data,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                user_id=current_user.id
            )
            db.session.add(payment)
            
            # تحديث حالة الدفع
            total_paid = sale.paid_amount + form.amount.data
            if total_paid >= sale.total_amount:
                sale.payment_status = 'paid'
            else:
                sale.payment_status = 'partial'
            
            db.session.commit()
            flash(f'تم تسجيل دفعة بمبلغ {form.amount.data:.2f} ج.م بنجاح', 'success')
            return redirect(url_for('customer_account', id=customer_id))
    
    return render_template('customers/payment.html', form=form, customer=customer, sale=sale)

@app.route('/debts')
@login_required
def debts_report():
    """تقرير الديون"""
    # العملاء الذين لديهم ديون
    customers_with_debts = []
    customers = Customer.query.all()
    
    for customer in customers:
        debt = customer.total_debt
        if debt > 0:
            customers_with_debts.append({
                'customer': customer,
                'debt': debt,
                'unpaid_sales': [sale for sale in customer.sales if not sale.is_fully_paid]
            })
    
    # ترتيب حسب قيمة الدين (الأكبر أولاً)
    customers_with_debts.sort(key=lambda x: x['debt'], reverse=True)
    
    total_debts = sum(item['debt'] for item in customers_with_debts)
    
    return render_template('debts/report.html', 
                         customers_with_debts=customers_with_debts, 
                         total_debts=total_debts,
                         current_datetime=datetime.now())

@app.route('/sales')
@login_required
def sales():
    page = request.args.get('page', 1, type=int)
    sales = Sale.query.order_by(desc(Sale.sale_date)).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('sales/list.html', sales=sales)

@app.route('/sales/new')
@login_required
def new_sale():
    return render_template('sales/new.html')

@app.route('/api/products')
@login_required
def api_products():
    """API endpoint to get all products"""
    products = Product.query.all()  # Get all products for stock update
    return jsonify([{
        'id': p.id,
        'name': p.name_ar,
        'wholesale_price': p.wholesale_price if hasattr(p, 'wholesale_price') and p.wholesale_price else p.price,
        'retail_price': p.retail_price if hasattr(p, 'retail_price') and p.retail_price else p.price,
        'price': p.retail_price if hasattr(p, 'retail_price') and p.retail_price else p.price,
        'stock': p.stock_quantity,
        'unit_type': p.unit_type,
        'category': p.category.name_ar if p.category else 'غير محدد',
        'min_stock_threshold': p.min_stock_threshold or 10,
        'profit_margin': p.profit_margin if hasattr(p, 'profit_margin') else 0,
        'profit_percentage': p.profit_percentage if hasattr(p, 'profit_percentage') else 0
    } for p in products])

@app.route('/api/categories')
@login_required
def api_categories():
    """API endpoint to get all categories"""
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name_ar,
        'description': c.description_ar or '',
        'product_count': len(c.products),
        'created_at': c.created_at.isoformat() if hasattr(c, 'created_at') and c.created_at else None
    } for c in categories])

@app.route('/api/customers')
@login_required
def api_customers():
    """API endpoint to get all customers"""
    customers = Customer.query.order_by(Customer.name).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone or '',
        'debt': c.total_debt
    } for c in customers])

@app.route('/api/sales', methods=['POST'])
@login_required
def api_create_sale():
    """API endpoint to create a new sale"""
    data = request.get_json()
    
    if not data.get('items'):
        return jsonify({'error': 'لا توجد عناصر في البيع'}), 400
    
    # Validate stock availability
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'error': f'المنتج غير موجود'}), 400
        if product.stock_quantity < item['quantity']:
            return jsonify({'error': f'الكمية المطلوبة غير متوفرة للمنتج {product.name_ar}'}), 400
    
    # Get payment info
    payment_type = data.get('payment_type', 'cash')  # 'cash' or 'credit'
    customer_id = data.get('customer_id') if payment_type == 'credit' else None
    paid_amount = float(data.get('paid_amount', 0))
    total_amount = float(data['total_amount'])
    
    # Validate customer for credit sales
    if payment_type == 'credit' and not customer_id:
        return jsonify({'error': 'يجب اختيار عميل للبيع الآجل'}), 400
    
    # تحديد حالة الدفع
    if payment_type == 'cash':
        payment_status = 'paid'
        paid_amount = total_amount  # في البيع النقدي يكون المبلغ مدفوع بالكامل
    else:
        if paid_amount >= total_amount:
            payment_status = 'paid'
        elif paid_amount > 0:
            payment_status = 'partial'
        else:
            payment_status = 'unpaid'
    
    # Create sale
    sale = Sale(
        total_amount=total_amount,
        user_id=current_user.id,
        customer_id=customer_id,
        payment_type=payment_type,
        payment_status=payment_status,
        notes=data.get('notes', '')
    )
    db.session.add(sale)
    db.session.flush()  # Get sale.id
    
    # Create sale items and update stock
    for item in data['items']:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            total_price=item['total_price']
        )
        db.session.add(sale_item)
        
        # Update product stock
        product = Product.query.get(item['product_id'])
        product.stock_quantity -= item['quantity']
    
    # إضافة دفعة في حالة البيع الآجل مع دفعة مقدمة
    if payment_type == 'credit' and paid_amount > 0:
        payment = Payment(
            sale_id=sale.id,
            amount=paid_amount,
            payment_method='نقدي',
            notes='دفعة مقدمة مع البيع',
            user_id=current_user.id
        )
        db.session.add(payment)
    
    db.session.commit()
    
    # تحديد الرسالة
    if payment_type == 'cash':
        message = 'تم تسجيل البيع نقداً بنجاح'
    elif payment_status == 'paid':
        message = 'تم تسجيل البيع وتم دفع المبلغ كاملاً'
    elif payment_status == 'partial':
        remaining = total_amount - paid_amount
        message = f'تم تسجيل البيع مع دفعة مقدمة {paid_amount:.2f} ج.م - المتبقي: {remaining:.2f} ج.م'
    else:
        message = 'تم تسجيل البيع آجلاً'
    
    return jsonify({
        'success': True,
        'sale_id': sale.id,
        'message': message,
        'payment_status': payment_status,
        'paid_amount': paid_amount,
        'remaining_amount': total_amount - paid_amount
    })

@app.route('/api/sales/<int:sale_id>')
@login_required
def api_sale_details(sale_id):
    """API endpoint to get sale details"""
    sale = Sale.query.get_or_404(sale_id)
    
    # Check permissions - sellers can only view their own sales, admins can view all
    if not current_user.is_admin() and sale.user_id != current_user.id:
        return jsonify({'error': 'ليس لديك صلاحية لعرض هذا البيع'}), 403
    
    # Get sale items
    sale_items = []
    for item in sale.sale_items:
        sale_items.append({
            'product_name': item.product.name_ar,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'total_price': float(item.total_price),
            'unit_type': item.product.unit_type
        })
    
    return jsonify({
        'id': sale.id,
        'sale_date': sale.sale_date.isoformat(),
        'total_amount': float(sale.total_amount),
        'notes': sale.notes,
        'user_name': sale.user.username,
        'user_role': sale.user.role,
        'items': sale_items
    })

# New API endpoints for data export
@app.route('/api/export/products')
@login_required
def api_export_products():
    if current_user.role not in ['admin', 'seller']:
        abort(403)
    
    products = Product.query.join(Category).all()
    return jsonify([{
        'id': p.id,
        'name': p.name_ar,
        'category': p.category.name_ar if p.category else 'غير محدد',
        'price': float(p.price),
        'stock': float(p.stock_quantity),
        'unit_type': p.unit_type,
        'is_whole_unit': p.is_whole_unit,
        'created_date': p.id  # Using id as proxy for creation order
    } for p in products])

@app.route('/api/export/sales')
@login_required
def api_export_sales():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Sale.query.join(User)
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date + ' 23:59:59')
    
    # Filter by user role
    if current_user.role != 'admin':
        query = query.filter(Sale.user_id == current_user.id)
    
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    sales_data = []
    for sale in sales:
        for item in sale.sale_items:
            sales_data.append({
                'sale_id': sale.id,
                'sale_date': sale.sale_date.strftime('%Y-%m-%d'),
                'sale_time': sale.sale_date.strftime('%H:%M:%S'),
                'seller_name': sale.user.username,
                'seller_role': sale.user.role,
                'product_name': item.product.name_ar,
                'product_category': item.product.category.name_ar if item.product.category else 'غير محدد',
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'unit_type': item.product.unit_type,
                'sale_total': float(sale.total_amount),
                'notes': sale.notes or ''
            })
    
    return jsonify(sales_data)

@app.route('/api/quick-payment', methods=['POST'])
@login_required
def api_quick_payment():
    """API endpoint for quick debt payment"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        amount = float(data.get('amount', 0))
        payment_method = data.get('payment_method', 'نقدي')
        notes = data.get('notes', '')
        
        if not customer_id or amount <= 0:
            return jsonify({'success': False, 'message': 'بيانات غير صحيحة'}), 400
        
        # Get customer
        customer = Customer.query.get_or_404(customer_id)
        
        # Get unpaid sales for this customer
        unpaid_sales = Sale.query.filter(
            Sale.customer_id == customer_id,
            Sale.payment_status.in_(['unpaid', 'partial'])
        ).order_by(Sale.sale_date.asc()).all()
        
        if not unpaid_sales:
            return jsonify({'success': False, 'message': 'لا توجد ديون لهذا العميل'}), 400
        
        remaining_amount = amount
        payments_made = []
        
        # Distribute payment across unpaid sales
        for sale in unpaid_sales:
            if remaining_amount <= 0:
                break
            
            sale_remaining = sale.remaining_amount
            if sale_remaining <= 0:
                continue
            
            payment_amount = min(remaining_amount, sale_remaining)
            
            # Create payment record
            payment = Payment(
                sale_id=sale.id,
                amount=payment_amount,
                payment_method=payment_method,
                notes=f"{notes} - تسديد سريع",
                user_id=current_user.id
            )
            
            db.session.add(payment)
            
            # Update sale payment status
            sale_total_paid = sale.paid_amount + payment_amount
            if sale_total_paid >= sale.total_amount:
                sale.payment_status = 'paid'
            else:
                sale.payment_status = 'partial'
            
            payments_made.append({
                'sale_id': sale.id,
                'amount': payment_amount
            })
            
            remaining_amount -= payment_amount
        
        db.session.commit()
        
        message = f"تم تسديد {amount:.2f} ج.م بنجاح"
        if remaining_amount > 0:
            message += f" (متبقي {remaining_amount:.2f} ج.م كرصيد)"
        
        return jsonify({
            'success': True,
            'message': message,
            'payments_made': payments_made
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export/inventory')
@login_required
def api_export_inventory():
    if current_user.role not in ['admin', 'seller']:
        abort(403)
    
    # Get products with stock status
    products = Product.query.join(Category).all()
    
    inventory_data = []
    for product in products:
        # Calculate stock status
        if product.stock_quantity <= 0:
            status = 'نفدت الكمية'
            status_en = 'Out of Stock'
        elif product.stock_quantity <= 10:
            status = 'كمية قليلة'
            status_en = 'Low Stock'
        else:
            status = 'متوفر'
            status_en = 'Available'
        
        # Calculate total sales for this product
        total_sold = db.session.query(db.func.sum(SaleItem.quantity)).filter(
            SaleItem.product_id == product.id
        ).scalar() or 0
        
        total_revenue = db.session.query(db.func.sum(SaleItem.total_price)).filter(
            SaleItem.product_id == product.id
        ).scalar() or 0
        
        inventory_data.append({
            'product_id': product.id,
            'product_name': product.name_ar,
            'category': product.category.name_ar if product.category else 'غير محدد',
            'current_stock': float(product.stock_quantity),
            'unit_type': product.unit_type,
            'unit_price': float(product.price),
            'stock_value': float(product.stock_quantity * product.price),
            'is_whole_unit': product.is_whole_unit,
            'status_ar': status,
            'status_en': status_en,
            'total_sold': float(total_sold),
            'total_revenue': float(total_revenue)
        })
    
    return jsonify(inventory_data)

@app.route('/reports')
@login_required
def reports():
    if current_user.role not in ['admin', 'seller']:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Sales in date range
    sales = Sale.query.filter(
        and_(func.date(Sale.sale_date) >= start_dt,
             func.date(Sale.sale_date) <= end_dt)
    ).all()
    
    total_revenue = sum(sale.total_amount for sale in sales)
    total_sales_count = len(sales)
    
    # حساب الأرباح والتكاليف
    total_profit = sum(sale.total_profit for sale in sales)
    total_cost = sum(sale.cost_amount for sale in sales)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # حساب المصاريف في نفس الفترة
    expenses = Expense.query.filter(
        and_(func.date(Expense.expense_date) >= start_dt,
             func.date(Expense.expense_date) <= end_dt)
    ).all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    # صافي الربح = إجمالي الأرباح - المصاريف
    net_profit = total_profit - total_expenses
    
    # تصنيف المصاريف حسب النوع
    expenses_by_type = {}
    for expense in expenses:
        expense_type = expense.expense_type_ar
        if expense_type not in expenses_by_type:
            expenses_by_type[expense_type] = 0
        expenses_by_type[expense_type] += expense.amount
    
    # Top products in date range
    top_products = db.session.query(
        Product.name_ar,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.total_price).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        and_(func.date(Sale.sale_date) >= start_dt,
             func.date(Sale.sale_date) <= end_dt)
    ).group_by(Product.id).order_by(desc('total_sold')).all()
    
    # Daily sales chart data
    daily_sales_raw = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        and_(func.date(Sale.sale_date) >= start_dt,
             func.date(Sale.sale_date) <= end_dt)
    ).group_by(func.date(Sale.sale_date)).order_by('date').all()
    
    # Convert to JSON-serializable format
    daily_sales = []
    for row in daily_sales_raw:
        date_str = row.date if isinstance(row.date, str) else row.date.strftime('%Y-%m-%d')
        daily_sales.append({'date': date_str, 'total': float(row.total or 0)})
    
    # Debt-related statistics
    # Total debts across all customers
    total_debts = sum(customer.total_debt for customer in Customer.query.all())
    
    # Count customers with debts
    customers_with_debts = Customer.query.filter(
        Customer.id.in_(
            db.session.query(Sale.customer_id).filter(
                Sale.payment_status.in_(['unpaid', 'partial'])
            ).distinct()
        )
    ).count()
    
    # Credit sales in date range
    credit_sales = Sale.query.filter(
        and_(func.date(Sale.sale_date) >= start_dt,
             func.date(Sale.sale_date) <= end_dt,
             Sale.payment_type == 'credit')
    ).all()
    total_credit_sales = len(credit_sales)
    
    # Total payments in date range
    total_payments = db.session.query(func.sum(Payment.amount)).join(Sale).filter(
        and_(func.date(Payment.payment_date) >= start_dt,
             func.date(Payment.payment_date) <= end_dt)
    ).scalar() or 0
    
    # Payment rate calculation
    total_credit_amount = sum(sale.total_amount for sale in credit_sales)
    payment_rate = (total_payments / total_credit_amount * 100) if total_credit_amount > 0 else 0
    
    # Top debtors
    top_debtors = []
    customers_with_debt = Customer.query.join(Sale).filter(
        Sale.payment_status.in_(['unpaid', 'partial'])
    ).distinct().all()
    
    for customer in customers_with_debt:
        if customer.total_debt > 0:
            unpaid_sales_count = Sale.query.filter(
                Sale.customer_id == customer.id,
                Sale.payment_status.in_(['unpaid', 'partial'])
            ).count()
            
            last_sale = Sale.query.filter(
                Sale.customer_id == customer.id
            ).order_by(Sale.sale_date.desc()).first()
            
            top_debtors.append((
                customer,
                customer.total_debt,
                unpaid_sales_count,
                last_sale.sale_date if last_sale else None
            ))
    
    # Sort by debt amount (highest first) and take top 10
    top_debtors.sort(key=lambda x: x[1], reverse=True)
    top_debtors = top_debtors[:10]
    
    return render_template('reports/index.html',
                         start_date=start_date,
                         end_date=end_date,
                         total_revenue=total_revenue,
                         total_sales_count=total_sales_count,
                         top_products=top_products,
                         daily_sales=daily_sales,
                         # Profit and expense data
                         total_profit=total_profit,
                         total_cost=total_cost,
                         profit_margin=profit_margin,
                         total_expenses=total_expenses,
                         net_profit=net_profit,
                         expenses_by_type=expenses_by_type,
                         # Debt-related data
                         total_debts=total_debts,
                         customers_with_debts=customers_with_debts,
                         total_credit_sales=total_credit_sales,
                         total_payments=total_payments,
                         payment_rate=payment_rate,
                         top_debtors=top_debtors)

# إدارة المصاريف
@app.route('/expenses')
@login_required
def expenses():
    """عرض قائمة المصاريف"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    expense_type = request.args.get('type', '', type=str)
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    
    query = Expense.query
    
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    
    if start_date:
        query = query.filter(func.date(Expense.expense_date) >= start_date)
    
    if end_date:
        query = query.filter(func.date(Expense.expense_date) <= end_date)
    
    expenses = query.order_by(desc(Expense.expense_date)).paginate(
        page=page, per_page=20, error_out=False)
    
    # حساب إجمالي المصاريف
    total_expenses = query.with_entities(func.sum(Expense.amount)).scalar() or 0
    
    return render_template('expenses/list.html', 
                         expenses=expenses, 
                         total_expenses=total_expenses,
                         expense_type=expense_type,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """إضافة مصروف جديد"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            description=form.description.data,
            amount=form.amount.data,
            expense_type=form.expense_type.data,
            category=form.category.data,
            expense_date=form.expense_date.data or datetime.utcnow(),
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('تم إضافة المصروف بنجاح', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expenses/add.html', form=form, title='إضافة مصروف جديد')

@app.route('/expenses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    """تعديل مصروف"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('expenses'))
    
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)
    
    if form.validate_on_submit():
        expense.description = form.description.data
        expense.amount = form.amount.data
        expense.expense_type = form.expense_type.data
        expense.category = form.category.data
        expense.expense_date = form.expense_date.data or expense.expense_date
        expense.notes = form.notes.data
        db.session.commit()
        flash('تم تحديث المصروف بنجاح', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expenses/edit.html', form=form, title='تعديل المصروف')

@app.route('/expenses/<int:id>/delete', methods=['POST'])
@login_required
def delete_expense(id):
    """حذف مصروف"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية لحذف المصاريف', 'error')
        return redirect(url_for('expenses'))
    
    expense = Expense.query.get_or_404(id)
    description = expense.description
    db.session.delete(expense)
    db.session.commit()
    flash(f'تم حذف المصروف "{description}" بنجاح', 'success')
    return redirect(url_for('expenses'))

@app.route('/test-export')
@login_required
def test_export():
    """صفحة اختبار وظائف التصدير"""
    return send_from_directory('.', 'test_export.html')

@app.route('/stock/update', methods=['GET', 'POST'])
@login_required
def update_stock():
    if not current_user.is_admin():
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    form = StockUpdateForm()
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        product.stock_quantity += form.quantity.data
        db.session.commit()
        flash(f'تم تحديث مخزون {product.name_ar} بنجاح', 'success')
        return redirect(url_for('products'))
    
    return render_template('stock/update.html', form=form)

def create_sample_data():
    """Create sample data for testing"""
    # Create default system admin user (hidden)
    system_admin = User.query.filter_by(username='araby').first()
    if not system_admin:
        system_admin = User(username='araby', role='admin', is_system=True)
        system_admin.set_password('92321066')
        db.session.add(system_admin)
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create seller user
    seller = User.query.filter_by(username='seller').first()
    if not seller:
        seller = User(username='seller', role='seller')
        seller.set_password('seller123')
        db.session.add(seller)
    
    # Create comprehensive categories for bookstore and school supplies
    if Category.query.count() == 0:
        categories = [
            # كتب ومراجع
            Category(name_ar='كتب أدبية وروايات', description_ar='الروايات والقصص والشعر والأدب العربي والعالمي'),
            Category(name_ar='كتب علمية وتقنية', description_ar='الكتب العلمية والتقنية والهندسية والطبية'),
            Category(name_ar='كتب دراسية ومناهج', description_ar='المناهج الدراسية والكتب الجامعية والمدرسية'),
            Category(name_ar='كتب الأطفال', description_ar='القصص والكتب التعليمية للأطفال والرسوم المتحركة'),
            Category(name_ar='كتب دينية وإسلامية', description_ar='القرآن الكريم والتفاسير والكتب الدينية'),
            Category(name_ar='مجلات وصحف', description_ar='المجلات العلمية والثقافية والصحف اليومية'),
            
            # أدوات الكتابة
            Category(name_ar='أقلام حبر وجاف', description_ar='أقلام الحبر الجاف والسائل بألوان مختلفة'),
            Category(name_ar='أقلام رصاص وملونة', description_ar='أقلام الرصاص العادية والملونة وأقلام التلوين'),
            Category(name_ar='أقلام ماركر وتحديد', description_ar='أقلام الماركر والهايلايتر وأقلام التحديد'),
            Category(name_ar='محايات وبراية', description_ar='المحايات البيضاء والملونة وبرايات الأقلام'),
            
            # دفاتر وكشاكيل
            Category(name_ar='كشاكيل ودفاتر خانات', description_ar='الكشاكيل المخططة والمربعة وذات الخانات'),
            Category(name_ar='دفاتر مسطرة وسادة', description_ar='الدفاتر المسطرة والسادة للكتابة'),
            Category(name_ar='دفاتر رسم وفنية', description_ar='دفاتر الرسم والأوراق الفنية للرسم والتلوين'),
            Category(name_ar='بلوكات وأوراق لاصقة', description_ar='البلوكات والملاحظات اللاصقة بأحجام مختلفة'),
            
            # مجلدات وحفظ
            Category(name_ar='مجلدات وحافظات', description_ar='المجلدات البلاستيكية والكرتونية لحفظ الأوراق'),
            Category(name_ar='أكياس وحافظات شفافة', description_ar='الأكياس الشفافة وحافظات الأوراق البلاستيكية'),
            Category(name_ar='ملفات ومنظمات', description_ar='الملفات المعدنية والبلاستيكية ومنظمات المكتب'),
            
            # أدوات هندسية ورياضية
            Category(name_ar='مساطر وأدوات قياس', description_ar='المساطر والزوايا وأدوات القياس الهندسية'),
            Category(name_ar='برجل وكوسات هندسية', description_ar='البرجل والكوسات وأدوات الرسم الهندسي'),
            Category(name_ar='آلات حاسبة', description_ar='الآلات الحاسبة العلمية والعادية'),
            Category(name_ar='أدوات رياضية تعليمية', description_ar='النماذج الهندسية والأدوات التعليمية للرياضيات'),
            
            # أدوات فنية وإبداعية
            Category(name_ar='ألوان وطلاء', description_ar='الألوان المائية والزيتية وألوان الأطفال'),
            Category(name_ar='فرش ولوازم الرسم', description_ar='فرش الرسم وإسفنج التلوين واللوازم الفنية'),
            Category(name_ar='ورق ملون وكارتون', description_ar='الأوراق الملونة والكارتون المقوى للأعمال الفنية'),
            Category(name_ar='لاصق وصمغ', description_ar='أنواع اللاصق والصمغ والشريط اللاصق'),
            
            # أدوات مكتبية عامة
            Category(name_ar='مقصات وقطاعات', description_ar='المقصات بأحجام مختلفة وقطاعات الورق'),
            Category(name_ar='دباسة وخرامة', description_ar='الدباسات والخرامات ولوازم التثبيت'),
            Category(name_ar='مشابك ودبابيس', description_ar='مشابك الورق والدبابيس وأدوات التثبيت'),
            Category(name_ar='لوازم المكتب المختلفة', description_ar='منظمات المكتب وحوامل الأقلام والأدوات المكتبية'),
            
            # حقائب وأدوات حمل
            Category(name_ar='حقائب مدرسية', description_ar='الحقائب المدرسية بأحجام وأشكال مختلفة'),
            Category(name_ar='مقلمات وحافظات أقلام', description_ar='المقلمات وحافظات الأقلام والأدوات'),
            Category(name_ar='شنط لابتوب ووثائق', description_ar='حقائب اللابتوب وحافظات الوثائق والملفات'),
            
            # لوازم إلكترونية ومكتبية
            Category(name_ar='بطاريات وشواحن', description_ar='البطاريات والشواحن للأجهزة الإلكترونية'),
            Category(name_ar='فلاش ميموري وأقراص', description_ar='فلاش ميموري وأقراص التخزين والـ CD/DVD'),
            Category(name_ar='لوازم الكمبيوتر', description_ar='ماوس وكيبورد وإكسسوارات الكمبيوتر'),
            
            # متنوعات
            Category(name_ar='هدايا ولعب تعليمية', description_ar='الهدايا والألعاب التعليمية والترفيهية'),
            Category(name_ar='لوازم التغليف', description_ar='أكياس الهدايا وورق التغليف والشرائط'),
            Category(name_ar='منتجات موسمية', description_ar='المنتجات الخاصة بالمواسم والمناسبات المختلفة'),
        ]
        
        for category in categories:
            db.session.add(category)
    
    db.session.commit()
    
    # Create diverse sample products for different categories
    if Product.query.count() == 0:
        products = [
            # كتب أدبية وروايات
            Product(name_ar='رواية مئة عام من العزلة', category_id=1, wholesale_price=65.00, retail_price=85.00, price=85.00, stock_quantity=25, min_stock_threshold=5, description_ar='رواية للكاتب غابرييل غارسيا ماركيز'),
            Product(name_ar='ديوان محمود درويش', category_id=1, wholesale_price=35.00, retail_price=45.00, price=45.00, stock_quantity=30, min_stock_threshold=8, description_ar='مجموعة قصائد للشاعر محمود درويش'),
            Product(name_ar='رواية مدن الملح', category_id=1, wholesale_price=75.00, retail_price=95.00, price=95.00, stock_quantity=20, min_stock_threshold=5, description_ar='رواية عبد الرحمن منيف'),
            
            # كتب علمية وتقنية
            Product(name_ar='كتاب البرمجة بالبايثون', category_id=2, wholesale_price=95.00, retail_price=120.00, price=120.00, stock_quantity=15, min_stock_threshold=3, description_ar='دليل شامل لتعلم البرمجة'),
            Product(name_ar='أساسيات الرياضيات', category_id=2, wholesale_price=60.00, retail_price=80.00, price=80.00, stock_quantity=35, min_stock_threshold=10, description_ar='كتاب تعليمي في الرياضيات'),
            
            # كتب دراسية ومناهج
            Product(name_ar='منهج الرياضيات - الصف الثالث الثانوي', category_id=3, wholesale_price=42.00, retail_price=55.00, price=55.00, stock_quantity=50, min_stock_threshold=15, description_ar='منهج وزارة التربية والتعليم'),
            Product(name_ar='كتاب الفيزياء - الصف الثاني الثانوي', category_id=3, wholesale_price=36.00, retail_price=48.00, price=48.00, stock_quantity=40, min_stock_threshold=12, description_ar='منهج معتمد'),
            
            # أقلام حبر وجاف
            Product(name_ar='قلم حبر جاف أزرق', category_id=7, wholesale_price=2.50, retail_price=3.50, price=3.50, stock_quantity=200, min_stock_threshold=50, unit_type='جزئي', unit_description='قلم حبر جاف لون أزرق'),
            Product(name_ar='علبة أقلام حبر ملونة (12 قلم)', category_id=7, wholesale_price=25.00, retail_price=35.00, price=35.00, stock_quantity=80, min_stock_threshold=20, description_ar='مجموعة أقلام ملونة'),
            Product(name_ar='قلم حبر أحمر', category_id=7, wholesale_price=2.50, retail_price=3.50, price=3.50, stock_quantity=150, min_stock_threshold=40, unit_type='جزئي', unit_description='قلم'),
            Product(name_ar='قلم حبر أسود', category_id=7, wholesale_price=2.50, retail_price=3.50, price=3.50, stock_quantity=180, min_stock_threshold=45, unit_type='جزئي', unit_description='قلم'),
            
            # أقلام رصاص وملونة
            Product(name_ar='قلم رصاص HB', category_id=8, price=2.00, stock_quantity=250, min_stock_threshold=60, unit_type='جزئي', unit_description='قلم'),
            Product(name_ar='علبة أقلام ملونة خشبية (24 لون)', category_id=8, price=45.00, stock_quantity=60, min_stock_threshold=15, description_ar='أقلام تلوين خشبية عالية الجودة'),
            Product(name_ar='قلم رصاص 2B للرسم', category_id=8, price=4.00, stock_quantity=100, min_stock_threshold=25, unit_type='جزئي', unit_description='قلم'),
            
            # كشاكيل ودفاتر
            Product(name_ar='كشكول 100 ورقة مخطط', category_id=11, price=15.00, stock_quantity=120, min_stock_threshold=30, description_ar='كشكول مخطط للكتابة'),
            Product(name_ar='كشكول 200 ورقة مربعات', category_id=11, price=25.00, stock_quantity=90, min_stock_threshold=25, description_ar='كشكول مربعات للرياضيات'),
            Product(name_ar='دفتر 48 ورقة سادة', category_id=12, price=8.00, stock_quantity=200, min_stock_threshold=50, description_ar='دفتر سادة للكتابة الحرة'),
            Product(name_ar='كشكول سبايرال A4', category_id=11, price=28.00, stock_quantity=75, min_stock_threshold=20, description_ar='كشكول سبايرال حجم A4'),
            
            # محايات وبراية
            Product(name_ar='محاية بيضاء كبيرة', category_id=10, price=2.50, stock_quantity=300, min_stock_threshold=75, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='براية معدنية', category_id=10, price=5.00, stock_quantity=150, min_stock_threshold=35, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='محاية ملونة صغيرة', category_id=10, price=1.50, stock_quantity=400, min_stock_threshold=100, unit_type='جزئي', unit_description='قطعة'),
            
            # مجلدات وحافظات
            Product(name_ar='مجلد بلاستيكي A4', category_id=15, price=12.00, stock_quantity=80, min_stock_threshold=20, description_ar='مجلد شفاف لحفظ الأوراق'),
            Product(name_ar='حافظة أوراق شفافة (10 قطع)', category_id=16, price=8.00, stock_quantity=100, min_stock_threshold=25, description_ar='حافظات شفافة مثقبة'),
            Product(name_ar='مجلد كرتوني ملون', category_id=15, price=18.00, stock_quantity=60, min_stock_threshold=15, description_ar='مجلد كرتوني بألوان مختلفة'),
            
            # أدوات هندسية
            Product(name_ar='مسطرة 30 سم شفافة', category_id=18, price=8.00, stock_quantity=120, min_stock_threshold=30, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='مجموعة أدوات هندسية (برجل + مسطرة + زاوية)', category_id=19, price=35.00, stock_quantity=40, min_stock_threshold=10, description_ar='مجموعة كاملة للرسم الهندسي'),
            Product(name_ar='آلة حاسبة علمية', category_id=20, price=85.00, stock_quantity=25, min_stock_threshold=5, description_ar='آلة حاسبة للطلاب والمهندسين'),
            
            # ألوان وطلاء
            Product(name_ar='علبة ألوان مائية (12 لون)', category_id=22, price=25.00, stock_quantity=50, min_stock_threshold=12, description_ar='ألوان مائية للرسم والفن'),
            Product(name_ar='ألوان فلوماستر (18 لون)', category_id=22, price=30.00, stock_quantity=70, min_stock_threshold=18, description_ar='أقلام ألوان فلوماستر'),
            
            # أدوات مكتبية
            Product(name_ar='مقص متوسط الحجم', category_id=26, price=12.00, stock_quantity=90, min_stock_threshold=20, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='دباسة صغيرة + علبة دبابيس', category_id=27, price=15.00, stock_quantity=60, min_stock_threshold=15, description_ar='دباسة مع دبابيس للاستعمال المكتبي'),
            Product(name_ar='صمغ أبيض 50 مل', category_id=25, price=6.00, stock_quantity=150, min_stock_threshold=35, unit_type='جزئي', unit_description='أنبوبة'),
            
            # حقائب ومقلمات
            Product(name_ar='حقيبة مدرسية متوسطة', category_id=30, price=95.00, stock_quantity=30, min_stock_threshold=8, description_ar='حقيبة مدرسية بجيوب متعددة'),
            Product(name_ar='مقلمة بسحاب', category_id=31, price=18.00, stock_quantity=85, min_stock_threshold=20, description_ar='مقلمة لحفظ الأقلام والأدوات'),
            Product(name_ar='حقيبة لابتوب 15 بوصة', category_id=32, price=150.00, stock_quantity=20, min_stock_threshold=5, description_ar='حقيبة واقية للابتوب'),
            
            # منتجات إلكترونية
            Product(name_ar='فلاش ميموري 16 جيجا', category_id=34, price=45.00, stock_quantity=40, min_stock_threshold=10, unit_type='جزئي', unit_description='قطعة'),
            Product(name_ar='بطاريات AA (4 قطع)', category_id=33, price=12.00, stock_quantity=100, min_stock_threshold=25, description_ar='بطاريات قلوية عالية الجودة'),
            
            # هدايا ومتنوعات
            Product(name_ar='لعبة تعليمية للأطفال', category_id=36, price=35.00, stock_quantity=25, min_stock_threshold=5, description_ar='لعبة تعليمية تفاعلية'),
            Product(name_ar='كيس هدية ملون', category_id=37, price=3.00, stock_quantity=200, min_stock_threshold=50, unit_type='جزئي', unit_description='كيس'),
            
            # مجلات
            Product(name_ar='مجلة العلوم العدد الجديد', category_id=6, price=15.00, stock_quantity=35, min_stock_threshold=10, description_ar='مجلة شهرية علمية'),
            Product(name_ar='مجلة الأطفال المصورة', category_id=6, price=12.00, stock_quantity=50, min_stock_threshold=15, description_ar='مجلة أسبوعية للأطفال'),
        ]
        
        for product in products:
            db.session.add(product)
    
    db.session.commit()
    
    # Create sample customers
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
        
        db.session.commit()

@app.route('/simple-export-test')
@login_required
def simple_export_test():
    """صفحة اختبار بسيطة للتصدير"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>اختبار التصدير</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>اختبار وظيفة التصدير</h1>
        <button onclick="testExport()">اختبار تصدير Excel</button>
        <div id="result"></div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
        <script>
            function testExport() {
                console.log('Testing export...');
                document.getElementById('result').innerHTML = 'جاري الاختبار...';
                
                if (typeof XLSX === 'undefined') {
                    document.getElementById('result').innerHTML = 'خطأ: مكتبة Excel غير محملة';
                    return;
                }
                
                try {
                    const testData = [
                        ['اختبار التصدير'],
                        ['المنتج', 'الكمية', 'السعر'],
                        ['منتج تجريبي', 10, 100]
                    ];
                    
                    const wb = XLSX.utils.book_new();
                    const ws = XLSX.utils.aoa_to_sheet(testData);
                    XLSX.utils.book_append_sheet(wb, ws, 'اختبار');
                    
                    const fileName = 'test_export_' + new Date().getTime() + '.xlsx';
                    XLSX.writeFile(wb, fileName);
                    
                    document.getElementById('result').innerHTML = 'نجح التصدير! ✅';
                } catch (error) {
                    document.getElementById('result').innerHTML = 'فشل التصدير: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/debug-export')
def debug_export():
    """صفحة تشخيص مشاكل التصدير - بدون تسجيل دخول للتشخيص"""
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تشخيص مشكلة التصدير</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; }
            .step { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .success { border-left: 5px solid #28a745; }
            .error { border-left: 5px solid #dc3545; }
            .warning { border-left: 5px solid #ffc107; }
            button { 
                background: #007bff; color: white; border: none; 
                padding: 12px 24px; margin: 8px; 
                border-radius: 5px; cursor: pointer; font-size: 16px;
            }
            button:hover { background: #0056b3; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; max-height: 300px; }
            .result { margin-top: 15px; padding: 10px; border-radius: 5px; }
            h1 { color: #333; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 تشخيص مشكلة التصدير</h1>
            <p style="text-align: center; color: #666;">هذه الأداة ستساعدك في تحديد سبب عدم عمل التصدير</p>
            
            <div class="step">
                <h3>الخطوة 1: فحص المكتبات المطلوبة</h3>
                <button onclick="checkLibraries()">فحص المكتبات</button>
                <div id="libraries-result" class="result"></div>
            </div>
            
            <div class="step">
                <h3>الخطوة 2: اختبار تصدير Excel بسيط</h3>
                <button onclick="simpleExcelTest()">اختبار Excel</button>
                <div id="excel-result" class="result"></div>
            </div>
            
            <div class="step">
                <h3>الخطوة 3: اختبار تحميل ملف نصي</h3>
                <button onclick="simpleDownloadTest()">اختبار التحميل</button>
                <div id="download-result" class="result"></div>
            </div>
            
            <div class="step">
                <h3>الخطوة 4: معلومات المتصفح</h3>
                <button onclick="browserInfo()">معلومات المتصفح</button>
                <div id="browser-result" class="result"></div>
            </div>
            
            <div class="step">
                <h3>سجل العمليات والأخطاء</h3>
                <pre id="debug-log">انتظار بدء التشخيص...</pre>
                <button onclick="clearLog()">مسح السجل</button>
            </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
        
        <script>
            let logs = [];
            
            function addLog(message) {
                const time = new Date().toLocaleTimeString();
                const logEntry = `[${time}] ${message}`;
                logs.push(logEntry);
                document.getElementById("debug-log").textContent = logs.join("\\n");
                console.log(logEntry);
            }
            
            function clearLog() {
                logs = [];
                document.getElementById("debug-log").textContent = "تم مسح السجل...";
            }
            
            function setResult(elementId, content, type = "info") {
                const element = document.getElementById(elementId);
                element.innerHTML = content;
                element.className = `result ${type}`;
            }
            
            function checkLibraries() {
                addLog("🔍 بدء فحص المكتبات...");
                
                let results = "<h4>نتائج الفحص:</h4>";
                let allOk = true;
                
                if (typeof XLSX !== "undefined") {
                    results += "✅ مكتبة XLSX: محملة بنجاح<br>";
                    results += `📋 الإصدار: ${XLSX.version || "غير محدد"}<br>`;
                    addLog("✅ XLSX library loaded");
                } else {
                    results += "❌ مكتبة XLSX: غير محملة<br>";
                    allOk = false;
                    addLog("❌ XLSX library missing");
                }
                
                if (typeof Blob !== "undefined") {
                    results += "✅ Blob API: متوفر<br>";
                } else {
                    results += "❌ Blob API: غير متوفر<br>";
                    allOk = false;
                }
                
                if (typeof URL.createObjectURL === "function") {
                    results += "✅ URL API: متوفر<br>";
                } else {
                    results += "❌ URL API: غير متوفر<br>";
                    allOk = false;
                }
                
                const downloadSupported = "download" in document.createElement("a");
                if (downloadSupported) {
                    results += "✅ Download Attribute: مدعوم<br>";
                } else {
                    results += "❌ Download Attribute: غير مدعوم<br>";
                    allOk = false;
                }
                
                setResult("libraries-result", results, allOk ? "success" : "error");
                addLog(`📊 فحص المكتبات: ${allOk ? "نجح" : "فشل"}`);
            }
            
            function simpleExcelTest() {
                addLog("📊 بدء اختبار Excel...");
                
                if (typeof XLSX === "undefined") {
                    setResult("excel-result", "❌ لا يمكن الاختبار - مكتبة XLSX غير محملة", "error");
                    addLog("❌ Excel test failed - no XLSX");
                    return;
                }
                
                try {
                    addLog("📝 إنشاء بيانات اختبار...");
                    const data = [
                        ["تجربة التصدير"],
                        ["العنصر", "القيمة", "التاريخ"],
                        ["اختبار 1", 100, new Date().toLocaleDateString()],
                        ["اختبار 2", 200, new Date().toLocaleDateString()],
                        ["المجموع", 300, ""]
                    ];
                    
                    addLog("🔧 إنشاء ملف Excel...");
                    const wb = XLSX.utils.book_new();
                    const ws = XLSX.utils.aoa_to_sheet(data);
                    XLSX.utils.book_append_sheet(wb, ws, "اختبار");
                    
                    addLog("💾 محاولة حفظ الملف...");
                    const fileName = `excel_test_${Date.now()}.xlsx`;
                    
                    XLSX.writeFile(wb, fileName);
                    
                    setResult("excel-result", "✅ تم إنشاء ملف Excel بنجاح! تحقق من مجلد التحميل.", "success");
                    addLog("✅ Excel file created successfully");
                    
                } catch (error) {
                    setResult("excel-result", `❌ خطأ في إنشاء Excel: ${error.message}`, "error");
                    addLog(`❌ Excel error: ${error.message}`);
                    console.error("Excel Error Details:", error);
                }
            }
            
            function simpleDownloadTest() {
                addLog("⬇️ بدء اختبار التحميل...");
                
                try {
                    const content = "اختبار التحميل\\nهذا ملف نصي تجريبي\\nالوقت: " + new Date().toLocaleString();
                    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
                    const url = URL.createObjectURL(blob);
                    
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `download_test_${Date.now()}.txt`;
                    link.style.display = "none";
                    
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    URL.revokeObjectURL(url);
                    
                    setResult("download-result", "✅ تم اختبار التحميل! تحقق من مجلد التحميل.", "success");
                    addLog("✅ Download test completed");
                    
                } catch (error) {
                    setResult("download-result", `❌ خطأ في التحميل: ${error.message}`, "error");
                    addLog(`❌ Download error: ${error.message}`);
                }
            }
            
            function browserInfo() {
                addLog("🌐 جمع معلومات المتصفح...");
                
                let info = "<h4>معلومات المتصفح:</h4>";
                info += `<strong>المتصفح:</strong> ${navigator.userAgent}<br><br>`;
                info += `<strong>النظام:</strong> ${navigator.platform}<br>`;
                info += `<strong>اللغة:</strong> ${navigator.language}<br>`;
                info += `<strong>Cookies مفعلة:</strong> ${navigator.cookieEnabled ? "نعم" : "لا"}<br>`;
                
                info += "<br><h5>🔧 نصائح لحل المشكلة:</h5>";
                info += "• تأكد أن مجلد التحميل محدد بشكل صحيح<br>";
                info += "• تحقق من إعدادات حظر النوافذ المنبثقة<br>";
                info += "• جرب متصفح آخر للمقارنة<br>";
                info += "• تأكد أن الإنترنت متصل لتحميل المكتبات<br>";
                info += "• اضغط F12 وافحص تبويب Console للأخطاء<br>";
                
                setResult("browser-result", info, "info");
                addLog("📋 Browser info collected");
            }
            
            window.addEventListener("load", function() {
                addLog("🚀 تم تحميل صفحة التشخيص");
                setTimeout(() => {
                    addLog("🔄 بدء الفحص التلقائي...");
                    checkLibraries();
                }, 500);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/export/full-database')
@login_required
def api_export_full_database():
    if current_user.role not in ['admin', 'seller']:
        abort(403)
    from models import Product, Category, Customer, User, Sale, SaleItem, Payment, Expense
    from sqlalchemy import func, desc
    data = {}
    # ملخص التقرير
    total_revenue = db.session.query(func.sum(Sale.total_amount)).scalar() or 0
    total_sales_count = Sale.query.count()
    total_customers = Customer.query.count()
    total_products = Product.query.count()
    total_debts = sum(getattr(c, 'total_debt', 0) for c in Customer.query.all())
    data['report_summary'] = [{
        'إجمالي المبيعات': total_revenue,
        'عدد عمليات البيع': total_sales_count,
        'عدد العملاء': total_customers,
        'عدد المنتجات': total_products,
        'إجمالي الديون': total_debts
    }]
    # المبيعات
    data['sales'] = [
        {
            'id': s.id,
            'sale_date': str(s.sale_date),
            'total_amount': float(s.total_amount),
            'user_id': s.user_id,
            'customer_id': getattr(s, 'customer_id', None),
            'payment_type': getattr(s, 'payment_type', ''),
            'payment_status': getattr(s, 'payment_status', ''),
            'notes': s.notes
        } for s in Sale.query.all()
    ]
    # تفاصيل المبيعات
    data['sale_items'] = [
        {
            'id': si.id,
            'sale_id': si.sale_id,
            'product_id': si.product_id,
            'quantity': float(si.quantity),
            'unit_price': float(si.unit_price),
            'total_price': float(si.total_price)
        } for si in SaleItem.query.all()
    ]
    # العملاء
    data['customers'] = [
        {
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'debt': getattr(c, 'total_debt', 0)
        } for c in Customer.query.all()
    ]
    # الديون (العملاء مع الديون غير المسددة)
    debts = []
    for c in Customer.query.all():
        if getattr(c, 'total_debt', 0) > 0:
            # آخر تاريخ بيع غير مسدد
            last_unpaid_sale = Sale.query.filter_by(customer_id=c.id).filter(Sale.payment_status.in_(['unpaid', 'partial'])).order_by(desc(Sale.sale_date)).first()
            last_sale_date = str(last_unpaid_sale.sale_date) if last_unpaid_sale else ''
            debts.append({
                'اسم العميل': c.name,
                'رقم الهاتف': c.phone,
                'إجمالي الدين': getattr(c, 'total_debt', 0),
                'آخر بيع غير مسدد': last_sale_date
            })
    data['debts'] = debts
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 