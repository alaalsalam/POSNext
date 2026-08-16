// Copyright (c) 2024, BrainWise and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Settings", {
	refresh(frm) {
		set_settings_context(frm);

		// Set query for loyalty program filtered by POS Profile company
		frm.set_query("default_loyalty_program", function () {
			if (!frm.doc.__company) {
				return { filters: {} };
			}
			return {
				filters: {
					company: frm.doc.__company,
				},
			};
		});

		// Fetch company when form loads
		if (frm.doc.pos_profile) {
			fetch_pos_profile_company(frm);
		}
	},

	pos_profile(frm) {
		// Clear loyalty program when POS Profile changes
		frm.set_value("default_loyalty_program", "");
		frm.doc.__company = null;

		if (frm.doc.pos_profile) {
			fetch_pos_profile_company(frm);
		}
	},
});

function fetch_pos_profile_company(frm) {
	frappe.db.get_value("POS Profile", frm.doc.pos_profile, "company", (r) => {
		if (r && r.company) {
			frm.doc.__company = r.company;
			frm.set_value("company", r.company);
			set_settings_context(frm);
		}
	});
}

function set_settings_context(frm) {
	const company = frm.doc.company || frm.doc.__company;
	if (!company) {
		frm.set_intro(__("Select a POS Profile to load its company and configuration context."), "blue");
		return;
	}
	frm.set_intro(
		__("These settings apply only to {0} through POS Profile {1}.", [company, frm.doc.pos_profile]),
		"green",
	);
	frm.set_query("wallet_account", () => ({ filters: { company, is_group: 0, disabled: 0 } }));
	frm.set_query("posa_surplus_account", () => ({ filters: { company, is_group: 0, disabled: 0 } }));
	frm.set_query("posa_default_expense_account", () => ({ filters: { company, is_group: 0, disabled: 0 } }));
	frm.set_query("posa_default_purchase_warehouse", () => ({ filters: { company, is_group: 0, disabled: 0 } }));
	frm.set_query("posa_default_purchase_tax_template", () => ({ filters: { company, disabled: 0 } }));
}
