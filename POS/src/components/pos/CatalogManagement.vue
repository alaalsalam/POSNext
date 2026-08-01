<template>
	<!-- Overlay -->
	<div v-if="show" class="fixed inset-0 z-40 bg-black/30" @click="$emit('close')" />

	<!-- Panel — slides in from right (LTR) / left (RTL) -->
	<transition name="slide-panel">
		<div
			v-if="show"
			class="fixed top-0 end-0 h-full w-full sm:w-96 z-50 flex flex-col bg-white shadow-2xl"
		>
			<!-- Header -->
			<div
				class="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-white"
			>
				<div class="flex items-center gap-3">
					<!-- Brand-colored icon -->
					<div
						class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center"
					>
						<svg
							class="w-5 h-5 text-white"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 4v16m8-8H4"
							/>
						</svg>
					</div>
					<div>
						<h2 class="text-base font-bold text-gray-900">
							{{ __("Catalog Management") }}
						</h2>
						<p class="text-xs text-gray-500">
							{{ __("Add items & groups quickly") }}
						</p>
					</div>
				</div>
				<button
					@click="$emit('close')"
					class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
				>
					<svg
						class="w-5 h-5"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Tabs -->
			<div
				class="flex border-b border-gray-100 bg-gray-50/50 px-4 pt-3 gap-1"
			>
				<button
					v-for="tab in tabs"
					:key="tab.key"
					@click="activeTab = tab.key"
					:class="[
						'px-4 py-2 rounded-t-lg text-xs font-semibold transition-all',
						activeTab === tab.key
							? 'bg-white border border-gray-200 border-b-white -mb-px text-blue-600'
							: 'text-gray-500 hover:text-gray-700',
					]"
				>
					{{ __(tab.label) }}
				</button>
			</div>

			<!-- Scrollable content -->
			<div class="flex-1 overflow-y-auto p-5">
				<!-- TAB: New Item -->
				<div v-if="activeTab === 'item'" class="flex flex-col gap-4">
					<div>
						<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Item Code") }} <span class="text-red-500">*</span></label>
						<input v-model="itemForm.item_code" type="text" :placeholder="__('Unique item code')" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
					</div>
					<!-- Item Name -->
					<div>
						<label class="block text-xs font-semibold text-gray-700 mb-1.5"
							>{{ __("Item Name") }}
							<span class="text-red-500">*</span></label
						>
						<input
							v-model="itemForm.item_name"
							type="text"
							:placeholder="__('e.g. iPhone 16 Pro Max')"
							class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
							@keydown.enter="createItem"
						/>
					</div>

					<!-- Item Group -->
					<div>
						<label class="block text-xs font-semibold text-gray-700 mb-1.5"
							>{{ __("Item Group") }}
							<span class="text-red-500">*</span></label
						>
						<select
							v-model="itemForm.item_group"
							class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white appearance-none"
						>
							<option value="" disabled>{{ __("Select group...") }}</option>
							<option v-for="g in itemGroups" :key="g" :value="g">{{ g }}</option>
						</select>
					</div>

					<!-- Selling + Buying Price + UOM -->
					<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
						<div>
							<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Selling Price") }} ({{ catalogDefaults.selling_currency }})</label>
							<input v-model.number="itemForm.selling_price" type="number" min="0" step="0.01" placeholder="0.00"
								class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
						</div>
						<div>
							<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Buying Price") }} ({{ catalogDefaults.buying_currency }})</label>
							<input v-model.number="itemForm.buying_price" type="number" min="0" step="0.01" placeholder="0.00"
								class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
						</div>
						<div>
							<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Stock UOM") }}</label>
							<select v-model="itemForm.stock_uom"
								class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white">
								<option v-for="u in uomOptions" :key="u" :value="u">{{ u }}</option>
							</select>
						</div>
					</div>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						<div>
							<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Barcode") }}</label>
							<input v-model="itemForm.barcode" type="text" :placeholder="__('Optional unique barcode')" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
						</div>
						<label class="flex items-center gap-2 min-h-10 mt-5 text-xs font-semibold text-gray-700">
							<input v-model="itemForm.is_stock_item" type="checkbox" class="w-5 h-5 accent-blue-600" />
							{{ __("Maintain Stock") }}
						</label>
					</div>
					<div class="grid grid-cols-2 gap-3">
						<div><label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Valid From") }}</label><input v-model="itemForm.valid_from" type="date" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm" /></div>
						<div><label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Valid Until") }}</label><input v-model="itemForm.valid_upto" type="date" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm" /></div>
					</div>

					<!-- Success feedback -->
					<transition name="fade">
						<div
							v-if="itemSuccess"
							class="flex items-center gap-2 px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg text-xs font-semibold text-green-700"
						>
							<svg
								class="w-4 h-4 text-green-500"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 13l4 4L19 7"
								/>
							</svg>
							{{ __('Item "{0}" created successfully', [itemSuccess]) }}
						</div>
					</transition>

					<!-- Error -->
					<transition name="fade">
						<div
							v-if="itemError"
							class="flex items-start gap-2 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700"
						>
							<svg
								class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							{{ itemError }}
						</div>
					</transition>

					<!-- Submit -->
					<button
						data-testid="catalog-create-item"
						@click="createItem"
						:disabled="itemLoading || !itemForm.item_code || !itemForm.item_name || !itemForm.item_group"
						class="w-full h-11 rounded-xl font-bold text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-sm"
					>
						<svg
							v-if="!itemLoading"
							class="w-4 h-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						<div
							v-else
							class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
						/>
						{{ itemLoading ? __("Creating...") : __("Create Item") }}
					</button>

					<!-- Hint -->
					<p class="text-[11px] text-gray-400 text-center leading-relaxed">
						{{
							__(
								"The item will be available in the POS catalog after the next sync"
							)
						}}
					</p>
				</div>

				<!-- TAB: New Group -->
				<div v-if="activeTab === 'group'" class="flex flex-col gap-4">
					<!-- Group Name -->
					<div>
						<label class="block text-xs font-semibold text-gray-700 mb-1.5"
							>{{ __("Group Name") }}
							<span class="text-red-500">*</span></label
						>
						<input
							v-model="groupForm.group_name"
							type="text"
							:placeholder="__('e.g. Samsung Tablets')"
							class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
							@keydown.enter="createGroup"
						/>
					</div>

					<!-- Parent Group -->
					<div>
						<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{
							__("Parent Group")
						}}</label>
						<select v-model="groupForm.parent_item_group" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
							<option v-for="group in parentGroups" :key="group.name" :value="group.name">{{ group.name }}</option>
						</select>
						<p class="text-[11px] text-gray-400 mt-1">
							{{ __("Leave blank to add under All Item Groups") }}
						</p>
					</div>

					<!-- Success -->
					<transition name="fade">
						<div
							v-if="groupSuccess"
							class="flex items-center gap-2 px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg text-xs font-semibold text-green-700"
						>
							<svg
								class="w-4 h-4 text-green-500"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 13l4 4L19 7"
								/>
							</svg>
							{{ __('Group "{0}" created', [groupSuccess]) }}
						</div>
					</transition>

					<!-- Error -->
					<transition name="fade">
						<div
							v-if="groupError"
							class="flex items-start gap-2 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700"
						>
							<svg
								class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							{{ groupError }}
						</div>
					</transition>

					<!-- Submit -->
					<button
						@click="createGroup"
						:disabled="groupLoading || !groupForm.group_name"
						class="w-full h-11 rounded-xl font-bold text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-sm"
					>
						<svg
							v-if="!groupLoading"
							class="w-4 h-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
							/>
						</svg>
						<div
							v-else
							class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
						/>
						{{ groupLoading ? __("Creating...") : __("Create Group") }}
					</button>

					<!-- Hint -->
					<p class="text-[11px] text-gray-400 text-center leading-relaxed">
						{{ __("New groups appear in category filter after next catalog sync") }}
					</p>
				</div>
			</div>
		</div>
	</transition>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from "vue"
