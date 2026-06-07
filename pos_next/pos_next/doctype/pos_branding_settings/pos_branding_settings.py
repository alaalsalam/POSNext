import frappe
from frappe.model.document import Document

from pos_next.api.branding import DEFAULT_BRANDING


class POSBrandingSettings(Document):
	def before_insert(self):
		self.apply_defaults()

	def validate(self):
		self.apply_defaults()

	def apply_defaults(self):
		for fieldname, value in DEFAULT_BRANDING.items():
			if self.get(fieldname) in (None, ""):
				self.set(fieldname, value)

		if not self.workspace_label:
			self.workspace_label = "POS"


@frappe.whitelist()
def reset_to_defaults():
	if not frappe.has_permission("POS Branding Settings", "write"):
		frappe.throw("Not permitted")

	doc = frappe.get_single("POS Branding Settings")
	for fieldname, value in DEFAULT_BRANDING.items():
		doc.set(fieldname, value)
	doc.save()
	return doc.as_dict()
