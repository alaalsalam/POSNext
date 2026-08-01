# Copyright (c) 2025, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from pos_next.api.constants import DEFAULT_POS_SETTINGS
from pos_next.api.feature_flags import (
	assert_feature_manager,
	assert_profile_access,
	publish_feature_flag_update,
	validate_feature_dependencies,
)


class POSSettings(Document):
	def validate(self):
		"""Validate POS Settings"""
		assert_feature_manager()
		validate_feature_dependencies(self)

		# Guard against None values and validate discount percentage
		max_discount = flt(self.max_discount_allowed)
		if max_discount < 0 or max_discount > 100:
			frappe.throw("Max Discount Allowed must be between 0 and 100")

		# Guard against None values and validate search limit
		if self.use_limit_search:
			search_limit = cint(self.search_limit)
			if search_limit <= 0:
				frappe.throw("Search Limit must be greater than 0")

		# Validate use_exact_amount cannot be enabled with credit sale or partial payment
		if cint(self.use_exact_amount):
			if cint(self.allow_credit_sale):
				frappe.throw(
					"'Use Exact Amount for Non-Cash' cannot be enabled together with 'Allow Credit Sale'. "
					"Please disable Credit Sale first."
				)
			if cint(self.allow_partial_payment):
				frappe.throw(
					"'Use Exact Amount for Non-Cash' cannot be enabled together with 'Allow Partial Payment'. "
					"Please disable Partial Payment first."
				)

	def on_update(self):
		"""Sync allow_negative_stock with Stock Settings"""
		self.sync_negative_stock_setting()
		publish_feature_flag_update(self)

	def sync_negative_stock_setting(self):
		"""
		Synchronize allow_negative_stock with Stock Settings.

		When enabled in POS Settings, it enables the global Stock Settings.
		When disabled, it only disables global Stock Settings if no other
		POS Settings have it enabled.

		Note: Runs in the same transaction as the save, no manual commits.
		"""
		current_stock_setting = cint(
			frappe.db.get_single_value("Stock Settings", "allow_negative_stock") or 0
		)

		if cint(self.allow_negative_stock):
			# Enable Stock Settings if not already enabled
			if not current_stock_setting:
				frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1, update_modified=False)
				frappe.msgprint(
					"Stock Settings 'Allow Negative Stock' has been automatically enabled.",
					indicator="green",
					alert=True,
				)
		else:
			# Only disable if no other enabled POS Settings have it enabled
			if current_stock_setting:
				# Use count for better performance and clarity
				other_enabled_count = frappe.db.count(
					"POS Settings",
					{
						"allow_negative_stock": 1,
						"enabled": 1,  # Only check enabled POS Settings
						"name": ["!=", self.name],
					},
				)

				if other_enabled_count == 0:
					frappe.db.set_single_value(
						"Stock Settings", "allow_negative_stock", 0, update_modified=False
					)
					frappe.msgprint(
						"Stock Settings 'Allow Negative Stock' has been automatically disabled.",
						indicator="orange",
						alert=True,
					)


@frappe.whitelist()
def get_pos_settings(pos_profile):
	"""
	Get POS Settings for a specific POS Profile.

	Also injects the current global Stock Settings value to show the actual
	source of truth, preventing confusion when the checkbox appears enabled
	but the global setting was changed elsewhere.
	"""
	if not pos_profile:
		return None

	assert_profile_access(pos_profile)
	frappe.has_permission("POS Settings", "read", throw=True)

	settings = frappe.db.get_value("POS Settings", {"pos_profile": pos_profile}, "*", as_dict=True)

	# A read must never create administrative configuration. Return secure defaults
	# until an authorized manager saves a POS Settings document.
	if not settings:
		settings = frappe._dict(DEFAULT_POS_SETTINGS.copy())
		settings.pos_profile = pos_profile

	# Inject the current global Stock Settings value for transparency
	# This helps UI reflect the actual state even if multiple POS Settings exist
	settings["_global_allow_negative_stock"] = cint(
		frappe.db.get_single_value("Stock Settings", "allow_negative_stock") or 0
	)

	return settings


def create_default_settings(pos_profile):
	"""Create default POS Settings for a POS Profile"""
	doc = frappe.new_doc("POS Settings")
	doc.pos_profile = pos_profile
	doc.enabled = 1
	doc.insert()

	return doc.as_dict()


@frappe.whitelist()
def update_pos_settings(pos_profile, settings):
	"""Update POS Settings for a POS Profile"""
	import json

	if isinstance(settings, str):
		settings = json.loads(settings)

	assert_feature_manager()
	assert_profile_access(pos_profile)
	frappe.has_permission("POS Settings", "write", throw=True)
	settings = _sanitize_settings_payload(pos_profile, settings)

	# Check if settings exist
	existing = frappe.db.exists("POS Settings", {"pos_profile": pos_profile})

	if existing:
		doc = frappe.get_doc("POS Settings", existing)
		doc.update(settings)
		doc.save()
	else:
		doc = frappe.new_doc("POS Settings")
		doc.pos_profile = pos_profile
		doc.update(settings)
		doc.insert()

	return doc.as_dict()


def _sanitize_settings_payload(pos_profile, settings):
	"""Keep the profile link immutable and accept only writable POS Settings fields."""
	if settings.get("pos_profile") and settings.get("pos_profile") != pos_profile:
		frappe.throw(_("POS Profile cannot be changed through the settings API"), frappe.PermissionError)

	meta = frappe.get_meta("POS Settings")
	layout_fields = {"Section Break", "Column Break", "Tab Break", "HTML", "Button"}
	return {
		fieldname: value
		for fieldname, value in settings.items()
		if fieldname != "pos_profile"
		and (df := meta.get_field(fieldname))
		and not df.read_only
		and df.fieldtype not in layout_fields
	}