import { call } from "@/utils/apiWrapper"

const props = defineProps({
	show: { type: Boolean, default: false },
	posProfile: { type: String, required: true },
})
const emit = defineEmits(["close"])

const activeTab = ref("item")
const tabs = [
	{ key: "item", label: "New Item" },
	{ key: "group", label: "New Group" },
]

// Item form state
const itemForm = reactive({
	item_code: "",
	item_name: "",
	item_group: "",
	selling_price: 0,
	buying_price: 0,
	stock_uom: "Unit",
	barcode: "",
	is_stock_item: true,
	valid_from: "",
	valid_upto: "",
})
const itemLoading = ref(false)
const itemSuccess = ref("")
const itemError = ref("")

// Group form state
const groupForm = reactive({
	group_name: "",
	parent_item_group: "All Item Groups",
})
const groupLoading = ref(false)
const groupSuccess = ref("")
const groupError = ref("")

// Reference data
const itemGroups = ref([])
const parentGroups = ref([])
const catalogDefaults = reactive({ selling_currency: "", buying_currency: "" })
const uomOptions = ref([])

// Load item groups when panel opens
watch(
	() => props.show,
	(val) => {
		if (val && itemGroups.value.length === 0) {
			loadItemGroups()
		}
	},
)

onMounted(() => {
	if (props.show) loadItemGroups()
})

