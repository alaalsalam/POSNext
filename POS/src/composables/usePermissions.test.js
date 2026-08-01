import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/utils/apiWrapper", () => ({ call: vi.fn() }))

import { call } from "@/utils/apiWrapper"
import {
	invalidatePOSPermissions,
	loadPOSPermissions,
	posPermissions,
	refreshPOSPermissions,
} from "./usePermissions"

describe("shared POS permission cache", () => {
	beforeEach(() => {
		invalidatePOSPermissions()
		call.mockReset()
	})

	it("loads permissions once for a session", async () => {
		call.mockResolvedValue({ can_view_reports: false })

		await loadPOSPermissions({ posProfile: "POS-A" })
		await loadPOSPermissions({ posProfile: "POS-A" })

		expect(call).toHaveBeenCalledTimes(1)
		expect(posPermissions.value.can_view_reports).toBe(false)
	})

	it("invalidates and reloads after a feature flag realtime event", async () => {
		call
			.mockResolvedValueOnce({ can_view_reports: false })
			.mockResolvedValueOnce({ can_view_reports: true })

		await loadPOSPermissions({ posProfile: "POS-A" })
		await refreshPOSPermissions("POS-A")

		expect(call).toHaveBeenCalledTimes(2)
		expect(call).toHaveBeenLastCalledWith(
			"pos_next.api.permissions.get_pos_permissions",
			{
				pos_profile: "POS-A",
			},
		)
		expect(posPermissions.value.can_view_reports).toBe(true)
	})
})
