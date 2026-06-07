# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
BrainWise Branding API
Provides secure branding configuration and validation endpoints
"""

import frappe
from frappe import _
import json
import base64
import hashlib


@frappe.whitelist(allow_guest=False)
def get_branding_config():
	"""
	Get branding configuration with encryption
	Returns obfuscated branding data for frontend use
	"""
	try:
		# Check if doctype exists and get config
		if not frappe.db.exists("DocType", "BrainWise Branding"):
			# Return default config if doctype doesn't exist yet
			return get_default_config()

		doc = frappe.get_single("BrainWise Branding")

		if not doc.enabled:
			return get_default_config()

		# Return obfuscated configuration
		config = {
			"_t": base64.b64encode(doc.brand_text.encode()).decode(),
			"_l": base64.b64encode(doc.brand_name.encode()).decode(),
			"_u": base64.b64encode(doc.brand_url.encode()).decode(),
			"_i": doc.check_interval or 10000,
			"_sig": doc.encrypted_signature,
			"_ts": frappe.utils.now(),
			"_v": doc.enable_server_validation,
			"_c": "pos-footer-component",
			"_s": {
				"p": "12px 20px",
				"bg": "#f8f9fa",
				"bt": "1px solid #e0e0e0",
				"ta": "center",
				"fs": "13px",
				"c": "#6b7280",
				"z": 100
			}
		}

		return config
	except Exception as e:
		frappe.log_error(f"Error fetching branding config: {str(e)}", "BrainWise Branding API")
		return get_default_config()


def get_default_config():
	"""Return default branding configuration"""
	return {
		"_t": base64.b64encode("Powered by".encode()).decode(),
		"_l": base64.b64encode("BrainWise".encode()).decode(),
		"_u": base64.b64encode("https://nexus.brainwise.me".encode()).decode(),
		"_i": 10000,
		"_v": True,
		"_c": "pos-footer-component",
		"_s": {
			"p": "12px 20px",
			"bg": "#f8f9fa",
			"bt": "1px solid #e0e0e0",
			"ta": "center",
			"fs": "13px",
			"c": "#6b7280",
			"z": 100
		}
	}


@frappe.whitelist(allow_guest=False)
def validate_branding(client_signature=None, brand_name=None, brand_url=None):
	"""
	Validate branding integrity from client
	Logs tampering attempts and validates signatures
	"""
	try:
		# Check if doctype exists
		if not frappe.db.exists("DocType", "BrainWise Branding"):
			return {"valid": True, "message": "Branding doctype not installed"}

		doc = frappe.get_single("BrainWise Branding")

		if not doc.enabled or not doc.enable_server_validation:
			return {"valid": True, "message": "Validation disabled"}

		# Validate branding data
		is_valid = (
			brand_name == doc.brand_name and
			brand_url == doc.brand_url
		)

		if not is_valid:
			# Log tampering attempt
			log_tampering_attempt(doc, {
				"type": "validation_failed",
				"user": frappe.session.user,
				"timestamp": frappe.utils.now(),
				"client_signature": client_signature,
				"expected_brand": doc.brand_name,
				"received_brand": brand_name,
				"expected_url": doc.brand_url,
				"received_url": brand_url,
				"ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
			})

		# Update last validation time
		frappe.db.set_value("BrainWise Branding", doc.name, "last_validation", frappe.utils.now())
		frappe.db.commit()

		return {
			"valid": is_valid,
			"timestamp": frappe.utils.now(),
			"message": "Validation successful" if is_valid else "Branding mismatch detected"
		}
	except Exception as e:
		frappe.log_error(f"Error validating branding: {str(e)}", "BrainWise Branding Validation")
		return {"valid": False, "error": str(e)}


@frappe.whitelist(allow_guest=False)
def log_client_event(event_type=None, details=None):
	"""
	Log client-side events (clicks, removals, modifications)
	Used for monitoring branding tampering attempts
	"""
	try:
		# Check if doctype exists
		if not frappe.db.exists("DocType", "BrainWise Branding"):
			return {"logged": False, "message": "Branding doctype not installed"}

		doc = frappe.get_single("BrainWise Branding")

		if not doc.log_tampering_attempts:
			return {"logged": False, "message": "Logging disabled"}

		# Parse details if string
		if isinstance(details, str):
			try:
				details = json.loads(details)
			except:
				pass

		# Log different event types
		if event_type in ["removal", "modification", "hide", "integrity_fail", "visibility_change"]:
			log_tampering_attempt(doc, {
				"event_type": event_type,
				"user": frappe.session.user,
				"timestamp": frappe.utils.now(),
				"details": details,
				"ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
			})

			return {"logged": True, "message": f"Event {event_type} logged"}
		elif event_type == "link_click":
			# Log link clicks (for analytics)
			frappe.log_error(
				title="BrainWise Branding - Link Click",
				message=json.dumps({
					"user": frappe.session.user,
					"timestamp": frappe.utils.now(),
					"details": details
				}, indent=2)
			)
			return {"logged": True, "message": "Link click logged"}

		return {"logged": False, "message": f"Unknown event type: {event_type}"}
	except Exception as e:
		frappe.log_error(f"Error logging client event: {str(e)}", "BrainWise Branding Event Log")
		return {"logged": False, "error": str(e)}


def log_tampering_attempt(doc, details):
	"""Internal function to log tampering attempts"""
	try:
		# Increment tampering counter
		current_attempts = frappe.db.get_value("BrainWise Branding", doc.name, "tampering_attempts") or 0
		frappe.db.set_value("BrainWise Branding", doc.name, "tampering_attempts", current_attempts + 1)
		frappe.db.commit()

		# Create error log
		frappe.log_error(
			title="BrainWise Branding - Tampering Detected",
			message=json.dumps(details, indent=2, default=str)
		)
	except Exception as e:
		frappe.log_error(f"Error logging tampering: {str(e)}", "BrainWise Branding")


@frappe.whitelist(allow_guest=False)
def get_tampering_stats():
	"""Get tampering statistics (admin only)"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		if not frappe.db.exists("DocType", "BrainWise Branding"):
			return {"enabled": False, "message": "Branding doctype not installed"}

		doc = frappe.get_single("BrainWise Branding")

		return {
			"enabled": doc.enabled,
			"tampering_attempts": doc.tampering_attempts or 0,
			"last_validation": doc.last_validation,
			"server_validation": doc.enable_server_validation,
			"logging_enabled": doc.log_tampering_attempts
		}
	except Exception as e:
		frappe.log_error(f"Error getting tampering stats: {str(e)}", "BrainWise Branding Stats")
		return {"error": str(e)}

