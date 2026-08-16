"""Extend POS company ownership to suppliers, groups, brands, and users."""

from pos_next.patches.v2_1_0.add_multi_company_master_fields import execute as add_fields


def execute():
	add_fields()
