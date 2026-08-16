"""Install the native POS inventory role and permissions."""

from pos_next.patches.v2_1_0.native_pos_roles import execute as install_roles


def execute():
	install_roles()
