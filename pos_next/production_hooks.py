"""Minimal lifecycle hooks for the production-safe POS release."""

import frappe


def after_install():
	"""Avoid automatic data provisioning on a live tenant."""
	frappe.clear_cache()


def after_migrate():
	"""Keep schema sync free of data, role, and workspace mutations."""
	frappe.clear_cache()
