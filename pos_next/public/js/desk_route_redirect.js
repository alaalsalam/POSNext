// Legacy-workspace redirect for pos_next.
//
// Keep Frappe's native Desk landing page at "/desk" and "/app". Only obsolete
// POS workspace URLs are forwarded to the current "pos" workspace.
//
// Loads via app_include_js, so it runs only on Desk pages — never the /pos SPA,
// web pages, or web forms.
(function () {
	const targetRoute = "pos";
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

	function maybeRedirect() {
		const slug = currentWorkspaceSlug();

		if (legacyRoutes.has(slug)) {
			goToWorkspace(targetRoute);
			return;
		}
	}

	window.addEventListener("load", maybeRedirect);
	window.addEventListener("popstate", maybeRedirect);
	window.addEventListener("hashchange", maybeRedirect);
	setTimeout(maybeRedirect, 0);
	setTimeout(maybeRedirect, 500);
})();
