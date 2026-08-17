frappe.ui.form.on("User", {
	async onload(frm) {
		const branding = await frappe.call({
			method: "pos_next.api.branding.get_pos_branding_settings",
		});
		if (branding.message?.tenant_mode !== "Multiple Companies") {
			frm.toggle_display("custom_pos_company", false);
			return;
		}

		frm.toggle_display("custom_pos_company", true);
		frm.set_df_property(
			"custom_pos_company",
			"description",
			__("Sets the user's default company and Company User Permission automatically on save."),
		);
		// Company has no `disabled` field in Frappe v16.  Filtering on it makes
		// the Link query fail before the user can select an allowed company.
		// Native Company read permission and Company User Permissions remain the
		// authority for the available choices.

		if (frm.is_new() && !frm.doc.custom_pos_company) {
			const context = await frappe.call({ method: "pos_next.api.utilities.check_user_company" });
			if (context.message?.has_company) {
				await frm.set_value("custom_pos_company", context.message.company);
			}
		}
	},
});
