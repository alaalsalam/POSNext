# تحسين عمليات POSNext Offline - مرتجعات ومدفوعات

## ملخص تنفيذي
تم تحسين وضع الأوفلاين في POSNext بحيث لا يقتصر على إنشاء فاتورة بيع فقط، بل أصبح يدعم عمليتين مهمتين للكاشير:

- حفظ مدفوعات الفواتير غير المسددة Offline ثم مزامنتها عند عودة الاتصال.
- إنشاء مرتجع من فاتورة محفوظة في الكاش Offline ثم إرساله عبر نفس مسار مزامنة الفواتير.

لم يتم تشغيل migrate، ولم يتم restart. تم تشغيل build للواجهة و bench build للتطبيق بنجاح.

## ما تم تحسينه

### 1. مدفوعات Offline
- تم تفعيل جدول `payment_queue` في IndexedDB بشكل عملي.
- عند إضافة دفعة لفاتورة غير مسددة أثناء الأوفلاين، تحفظ العملية محلياً بدلاً من الفشل.
- عند عودة الاتصال، تتم مزامنة المدفوعات تلقائياً مع السيرفر عبر API المدفوعات الجزئية.
- تم حفظ `retry_count` و `last_error` و `last_retry_at` عند فشل المزامنة.
- تم جعل كل دفعة تحمل `offline_id/reference_no` لمنع التكرار عند إعادة المحاولة.

### 2. منع تكرار المدفوعات
- تم تعديل backend في `partial_payments.py` بحيث إذا وصل نفس `reference_no` مرة أخرى لا ينشئ Payment Entry مكرر.
- هذا مهم عند انقطاع الاتصال أثناء المزامنة أو تكرار retry من المتصفح.

### 3. مرتجعات Offline
- شاشة المرتجع لم تعد تمنع العمل مباشرة عند الأوفلاين.
- يمكن فتح المرتجع من الفواتير المحفوظة في الكاش.
- يتم تجهيز مستند Return Sales Invoice محلياً مع:
  - `is_return = 1`
  - `return_against`
  - كميات سالبة للأصناف المرتجعة
  - دفعات سالبة أو إضافة الرصيد للعميل حسب الاختيار
- يتم حفظ المرتجع في `invoice_queue` ثم تتم مزامنته عند عودة الاتصال.

### 4. Payment Methods Offline
- شاشة الدفع أصبحت تستخدم وسائل الدفع المخزنة محلياً إذا فشل تحميلها من السيرفر.
- هذا ينطبق على الدفع العادي وعلى نافذة المرتجعات.

### 5. عداد المزامنة
- عداد العمليات المعلقة أصبح يحسب الفواتير والمدفوعات المؤجلة معاً.
- رسالة المزامنة أصبحت تعرض "offline operation(s)" بدلاً من حصرها في invoices فقط.

## الملفات المعدلة
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/utils/offline/db.js`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/utils/offline/sync.js`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/utils/offline/index.js`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/stores/posSync.js`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/components/sale/PaymentDialog.vue`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/components/invoices/InvoiceManagement.vue`
- `/home/frappe/frappe-bench/apps/pos_next/POS/src/components/sale/ReturnInvoiceDialog.vue`
- `/home/frappe/frappe-bench/apps/pos_next/pos_next/api/partial_payments.py`

## نتائج التحقق
- `python -m py_compile partial_payments.py`: نجح.
- `git diff --check` للملفات المعدلة: نجح.
- `npm run build` داخل POS: نجح.
- `bench build --app pos_next`: نجح.
- `bench --site pos.yemenfrappe.com clear-cache`: نجح.
- `bench --site pos.yemenfrappe.com clear-website-cache`: نجح.
- `/pos`: يرجع HTTP 200.
- `sw.js`: يرجع HTTP 200 مع `Service-Worker-Allowed: /pos` و `Cache-Control: no-cache, no-store, must-revalidate`.

## حدود العمل الحالية
- المرتجع Offline يحتاج أن تكون الفاتورة الأصلية محفوظة في كاش الفواتير وبداخلها تفاصيل الأصناف. إذا لم تكن التفاصيل محفوظة، يجب فتح سجل الفاتورة مرة واحدة Online قبل استخدامها Offline.
- صلاحية المرتجع النهائية والمحاسبة والمخزون لا يتم تجاوزها؛ إذا تغيرت حالة الفاتورة على السيرفر أو حدث تعارض محاسبي فستفشل المزامنة وتظهر في الأخطاء.
- المدفوعات Offline تتم مزامنتها عند عودة الاتصال، لكنها تخضع لنفس صلاحيات وحالة الفاتورة على السيرفر.
- لم يتم تنفيذ اختبار متصفح كامل لإنشاء مرتجع Offline ومدفوعة Offline في هذا التشغيل؛ تم تنفيذ build وفحص تقني فقط.

## التوصية التالية
اختبار عملي من المتصفح على يوزر مثل `supermarket@gmail.com` أو `cafe@gmail.com`:

1. افتح POS Online واتركه يحمل الفواتير ووسائل الدفع.
2. افصل الإنترنت من DevTools.
3. افتح فواتير غير مسددة وأضف دفعة.
4. افتح فاتورة محفوظة وأنشئ مرتجع.
5. أعد الاتصال.
6. تأكد أن العمليات ظهرت في النظام بدون تكرار.
