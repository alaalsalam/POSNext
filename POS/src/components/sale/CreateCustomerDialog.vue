<template>
	<Dialog
		v-model="show"
		:options="{
			title: isEditMode ? __('Edit Customer') : __('New Customer'),
			size: 'lg',
		}"
	>
		<template #body-content>
			<div class="flex flex-col gap-0">

				<!-- ── Type Toggle ── -->
				<div class="flex gap-2 mb-5">
					<button
						v-for="t in customerTypes"
						:key="t.value"
						type="button"
						@click="customerData.customer_type = t.value"
						class="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium border transition-all"
						:class="customerData.customer_type === t.value
							? 'bg-gray-900 text-white border-gray-900 shadow-sm'
							: 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'"
					>
						<component :is="t.icon" class="w-4 h-4" />
						{{ __(t.label) }}
					</button>
				</div>

				<!-- ── Section: Basic Info ── -->
				<SectionLabel :label="__('Basic Info')" icon="user" />
				<div class="grid grid-cols-2 gap-3 mb-4">

					<!-- Customer Name -->
					<div class="col-span-2">
						<FieldLabel :label="__('Customer Name')" required />
						<Input
							v-model="customerData.customer_name"
							type="text"
							:placeholder="customerData.customer_type === 'Company' ? __('Company / Store name') : __('Full name')"
						/>
					</div>

					<!-- Mobile -->
					<div class="col-span-2">
						<FieldLabel :label="__('Mobile Number')" required />
						<div class="flex gap-2">
							<!-- Country Code -->
							<div class="relative" ref="dropdownRef">
								<button
									type="button"
									@click="showCountryDropdown = !showCountryDropdown"
									class="flex items-center gap-1 w-24 ps-2 pe-1 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white hover:bg-gray-50"
								>
									<img
										:src="`https://flagcdn.com/h24/${currentCountryCode}.png`"
										:alt="currentCountryCode"
										class="w-6 h-auto rounded-sm"
										@error="handleFlagError"
									/>
									<span class="flex-1 text-start text-xs">{{ selectedCountryCode || "+966" }}</span>
									<ChevronDownIcon class="w-3 h-3 text-gray-400" />
								</button>

								<!-- Dropdown -->
								<div
									v-if="showCountryDropdown"
									class="absolute start-0 z-50 mt-1 w-80 max-h-80 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
								>
									<div class="sticky top-0 bg-white border-b border-gray-200 p-2">
										<input
											ref="countrySearchRef"
											v-model="countrySearchQuery"
											type="text"
											:placeholder="__('Search country...')"
											class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
											@keydown.escape="showCountryDropdown = false"
										/>
									</div>
									<div class="overflow-y-auto max-h-64">
										<button
											v-for="country in filteredCountries"
											:key="country.code"
											type="button"
											@click="selectCountry(country)"
											class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-start"
											:class="{ 'bg-gray-50': selectedCountryCode === country.isd }"
										>
											<img
												:src="`https://flagcdn.com/h24/${country.code.toLowerCase()}.png`"
												:alt="country.name"
												class="w-6 h-auto rounded-sm shadow-sm"
												@error="(e) => (e.target.style.display = 'none')"
											/>
											<span class="flex-1 text-sm font-medium text-gray-700">{{ country.name }}</span>
											<span class="text-sm text-gray-400">{{ country.isd }}</span>
										</button>
										<div v-if="filteredCountries.length === 0" class="px-4 py-8 text-center text-sm text-gray-500">
											{{ __("No countries found") }}
										</div>
									</div>
								</div>
							</div>

							<input
								v-model="phoneNumber"
								type="tel"
								:placeholder="__('5xxxxxxxx')"
								class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
								@input="updateMobileNumber"
								required
							/>
						</div>
					</div>
				</div>

				<!-- ── Section: Tax & Legal (Company only) ── -->
				<template v-if="customerData.customer_type === 'Company'">
					<SectionLabel :label="__('Tax & Legal')" icon="shield" />
					<div class="grid grid-cols-2 gap-3 mb-4">

						<!-- VAT Number -->
						<div>
							<FieldLabel :label="__('VAT Number (الرقم الضريبي)')" />
							<input
								v-model="customerData.tax_id"
								type="text"
								maxlength="15"
								:placeholder="__('300xxxxxxxxxx003')"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 font-mono"
								dir="ltr"
							/>
						</div>

						<!-- CR Number -->
						<div>
							<FieldLabel :label="__('CR No. (السجل التجاري)')" />
							<input
								v-model="customerData.custom_commercial_registration"
								type="text"
								:placeholder="__('1010xxxxxx')"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 font-mono"
								dir="ltr"
							/>
						</div>
					</div>
				</template>

				<!-- ── Section: Address ── -->
				<SectionLabel :label="__('Address')" icon="map-pin" />
				<div class="grid grid-cols-2 gap-3 mb-4">

					<!-- Governorate -->
					<div>
						<FieldLabel :label="__('City / Governorate')" />
						<select
							v-model="customerData.custom_governorate"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
						>
							<option value="">{{ __("Select city") }}</option>
							<option v-for="g in governorates" :key="g" :value="g">{{ g }}</option>
						</select>
					</div>

					<!-- District -->
					<div>
						<FieldLabel :label="__('District / Neighbourhood')" />
						<select
							v-model="customerData.custom_district"
							:disabled="!customerData.custom_governorate || districts.length === 0"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white disabled:bg-gray-50 disabled:text-gray-400"
						>
							<option value="">{{ customerData.custom_governorate ? __("Select district") : __("Select city first") }}</option>
							<option v-for="d in districts" :key="d.name" :value="d.name">{{ d.district }}</option>
						</select>
					</div>

					<!-- Customer Group -->
					<div>
						<FieldLabel :label="__('Customer Group')" />
						<select
							v-model="customerData.customer_group"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
						>
							<option value="">{{ __("Select group") }}</option>
							<option v-for="g in customerGroups" :key="g" :value="g">{{ g }}</option>
						</select>
					</div>

					<!-- Territory -->
					<div>
						<FieldLabel :label="__('Territory')" />
						<select
							v-model="customerData.territory"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
						>
							<option value="">{{ __("Select territory") }}</option>
							<option v-for="t in territories" :key="t" :value="t">{{ t }}</option>
						</select>
					</div>
				</div>

				<!-- ── Referral (new only) ── -->
				<template v-if="!isEditMode">
					<SectionLabel :label="__('Referral')" icon="gift" optional />
					<div class="mb-1">
						<FieldLabel :label="__('Referral Code')" />
						<Input
							v-model="referralCode"
							type="text"
							:placeholder="__('Enter referral code (optional)')"
						/>
						<p class="text-xs text-gray-400 mt-1">{{ __("Coupons are generated for both parties on valid referral") }}</p>
					</div>
				</template>

				<!-- ── Permission Warning ── -->
				<div
					v-if="!hasPermission"
					class="mt-4 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2"
				>
					<ExclamationTriangleIcon class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
					<div>
						<p class="text-sm font-medium text-amber-900">{{ __("Permission Required") }}</p>
						<p class="text-xs text-amber-700 mt-0.5">{{ __("Contact your administrator to create customers.") }}</p>
					</div>
				</div>

			</div>
		</template>

		<template #actions>
			<div class="flex gap-2">
				<Button
					variant="solid"
					@click="handleCreate"
					:loading="createCustomerResource.loading || updateCustomerResource.loading || checkingPermission"
					:disabled="!customerData.customer_name || !phoneNumber || !hasPermission"
				>
					{{ isEditMode ? __("Save Changes") : __("Create Customer") }}
				</Button>
				<Button variant="subtle" @click="show = false">{{ __("Cancel") }}</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { usePOSPermissions } from "@/composables/usePermissions";
