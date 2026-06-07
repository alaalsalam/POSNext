frappe.ui.form.on("POS Branding Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Reset to Generic Defaults"), () => {
			frappe.confirm(
				__("Reset POS branding to generic defaults?"),
				() => {
					frappe.call({
						method: "pos_next.pos_next.doctype.pos_branding_settings.pos_branding_settings.reset_to_defaults",
						callback() {
							frm.reload_doc()
						},
					})
				}
			)
		})
	},
})
