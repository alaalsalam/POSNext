// Account overview injected only into the POS Desk workspace.
(function () {
	const ROOT_ID = "pos-workspace-overview";
	const routeIsPOS = () => (frappe.get_route() || [])[0] === "pos";
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const money = (value, currency) => format_currency(value || 0, currency || undefined);

	function card(icon, label, value, note, tone) {
		return `<article class="pos-overview-card ${tone}">
			<div class="pos-overview-card-icon">${frappe.utils.icon(icon, "md")}</div>
			<div><span>${escape(label)}</span><strong>${escape(value)}</strong><small>${escape(note)}</small></div>
		</article>`;
	}

	function render(data) {
		const root = document.getElementById(ROOT_ID);
		if (!root) return;
		const scope = `${data.profile_count} ${__("POS profiles")} · ${data.company_count} ${__("companies")}`;
		const invoices = (data.recent_invoices || []).map((invoice) => `
			<a class="pos-overview-invoice" href="/desk/sales-invoice/${encodeURIComponent(invoice.name)}">
				<span><b>${escape(invoice.name)}</b><small>${escape(invoice.customer_name)}</small></span>
				<strong class="${invoice.is_return ? "is-return" : ""}">${invoice.is_return ? "−" : ""}${escape(money(invoice.grand_total, data.currency))}</strong>
			</a>`).join("") || `<p class="pos-overview-empty">${escape(__("No POS invoices have been submitted today."))}</p>`;

		root.innerHTML = `<section class="pos-overview" dir="auto">
			<header class="pos-overview-hero">
				<div><p>${escape(__("POS account overview"))}</p><h2>${escape(__("Today at a glance"))}</h2><small>${escape(scope)}</small></div>
				<a class="btn btn-primary" href="/pos/">${frappe.utils.icon("shopping-cart", "sm")} ${escape(__("Start Selling"))}</a>
			</header>
			<div class="pos-overview-grid">
				${card("banknote", __("Today's sales"), money(data.today_sales, data.currency), `${data.today_invoices} ${__("invoices")}`, "emerald")}
				${card("calendar-days", __("This month's net sales"), money(data.month_sales, data.currency), __("after returns"), "blue")}
				${card("rotate-ccw", __("Returns today"), money(data.today_returns, data.currency), __("submitted returns"), "amber")}
				${card("store", __("Open shifts"), data.open_shifts, __("currently active"), "violet")}
			</div>
			<section class="pos-overview-recent"><div class="pos-overview-section-title"><h3>${escape(__("Recent sales"))}</h3><a href="/desk/sales-invoice">${escape(__("View all invoices"))}</a></div>${invoices}</section>
		</section>`;
	}

	function mount() {
		if (!routeIsPOS() || document.getElementById(ROOT_ID)) return;
		const workspace = document.querySelector(".workspace-page .layout-main-section, .workspace-page .page-content");
		if (!workspace) return;
		const root = document.createElement("div");
		root.id = ROOT_ID;
		root.innerHTML = `<div class="pos-overview-loading">${escape(__("Loading POS overview…"))}</div>`;
		workspace.prepend(root);
		frappe.call({ method: "pos_next.api.workspace_dashboard.get_workspace_overview" })
			.then((response) => render(response.message || {}))
			.catch(() => root.remove());
	}

	function scheduleMount() {
		[0, 180, 700].forEach((delay) => setTimeout(mount, delay));
	}
	frappe.router.on("change", scheduleMount);
	$(scheduleMount);
})();