# -----------------------------------------------------------------------------
# POS Branding Settings
# -----------------------------------------------------------------------------
import re
from werkzeug.wrappers import Response

POS_BRANDING_DOCTYPE = "POS Branding Settings"

POS_DEFAULT_BRANDING = {
	"enabled": 1,
	"app_name": "POSNext",
	"app_short_name": "POS",
	"workspace_label": "POS",
	"login_title": "Sign in to POS",
	"login_subtitle": "Enter your username and password to open the point of sale.",
	"primary_logo": "",
	"header_logo": "",
	"app_icon": "",
	"pwa_icon_192": "",
	"pwa_icon_512": "",
	"primary_color": "#4F46E5",
	"secondary_color": "#2563EB",
	"theme_color": "#4F46E5",
	"background_color": "#ffffff",
	"install_button_label": "Install",
	"receipt_title": "POS",
	"receipt_footer": "",
	"demo_banner_enabled": 0,
	"demo_banner_text": "",
	"custom_css_optional": "",
}

POS_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")

DEFAULT_BRANDING = POS_DEFAULT_BRANDING


def _has_pos_branding_doctype():
	return frappe.db.exists("DocType", POS_BRANDING_DOCTYPE)


def _clean_pos_text(value, fallback):
	value = (value or "").strip()
	return value or fallback


