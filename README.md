# نظام إدارة مكتبة Norko

نظام متكامل لإدارة المكتبات، مبني باستخدام Flask مع تحسينات الأداء والحجم.

## المتطلبات

- Python 3.8+
- Flask 2.3.3
- SQLAlchemy
- Flask-Login
- Flask-WTF

## التحسينات الجديدة

✅ **تحسين الأداء والحجم:**

- إزالة مكتبة pandas الثقيلة (توفير ~50MB)
- استخدام Chart.js بدلاً من plotly للرسوم البيانية
- تحسين إعدادات قاعدة البيانات للإنتاج
- دعم PostgreSQL و SQLite

✅ **إعدادات متقدمة:**

- إعدادات منفصلة للتطوير والإنتاج
- دعم PythonAnywhere المحسن
- إعدادات الأمان المحسنة
- تحسين إدارة الجلسات

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
APP_NAME=نظام إدارة مكتبة Norko
APP_VERSION=1.0.0
```

5. قم بتشغيل التطبيق:

```bash
python app.py
```

## الاستضافة

### Railway/Heroku (PostgreSQL)

1. قم بإنشاء حساب على Railway أو Heroku
2. قم بربط المشروع بـ Git
3. سيتم التعرف على PostgreSQL تلقائياً
4. المتغيرات المطلوبة:
   - `SECRET_KEY`: مفتاح سري قوي
   - `DATABASE_URL`: سيتم تعيينه تلقائياً

### PythonAnywhere

1. قم بإنشاء حساب على PythonAnywhere
2. قم بإنشاء تطبيق ويب جديد
3. قم برفع الملفات عبر Git أو SFTP
4. قم بتحديث `config.py` واستبدال `yourusername` باسم المستخدم الخاص بك
5. قم بتعيين المسار إلى `wsgi.py`

### الاستضافة المحلية

```bash
# للتطوير
export FLASK_ENV=development
python app.py

# للإنتاج
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## الميزات

- 🔐 تسجيل الدخول وإدارة المستخدمين
- 📚 إدارة الكتب والمخزون المتقدمة
- 💰 إدارة المبيعات والفواتير
- 👥 إدارة العملاء والديون
- 📊 التقارير والإحصائيات التفاعلية
- 📈 رسوم بيانية خفيفة باستخدام Chart.js
- 📱 واجهة مستخدم متجاوبة
- 🔄 تصدير البيانات إلى Excel
- ⚡ أداء محسن وحجم أصغر

## تحسينات الأداء

- **حجم أصغر**: إزالة pandas وplotly يوفر ~50MB
- **سرعة أكبر**: استخدام Chart.js للرسوم البيانية
- **ذاكرة أقل**: تحسين إعدادات قاعدة البيانات
- **استجابة أفضل**: تحسين الاستعلامات والفهرسة

## المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد
3. قم بإجراء التغييرات
4. قم بعمل Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT.