import { useToast } from "@/composables/useToast";
import { useCountriesStore } from "@/stores/countries";
import { logger } from "@/utils/logger";
import { Button, Dialog, Input, call, createResource } from "frappe-ui";
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const log = logger.create("CreateCustomerDialog");

// ── Mini components ────────────────────────────────────────────────────────
const SectionLabel = defineComponent({
	props: { label: String, icon: String, optional: Boolean },
	setup(props) {
		return () => h("div", {
			class: "flex items-center gap-2 mb-2 mt-1"
		}, [
			h("span", { class: "text-xs font-semibold text-gray-500 uppercase tracking-wide" }, props.label),
			props.optional ? h("span", { class: "text-xs text-gray-300" }, `(${__("optional")})`) : null,
			h("div", { class: "flex-1 h-px bg-gray-100" }),
		]);
	},
});

const FieldLabel = defineComponent({
	props: { label: String, required: Boolean },
	setup(props) {
		return () => h("label", {
			class: "block text-xs font-medium text-gray-600 mb-1.5"
		}, [
			props.label,
			props.required ? h("span", { class: "text-red-500 ms-0.5" }, " *") : null,
		]);
	},
});

// Heroicon stubs (inline SVG)
const ChevronDownIcon = defineComponent({
	setup: () => () => h("svg", { viewBox: "0 0 20 20", fill: "currentColor", class: "w-4 h-4" }, [
		h("path", { "fill-rule": "evenodd", d: "M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z", "clip-rule": "evenodd" }),
	]),
});
const ExclamationTriangleIcon = defineComponent({
	setup: () => () => h("svg", { viewBox: "0 0 20 20", fill: "currentColor", class: "w-5 h-5" }, [
		h("path", { "fill-rule": "evenodd", d: "M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z", "clip-rule": "evenodd" }),
	]),
});

