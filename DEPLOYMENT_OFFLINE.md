# تعليمات نشر الوظائف غير المتصلة - نظام Norko Store

## 📋 متطلبات النشر

### 1. متطلبات الخادم

- **Python 3.8+** مع Flask
- **HTTPS مطلوب** لـ Service Workers (في الإنتاج)
- **مساحة تخزين كافية** للملفات الثابتة
- **RAM إضافية** لتعامل مع IndexedDB والتخزين المؤقت

### 2. متطلبات المتصفح (للمستخدمين)

- **Chrome 45+**, **Firefox 44+**, **Safari 11.1+**, **Edge 17+**
- دعم **Service Workers**
- دعم **IndexedDB**
- دعم **ES6 Promises**

## 🚀 خطوات النشر

### الخطوة 1: فحص الملفات المطلوبة

تأكد من وجود جميع ملفات الوظائف غير المتصلة:

```bash
# فحص ملفات JavaScript
ls -la static/js/
# يجب أن تجد:
# - service-worker.js
# - db-manager.js
# - sync-manager.js
# - offline-handler.js

# فحص ملفات القوالب
ls -la templates/
# يجب أن تجد:
# - offline.html
# - offline-demo.html
```

### الخطوة 2: تشغيل اختبار الوظائف

```bash
# تشغيل اختبار شامل
python test_offline.py

# أو تشغيل مع عنوان خادم مخصص
python test_offline.py http://your-server.com:5000
```

### الخطوة 3: تكوين HTTPS (ضروري للإنتاج)

Service Workers تتطلب HTTPS في الإنتاج. استخدم:

