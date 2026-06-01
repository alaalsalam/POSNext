# تقرير تحسين عمليات Offline في POSNext

## ملخص تنفيذي
تم فحص واجهات POSNext التي كانت تعتمد على API مباشر أثناء وضع الأوفلاين، وتمت إضافة fallback آمن من IndexedDB/cache حتى لا تظهر أخطاء عند فتح الشاشات الأساسية داخل POS.

الموقع: pos.yemenfrappe.com  
التاريخ: 2026-05-25T22:30:20

## ما تم تحسينه
- Bootstrap startup now falls back to cached initial POS data when the network/API is unavailable.
- POS Settings are cached per POS Profile and can be viewed offline from the settings dialog.
- Saving POS Settings is blocked gracefully while offline instead of throwing an API error.
- Promotions management now shows cached promotions, item groups, and brands offline, while create/update/delete actions are blocked with a clear message.
- Warehouse/stock lookup search now uses cached items while offline and shows cached POS warehouse stock instead of failing API calls.
- Manual refresh and cache clearing are blocked safely while offline to avoid deleting the only local working cache.

## الواجهات التي أصبحت أكثر أمانًا في Offline
- فتح POS بعد أول تحميل Online: يستخدم Bootstrap cached fallback.
- Settings: عرض الإعدادات من الكاش، ومنع الحفظ أوفلاين برسالة واضحة.
- Promotions: عرض العروض المحفوظة محليًا، ومنع التعديل أو الحذف أو الإنشاء أوفلاين.
- Products / Stock Lookup: البحث في الأصناف من الكاش وعرض كمية المخزون المحفوظة بدل فشل API.
- Refresh / Clear Cache: منع العمليات التي قد تكسر الكاش أثناء الأوفلاين.

## حدود Offline المتبقية
- Creating or editing master/setup data offline is intentionally not synced in this phase: promotions/settings/customer creation still require network for writes.
- Return invoices and adding payments to previous unpaid invoices remain online-only unless a dedicated accounting-safe offline queue is designed.
- Warehouse availability offline is limited to the cached POS stock snapshot, not a live all-warehouse server query.
- Browser verification was run for Service Worker control; full cashier UI offline traversal should be performed with a logged-in cashier session after the presenter refreshes once online.

## نتائج الاختبار
- npm run build: نجح.
- bench build --app pos_next: نجح.
- /pos: HTTP/2 200.
- sw.js Service-Worker-Allowed: /pos.
- sw.js Cache-Control: no-cache, no-store, must-revalidate.
- Browser SW verification: controlled_by_sw=true; scope=https://pos.yemenfrappe.com/pos; script=https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js.

## الملفات المعدلة في هذا الإصلاح
- apps/pos_next/POS/src/stores/bootstrap.js
- apps/pos_next/POS/src/stores/posSettings.js
- apps/pos_next/POS/src/components/settings/POSSettings.vue
- apps/pos_next/POS/src/components/sale/PromotionManagement.vue
- apps/pos_next/POS/src/components/sale/WarehouseAvailabilityDialog.vue
- apps/pos_next/POS/src/pages/POSSale.vue

## ملاحظة تشغيلية
قبل اختبار الأوفلاين الحقيقي من الكاش، افتح POS مرة واحدة Online لكل مستخدم/بروفايل حتى يكتمل تخزين الأصناف والعملاء وطرق الدفع والإعدادات، ثم افصل الشبكة واختبر البيع والواجهات.

## تحديث إضافي لشاشة الفواتير
- Invoice Detail now loads cached invoice history when offline instead of calling the server.
- Invoice printing now prints cached invoice details when available before falling back to server print-by-name.
- Legacy Invoice History dialog now caches loaded invoices and reads them from cache while offline.
- Return creation from invoice history is disabled offline with a clear message.
