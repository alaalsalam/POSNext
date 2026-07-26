/**
 * POS Settings Configuration
 * Centralized configuration for themes, icons, and section structures
 * Design: clean white cards, colored icons only — no heavy colored backgrounds.
 */

// SVG Icon Paths
export const icons = {
	warehouse: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
	shoppingCart:
		"M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z",
	checkCircle: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
	currency:
		"M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
	location:
		"M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z",
	clipboard:
		"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
	tag: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
	info: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
	warning: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

/**
 * Section header themes — clean white, icon-only color accents.
 * Each key maps to a module section (stock, sales, etc.)
 */
const sectionThemes = {
	/* Inventory / Stock */
	purple: {
		header: "px-6 py-4 bg-white border-b border-gray-100",
		iconContainer: "p-2 bg-emerald-50 rounded-lg",
		icon: "w-6 h-6 text-emerald-600",
		badge: "flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full",
		badgeIcon: "w-3.5 h-3.5 text-emerald-600",
		badgeText: "text-xs font-semibold text-emerald-700",
	},
	/* Sales / Operations */
	green: {
		header: "px-6 py-4 bg-white border-b border-gray-100",
		iconContainer: "p-2 bg-slate-100 rounded-lg",
		icon: "w-6 h-6 text-slate-600",
		badge: "flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200 rounded-full",
		badgeIcon: "w-3.5 h-3.5 text-slate-500",
		badgeText: "text-xs font-semibold text-slate-600",
	},
};

/**
 * Subsection card themes — white cards with subtle borders, no gradient fills.
 */
const subsectionThemes = {
	/* Neutral / general */
	gray: {
		container: "bg-gray-50 rounded-xl p-5 border border-gray-200",
		icon: "w-5 h-5 text-gray-500",
	},
	/* Stock policy — white card */
	blue: {
		container: "bg-white rounded-xl p-5 border border-gray-200 shadow-sm",
		icon: "w-5 h-5 text-emerald-600",
	},
	/* Pricing / highlight — very faint emerald tint */
	emerald: {
		container: "bg-emerald-50/50 rounded-xl p-5 border border-emerald-100",
		icon: "w-5 h-5 text-emerald-600",
	},
	/* Operations / misc */
	teal: {
		container: "bg-white rounded-xl p-5 border border-gray-200 shadow-sm",
		icon: "w-5 h-5 text-slate-500",
	},
	/* Stock sync — white card */
	indigo: {
		container: "bg-white rounded-xl p-5 border border-gray-200 shadow-sm",
		icon: "w-5 h-5 text-slate-500",
	},
};

/**
 * Returns section header classes for a given theme key.
 * Returns the full class strings directly (no string concatenation with unknown tokens).
 */
export function getSectionHeaderClasses(theme) {
	const config = sectionThemes[theme] || sectionThemes.purple;
	return { ...config };
}

/**
 * Returns subsection card classes for a given theme key.
 */
export function getSubsectionClasses(theme) {
	const config = subsectionThemes[theme] || subsectionThemes.gray;
	return {
		container: config.container,
		icon: config.icon,
	};
}