// ── Customer type toggle ────────────────────────────────────────────────────
const customerTypes = [
	{
		value: "Individual",
		label: "Individual",
		icon: defineComponent({ setup: () => () => h("svg", { viewBox: "0 0 20 20", fill: "currentColor", class: "w-4 h-4" }, [h("path", { "fill-rule": "evenodd", d: "M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z", "clip-rule": "evenodd" })]) }),
	},
	{
		value: "Company",
		label: "Company / Business",
		icon: defineComponent({ setup: () => () => h("svg", { viewBox: "0 0 20 20", fill: "currentColor", class: "w-4 h-4" }, [h("path", { "fill-rule": "evenodd", d: "M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z", "clip-rule": "evenodd" })]) }),
	},
];

// ── Stores & composables ────────────────────────────────────────────────────
const countriesStore = useCountriesStore();
const { canCreateCustomer } = usePOSPermissions();
const { showSuccess, showError } = useToast();

// ── Props & emits ───────────────────────────────────────────────────────────
const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	initialName: String,
	customer: Object,
});
const emit = defineEmits(["update:modelValue", "customer-created", "customer-updated"]);

// ── State ───────────────────────────────────────────────────────────────────
const hasPermission = ref(true);
const checkingPermission = ref(false);
const selectedCountryCode = ref("+966");
const phoneNumber = ref("");
const referralCode = ref("");
const showCountryDropdown = ref(false);
const countrySearchQuery = ref("");
const dropdownRef = ref(null);
const countrySearchRef = ref(null);

const customerGroups = ref([]);
const territories = ref([]);
const governorates = ref([]);
const districts = ref([]);

const customerData = ref({
	customer_name: "",
	customer_type: "Individual",
	mobile_no: "",
	customer_group: "",
	territory: "",
	tax_id: "",
	custom_commercial_registration: "",
	custom_governorate: "",
	custom_district: "",
});

// ── Computed ────────────────────────────────────────────────────────────────
const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
});
const isEditMode = computed(() => !!props.customer?.name);
const currentCountryCode = computed(() => {
	const c = countriesStore.countries.find((c) => c.isd === selectedCountryCode.value);
	return c?.code.toLowerCase() || "sa";
});
const filteredCountries = computed(() => {
	if (!countrySearchQuery.value) return countriesStore.countries;
	const q = countrySearchQuery.value.toLowerCase();
	return countriesStore.countries.filter(
		(c) => c.name.toLowerCase().includes(q) || c.isd.includes(q) || c.code.toLowerCase().includes(q)
	);
});

// ── Country / mobile helpers ────────────────────────────────────────────────
const handleFlagError = (e) => (e.target.style.display = "none");
const selectCountry = (country) => {
	selectedCountryCode.value = country.isd;
	showCountryDropdown.value = false;
	countrySearchQuery.value = "";
	updateMobileNumber();
};
const updateMobileNumber = () => {
	customerData.value.mobile_no = phoneNumber.value
		? `${selectedCountryCode.value}-${phoneNumber.value}`
		: "";
};
const handleClickOutside = (e) => {
	if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
		showCountryDropdown.value = false;
	}
};
const setCountryFromName = (countryName) => {
	if (!countryName) { selectedCountryCode.value = "+966"; return; }
	const isd = countriesStore.countryNameToISDMap[countryName];
	selectedCountryCode.value = isd || "+966";
};
const updateTerritoryFromCountry = () => {
	if (!territories.value.length) return;
	const country = countriesStore.countries.find((c) => c.isd === selectedCountryCode.value);
	if (!country) return;
	const exact = territories.value.find((t) => t === country.name);
	if (exact) { customerData.value.territory = exact; return; }
	const fuzzy = territories.value.find(
		(t) => t.toLowerCase().includes(country.name.toLowerCase()) || country.name.toLowerCase().includes(t.toLowerCase())
	);
	if (fuzzy) customerData.value.territory = fuzzy;
};

