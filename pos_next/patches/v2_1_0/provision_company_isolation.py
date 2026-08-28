"""Provision durable company boundaries after the User selector is synced."""

from pos_next.api.pos_defaults import (
	provision_all_company_pos_defaults,
	repair_user_company_boundaries,
)


def execute():
	provision_all_company_pos_defaults()
	repair_user_company_boundaries()
