# دليل الوظائف غير المتصلة (Offline-First) - نظام إدارة Norko Store

## 📋 نظرة عامة

تم تطوير نظام إدارة Norko Store ليعمل بفعالية حتى في حالة انقطاع الاتصال بالإنترنت. يمكن للمستخدمين الآن:

- ✅ عرض المنتجات والعملاء المحفوظة محلياً
- ✅ إضافة مبيعات جديدة دون اتصال بالإنترنت
- ✅ البحث في البيانات المحلية
- ✅ مزامنة تلقائية عند استعادة الاتصال

## 🏗️ المكونات الرئيسية

### 1. Service Worker (`static/js/service-worker.js`)

- تخزين مؤقت للملفات الثابتة (CSS, JS, Images)
- تخزين مؤقت لاستجابات API الأساسية
- عرض صفحة offline عند عدم توفر المحتوى

### 2. مدير قاعدة البيانات المحلية (`static/js/db-manager.js`)

- استخدام IndexedDB لتخزين البيانات محلياً
- إدارة المنتجات، العملاء، المبيعات، والفئات
- نظام العمليات المعلقة للمزامنة

### 3. مدير المزامنة (`static/js/sync-manager.js`)

- مراقبة حالة الاتصال
- مزامنة البيانات بين المحلي والخادم
- إدارة العمليات المعلقة
- إشعارات المستخدم

### 4. معالج العمليات غير المتصلة (`static/js/offline-handler.js`)

- تحسين واجهة المستخدم للعمل بدون اتصال
- معالجة البحث المحلي
- إدارة عمليات البيع غير المتصلة

## 🚀 المزايا الجديدة

### شريط الحالة

```html
- مؤشر حالة الاتصال (متصل/غير متصل) - مؤشر المزامنة الجارية - وقت آخر مزامنة -
زر المزامنة اليدوية
```

### البيع بدون اتصال

```javascript
// يمكن إضافة مبيعات جديدة حتى بدون إنترنت
await window.syncManager.saveSaleLocal({
  customer_id: customerId,
  items: cartItems,
  payment_status: "paid",
  payment_type: "cash",
});
```

### البحث المحلي

```javascript
// البحث في البيانات المحفوظة محلياً
const products = await window.syncManager.getProductsLocal({
  search: "منتج",
  category_id: 1,
});
```

## 📱 كيفية الاستخدام

### 1. التشغيل لأول مرة

1. افتح التطبيق مع الاتصال بالإنترنت
2. ستتم مزامنة البيانات الأساسية تلقائياً
3. Service Worker سيحفظ الملفات الثابتة

### 2. العمل بدون اتصال

1. عند انقطاع الإنترنت، ستظهر رسالة "غير متصل"
2. يمكن الوصول للصفحات المحفوظة مسبقاً
3. البحث والبيع يعملان بالبيانات المحلية

### 3. المزامنة التلقائية

1. عند استعادة الاتصال، تبدأ المزامنة تلقائياً
2. البيانات المحلية تُرفع للخادم
3. البيانات الجديدة من الخادم تُحدّث محلياً

## 🔧 API Endpoints الجديدة

### `/api/sync` (POST)

مزامنة العمليات المعلقة:

```json
{
  "type": "sales",
  "data": [
    {
      "local_id": 123456789,
      "customer_id": 1,
      "items": [
        {
          "product_id": 5,
          "quantity": 2,
          "unit_price": 50.0,
          "total_price": 100.0
        }
      ],
      "total_amount": 100.0,
      "payment_status": "paid"
    }
  ]
}
```

### `/api/offline-status` (GET)

معلومات حالة التطبيق:

```json
{
  "status": "online",
  "timestamp": "2025-01-11T...",
  "stats": {
    "products": { "total": 150, "low_stock": 5 },
    "customers": { "total": 45 },
    "sales_today": { "count": 12, "revenue": 1500.0 }
  },
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

## 🔄 دورة حياة المزامنة

### عند الاتصال:

1. جلب آخر إصدار من المنتجات
2. جلب قائمة العملاء المحدّثة
3. جلب الفئات الجديدة
4. رفع العمليات المعلقة

### عند قطع الاتصال:

1. حفظ العمليات في قائمة الانتظار
2. الاعتماد على البيانات المحلية
3. إظهار تنبيهات للمستخدم

### عند استعادة الاتصال:

1. إشعار المستخدم
2. بدء المزامنة التلقائية
3. حل تضارب البيانات (Client wins)

## 🎨 تحسينات واجهة المستخدم

### مؤشرات بصرية

```css
.network-status.online {
  background: #d4edda;
  color: #155724;
}