// ── Resources ───────────────────────────────────────────────────────────────
const createCustomerResource = createResource({
	url: "pos_next.api.customers.create_customer",
	makeParams: () => ({
		customer_name: customerData.value.customer_name,
		mobile_no: customerData.value.mobile_no || "",
		customer_type: customerData.value.customer_type,
		customer_group: customerData.value.customer_group || "",
		territory: customerData.value.territory || "",
		tax_id: customerData.value.tax_id || "",
		custom_commercial_registration: customerData.value.custom_commercial_registration || "",
		custom_governorate: customerData.value.custom_governorate || "",
		custom_district: customerData.value.custom_district || "",
		pos_profile: props.posProfile,
	}),
	onSuccess: (data) => {
		showSuccess(__("Customer {0} created", [data.customer_name]));
		emit("customer-created", data);
		show.value = false;
	},
	onError: (err) => {
		log.error("Error creating customer", err);
		showError(err.message || __("Failed to create customer"));
	},
});

const updateCustomerResource = createResource({
	url: "frappe.client.set_value",
	makeParams: () => ({
		doctype: "Customer",
		name: props.customer?.name,
		fieldname: {
			customer_name: customerData.value.customer_name,
			customer_type: customerData.value.customer_type,
			customer_group: customerData.value.customer_group || "",
			territory: customerData.value.territory || "",
			mobile_no: customerData.value.mobile_no || "",
			tax_id: customerData.value.tax_id || "",
			custom_commercial_registration: customerData.value.custom_commercial_registration || "",
			custom_governorate: customerData.value.custom_governorate || "",
			custom_district: customerData.value.custom_district || "",
		},
	}),
	onSuccess: (data) => {
		showSuccess(__("Customer {0} updated", [data.customer_name]));
		emit("customer-updated", data);
		show.value = false;
	},
	onError: (err) => {
		log.error("Error updating customer", err);
		showError(err.message || __("Failed to update customer"));
	},
});

const sellingSettingsResource = createResource({
	url: "frappe.client.get_value",
	makeParams: () => ({ doctype: "Selling Settings", fieldname: ["customer_group", "territory"] }),
	auto: false,
	onError: (err) => log.error("Error loading Selling Settings", err),
});

function pickDefault(settingsValue, list, fallbackFn = null) {
	if (settingsValue && list.includes(settingsValue)) return settingsValue;
	if (fallbackFn) return fallbackFn(list) || list[0] || "";
	return list[0] || "";
}

const createListResource = (doctype, onSuccess) =>
	createResource({
		url: "frappe.client.get_list",
		makeParams: () => ({
			doctype,
			fields: ["name"],
			filters: doctype === "Customer Group" ? { is_group: 0 } : {},
			limit_page_length: 500,
		}),
		auto: false,
		onSuccess: (data) => data?.length && onSuccess(data.map((d) => d.name)),
		onError: (err) => log.error(`Error loading ${doctype}`, err),
	});

const customerGroupsResource = createListResource("Customer Group", (names) => {
	customerGroups.value = names;
	if (!customerData.value.customer_group && names.length) {
		customerData.value.customer_group = pickDefault(sellingSettingsResource.data?.customer_group, names);
	}
});
const territoriesResource = createListResource("Territory", (names) => {
	territories.value = names;
	if (!customerData.value.territory && names.length) {
		customerData.value.territory = pickDefault(
			sellingSettingsResource.data?.territory, names,
			(list) => list.find((n) => n === "All Territories")
		);
	}
});
const governoratesResource = createListResource("Governorate", (names) => {
	governorates.value = names;
});

const districtsResource = createResource({
	url: "frappe.client.get_list",
	makeParams: () => ({
		doctype: "District",
		fields: ["name", "district"],
		filters: { governorate: customerData.value.custom_governorate },
		limit_page_length: 0,
		order_by: "district asc",
	}),
	auto: false,
	onSuccess: (data) => {
		districts.value = data || [];
		if (customerData.value.custom_district && !districts.value.some((d) => d.name === customerData.value.custom_district)) {
			customerData.value.custom_district = "";
		}
	},
	onError: (err) => log.error("Error loading Districts", err),
});

