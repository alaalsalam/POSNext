/* Clear, translatable field guidance for the main POS setup screens. */
(function () {
	const guidance = {
		"POS Profile": {
			intro: "Set up the store, warehouse, default walk-in customer, payment methods, and the users who can operate this POS.",
			fields: {
				company: "The company that owns this POS. It determines the available masters, accounts, and users.",
				warehouse: "Stock is sold from this warehouse and availability is calculated from it.",
				customer: "Used automatically for walk-in sales when no named customer is selected.",
				selling_price_list: "The selling prices shown to the cashier for this POS.",
				payments: "Choose the payment methods accepted at this checkout and mark one as the default.",
				item_groups: "Only products in these groups are available in this POS catalog.",
				applicable_for_users: "Only these users can open a shift and sell through this POS.",
			},
		},
		"POS Settings": {
			intro: "Configure how this POS profile sells, pays, prints, and exposes management features.",
			fields: {
				pos_profile: "The POS Profile these settings control.",
				company: "Filled from the POS Profile to make the scope clear.",
				enabled: "Turn off to use the safe system defaults for this POS profile.",
				allow_credit_sale: "Allow a customer to complete a sale with an outstanding balance.",
				allow_return: "Show the return flow and allow authorized users to create returns.",
				allow_user_to_edit_rate: "Lets the cashier edit an item price; promotional pricing still remains protected.",
				enable_purchases: "Show purchases inside POS for users who have the required native permissions.",
				enable_cash_management: "Enable cash entries and cash-control tools for this POS profile.",
			},
		},
		"POS Branding Settings": {
			intro: "Set the site-wide identity and operating mode. These choices apply to every POS profile on this site.",
			fields: {
				tenant_mode: "Multiple Companies isolates POS master data and users by company. Enable it only after company setup is complete.",
				show_demo_accounts: "Shows preconfigured demo accounts on the sign-in page. Keep this off in production.",
				application_name: "The full product name shown in the POS experience.",
				workspace_label: "The name displayed for the POS workspace in the Desk.",
				login_logo: "Logo shown on the POS sign-in screen.",
				receipt_footer: "Short message printed at the bottom of POS receipts.",
			},
		},
		Item: {
			intro: "Create a product once, then use prices and stock transactions to make it ready for sale.",
			fields: {
				item_code: "Unique internal code used in stock, imports, and barcode operations.",
				item_name: "Customer-facing product name shown in POS search and receipts.",
				item_group: "Determines the POS catalog section and company ownership in multi-company mode.",
				stock_uom: "The base unit used to count stock, for example Nos, Kg, or Box.",
				is_stock_item: "Enable when quantities are tracked in warehouses.",
				custom_pos_company: "The company allowed to view and sell this item in multi-company mode.",
			},
		},
		Customer: {
			intro: "Customers are company-scoped in multi-company mode and can be selected during POS checkout.",
			fields: {
				customer_name: "Name shown to the cashier, on invoices, and in customer search.",
				customer_group: "Groups customers for reporting, pricing, and company organization.",
				mobile_no: "Use a unique mobile number when sending receipts or identifying a customer quickly.",
				custom_pos_company: "The company allowed to access this customer in multi-company mode.",
			},
		},
		"Stock Reconciliation": {
			intro: "Use this screen for opening quantities or physical-count adjustments. Submitted rows update inventory and optional POS prices.",
			fields: {
				company: "Filled from the active POS Profile; inventory cannot cross company boundaries.",
				set_warehouse: "The warehouse whose counted quantities will be updated.",
				purpose: "Use Opening Stock for first balances; use Stock Reconciliation for a physical count correction.",
				custom_pos_profile: "Connects optional buying and selling prices to the correct POS price lists.",
			},
		},
	};

	Object.entries(guidance).forEach(([doctype, config]) => {
		frappe.ui.form.on(doctype, {
			refresh(frm) {
				frm.set_intro(__(config.intro));
				Object.entries(config.fields).forEach(([fieldname, description]) => {
					if (frm.fields_dict[fieldname]) frm.set_df_property(fieldname, "description", __(description));
				});
			},
		});
	});
})();
