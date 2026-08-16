"""Refresh the live POS workspace labels after the UX copy update."""

import frappe


LINK_LABELS = {
	"Sales Invoice": "فواتير المبيعات",
	"Customer": "العملاء",
	"Payment Entry": "سندات الدفع",
	"POS Profile": "ملفات نقطة البيع",
	"Item": "الأصناف",
	"Warehouse": "المستودعات",
	"Stock Entry": "حركات المخزون",
	"Stock Reconciliation": "جرد وتسوية المخزون",
	"Sales vs Shifts Report": "تقرير المبيعات والورديات",
	"Cashier Performance Report": "تقرير أداء الكاشير",
	"Payments and Cash Control Report": "تقرير المدفوعات والرقابة النقدية",
	"Inventory Impact and Fast Movers Report": "تقرير حركة المخزون والأصناف السريعة",
	"Offline Sync and System Health Report": "تقرير المزامنة وصحة النظام",
	"POS Settings": "إعدادات نقطة البيع",
	"POS Branding Settings": "هوية نقطة البيع",
	"POS Opening Shift": "فتح وردية",
	"POS Closing Shift": "إغلاق وردية",
	"POS Offer": "عروض نقطة البيع",
	"POS Coupon": "كوبونات نقطة البيع",
}


def execute():
	if not frappe.db.exists("Workspace", "POS"):
		return
	workspace = frappe.get_doc("Workspace", "POS")
	for row in workspace.links:
		if row.link_to in LINK_LABELS:
			row.label = LINK_LABELS[row.link_to]
	for row in workspace.shortcuts:
		if row.link_to in LINK_LABELS:
			row.label = LINK_LABELS[row.link_to]
	workspace.save(ignore_permissions=True)
	frappe.clear_cache()
