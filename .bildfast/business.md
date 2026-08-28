# POS Next

## Scope
Existing Frappe app: `pos_next`.
Primary site: `pos.yemenfrappe.com`.
Lovable/BildFast project: `LP-00022`.
Preview target: `https://pos.yemenfrappe.com/desk`.

## Operating Rule
BildFast must work on this existing app in place. Do not scaffold or create a replacement app for this business domain.

## إدارة الأصناف (Item management)
شاشة كلاسيكية (Master–Detail) لإدارة الأصناف: **إضافة** صنف جديد وإدخال الكمية المشتراة لإضافتها
للمخزون، **تعديل** حقول/كميات/أسعار صنفٍ مُختار (للمدير فقط)، و**الاستعلام/السرد**. الحقول: الاسم،
كود تلقائي (سلسلة `POS-ITM`)، المجموعة، الوحدة، الكمية، الكمية المتاحة (المخزون − المحجوز، عرض فقط)،
سعر التكلفة، سعر البيع، الباركود، الوصف، الصورة، السريال (نص مرجعي، لا ترقيم لكل قطعة). الكمية تُكتب
للمخزون عبر تسوية مخزون (سعر التكلفة = سعر التقييم)؛ الحذف = تعطيل ناعم؛ لا نظام حجز فعلي. مقصورة على
مديري الأصناف (`canManageCatalog`) وضمن صلاحيات الشركة.

## أنواع المصاريف (Expense Types)
شاشة **للمدير فقط** (صلاحية «POS Expense Type» + ميزة `enable_expense_types`) لتعريف أنواع المصاريف
والحساب المرتبط بكل نوع. حقل «حساب المصروف» يعرض **فقط الحسابات التي أنشأها المدير من الشاشة** (مع ترحيل
الحسابات المستخدمة سابقاً)، ويستطيع المدير **إنشاء حساب مصروف جديد** من الشاشة مباشرةً.