async function loadItemGroups() {
	try {
		const [groups, parents, defaults] = await Promise.all([
			call("pos_next.api.catalog.get_item_groups_for_select", {
				pos_profile: props.posProfile,
			}),
			call("pos_next.api.catalog.get_item_groups_for_select", {
				pos_profile: props.posProfile,
				include_parents: 1,
			}),
			call("pos_next.api.catalog.get_catalog_defaults", {
				pos_profile: props.posProfile,
			}),
		])
		itemGroups.value = groups || []
		parentGroups.value = (parents || []).filter((row) => row.is_group)
		Object.assign(catalogDefaults, defaults || {})
		uomOptions.value = defaults?.uoms || []
		if (!uomOptions.value.includes(itemForm.stock_uom))
			itemForm.stock_uom = uomOptions.value[0] || "Nos"
		if (
			!parentGroups.value.some(
				(row) => row.name === groupForm.parent_item_group,
			)
		)
			groupForm.parent_item_group = parentGroups.value[0]?.name || ""
	} catch (e) {
		console.error("Failed to load item groups", e)
	}
}

async function createItem() {
	if (itemLoading.value || !itemForm.item_name || !itemForm.item_group) return
	itemError.value = ""
	itemSuccess.value = ""
	itemLoading.value = true
	try {
		const result = await call("pos_next.api.catalog.create_quick_item", {
			item_code: itemForm.item_code,
			item_name: itemForm.item_name,
			item_group: itemForm.item_group,
			price: itemForm.selling_price || 0,
			buying_price: itemForm.buying_price || 0,
			stock_uom: itemForm.stock_uom || "Unit",
			barcode: itemForm.barcode || null,
			is_stock_item: itemForm.is_stock_item ? 1 : 0,
			valid_from: itemForm.valid_from || null,
			valid_upto: itemForm.valid_upto || null,
			pos_profile: props.posProfile,
		})
		itemSuccess.value = result?.item_name || itemForm.item_name
		// Reset form for next entry
		itemForm.item_name = ""
		itemForm.item_code = ""
		itemForm.barcode = ""
		itemForm.selling_price = 0
		itemForm.buying_price = 0
		// Keep item_group and uom for faster repeated entry
		setTimeout(() => {
			itemSuccess.value = ""
		}, 4000)
	} catch (e) {
		itemError.value =
			e?.message ||
			e?.exc_type ||
			__("Failed to create item. Please try again.")
		setTimeout(() => {
			itemError.value = ""
		}, 5000)
	} finally {
		itemLoading.value = false
	}
}

async function createGroup() {
	if (groupLoading.value || !groupForm.group_name) return
	groupError.value = ""
	groupSuccess.value = ""
	groupLoading.value = true
	try {
		await call("pos_next.api.catalog.create_item_group", {
			group_name: groupForm.group_name,
			parent_item_group: groupForm.parent_item_group || "All Item Groups",
			pos_profile: props.posProfile,
		})
		groupSuccess.value = groupForm.group_name
		groupForm.group_name = ""
		// Refresh item groups list
		await loadItemGroups()
		setTimeout(() => {
			groupSuccess.value = ""
		}, 4000)
	} catch (e) {
		groupError.value =
			e?.message ||
			e?.exc_type ||
			__("Failed to create group. Please try again.")
		setTimeout(() => {
			groupError.value = ""
		}, 5000)
	} finally {
		groupLoading.value = false
	}
}
</script>

<style scoped>
.slide-panel-enter-active,
.slide-panel-leave-active {
	transition: transform 0.25s ease;
}
.slide-panel-enter-from,
.slide-panel-leave-to {
	transform: translateX(100%);
}
[dir="rtl"] .slide-panel-enter-from,
[dir="rtl"] .slide-panel-leave-to {
	transform: translateX(-100%);
}
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
