"""Grant read-only master-data access required to complete a POS sale."""

from pos_next.patches.v2_1_0.native_pos_roles import _apply_permissions


def execute():
	# The original role patch may already have run on upgraded sites. Reapply the
	# declarative native permissions so those sites receive the new sales-only
	# dependencies as well as fresh installations.
	_apply_permissions()
