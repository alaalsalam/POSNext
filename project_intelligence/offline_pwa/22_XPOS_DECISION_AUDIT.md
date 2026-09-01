# XPOS Decision Audit

## ملخص تنفيذي
القرار النهائي: `ISOLATED_LAB_TEST`

الخلاصة العملية:
- لا نركب XPOS على `pos.yemenfrappe.com` الآن.
- فرع `develop` غير مناسب لبيئتنا الحالية.
- فرع `version-15` يستحق مختبرًا معزولًا فقط، وليس دمجًا داخل الديمو الجاهز.
- أفضل استخدام حالي لـ XPOS هو: مصدر أفكار قوية لبعض قدرات UX وOffline المتقدمة، مع اختبار منفصل لاحقًا إن أردنا تقييمه بجدية.

## ما هو XPOS
XPOS هو تطبيق POS مبني على Frappe/ERPNext مع واجهة Vue 3 حديثة، دعم PWA، مسار Electron، Offline queue، مزامنة، باركود، وبعض تدفقات الشراء والاستلام من داخل واجهة الـ POS نفسها.

## الترخيص
- الترخيص: `MIT`
- المصدر: `license.txt`

## المتطلبات التقنية
### فرع develop
- Frappe: `v16`
- ERPNext: `v18` بحسب README
- Python: `>=3.14` بحسب README
- Python: `>=3.10` بحسب `pyproject.toml` (يوجد تعارض يجب اعتباره مخاطرة توثيقية)
- Node.js: `>=24` بحسب README

### فرع version-15
- Frappe: `v15`
- ERPNext: `v15`
- Python: `>=3.10`
- Node.js: `>=18`

## التوافق مع بيئتنا الحالية
### بيئتنا الحالية على السيرفر
- Frappe: `15.107.2`
- ERPNext: `15.107.0`
- POSNext: `1.16.0`
- Python: `3.10.12`
- Node.js على السيرفر: `12.22.9`
- فرع POSNext الحالي: `feature/posnext-pwa-offline-hardening`

### النتيجة
- `develop` من XPOS: غير متوافق مع البيئة الحالية.
- `version-15` من XPOS: متوافق نظريًا فقط، لكنه غير مناسب للتركيب على الموقع الحالي مباشرة.
- السبب ليس route فقط، بل عمق التدخل في ERPNext نفسه.

## لماذا التركيب على الموقع الحالي خطر
XPOS لا يضيف صفحة `/xpos` فقط، بل يمدد سلوك النظام نفسه عبر:
- `doctype_js` على `POS Profile`, `Sales Invoice`, `Company`
- `extend_bootinfo`
- `override_doctype_class` لـ `POS Invoice`
- `doc_events` على `Sales Invoice`, `POS Invoice`, `Customer`

هذا يعني أن تركيبه قد يؤثر على:
- تدفق POS Invoice الحالي في POSNext
- سلوك Sales Invoice
- صلاحيات وإعدادات POS Profile
- المحاسبة والدفع
- boot/session data

## مقارنة مختصرة مع POSNext الحالي
### وضع POSNext الحالي
POSNext على `pos.yemenfrappe.com` جاهز للديمو العميل الآن، مع:
- PWA يعمل
- `/pos` controlled by Service Worker
- Offline create + sync يعمل
- 7/7 Online POS ناجح
- Offline Sync ناجح
- baseline محاسبي مضبوط على `YER`

### وضع XPOS
XPOS يبدو غنيًا جدًا من ناحية الميزات، لكنه أوسع من مجرد تحسين PWA؛ هو منتج POS كامل بفرضياته الخاصة وتدخله في سلوك ERPNext.

## نقاط القوة في XPOS
1. Command palette واختصارات لوحة مفاتيح قوية
2. Offline UX أوضح من كثير من التطبيقات
3. Electron desktop path جاهز
4. دعم multi-payment أغنى
5. لوحة pending/offline عمليات متقدمة
6. طباعة وحراريات وQZ بشكل أعمق
7. Permission flags كثيرة ومفصلة
8. دعم RTL وDark Mode واضح
9. بنية TypeScript/Vue حديثة
10. وجود tests وCI وSecurity policy

## المخاطر
1. `develop` غير مناسب تمامًا لنسختنا الحالية
2. حتى `version-15` سيخلق مخاطرة دمج بسبب hooks العميقة
3. تضارب محتمل مع `POS Invoice`, `Sales Invoice`, `POS Profile`, `Company`
4. منطق المحاسبة والدفع مختلف وقد يربك baseline الذي أصلحناه
5. Node المطلوب للبناء أعلى من Node الحالي على السيرفر
6. توسيع النطاق ليشمل purchase workflows يزيد التعقيد
7. مسار Electron ليس ذا أولوية حالية للديمو وقد يفتح جبهة إضافية
8. تغيير المنتج الآن يعرّض ديمو جاهز فعليًا للخطر