def _clean_pos_color(value, fallback):
	value = (value or "").strip()
	return value if POS_COLOR_RE.match(value) else fallback


def _clean_pos_asset_url(value):
	value = (value or "").strip()
	if not value:
		return ""
	if value.startswith(("/files/", "/private/files/", "/assets/")):
		return value
	if value.startswith(("http://", "https://")):
		return value
	return ""


def get_pos_branding_settings_doc():
	"""Return normalized POS branding settings with safe generic fallbacks."""
	settings = POS_DEFAULT_BRANDING.copy()

	if _has_pos_branding_doctype():
		try:
			doc = frappe.get_single(POS_BRANDING_DOCTYPE)
			if not doc.get("enabled"):
				return settings

			for fieldname in settings:
				value = doc.get(fieldname)
				if value not in (None, ""):
					settings[fieldname] = value
		except Exception:
			frappe.log_error(frappe.get_traceback(), "POS Branding Settings Load Error")

	for key in ("app_name", "app_short_name", "workspace_label", "login_title", "login_subtitle", "install_button_label", "receipt_title"):
		settings[key] = _clean_pos_text(settings.get(key), POS_DEFAULT_BRANDING[key])

	for key in ("primary_logo", "header_logo", "app_icon", "pwa_icon_192", "pwa_icon_512"):
		settings[key] = _clean_pos_asset_url(settings.get(key))

	for key in ("primary_color", "secondary_color", "theme_color", "background_color"):
		settings[key] = _clean_pos_color(settings.get(key), POS_DEFAULT_BRANDING[key])

	settings["enabled"] = 1 if settings.get("enabled") else 0
	settings["demo_banner_enabled"] = 1 if settings.get("demo_banner_enabled") else 0
	settings["receipt_footer"] = settings.get("receipt_footer") or ""
	settings["demo_banner_text"] = settings.get("demo_banner_text") or ""
	settings["custom_css_optional"] = settings.get("custom_css_optional") or ""
	return settings


@frappe.whitelist(allow_guest=True)
def get_pos_branding_settings():
	"""Public read endpoint used by the POS frontend before login."""
	return get_pos_branding_settings_doc()


def build_pos_manifest():
	branding = get_pos_branding_settings_doc()
	icon_192 = branding.get("pwa_icon_192") or branding.get("app_icon") or "/assets/pos_next/pos/icon.svg"
	icon_512 = branding.get("pwa_icon_512") or branding.get("app_icon") or "/assets/pos_next/pos/icon.svg"

	return {
		"name": branding["app_name"],
		"short_name": branding["app_short_name"],
		"id": "/pos",
		"start_url": "/pos",
		"scope": "/pos",
		"display": "standalone",
		"lang": "ar",
		"dir": "rtl",
		"background_color": branding["background_color"],
		"theme_color": branding["theme_color"],
		"description": branding.get("login_subtitle") or _("Point of Sale application"),
		"categories": ["business", "productivity"],
		"icons": [
			{"src": icon_192, "sizes": "192x192", "type": "image/svg+xml" if icon_192.endswith(".svg") else "image/png", "purpose": "any"},
			{"src": icon_512, "sizes": "512x512", "type": "image/svg+xml" if icon_512.endswith(".svg") else "image/png", "purpose": "any"},
			{"src": icon_512, "sizes": "512x512", "type": "image/svg+xml" if icon_512.endswith(".svg") else "image/png", "purpose": "maskable"},
		],
	}


@frappe.whitelist(allow_guest=True)
def get_pos_manifest():
	"""Return the PWA manifest as top-level JSON for browser manifest loading."""
	return Response(
		json.dumps(build_pos_manifest(), separators=(",", ":")),
		mimetype="application/manifest+json",
		headers={"Cache-Control": "no-store"},
	)