.network-status.offline {
  background: #f8d7da;
  color: #721c24;
}
```

### إشعارات ذكية

- إشعارات عند انقطاع/استعادة الاتصال
- مؤشر تقدم المزامنة
- رسائل نجاح/فشل العمليات

## 🛠️ الاختبار والتطوير

### اختبار الوضع غير المتصل:

1. افتح Developer Tools (F12)
2. انتقل إلى تبويب Network
3. حدد "Offline" من القائمة المنسدلة
4. جرب استخدام التطبيق

### مراقبة IndexedDB:

1. افتح Developer Tools
2. انتقل إلى تبويب Application
3. في الشريط الجانبي، اختر IndexedDB
4. تصفح بيانات "NorkoStoreDB"

### مراقبة Service Worker:

1. في Developer Tools، انتقل إلى Application
2. اختر Service Workers من الشريط الجانبي
3. راقب حالة التخزين المؤقت

## 📈 الإحصائيات والمراقبة

### حجم التخزين المحلي:

```javascript
const status = await window.syncManager.getStatus();
console.log("العمليات المعلقة:", status.pendingOperations);
console.log("آخر مزامنة:", status.lastSyncTime);
```

### مسح البيانات المحلية:

```javascript
// مسح جميع البيانات المحلية
await window.dbManager.clearAllData();

// مسح التخزين المؤقت
await window.syncManager.resetAllData();
```

## ⚠️ اعتبارات مهمة

### الأمان:

- البيانات المحلية غير مشفرة
- لا تحفظ كلمات المرور محلياً
- التحقق من الصلاحيات يتم على الخادم

### الأداء:

- البيانات المحلية محدودة بـ حوالي 50MB
- المزامنة تحدث في الخلفية
- أولوية للعمليات الحديثة

### التوافق:

- يتطلب متصفحات حديثة تدعم:
  - Service Workers
  - IndexedDB
  - ES6 Promises

## 🔮 التطوير المستقبلي

### مزايا مخططة:

- [ ] مزامنة الصور والملفات
- [ ] دعم العمل الجماعي غير المتصل
- [ ] تشفير البيانات المحلية
- [ ] ضغط البيانات لتوفير المساحة
- [ ] مزامنة ذكية حسب الأولوية

### تحسينات ممكنة:

- [ ] واجهة إدارة البيانات المحلية
- [ ] تقارير استخدام التخزين
- [ ] نسخ احتياطي محلي
- [ ] استيراد/تصدير البيانات المحلية

## 📞 الدعم والمساعدة

### تشخيص المشاكل:

1. تحقق من إعدادات المتصفح
2. امسح بيانات التطبيق وحمّل مرة أخرى
3. تحقق من سجلات الأخطاء في Console

### الأخطاء الشائعة:

- "Service Worker failed to register": تحقق من مسار الملفات
- "IndexedDB quota exceeded": امسح البيانات القديمة
- "Sync failed": تحقق من اتصال الإنترنت

---

## 📄 مثال كامل: استخدام API للمطورين

```javascript
// مثال: إضافة بيع جديد في الوضع غير المتصل
async function addOfflineSale() {
  const saleData = {
    customer_id: 1,
    items: [
      {
        product_id: 5,
        quantity: 2,
        unit_price: 25.0,
        total_price: 50.0,
      },
    ],
    total_amount: 50.0,
    payment_status: "paid",
    payment_type: "cash",
    notes: "بيع تجريبي",
  };

  try {
    const saleId = await window.syncManager.saveSaleLocal(saleData);
    console.log("تم حفظ البيع محلياً:", saleId);

    // المزامنة ستحدث تلقائياً عند توفر الاتصال
    if (window.syncManager.isOnline) {
      window.syncManager.performSync();
    }
  } catch (error) {
    console.error("خطأ في حفظ البيع:", error);
  }
}

// مثال: البحث في المنتجات محلياً
async function searchProducts(searchTerm) {
  const products = await window.dbManager.getProducts({
    search: searchTerm,
    low_stock: false,
  });

  console.log("نتائج البحث:", products);
  return products;
}

// مثال: مراقبة حالة الاتصال
window.addEventListener("online", () => {
  console.log("تم استعادة الاتصال");
  window.syncManager.performSync();
});

window.addEventListener("offline", () => {
  console.log("تم قطع الاتصال - التبديل للوضع المحلي");
});
```

---

🎉 **تهانينا!** أصبح نظام Norko Store يدعم العمل بدون اتصال بالإنترنت بشكل كامل.
