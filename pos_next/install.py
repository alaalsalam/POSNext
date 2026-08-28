"""
Installation and Migration hooks for POS Next

This module relies on Frappe's fixture system for:
- Custom fields (custom_field.json)
- Roles (role.json)
- Custom DocPerm (custom_docperm.json)
- Print formats (print_format.json)

The fixtures are defined in hooks.py and synced automatically during install/migrate.
This module handles post-fixture tasks like setting defaults and clearing cache.
"""

import logging

import frappe

# Configure logger
logger = logging.getLogger(__name__)


def after_install():
	"""Hook that runs after app installation"""
	try:
		log_message("POS: Running post-install setup", level="info")
		# A site normally already has its first Company before POS Next is
		# installed, so Company.after_insert cannot prepare it.  Bootstrap the
		# same idempotent company branch here for every fresh installation.
		from pos_next.api.pos_defaults import provision_all_company_pos_defaults

		provision_all_company_pos_defaults()

		# Setup default print format for POS Profiles
		setup_default_print_format()

		# Clear cache to ensure changes take effect
		frappe.clear_cache()
		frappe.db.commit()

		log_message("POS: Installation completed successfully", level="success")
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="POS Installation Error", message=frappe.get_traceback())
		log_message(f"POS: Installation error - {e!s}", level="error")
		raise


def after_migrate():
	"""Hook that runs after bench migrate"""
	try:
		# Reclaim POS Settings if ERPNext re-imported its Single on top of ours.
		# Must run in after_migrate (not as a one-shot patch) because ERPNext's
		# doctype sync runs after pos_next's and would overwrite anything we did
		# during pre/post-model-sync.
		reclaim_pos_settings_doctype(quiet=True)
		migrate_legacy_print_format_names()
		normalize_legacy_pos_branding()

		# Setup default print format
		setup_default_print_format(quiet=True)

		# Keep the durable company branch in sync after an app update as well.
		# This repairs records created while the app was temporarily disabled.
		from pos_next.api.pos_defaults import sync_multi_company_defaults

		sync_multi_company_defaults()

		# Clear cache
		frappe.clear_cache()
		frappe.db.commit()

		log_message("POS: Migration completed successfully", level="success")
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="POS Migration Error", message=frappe.get_traceback())
		log_message(f"POS: Migration error - {str(e)}", level="error")
		raise


def migrate_legacy_print_format_names():
	"""Replace legacy display names without leaving duplicate print formats behind.

	The app package remains ``pos_next`` for compatibility, while print formats are
	user-facing records and must carry the neutral POS identity.  This routine is
	idempotent: it handles both an upgrade where the old record is the only one
	present and a sync where Frappe has already created the new record.
	"""
	for old_name, new_name in {
		"POS Next Receipt": "POS Receipt",
		"POS Next EOD Report": "POS EOD Report",
	}.items():
		if not frappe.db.exists("Print Format", old_name):
			continue

		if frappe.db.exists("Print Format", new_name):
			frappe.db.set_value(
				"POS Profile",
				{"print_format": old_name},
				"print_format",
				new_name,
				update_modified=False,
			)
			frappe.delete_doc("Print Format", old_name, force=True, ignore_permissions=True)
		else:
			frappe.rename_doc("Print Format", old_name, new_name, force=True, ignore_permissions=True)


def normalize_legacy_pos_branding():
	"""Replace only the known legacy default identity stored in existing sites."""
	if not frappe.db.exists("DocType", "POS Branding Settings"):
		return

	legacy_values = {
		"app_name": ("Digit POS", "POS"),
		"app_short_name": ("Digit", "POS"),
		"workspace_label": ("Digit POS", "POS"),
		"login_title": ("تسجيل الدخول إلى Digit POS", "تسجيل الدخول إلى نقطة البيع"),
		"receipt_title": ("Digit POS", "نقطة البيع"),
	}
	for fieldname, (old_value, new_value) in legacy_values.items():
		if frappe.db.get_single_value("POS Branding Settings", fieldname) == old_value:
			frappe.db.set_single_value("POS Branding Settings", fieldname, new_value)


def setup_default_print_format(quiet=False):
	"""
	Set POS Receipt as default print format for POS Profiles if not already set.

	Args:
		quiet (bool): If True, suppress detailed logs
	"""
	try:
		# Check if the print format exists
		if not frappe.db.exists("Print Format", "POS Receipt"):
			if not quiet:
				log_message(
					"POS Receipt print format not found, skipping default setup", level="warning"
				)
			return

		# Get all POS Profiles without a print format
		pos_profiles = frappe.get_all(
			"POS Profile", filters={"print_format": ["in", ["", None]]}, fields=["name"]
		)

		if pos_profiles:
			updated_count = 0
			for profile in pos_profiles:
				try:
					frappe.db.set_value(
						"POS Profile", profile.name, "print_format", "POS Receipt", update_modified=False
					)
					if not quiet:
						log_message(f"Set default print format for: {profile.name}", level="info", indent=1)
					updated_count += 1
				except Exception as e:
					log_message(
						f"Error updating POS Profile {profile.name}: {str(e)}", level="error", indent=1
					)

			if updated_count > 0 and not quiet:
				log_message(
					f"Updated {updated_count} POS Profile(s) with default print format", level="success"
				)

	except Exception as e:
		log_message(f"Error setting up default print format: {str(e)}", level="error")
		frappe.log_error(title="Default Print Format Setup Error", message=frappe.get_traceback())