## Feature Gap Comparison
| Feature | Current POSNext status | XPOS status | Business value | Risk | Recommendation |
|---|---|---|---|---|---|
| PWA | مثبت ويعمل | قوي ومتكامل | عالٍ | متوسط | Inspiration only |
| Offline invoice | يعمل مع sync | قوي مع queue/retry UX | عالٍ | متوسط | Compare UX only |
| Sync/idempotency | يعمل | موجود | عالٍ | متوسط | Audit ideas only |
| Barcode | جاهز | قوي وكاميرا مسح | عالٍ | منخفض | Partial adoption idea |
| Serial/IMEI | جزئي في الديمو | أقوى | متوسط | متوسط | Lab test only |
| Batch/expiry | جزئي في الديمو | أقوى | متوسط | متوسط | Lab test only |
| Multi-payment | محدود/أساسي | أقوى بوضوح | عالٍ | متوسط | Consider adoption |
| Returns | يحتاج تقييم أوسع | مدعوم | متوسط | متوسط | Lab test |
| Opening/closing shift | موجود بشكل أساسي | أغنى | متوسط | متوسط | Inspiration |
| Print/thermal printer | جيد | أعمق مع QZ/ESC-POS | عالٍ | متوسط | Selective adoption |
| Keyboard shortcuts | محدود | قوي جدًا | عالٍ | منخفض | Adopt idea |
| Command palette | غير بارز | موجود | متوسط | منخفض | Adopt idea |
| RTL | موجود | موجود | متوسط | منخفض | Keep current |
| Dark mode | محدود | جاهز | منخفض إلى متوسط | منخفض | Adopt later |
| Desktop/Electron | غير موجود | موجود | حسب السوق | عالٍ | Separate exploration |
| Permissions | كافٍ للديمو | غني جدًا | متوسط | متوسط | Study only |
| License/trial idea | غير ذي صلة الآن | موجود بالتصور التجاري | منخفض | منخفض | Ignore for now |
| Accounting stability | مثبت بعد Phase 8 | غير مثبت عندنا | حرج | عالٍ | Do not swap |
| ERPNext v15 readiness | مثبت عندنا | branch مخصص موجود | متوسط | متوسط | Isolated lab test |

## مراجعة الجودة الهندسية
- المشروع نشط وله tags حتى `v2.2.2`
- توجد فروع `develop`, `version-15`, `version-16`
- توجد اختبارات frontend/backend
- توجد GitHub Actions وsemantic release
- يوجد `SECURITY.md`
- الواجهة الحديثة جيدة من ناحية البنية
- لكن نضج المشروع لا يعني أمان دمجه داخل بيئة ديمو مستقرة بدون sandbox منفصل

## القرار النهائي
`ISOLATED_LAB_TEST`

### معنى القرار
- لا نركب XPOS على `pos.yemenfrappe.com`
- لا نستبدل POSNext الحالي الآن
- إذا أردنا الاستفادة منه، فالخطوة الصحيحة هي:
  1. إنشاء bench/site منفصلين
  2. تجربة فرع `version-15` فقط
  3. قياس التوافق مع POS Invoice والحسابات والـ POS Profile
  4. نقل الأفكار الجيدة فقط إلى POSNext إن ثبتت قيمتها

## ما الأفكار التي ننقلها إلى POSNext
1. Command palette `Ctrl+K`
2. keyboard shortcuts panel أقوى
3. Offline pending queue panel أوضح
4. last sync / retry UX أفضل
5. camera barcode scanning polish
6. multi-payment UX أفضل
7. print format rules
8. about/system diagnostics dialog
9. dark mode toggle
10. richer role/permission flags model

## هل نعتبره مستقبلًا بديلاً كاملًا؟
ليس الآن. يمكن أن يصبح `FUTURE_REPLACEMENT_CANDIDATE` فقط إذا نجح مختبر v15 المعزول محاسبيًا ووظيفيًا ولم يتعارض مع baseline الحالي.

## أوامر المرحلة التالية إن لزم
- إنشاء bench معزول لاختبار `origin/version-15`
- عدم لمس `pos.yemenfrappe.com`
- توثيق نتائج serial/batch/returns/multi-payment داخل بيئة الاختبار المنفصلة
