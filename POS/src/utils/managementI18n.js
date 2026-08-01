const ARABIC_TO_ENGLISH = {
	"...": "...",
	"أدخل مبلغ دفع أكبر من صفر": "Enter a payment amount greater than zero",
	"أنشئ فاتورة جديدة للبدء": "Create a new invoice to get started",
	"إجمالي المستحق": "Total Outstanding",
	"إجمالي النتائج: {0}": "Total results: {0}",
	"إدارة المشتريات": "Manage Purchases",
	"إضافة صنف": "Add Item",
	إعادة: "Reset",
	"إلغاء الدفعة": "Cancel Payment",
	إلغاء: "Cancel",
	"إنشاء مورد جديد: {0}": "Create new supplier: {0}",
	إنشاء: "Create",
	"اختر الحساب...": "Select account...",
	"اختر حساب الصندوق أو البنك": "Select a cash or bank account",
	"اختر...": "Select...",
	"اعتماد الدفعة": "Submit Payment",
	"اعتماد الفاتورة": "Submit Invoice",
	اعتماد: "Submit",
	الأصناف: "Items",
	"الإجمالي الكلي": "Grand Total",
	الإجمالي: "Total",
	"الإجمالي:": "Total:",
	"الرصيد المستحق": "Outstanding Amount",
	الصنف: "Item",
	الضريبة: "Tax",
	"الفاتورة معتمدة — للتعديل يجب الإلغاء أولاً":
		"The invoice is submitted; cancel it through the standard workflow to reverse it",
	الكمية: "Quantity",
	"المجموع قبل الضريبة": "Total Before Tax",
	"المرجع: {0}": "Reference: {0}",
	المورد: "Supplier",
	الوحدة: "UOM",
	"تأكيد الاعتماد": "Confirm Submission",
	"تاريخ الاستحقاق": "Due Date",
	"تاريخ الدفع": "Payment Date",
	"تاريخ الفاتورة": "Invoice Date",
	"تاريخ المرجع": "Reference Date",
	"تحميل المزيد ({0} متبقية)": "Load more ({0} remaining)",
	"تسجيل دفعة للمورد": "Record Supplier Payment",
	"تسجيل دفعة": "Record Payment",
	تطبيق: "Apply",
	"تعديل فاتورة": "Edit Invoice",
	"تعذر إنشاء دفعة المورد": "Could not create the supplier payment",
	"تعذر تحميل بيانات الدفع": "Could not load payment details",
	"تم اعتماد الفاتورة بنجاح": "Invoice submitted successfully",
	"تم الحفظ بنجاح": "Saved successfully",
	"جاري الاعتماد...": "Submitting...",
	"جاري التحميل...": "Loading...",
	"جاري الحفظ...": "Saving...",
	"جاري تحميل بيانات الدفع...": "Loading payment details...",
	"حدث خطأ أثناء الاعتماد": "An error occurred while submitting",
	"حدث خطأ أثناء الحفظ": "An error occurred while saving",
	"حساب الصندوق أو البنك": "Cash or Bank Account",
	"حفظ كمسودة": "Save as Draft",
	"حفظ مسودة": "Save Draft",
	"دفعات الموردين": "Supplier Payments",
	"رقم المرجع": "Reference Number",
	"رقم فاتورة المورد": "Supplier Invoice Number",
	"سجل الدفعات النقدية والبنكية": "Cash and bank payment history",
	"سعر الشراء": "Buying Rate",
	"سيتم اعتماد فاتورة الشراء وتحديث المخزون والحسابات. لا يمكن التراجع عن هذه العملية.":
		"Submitting posts the Purchase Invoice to accounts and, when enabled, stock. Use standard cancellation to reverse it.",
	"طريقة الدفع": "Mode of Payment",
	"غير محدد": "Not specified",
	"غير مدفوعة": "Unpaid",
	"فاتورة جديدة": "New Invoice",
	"فاتورة شراء جديدة": "New Purchase Invoice",
	"فشل إنشاء المورد": "Could not create supplier",
	"فشل الاعتماد": "Submission failed",
	"فشل البحث عن الأصناف": "Item search failed",
	"فشل البحث عن الموردين": "Supplier search failed",
	"فشل الحفظ": "Save failed",
	"فشل تحميل الفاتورة": "Could not load invoice",
	"فواتير الشراء": "Purchase Invoices",
	كامل: "Full",
	"كل الحالات": "All Statuses",
	"لا توجد أصناف. أضف صنفًا للبدء.": "No items yet. Add an item to get started.",
	"لا توجد دفعات موردين": "No supplier payments",
	"لا توجد فواتير شراء": "No purchase invoices",
	"مبلغ الدفع أكبر من الرصيد المستحق":
		"Payment amount exceeds the outstanding amount",
	"مبلغ الدفعة": "Payment Amount",
	متأخرة: "Overdue",
	"متبقي: {0}": "Outstanding: {0}",
	مدفوع: "Paid",
	"مدفوعة جزئيًا": "Partly Paid",
	مدفوعة: "Paid",
	مرتجع: "Return",
	مسودة: "Draft",
	معتمدة: "Submitted",
	"معلومات إضافية": "Additional Information",
	ملاحظات: "Remarks",
	ملغاة: "Cancelled",
	"هل تريد إلغاء هذه الدفعة؟":
		"Cancel this payment using the standard reversal workflow?",
	"يرجى إضافة صنف واحد على الأقل": "Add at least one item",
	"يرجى اختيار المورد أولاً": "Select a supplier first",
	"إلى تاريخ": "To Date",
	"ابحث عن صنف...": "Search for an item...",
	"ابحث عن مورد...": "Search for a supplier...",
	اختياري: "Optional",
	"اسم المورد الجديد": "New supplier name",
	"بحث...": "Search...",
	"رمز المورد": "Supplier code",
	"شيك/تحويل/إيصال": "Cheque/transfer/receipt",
	"ملاحظات اختيارية...": "Optional remarks...",
	"من تاريخ": "From Date",
}

function interpolate(message, values = []) {
	return values.reduce(
		(result, value, index) => result.replaceAll(`{${index}}`, String(value)),
		message,
	)
}

export function managerTranslate(source, values = []) {
	const language =
		globalThis.frappe?.boot?.lang ||
		globalThis.document?.documentElement?.lang ||
		"en"
	const isArabic = language.toLowerCase().startsWith("ar")
	const isArabicSource = Object.hasOwn(ARABIC_TO_ENGLISH, source)
	if (isArabicSource) {
		return interpolate(isArabic ? source : ARABIC_TO_ENGLISH[source], values)
	}
	const translated =
		globalThis.__?.(source, values) || interpolate(source, values)
	return translated
}

export { ARABIC_TO_ENGLISH }
