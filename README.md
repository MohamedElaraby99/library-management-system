# نظام إدارة المكتبة

نظام متكامل لإدارة المكتبات، مبني باستخدام Flask.

## المتطلبات

- Python 3.11+
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF

## التثبيت

1. قم بنسخ المشروع:

```bash
git clone [رابط المشروع]
cd library-system
```

2. قم بإنشاء بيئة افتراضية:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. قم بتثبيت المتطلبات:

```bash
pip install -r requirements.txt
```

4. قم بإنشاء ملف `.env`:

```
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///library.db
```

5. قم بتشغيل التطبيق:

```bash
python wsgi.py
```

## الاستضافة

### Heroku

1. قم بإنشاء حساب على Heroku
2. قم بتثبيت Heroku CLI
3. قم بتسجيل الدخول:

```bash
heroku login
```

4. قم بإنشاء تطبيق جديد:

```bash
heroku create your-app-name
```

5. قم برفع المشروع:

```bash
git push heroku main
```

### PythonAnywhere

1. قم بإنشاء حساب على PythonAnywhere
2. قم بإنشاء تطبيق ويب جديد
3. قم برفع الملفات عبر Git أو SFTP
4. قم بتعيين المسار إلى `wsgi.py`
5. قم بتشغيل التطبيق

## الميزات

- تسجيل الدخول وإدارة المستخدمين
- إدارة الكتب والمخزون
- إدارة المبيعات
- إدارة العملاء
- التقارير والإحصائيات

## المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد
3. قم بإجراء التغييرات
4. قم بعمل Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT.
