// Desk landing + legacy-workspace redirect for pos_next.
//
// 1. Empty Desk route ("/desk" or "/app" with no workspace) is redirected to the
//    user's OWN default workspace (User.default_workspace) — and ONLY when they
//    have one set. Users without a default workspace are left on Frappe's stock
//    app-launcher grid, so this never forces POS on non-POS admins. Frappe v16
//    shows the grid at the empty route instead of honoring default_workspace on a
//    hard load; this bridges that gap using each user's own configured default.
// 2. Legacy renamed workspace routes are forwarded to the current "pos" workspace.
//
// Loads via app_include_js, so it runs only on Desk pages — never the /pos SPA,
// web pages, or web forms.
(function () {
	const targetRoute = "pos";
	const posRoles = new Set(["POS Cashier", "POS Manager", "POS Purchases", "POS Expenses", "POS Cash Management", "POS Reports", "POS Catalog Manager", "POS Inventory Controller"]);
	const legacyRoutes = new Set([
		"pos-trilogy",
		"pos_trilogy",
		"pos-yemenfrappe",
		"pos_yemenfrappe",
		"posnext",
	]);

	function currentWorkspaceSlug() {
		if (window.frappe && typeof frappe.get_route === "function") {
			const route = frappe.get_route();
			if (!Array.isArray(route)) return null;
			// Desk workspace routes look like ["<slug>"] or ["app"/"desk", "<slug>"].
			if (route[0] === "app" || route[0] === "desk" || route[0] === "Workspaces") {
				return route[1] || "";
			}
			return route[0] != null ? route[0] : "";
		}
		const match = window.location.pathname.match(/\/(?:app|desk)\/([^/?#]+)/);
		return match ? decodeURIComponent(match[1]) : "";
	}

	function goToWorkspace(slug) {
		if (window.frappe && typeof frappe.set_route === "function") {
			frappe.set_route(slug);
		} else {
			// The base path (/app vs /desk) differs per site; reuse the current one.
			const base = window.location.pathname.startsWith("/desk") ? "/desk" : "/app";
			window.location.replace(`${base}/${slug}`);
		}
	}

	function defaultWorkspaceSlug() {
		const name = window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.default_workspace
			? frappe.boot.user.default_workspace.name
			: null;
		if (!name) return null;
		const slug = frappe.router && typeof frappe.router.slug === "function"
			? frappe.router.slug(name)
			: String(name).toLowerCase();
		// Only redirect to a workspace that actually exists for this user.
		if (frappe.workspaces && !frappe.workspaces[slug]) return null;
		return slug;
	}

	function isPosUser() {
		const roles = (window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
		return roles.some((role) => posRoles.has(role));
	}

	function maybeRedirect() {
		const slug = currentWorkspaceSlug();

		if (legacyRoutes.has(slug)) {
			goToWorkspace(targetRoute);
			return;
		}

		// Empty route → user's own default workspace (if any).
		if (slug === "" || slug == null) {
			const dw = defaultWorkspaceSlug();
			if (dw) {
				goToWorkspace(dw);
				return;
			}
			if (isPosUser()) {
				goToWorkspace(targetRoute);
			}
		}
	}

	window.addEventListener("load", maybeRedirect);
	window.addEventListener("popstate", maybeRedirect);
	window.addEventListener("hashchange", maybeRedirect);
	setTimeout(maybeRedirect, 0);
	setTimeout(maybeRedirect, 500);
})();
