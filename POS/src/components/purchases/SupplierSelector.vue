<!--
  Compact supplier picker for purchase mode on the main POS screen.
  Mirrors the sales customer card (avatar + name + Change / Create / Clear).
  There is no "edit supplier details" action (no update_supplier backend).
  Reuses the supplier search + quick-create logic backed by the same
  pos_next.api.purchases endpoints.
-->
<template>
	<div ref="rootRef" class="relative">
		<!-- Selected supplier card (mirrors the sales customer card) -->
		<div
			v-if="modelValue && !searching"
			class="flex items-center gap-1.5 bg-white border border-gray-200 rounded-xl p-1.5 shadow-sm min-w-0"
		>
			<div
				class="w-8 h-8 bg-gradient-to-br from-orange-500 to-orange-600 rounded-full flex items-center justify-center flex-shrink-0"
			>
				<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17M17 13v6a2 2 0 11-4 0"
					/>
				</svg>
			</div>
			<div class="min-w-0 flex-1 px-1">
				<p class="text-xs font-semibold text-gray-900 truncate leading-tight">
					{{ modelValue.supplier_name || modelValue.name }}
				</p>
				<p class="text-[10px] text-gray-500 truncate leading-tight">{{ __("Supplier") }}</p>
			</div>

			<!-- Action Buttons: Change / Create / Clear (no Edit) -->
			<div class="flex items-center gap-0.5 flex-shrink-0" @click.stop>
				<button
					type="button"
					data-testid="supplier-change"
					@click.stop="startChange"
					class="w-7 h-7 flex items-center justify-center text-orange-500 hover:bg-orange-50 active:bg-orange-100 rounded-lg transition-colors touch-manipulation"
					:title="__('Change supplier')"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
				<button
					type="button"
					data-testid="supplier-create"
					@click.stop="openCreate"
					class="w-7 h-7 flex items-center justify-center text-green-600 hover:bg-green-50 active:bg-green-100 rounded-lg transition-colors touch-manipulation"
					:title="__('Create new supplier')"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
					</svg>
				</button>
				<button
					type="button"
					data-testid="supplier-clear"
					@click.stop="clearSupplier"
					class="w-7 h-7 flex items-center justify-center text-red-500 hover:bg-red-50 active:bg-red-100 rounded-lg transition-colors touch-manipulation"
					:title="__('Remove supplier')"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
		</div>

		<!-- Empty / searching state — SAME card shell as the selected card, so the
		     un-interacted first impression is a sibling of the sales customer card:
		     [orange avatar] [inline borderless search input] [green create icon]. -->
		<div v-else class="relative">
			<div class="flex items-center gap-1.5 bg-white border border-gray-200 rounded-xl p-1.5 shadow-sm min-w-0 focus-within:ring-2 focus-within:ring-orange-500 focus-within:border-transparent transition-shadow">
				<div
					class="w-8 h-8 bg-gradient-to-br from-orange-500 to-orange-600 rounded-full flex items-center justify-center flex-shrink-0"
				>
					<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17M17 13v6a2 2 0 11-4 0"
						/>
					</svg>
				</div>
				<input
					id="cart-supplier-search"
					name="cart-supplier-search"
					ref="searchInput"
					v-model="search"
					@input="onSearch"
					@focus="showDropdown = true"
					type="text"
					autocomplete="off"
					:placeholder="__('Search or add supplier...')"
					:aria-label="__('Search supplier in cart')"
					class="min-w-0 flex-1 h-8 px-1 text-xs bg-transparent border-0 focus:outline-none focus:ring-0 placeholder:text-gray-400"
				/>
				<button
					type="button"
					data-testid="supplier-create"
					@click.stop="openCreate"
					class="w-7 h-7 flex items-center justify-center text-green-600 hover:bg-green-50 active:bg-green-100 rounded-lg transition-colors touch-manipulation flex-shrink-0"
					:title="__('Create new supplier')"
					:aria-label="__('Create new supplier')"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
					</svg>
				</button>
			</div>

			<!-- Dropdown -->
			<div
				v-if="showDropdown && (options.length || search.trim().length >= 2)"
				class="absolute z-50 mt-0.5 w-full bg-white border border-gray-200 rounded-xl shadow-lg max-h-48 overflow-y-auto"
			>
				<!-- Frequent Suppliers header (when showing the preloaded list) -->
				<div
					v-if="search.trim().length < 2 && options.length"
					class="px-2 py-1 bg-gray-50 border-b border-gray-200"
				>
					<span class="text-[10px] font-medium text-gray-500 uppercase tracking-wide">
						{{ __("Suppliers") }}
					</span>
				</div>

				<button
					type="button"
					v-for="s in options"
					:key="s.name"
					@mousedown.prevent="selectSupplier(s)"
					class="w-full text-start px-3 py-2 text-xs hover:bg-orange-50 transition-colors border-b border-gray-100 last:border-0"
				>
					<span class="font-semibold text-gray-900">{{ s.supplier_name || s.name }}</span>
					<span v-if="s.supplier_group" class="text-gray-400 ms-2">{{ s.supplier_group }}</span>
				</button>

				<!-- No results for a 2+ char search -->
				<div
					v-if="search.trim().length >= 2 && !options.length"
					class="px-3 py-2 text-center text-[11px] font-medium text-gray-500 border-b border-gray-100"
				>
					{{ __('No results for "{0}"', [search]) }}
				</div>

				<button
					type="button"
					v-if="search.trim().length >= 2"
					@mousedown.prevent="openCreate"
					class="w-full text-start px-3 py-2 text-xs text-orange-600 font-semibold hover:bg-orange-50 border-t border-gray-100 flex items-center gap-1"
				>
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					{{ __("Create new supplier: {0}", [search]) }}
				</button>
			</div>
		</div>

		<!-- Quick create supplier -->
		<div
			v-if="showCreate"
			class="mt-2 p-3 bg-orange-50 border border-orange-200 rounded-xl grid grid-cols-1 gap-2"
		>
			<input
				v-model="newName"
				:placeholder="__('New supplier name')"
				class="h-9 px-3 text-xs rounded-lg border border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-400"
			/>
			<select v-model="newGroup" class="h-9 px-2 text-xs rounded-lg border border-orange-300 bg-white">
				<option value="">{{ __("Supplier Group") }}</option>
				<option v-for="g in supplierGroups" :key="g.name" :value="g.name">{{ g.name }}</option>
			</select>
			<div class="flex gap-2">
				<button
					type="button"
					@click="createSupplier"
					:disabled="!newName || !newGroup || creating"
					class="flex-1 h-9 px-3 bg-orange-600 text-white text-xs font-semibold rounded-lg hover:bg-orange-700 disabled:opacity-50 transition-colors"
				>
					{{ creating ? __("Creating...") : __("Create") }}
				</button>
				<button
					type="button"
					@click="cancelCreate"
					class="h-9 px-3 text-xs font-semibold text-gray-600 bg-white border border-orange-200 rounded-lg"
				>
					{{ __("Cancel") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { call } from "@/utils/apiWrapper";
import { useToast } from "@/composables/useToast";
import { managerTranslate as __ } from "@/utils/managementI18n";

const props = defineProps({
	modelValue: { type: Object, default: null },
	posProfile: { type: String, required: true },
	// Settings default supplier ({ name, supplier_name }) — clearing reverts to it
	// when configured, mirroring the sales default-customer behaviour.
	defaultSupplier: { type: Object, default: null },
});
const emit = defineEmits(["update:modelValue"]);

const { showError } = useToast();

const rootRef = ref(null);
const searchInput = ref(null);
const search = ref("");
// Preloaded supplier list (mirrors the customer selector's cached allCustomers) so
// clicking the field shows results instantly with in-memory filtering.
const allSuppliers = ref([]);
const showDropdown = ref(false);
const showCreate = ref(false);
const searching = ref(false); // "Change" pressed on a selected supplier → show the picker
const newName = ref("");
const newGroup = ref("");
const supplierGroups = ref([]);
const creating = ref(false);

// Instant results, mirroring InvoiceCart's customerResults:
// - focused with <2 chars → top 10 suppliers (the "click shows a list" behaviour)
// - otherwise → in-memory filter on name / id / group.
const options = computed(() => {
	const q = search.value.trim().toLowerCase();
	if (q.length < 2) {
		return showDropdown.value ? allSuppliers.value.slice(0, 10) : [];
	}
	return allSuppliers.value
		.filter((s) => {
			const name = (s.supplier_name || "").toLowerCase();
			const id = (s.name || "").toLowerCase();
			const group = (s.supplier_group || "").toLowerCase();
			return name.includes(q) || id.includes(q) || group.includes(q);
		})
		.slice(0, 20);
});

let searchTimer = null;
// Client-side filtering covers the (small) supplier set; the API is only a fallback
// for a 2+ char query that matches nothing locally (e.g. a supplier added elsewhere).
function onSearch() {
	showDropdown.value = true;
	clearTimeout(searchTimer);
	const q = search.value.trim();
	if (q.length < 2 || options.value.length > 0) return;
	searchTimer = setTimeout(async () => {
		try {
			const res = await call("pos_next.api.purchases.get_suppliers", {
				search: q,
				limit: 10,
				pos_profile: props.posProfile,
			});
			// Merge any server-only matches into the cache so the computed picks them up.
			for (const s of res || []) {
				if (!allSuppliers.value.some((x) => x.name === s.name)) {
					allSuppliers.value.push(s);
				}
			}
		} catch (error) {
			showError(error?.message || __("Failed to search suppliers"));
		}
	}, 300);
}

function selectSupplier(s) {
	emit("update:modelValue", { name: s.name, supplier_name: s.supplier_name });
	resetPicker();
}

// Change: reveal the search input over the selected supplier card, with the list
// already showing (parity with clicking the empty customer field).
async function startChange() {
	searching.value = true;
	await nextTick();
	searchInput.value?.focus();
	showDropdown.value = true;
}

// Clear: revert to the configured default supplier when one exists, otherwise
// deselect entirely (which reveals the inline picker).
function clearSupplier() {
	if (props.defaultSupplier?.name) {
		emit("update:modelValue", { ...props.defaultSupplier });
	} else {
		emit("update:modelValue", null);
	}
	resetPicker();
}

function resetPicker() {
	search.value = "";
	showDropdown.value = false;
	searching.value = false;
}

function openCreate() {
	newName.value = search.value.trim();
	showCreate.value = true;
	showDropdown.value = false;
}

function cancelCreate() {
	showCreate.value = false;
	newName.value = "";
	// If nothing is selected, keep the picker visible; otherwise return to the card.
	if (props.modelValue) searching.value = false;
}

async function createSupplier() {
	if (!newName.value || !newGroup.value) return;
	creating.value = true;
	try {
		const res = await call("pos_next.api.purchases.create_supplier", {
			supplier_name: newName.value,
			supplier_group: newGroup.value,
			supplier_type: "Company",
			pos_profile: props.posProfile,
		});
		if (res?.name) {
			selectSupplier(res);
			showCreate.value = false;
			newName.value = "";
		}
	} catch (error) {
		showError(error?.message || __("Failed to create supplier"));
	} finally {
		creating.value = false;
	}
}

function handleClickOutside(event) {
	if (rootRef.value && !rootRef.value.contains(event.target)) {
		showDropdown.value = false;
		// Abandoning a "Change" without picking anything returns to the card.
		if (searching.value && props.modelValue) searching.value = false;
	}
}

onMounted(async () => {
	document.addEventListener("mousedown", handleClickOutside);
	// Preload suppliers + groups so the field shows a list the instant it's focused
	// (the supplier set is small; client-side filtering fully covers it).
	try {
		const [suppliers, groups] = await Promise.all([
			call("pos_next.api.purchases.get_suppliers", {
				limit: 100,
				pos_profile: props.posProfile,
			}).catch(() => []),
			call("pos_next.api.purchases.get_supplier_groups", {
				pos_profile: props.posProfile,
			}).catch(() => []),
		]);
		allSuppliers.value = suppliers || [];
		supplierGroups.value = groups || [];
		newGroup.value = supplierGroups.value[0]?.name || "";
	} catch (error) {
		showError(error?.message || __("Failed to load suppliers"));
	}
});

onBeforeUnmount(() => {
	document.removeEventListener("mousedown", handleClickOutside);
	clearTimeout(searchTimer);
});
</script>
