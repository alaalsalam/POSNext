<template>
	<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
		<!-- Header -->
		<div
			class="px-6 py-4 bg-gradient-to-r from-emerald-50 via-green-50 to-teal-50 border-b border-gray-200"
		>
			<div class="flex items-center gap-3">
				<div class="p-2 bg-green-100 rounded-lg">
					<svg
						class="w-6 h-6 text-green-600"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
						/>
					</svg>
				</div>
				<div>
					<h3 class="text-base font-bold text-gray-900">{{ __("Brand Identity") }}</h3>
					<p class="text-xs text-gray-500">
						{{ __("Change the app name, logo and colors — applied instantly.") }}
					</p>
				</div>
			</div>
		</div>

		<div class="p-6 flex flex-col gap-5">
			<!-- Site operation mode -->
			<div class="rounded-lg border border-amber-200 bg-amber-50 p-4">
				<h4 class="text-sm font-bold text-amber-950">{{ __("Site operation") }}</h4>
				<label class="mt-3 flex flex-col gap-1">
					<span class="text-sm font-medium text-gray-700">{{ __("Company mode") }}</span>
					<select v-model="form.tenant_mode" class="rounded-md border border-gray-300 px-3 py-2 text-sm">
						<option value="Single Company">{{ __("Single Company") }}</option>
						<option value="Multiple Companies">{{ __("Multiple Companies") }}</option>
					</select>
					<span class="text-xs text-amber-800">{{ __("Multiple Companies hides unassigned items, item groups and customers until they are assigned to a company.") }}</span>
				</label>
				<label class="mt-3 flex items-start gap-2 text-sm text-gray-700">
					<input v-model="form.show_demo_accounts" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-gray-300" />
					<span>{{ __("Show demo login accounts on the sign-in screen") }}</span>
				</label>
			</div>

			<!-- Names -->
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium text-gray-700">{{ __("App Name") }}</span>
					<input
						v-model="form.app_name"
						type="text"
						class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500"
						:placeholder="__('Digit POS')"
					/>
				</label>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium text-gray-700">{{ __("Short Name") }}</span>
					<input
						v-model="form.app_short_name"
						type="text"
						class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500"
						:placeholder="__('Digit')"
					/>
				</label>
			</div>

			<!-- Logo -->
			<div class="flex items-center gap-4">
				<div
					class="w-16 h-16 shrink-0 rounded-lg border border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden"
				>
					<img
						v-if="form.primary_logo"
						:src="form.primary_logo"
						class="w-full h-full object-contain"
						alt="logo"
					/>
					<span v-else class="text-[10px] text-gray-400 text-center px-1">{{
						__("No logo")
					}}</span>
				</div>
				<div class="flex flex-col gap-1.5">
					<span class="text-sm font-medium text-gray-700">{{ __("Logo") }}</span>
					<div class="flex items-center gap-2">
						<input
							ref="logoInput"
							type="file"
							accept="image/*"
							class="hidden"
							@change="onLogoChange"
						/>
						<button
							type="button"
							class="px-3 py-1.5 rounded-md bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-60"
							:disabled="uploading"
							@click="logoInput?.click()"
						>
							{{ uploading ? __("Uploading…") : __("Upload logo") }}
						</button>
						<button
							v-if="form.primary_logo"
							type="button"
							class="text-xs text-red-600 hover:underline"
							@click="clearLogo"
						>
							{{ __("Remove") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Colors -->
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<label class="flex items-center justify-between gap-3 rounded-md border border-gray-200 px-3 py-2">
					<span class="text-sm font-medium text-gray-700">{{ __("Primary color") }}</span>
					<span class="flex items-center gap-2">
						<span class="text-xs text-gray-400 font-mono">{{ form.primary_color }}</span>
						<input
							v-model="form.primary_color"
							type="color"
							class="h-8 w-10 cursor-pointer rounded border border-gray-300 bg-white p-0.5"
							@input="applyPreview"
						/>
					</span>
				</label>
				<label class="flex items-center justify-between gap-3 rounded-md border border-gray-200 px-3 py-2">
					<span class="text-sm font-medium text-gray-700">{{ __("Secondary color") }}</span>
					<span class="flex items-center gap-2">
						<span class="text-xs text-gray-400 font-mono">{{ form.secondary_color }}</span>
						<input
							v-model="form.secondary_color"
							type="color"
							class="h-8 w-10 cursor-pointer rounded border border-gray-300 bg-white p-0.5"
							@input="applyPreview"
						/>
					</span>
				</label>
			</div>

			<!-- Titles -->
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium text-gray-700">{{ __("Login title") }}</span>
					<input
						v-model="form.login_title"
						type="text"
						class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500"
					/>
				</label>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium text-gray-700">{{ __("Receipt title") }}</span>
					<input
						v-model="form.receipt_title"
						type="text"
						class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500"
					/>
				</label>
			</div>

			<!-- Actions -->
			<div class="flex items-center gap-2 pt-1">
				<button
					type="button"
					class="px-4 py-2 rounded-md bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-60"
					:disabled="saving"
					@click="save"
				>
					{{ saving ? __("Saving…") : __("Save identity") }}
				</button>
				<button
					type="button"
					class="px-4 py-2 rounded-md border border-gray-300 text-gray-700 text-sm hover:bg-gray-50"
					:disabled="saving"
					@click="reset"
				>
					{{ __("Reset") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { useBrandingStore } from "@/stores/branding";
import { useToast } from "@/composables/useToast";
import { call } from "@/utils/apiWrapper";
import { __ } from "@/utils/translation";
import { onMounted, reactive, ref } from "vue";

const branding = useBrandingStore();
const { showSuccess, showError } = useToast();

const saving = ref(false);
const uploading = ref(false);
const logoInput = ref(null);

const FIELDS = [
	"app_name",
	"app_short_name",
	"login_title",
	"receipt_title",
	"primary_color",
	"secondary_color",
	"primary_logo",
	"header_logo",
	"tenant_mode",
	"show_demo_accounts",
];

const form = reactive({});

function loadForm() {
	const s = branding.settings || {};
	for (const f of FIELDS) form[f] = s[f] || "";
	if (!form.primary_color) form.primary_color = "#0a8754";
	if (!form.secondary_color) form.secondary_color = "#064e3b";
}

onMounted(async () => {
	await branding.loadBranding();
	loadForm();
});

// Live preview: push the chosen colours into the store and re-apply the ramp.
function applyPreview() {
	branding.settings.primary_color = form.primary_color;
	branding.settings.secondary_color = form.secondary_color;
	branding.applyBranding();
}

async function onLogoChange(event) {
	const file = event.target.files?.[0];
	if (!file) return;
	uploading.value = true;
	try {
		const fd = new FormData();
		fd.append("file", file, file.name);
		fd.append("is_private", "0");
		fd.append("folder", "Home");
		fd.append("optimize", "1");
		const res = await fetch("/api/method/upload_file", {
			method: "POST",
			headers: { "X-Frappe-CSRF-Token": window.csrf_token || "" },
			body: fd,
		});
		const data = await res.json();
		const url = data?.message?.file_url;
		if (!url) throw new Error("upload failed");
		form.primary_logo = url;
		form.header_logo = url;
	} catch {
		showError(__("Logo upload failed. Try a smaller image."));
	} finally {
		uploading.value = false;
		if (logoInput.value) logoInput.value.value = "";
	}
}

function clearLogo() {
	form.primary_logo = "";
	form.header_logo = "";
}

async function save() {
	saving.value = true;
	try {
		const payload = {};
	for (const f of FIELDS) payload[f] = form[f];
		payload.header_logo = form.header_logo || form.primary_logo;
		payload.theme_color = form.primary_color;
		await call("pos_next.api.branding.save_pos_branding_settings", { settings: payload });
		await branding.loadBranding({ force: true });
		loadForm();
		showSuccess(__("Brand identity saved."));
	} catch (err) {
		showError(err?.message || __("Could not save. You may not have permission."));
	} finally {
		saving.value = false;
	}
}

function reset() {
	branding.loadBranding({ force: true }).then(loadForm);
}
</script>