def log_message(message, level="info", indent=0):
	"""
	Standardized logging function with consistent formatting.

	Args:
		message (str): The message to log
		level (str): Log level - info, success, warning, error
		indent (int): Indentation level (0, 1, 2, etc.)
	"""
	indent_str = "  " * indent

	prefixes = {
		"info": "[INFO]",
		"success": "[SUCCESS]",
		"warning": "[WARNING]",
		"error": "[ERROR]",
	}

	prefix = prefixes.get(level, "[INFO]")
	formatted_message = f"{indent_str}{prefix} {message}"

	# Print to console
	print(formatted_message)

	# Also log to frappe logger
	if level == "error":
		logger.error(message)
	elif level == "warning":
		logger.warning(message)
	else:
		logger.info(message)


def reclaim_pos_settings_doctype(quiet=False):
	"""Reclaim the `POS Settings` DocType from ERPNext.

	ERPNext ships a Single `POS Settings` (module Accounts) with only
	`invoice_fields` and `pos_search_fields`. POS Next ships its own
	non-Single `POS Settings` (module POS Next) with per-profile config
	and a `barcode_rules` child table. Because ERPNext is in our
	`required_apps` its doctype sync runs after ours during `bench
	migrate`, so its JSON wins on disk unless we re-install our version
	after both apps have finished syncing.

	Runs from `after_migrate`. Idempotent: if the live doctype already
	belongs to POS Next (module == 'POS Next' and not Single), exits
	without touching anything.
	"""
	if not frappe.db.exists("DocType", "POS Settings"):
		if not quiet:
			log_message("POS Settings DocType missing, skipping reclaim", level="warning")
		return

	row = frappe.db.get_value("DocType", "POS Settings", ["module", "issingle"], as_dict=True)
	if row and row.module == "POS Next" and not row.issingle:
		if not quiet:
			log_message("POS Settings already owned by POS Next, nothing to reclaim", level="info")
		return

	if not quiet:
		log_message(
			f"Reclaiming POS Settings DocType (was module={row.module if row else '?'}, "
			f"issingle={row.issingle if row else '?'})",
			level="warning",
		)

	try:
		# Commit any open transaction first — DROP TABLE is DDL and would
		# otherwise trigger ImplicitCommitError under Frappe's safety check.
		frappe.db.commit()
		frappe.db.sql("DROP TABLE IF EXISTS `tabPOS Settings`")
		frappe.db.commit()
		frappe.db.sql("DELETE FROM `tabSingles` WHERE doctype = 'POS Settings'")
		frappe.db.sql("DELETE FROM `tabDocField` WHERE parent = 'POS Settings'")
		frappe.db.sql("DELETE FROM `tabDocPerm` WHERE parent = 'POS Settings'")
		frappe.db.sql("DELETE FROM `tabDocType` WHERE name = 'POS Settings'")
		frappe.db.commit()
		log_message("Dropped legacy POS Settings meta + table", level="info", indent=1)
	except Exception:
		frappe.log_error(
			title="POS Settings Reclaim Error",
			message="Failed to drop legacy POS Settings\n\n" + frappe.get_traceback(),
		)
		raise

	try:
		frappe.reload_doc("pos_next", "doctype", "pos_settings", force=True)
		frappe.reload_doc("pos_next", "doctype", "pos_barcode_rules", force=True)
		frappe.reload_doc("pos_next", "doctype", "pos_allowed_locale", force=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			title="POS Settings Reclaim Error",
			message="Failed to reload pos_next doctypes\n\n" + frappe.get_traceback(),
		)
		raise

	after = frappe.db.get_value("DocType", "POS Settings", ["module", "issingle"], as_dict=True)
	if not after or after.module != "POS Next" or after.issingle:
		frappe.log_error(
			title="POS Settings Reclaim Error",
			message=(
				f"Reclaim ran but doctype still wrong: {after}. "
				"ERPNext may be re-importing POS Settings later in the migration."
			),
		)
		log_message(f"Reclaim verification FAILED — doctype is now {after}", level="error")
		return

	if not quiet:
		log_message(
			f"POS Settings reclaimed (module={after.module}, issingle={after.issingle})",
			level="success",
		)
