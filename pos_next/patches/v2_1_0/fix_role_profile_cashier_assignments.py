"""Migrate legacy cashier assignments stored in Frappe Role Profiles."""

from pos_next.patches.v2_1_0.native_pos_roles import _migrate_legacy_cashier_role


def execute():
	_migrate_legacy_cashier_role()
