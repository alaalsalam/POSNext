import { silentPrintDoc } from "./printInvoice";

const EOD_PRINT_FORMAT = "POS Next EOD Report";

function openBrowserEODPrint(closingShiftName) {
	const params = new URLSearchParams({
		doctype: "POS Closing Shift",
		name: closingShiftName,
		format: EOD_PRINT_FORMAT,
		no_letterhead: "1",
		trigger_print: "1",
		_lang: window.frappe?.boot?.lang || "en",
		_t: String(Date.now()),
	});

	const printWindow = window.open(`/printview?${params}`, "_blank", "width=800,height=650");
	if (!printWindow) {
		throw new Error(__("Popup blocked — check your browser settings."));
	}
	return true;
}

export async function printEODReport(closingShiftName) {
	try {
		await silentPrintDoc("POS Closing Shift", closingShiftName, EOD_PRINT_FORMAT);
		return { method: "silent" };
	} catch (error) {
		// Closing a shift must not depend on QZ Tray or a preselected local printer.
		openBrowserEODPrint(closingShiftName);
		return { method: "browser" };
	}
}
