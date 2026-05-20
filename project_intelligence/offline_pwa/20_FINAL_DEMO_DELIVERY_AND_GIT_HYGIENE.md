# POSNext Final Demo Delivery Pack

## ملخص تنفيذي
القرار النهائي: `READY_FOR_CLIENT_DEMO`

الديمو جاهز للعرض: Online POS نجح للشركات السبع، Offline Sync نجح من المتصفح، وPWA/Service Worker يعمل على `/pos`.

## حالة الديمو النهائية
- رابط الدخول: https://pos.yemenfrappe.com/pos
- الشركات الجاهزة: `7`
- المستخدمون الجاهزون: `7`
- العملة: `YER`
- Online POS: ناجح
- Offline Sync: ناجح
- PWA: Service Worker مفعل
- منع التكرار: لا يوجد تكرار

## قائمة المستخدمين والشركات

- Gold and Jewelry: `gold@gmail.com`
- Perfumes: `perfumes@gmail.com.sa`
- Cafe: `cafe@gmail.com`
- Phones: `phones@gmail.com`
- Pharmacy: `pharmacy@gmail.com`
- Hairdressing: `hairdressing@gmail.com`
- Super Market: `supermarket@gmail.com`

## كلمة المرور
كلمة المرور موحدة لدى مدير النظام عبر POS_DEMO_PASSWORD

## اختبار البيع Online

- Gold and Jewelry: `ACC-SINV-2026-00012` - موجود ومقدم
- Perfumes: `ACC-SINV-2026-00013` - موجود ومقدم
- Cafe: `ACC-SINV-2026-00014` - موجود ومقدم
- Phones: `ACC-SINV-2026-00015` - موجود ومقدم
- Pharmacy: `ACC-SINV-2026-00016` - موجود ومقدم
- Hairdressing: `ACC-SINV-2026-00017` - موجود ومقدم
- Super Market: `ACC-SINV-2026-00018` - موجود ومقدم

## اختبار البيع Offline
- offline_id: `pos_offline_4d5d9f84-1327-465b-b5ff-1550e10af281`
- Sales Invoice: `ACC-SINV-2026-00019`
- الحالة: Synced

## إعدادات العملة والحسابات
تم اعتماد YER وربط حسابات Cash/Receivable/POS Profile/Mode of Payment بالديمو.

## القيود المعروفة

- Phones: البيع العادي بالباركود جاهز، أما عرض IMEI/Serial الكامل يحتاج أصناف مخصصة serialized.
- Pharmacy: البيع العادي بالباركود جاهز، أما Batch/Expiry الكامل يحتاج أصناف batch-enabled مخصصة.
- يوجد ملفات قديمة dirty تخص الديمو/البراندنج تحتاج قرار منفصل قبل الدمج.

## حالة Git والملفات غير الملتزمة

- `OS/index.html`: risky/unrelated - leave unstaged until owner reviews
- `POS/src/components/common/InstallAppBadge.vue`: likely POS/PWA functional change - review manually in a separate code-quality pass before commit
- `POS/src/pages/Home.vue`: likely demo/branding UI change - review manually then commit as branding/demo pack or keep pending
- `POS/src/pages/Login.vue`: likely demo/branding UI change - review manually then commit as branding/demo pack or keep pending
- `POS/src/pages/POSSale.vue`: likely POS/PWA functional change - review manually in a separate code-quality pass before commit
- `POS/src/utils/errorHandler.js`: likely POS/PWA functional change - review manually in a separate code-quality pass before commit
- `POS/src/utils/printInvoice.js`: likely POS/PWA functional change - review manually in a separate code-quality pass before commit
- `pos_next/hooks.py`: needs human decision - do not commit with final docs; review scope and risk
- `pos_next/pos_next/print_format/pos_next_receipt/pos_next_receipt.json`: needs human decision - do not commit with final docs; review scope and risk
- `pos_next/pos_next/workspace/posnext/posnext.json`: needs human decision - do not commit with final docs; review scope and risk
- `pos_next/translations/ar.csv`: likely demo/branding UI change - review manually then commit as branding/demo pack or keep pending
- `project_intelligence/offline_pwa/13_PHASE7C_OFFLINE_INVOICE_REGRESSION.md`: safe documentation/report - commit separately if relevant
- `project_intelligence/offline_pwa/14_PHASE7C_RERUN_OFFLINE_INVOICE_REGRESSION.md`: safe documentation/report - commit separately if relevant

## القرار النهائي
`READY_FOR_CLIENT_DEMO`
