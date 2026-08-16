frappe.ui.form.on("Stock Reconciliation", {
	refresh(frm) {
		frm.set_query("set_warehouse", () => ({ filters: { company: frm.doc.company, is_group: 0, disabled: 0 } }));
		frm.set_query("expense_account", () => ({ filters: { company: frm.doc.company, is_group: 0, disabled: 0 } }));
		if (frm.is_new() && !frm.doc.company) load_pos_inventory_context(frm);
	},
});

async function load_pos_inventory_context(frm) {
	try {
		const response = await frappe.call({ method: "pos_next.api.inventory.get_stock_reconciliation_context" });
		const context = response.message;
		if (!context) return;
		await frm.set_value("company", context.company);
		await frm.set_value("set_warehouse", context.warehouse);
		await frm.set_value("custom_pos_profile", context.pos_profile);
		await frm.set_value("purpose", "Stock Reconciliation");
		frm.set_intro(__("Inventory adjustment for {0} in warehouse {1}. Choose Opening Stock only for initial balances.", [context.company, context.warehouse]), "blue");
	} catch (error) {
		console.warn("POS inventory context was not loaded", error);
	}
}

frappe.ui.form.on("Stock Reconciliation Item", {
	custom_pos_buying_rate(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.custom_pos_buying_rate) frappe.model.set_value(cdt, cdn, "valuation_rate", row.custom_pos_buying_rate);
	},
});
