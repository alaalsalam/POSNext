# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class POSExpenseType(Document):
	def validate(self):
		account = frappe.db.get_value(
			"Account", self.expense_account, ["company", "root_type", "is_group", "disabled"], as_dict=True
		)
		if not account:
			frappe.throw(_("Expense account not found"))
		if account.company != self.company:
			frappe.throw(_("The expense account must belong to {0}").format(self.company))
		if account.root_type != "Expense":
			frappe.throw(_("Select an expense-type account"))
		if account.is_group or account.disabled:
			frappe.throw(_("The expense account must be a non-group, enabled account"))
		# Type name unique per company.
		duplicate = frappe.db.exists(
			"POS Expense Type",
			{"expense_type_name": self.expense_type_name, "company": self.company, "name": ["!=", self.name]},
		)
		if duplicate:
			frappe.throw(_("An expense type named {0} already exists for this company").format(self.expense_type_name))
