(function () {
  const targetRoute = 'pos-trilogy';
  const legacyRoutes = new Set(['pos-yemenfrappe', 'pos_yemenfrappe', 'posnext']);

  function getDeskRoute() {
    if (window.frappe && typeof frappe.get_route === 'function') {
      const route = frappe.get_route();
      if (Array.isArray(route) && route[0] === 'app') {
        return route[1];
      }
      return Array.isArray(route) ? route[0] : null;
    }

    const match = window.location.pathname.match(/\/app\/([^/?#]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  function redirectLegacyWorkspace() {
    const route = getDeskRoute();
    if (!legacyRoutes.has(route)) return;

    if (window.frappe && typeof frappe.set_route === 'function') {
      frappe.set_route('app', targetRoute);
    } else {
      window.location.replace('/app/' + targetRoute);
    }
  }

  window.addEventListener('load', redirectLegacyWorkspace);
  window.addEventListener('popstate', redirectLegacyWorkspace);
  window.addEventListener('hashchange', redirectLegacyWorkspace);
  setTimeout(redirectLegacyWorkspace, 0);
  setTimeout(redirectLegacyWorkspace, 500);
})();