const posProfileResource = createResource({
	url: "frappe.client.get_value",
	makeParams: () => ({ doctype: "POS Profile", filters: { name: props.posProfile }, fieldname: ["country"] }),
	auto: false,
	onSuccess: (data) => setCountryFromName(data?.country || "Saudi Arabia"),
	onError: () => { selectedCountryCode.value = "+966"; },
});

// ── Dialog lifecycle ────────────────────────────────────────────────────────
const loadDialogData = async () => {
	countriesStore.loadCountries();
	await sellingSettingsResource.reload();
	if (!isEditMode.value) {
		customerData.value.customer_group = "";
		customerData.value.territory = "";
	}
	await Promise.all([territoriesResource.reload(), customerGroupsResource.reload(), governoratesResource.reload()]);
	if (isEditMode.value && props.customer?.name && customerData.value.custom_governorate) {
		await districtsResource.reload();
	}
	checkPermissions();
	if (props.posProfile) await posProfileResource.reload();
	else selectedCountryCode.value = "+966";
};

const checkPermissions = async () => {
	checkingPermission.value = true;
	try { hasPermission.value = await canCreateCustomer(); }
	catch (err) { hasPermission.value = false; }
	finally { checkingPermission.value = false; }
};

const handleCreate = async () => {
	if (!customerData.value.customer_name) return showError(__("Customer Name is required"));
	if (!phoneNumber.value) {
		return showError(__("Mobile Number is required"));
	}
	if (isEditMode.value) {
		await updateCustomerResource.submit();
	} else {
		await createCustomerResource.submit();
		if (referralCode.value && createCustomerResource.data?.name) {
			try {
				await call("pos_next.api.promotions.apply_referral_code", {
					referral_code: referralCode.value,
					customer: createCustomerResource.data.name,
				});
				showSuccess(__("Referral code applied"));
			} catch (e) {
				showError(e.message || __("Failed to apply referral code"));
			}
		}
	}
};

const resetForm = () => {
	const s = sellingSettingsResource.data || {};
	Object.assign(customerData.value, {
		customer_name: "",
		customer_type: "Individual",
		mobile_no: "",
		tax_id: "",
		custom_commercial_registration: "",
		customer_group: pickDefault(s.customer_group, customerGroups.value),
		territory: pickDefault(s.territory, territories.value, (l) => l.find((n) => n === "All Territories")),
		custom_governorate: "",
		custom_district: "",
	});
	districts.value = [];
	selectedCountryCode.value = "+966";
	phoneNumber.value = "";
	referralCode.value = "";
};

// ── Watchers ────────────────────────────────────────────────────────────────
watch(() => props.initialName, (name) => name && (customerData.value.customer_name = name));

watch(() => props.customer, (customer) => {
	if (!customer?.name) return;
	customerData.value.customer_name = customer.customer_name || "";
	customerData.value.customer_type = customer.customer_type || "Individual";
	customerData.value.tax_id = customer.tax_id || "";
	customerData.value.custom_commercial_registration = customer.custom_commercial_registration || "";
	customerData.value.customer_group = customer.customer_group || customerGroups.value[0] || "";
	customerData.value.territory = customer.territory || territories.value.find((n) => n === "All Territories") || territories.value[0] || "";
	customerData.value.custom_governorate = customer.custom_governorate || "";
	customerData.value.custom_district = customer.custom_district || "";
	if (customer.mobile_no) {
		customerData.value.mobile_no = customer.mobile_no;
		if (customer.mobile_no.includes("-")) {
			const [code, ...rest] = customer.mobile_no.split("-");
			selectedCountryCode.value = code;
			phoneNumber.value = rest.join("-");
		} else {
			phoneNumber.value = customer.mobile_no;
		}
	}
}, { immediate: true });

watch(selectedCountryCode, async (newVal, oldVal) => {
	if (!oldVal) return;
	await nextTick();
	updateTerritoryFromCountry();
});

watch(() => customerData.value.custom_governorate, (gov) => {
	if (gov) districtsResource.reload();
	else { districts.value = []; customerData.value.custom_district = ""; }
});

watch(showCountryDropdown, async (isOpen) => {
	if (isOpen) { await nextTick(); countrySearchRef.value?.focus(); }
});

watch(() => props.modelValue, async (isOpen) => {
	isOpen ? await loadDialogData() : resetForm();
});

onMounted(() => document.addEventListener("click", handleClickOutside));
onBeforeUnmount(() => document.removeEventListener("click", handleClickOutside));
</script>
