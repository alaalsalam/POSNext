export function isRtlLocale(language, documentDirection) {
	return documentDirection === "rtl" || language === "ar"
}

export function buildDeskReportUrl(name, posProfile, fromDate, toDate) {
	const query = new URLSearchParams({
		pos_profile: posProfile || "",
		from_date: fromDate || "",
		to_date: toDate || "",
	})
	return `/app/query-report/${encodeURIComponent(name)}?${query.toString()}`
}
