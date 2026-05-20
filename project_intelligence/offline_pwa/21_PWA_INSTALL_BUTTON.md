# Phase 10 - PWA Install Button

## ملخص تنفيذي
تمت إضافة زر تثبيت واضح داخل شريط POSNext العلوي. الزر يظهر فقط عندما يطلق المتصفح حدث `beforeinstallprompt`، ويختفي إذا كان التطبيق مثبتًا أو يعمل بوضع standalone.

## أين تمت إضافة زر التثبيت
أضيف الزر في:

- `POS/src/components/pos/POSHeader.vue`

ويظهر في التوب بار بجانب مؤشرات الاتصال والكاش على الشاشات المتوسطة والكبيرة، مع نص عربي:

`تثبيت التطبيق`

## سلوك الزر في Chrome/Edge/Android
- يستمع التطبيق إلى `window.beforeinstallprompt`.
- يتم تنفيذ `event.preventDefault()` وحفظ الـ prompt.
- يظهر الزر فقط عندما يكون الـ prompt متاحًا.
- عند الضغط على الزر يتم استدعاء `prompt()`.
- بعد قبول التثبيت أو حدث `appinstalled` يتم إخفاء الزر وتسجيل حالة التثبيت محليًا.

## سلوك iOS/Safari
عند عدم توفر `beforeinstallprompt` وظهور المتصفح كـ iOS Safari، تظهر إرشادات صغيرة:

`للتثبيت على iPhone: افتح المشاركة ثم اختر إضافة إلى الشاشة الرئيسية`

لا يتم عرض prompt وهمي على iOS.

## نتائج build
- `npm run build`: نجح باستخدام Node الحديث في `/home/frappe/.local/node-v24/bin`.
- `bench build --app pos_next`: نجح باستخدام نفس بيئة Node الحديثة.
- محاولة أولى بدون تعديل PATH فشلت لأن Node النظام هو `v12.22.9`، ثم نجحت بإضافة Node الحديث مؤقتًا للـ PATH.

## نتائج فحص Service Worker
- `/pos`: HTTP 200.
- `sw.js`: HTTP 200.
- `Service-Worker-Allowed`: `/pos`.
- `Cache-Control`: `no-cache, no-store, must-revalidate`.

## الملفات المعدلة
- `POS/src/components/pos/POSHeader.vue`
- `POS/src/composables/usePWAInstall.js`

## القيود المتبقية
- زر التثبيت يظهر فقط عندما يسمح المتصفح بتثبيت PWA.
- iOS لا يدعم native install prompt، لذلك يتم عرض تعليمات فقط.
- توجد ملفات dirty قديمة غير متعلقة بهذه المرحلة وبقيت unstaged.
