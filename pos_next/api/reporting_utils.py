# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Pure helpers shared by profile-scoped POS reports."""

import hashlib
import re
import unicodedata

from frappe.utils import add_days, date_diff, get_datetime, getdate


def add_datetime_bounds(filters):
	"""Add half-open datetime bounds while retaining the user's date filters."""
	filters = filters if filters is not None else {}
	if filters.get("from_date"):
		filters["from_datetime"] = str(get_datetime(getdate(filters.get("from_date"))))
	if filters.get("to_date"):
		filters["to_datetime_exclusive"] = str(
			get_datetime(add_days(getdate(filters.get("to_date")), 1))
		)
	return filters


def inclusive_date_days(from_date, to_date, default=30):
	"""Return an inclusive calendar-day count for rate calculations."""
	if not from_date or not to_date:
		return default
	return max(date_diff(to_date, from_date) + 1, 1)


def payment_method_fieldnames(methods):
	"""Return stable, ASCII, collision-resistant field prefixes for payment methods."""
	result = {}
	for method in methods:
		text = unicodedata.normalize("NFKC", str(method or "Unspecified"))
		ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
		base = re.sub(r"[^a-z0-9]+", "_", ascii_text.casefold()).strip("_") or "payment"
		digest = hashlib.blake2s(text.encode("utf-8"), digest_size=4).hexdigest()
		result[method] = f"m_{base[:32]}_{digest}"
	return result