#### أ) مع nginx (موصى به):

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # إعدادات خاصة للـ Service Worker
    location /static/js/service-worker.js {
        proxy_pass http://127.0.0.1:5000;
        add_header Service-Worker-Allowed /;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

#### ب) مع Let's Encrypt:

```bash
# تثبيت certbot
sudo apt install certbot python3-certbot-nginx

# الحصول على شهادة SSL
sudo certbot --nginx -d your-domain.com

# التجديد التلقائي
sudo crontab -e
# أضف: 0 12 * * * /usr/bin/certbot renew --quiet
```

### الخطوة 4: تكوين Flask للإنتاج

تأكد من إعدادات الإنتاج في `config.py`:

```python
class ProductionConfig(Config):
    DEBUG = False

    # تأكد من تمكين HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # إعدادات Service Worker
    SEND_FILE_MAX_AGE_DEFAULT = 3600  # ساعة واحدة للملفات الثابتة

    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/norko_store'
```

### الخطوة 5: تحديث متغيرات البيئة

```bash
# .env
FLASK_CONFIG=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/norko_store

# Service Worker settings
SW_CACHE_VERSION=1.2.0
SW_DEBUG=false
```

### الخطوة 6: نشر مع Gunicorn

```bash
# تثبيت gunicorn
pip install gunicorn

# تشغيل الخادم
gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app

# أو مع ملف تكوين
gunicorn -c gunicorn.conf.py wsgi:app
```

ملف `gunicorn.conf.py`:

```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

### الخطوة 7: إعداد Systemd Service

ملف `/etc/systemd/system/norko-store.service`:

```ini
[Unit]
Description=Norko Store Flask App
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/norko-store
Environment=PATH=/var/www/norko-store/venv/bin
ExecStart=/var/www/norko-store/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

تفعيل الخدمة:

```bash
sudo systemctl daemon-reload
sudo systemctl enable norko-store
sudo systemctl start norko-store
sudo systemctl status norko-store
```

## 🔧 تكوين قاعدة البيانات

### PostgreSQL (موصى به للإنتاج):

```sql
-- إنشاء قاعدة البيانات والمستخدم
CREATE DATABASE norko_store;
CREATE USER norko_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE norko_store TO norko_user;

-- تحسينات الأداء
ALTER DATABASE norko_store SET timezone TO 'Africa/Cairo';
```

### تهجير البيانات:

```bash
# تهيئة قاعدة البيانات
python manage.py db init
python manage.py db migrate -m "Initial migration"
python manage.py db upgrade

# إضافة بيانات أولية
python add_sample_products.py
```

## 📊 مراقبة الأداء

### 1. مراقبة Service Worker

أضف هذا لـ nginx logs:

```nginx
log_format sw_monitor '$remote_addr - $remote_user [$time_local] '
                     '"$request" $status $body_bytes_sent '
                     '"$http_referer" "$http_user_agent" '
                     'sw="$http_service_worker"';

access_log /var/log/nginx/sw_access.log sw_monitor;
```

### 2. مراقبة استخدام IndexedDB

أضف إلى `app.py`:

```python
@app.route('/api/storage-stats')
@login_required
def storage_stats():
    # إحصائيات استخدام التخزين
    return jsonify({
        'server_storage': get_db_size(),
        'cache_version': app.config.get('SW_CACHE_VERSION'),
        'active_users': get_active_users_count()
    })
```

### 3. لوحة مراقبة

```bash
# تثبيت monitoring tools
pip install flask-monitoring-dashboard

# إضافة للتطبيق
from flask_monitoringdashboard import dashboard
dashboard.bind(app)
```

## 🛡️ الأمان والبيانات

### 1. حماية البيانات المحلية

- البيانات المحلية **غير مشفرة** في IndexedDB
- لا تحفظ معلومات حساسة محلياً
- انتهاء صلاحية الجلسة يمسح البيانات

### 2. التحكم في التخزين المؤقت

```javascript
// في service-worker.js
const SENSITIVE_URLS = ["/api/users", "/api/payments"];

// عدم تخزين URLs الحساسة
if (SENSITIVE_URLS.some((url) => request.url.includes(url))) {
  return fetch(request); // لا تخزين مؤقت
}
```

### 3. مسح البيانات عند الخروج

```javascript
// في logout
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    registrations.forEach((registration) => {
      registration.postMessage({ type: "CLEAR_CACHE" });
    });
  });
}
```

## 🔍 استكشاف الأخطاء

### مشاكل شائعة وحلولها:

#### 1. Service Worker لا يسجل:

```bash
# فحص console في المتصفح
# خطأ شائع: Content-Type خاطئ
# الحل: تأكد من content-type: application/javascript
```

#### 2. IndexedDB لا يعمل:

```javascript
// فحص دعم المتصفح
if (!("indexedDB" in window)) {
  console.error("IndexedDB not supported");
  // fallback to localStorage
}
```

#### 3. مشاكل CORS مع Service Worker:

```python
# في app.py
from flask_cors import CORS
CORS(app, origins=['https://your-domain.com'])

@app.after_request
def after_request(response):
    response.headers['Service-Worker-Allowed'] = '/'
    return response
```

### 4. مشاكل المزامنة:

```bash
# فحص logs الخادم
tail -f /var/log/nginx/access.log | grep "/api/sync"

# فحص قاعدة البيانات
sudo -u postgres psql norko_store -c "SELECT COUNT(*) FROM sale WHERE created_at > NOW() - INTERVAL '1 hour';"
```

## 📈 التحسين والأداء

### 1. تحسين Service Worker Cache:

```javascript
// تخزين انتقائي للملفات الكبيرة
const LARGE_FILES = ["/static/js/chart.js"];
const shouldCache = (request) => {
  return !LARGE_FILES.some((file) => request.url.includes(file));
};
```

### 2. ضغط البيانات المحلية:

```javascript
// استخدام compression للبيانات الكبيرة
const compressData = (data) => {
  return LZString.compress(JSON.stringify(data));
};
```

### 3. تحسين قاعدة البيانات:

```sql
-- فهارس لتحسين الاستعلامات
CREATE INDEX idx_sale_date ON sale(sale_date);
CREATE INDEX idx_product_stock ON product(stock_quantity);
CREATE INDEX idx_customer_phone ON customer(phone);
```

## 📝 نسخ احتياطي للبيانات المحلية

### إعداد نسخ احتياطي دورية:

```bash
#!/bin/bash
# backup_offline_data.sh

# نسخ احتياطي لملفات JavaScript
tar -czf offline_js_backup_$(date +%Y%m%d).tar.gz static/js/

# نسخ احتياطي لقاعدة البيانات
pg_dump norko_store > norko_backup_$(date +%Y%m%d).sql

# مسح النسخ القديمة (أكثر من 30 يوم)
find . -name "*backup*.tar.gz" -mtime +30 -delete
find . -name "*backup*.sql" -mtime +30 -delete
```

## 🎯 اختبار الإنتاج

### قائمة فحص ما قبل النشر:

- [ ] HTTPS يعمل بشكل صحيح
- [ ] Service Worker يسجل بدون أخطاء
- [ ] IndexedDB يحفظ ويسترجع البيانات
- [ ] المزامنة تعمل عند استعادة الاتصال
- [ ] صفحة offline تظهر عند انقطاع الاتصال
- [ ] جميع API endpoints تستجيب بشكل صحيح
- [ ] البيانات الحساسة لا تُحفظ محلياً
- [ ] النسخ الاحتياطي والاستعادة تعمل

### اختبار التحميل:

```bash
# استخدام Apache Bench لاختبار التحميل
ab -n 1000 -c 10 https://your-domain.com/api/products

# اختبار مع Offline functionality
ab -n 500 -c 5 https://your-domain.com/api/sync
```

---

## 📞 الدعم الفني

### في حالة المشاكل:

1. فحص سجلات النظام: `journalctl -u norko-store -f`
2. فحص سجلات nginx: `tail -f /var/log/nginx/error.log`
3. فحص المتصفح Console لأخطاء JavaScript
4. تشغيل اختبار الوظائف: `python test_offline.py`

### معلومات الاتصال للدعم:

- **البريد الإلكتروني**: support@fikra.solutions
- **الهاتف**: +20-xxx-xxx-xxxx
- **الموقع**: https://fikra.solutions

---

🎉 **تم!** أصبح نظام Norko Store جاهزاً للعمل بوظائف غير متصلة كاملة في بيئة الإنتاج.
