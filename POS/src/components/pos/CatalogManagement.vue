<template>
	<div
		v-if="show"
		class="pos-management-screen absolute inset-0 z-[300] flex flex-col"
	>
		<!-- Header -->
		<header class="pos-management-header flex items-center justify-between flex-shrink-0">
			<div class="flex items-center gap-3">
				<div class="cat-brand-icon">
					<FeatherIcon name="package" class="w-5 h-5 text-white" />
				</div>
				<div>
					<h2 class="text-base font-bold text-gray-900">{{ __("شاشة الأصناف") }}</h2>
					<p class="text-xs text-gray-500">{{ __("إدارة الأصناف — إضافة وتعديل وحذف") }}</p>
				</div>
			</div>
			<button
				type="button"
				class="pos-management-close"
				:title="__('إغلاق')"
				@click="$emit('close')"
			>
				<FeatherIcon name="x" class="w-5 h-5" />
			</button>
		</header>

		<!-- Toolbar -->
		<div class="cat-toolbar flex-shrink-0">
			<div class="flex items-center gap-2 flex-wrap">
				<button
					type="button"
					class="cat-tb-btn"
					data-testid="cat-add"
					:title="__('إضافة')"
					@click="enterAddMode"
				>
					<span class="cat-tb-icon bg-orange-600"><FeatherIcon name="plus" class="w-4 h-4 text-white" /></span>
					<span>{{ __("إضافة") }}</span>
				</button>

				<button
					type="button"
					class="cat-tb-btn"
					data-testid="cat-save"
					:title="__('حفظ')"
					:disabled="!isEditable || saving"
					@click="onSave"
				>
					<span class="cat-tb-icon bg-orange-500"><FeatherIcon name="save" class="w-4 h-4 text-white" /></span>
					<span>{{ saving ? __("جارٍ الحفظ...") : __("حفظ") }}</span>
				</button>

				<button
					v-if="canManageCatalog"
					type="button"
					class="cat-tb-btn"
					data-testid="cat-edit"
					:title="__('تعديل')"
					:disabled="selectedIndex < 0 || loading"
					@click="onEdit"
				>
					<span class="cat-tb-icon bg-amber-500"><FeatherIcon name="edit-2" class="w-4 h-4 text-white" /></span>
					<span>{{ __("تعديل") }}</span>
				</button>

				<button
					v-if="canManageCatalog"
					type="button"
					class="cat-tb-btn"
					data-testid="cat-delete"
					:title="__('حذف')"
					:disabled="selectedIndex < 0 || deleting"
					@click="onDelete"
				>
					<span class="cat-tb-icon bg-red-500"><FeatherIcon name="trash-2" class="w-4 h-4 text-white" /></span>
					<span>{{ __("حذف") }}</span>
				</button>

				<div class="cat-tb-divider" />

				<!-- Record navigation (client-side cursor over the sorted grid) -->
				<div class="flex items-center gap-1">
					<button type="button" class="cat-nav-btn" data-testid="cat-nav-first" :title="__('أول صنف')" :disabled="!canGoPrev" @click="navTo('first')"><FeatherIcon name="chevrons-right" class="w-4 h-4" /></button>
					<button type="button" class="cat-nav-btn" data-testid="cat-nav-prev" :title="__('الصنف السابق')" :disabled="!canGoPrev" @click="navTo('prev')"><FeatherIcon name="chevron-right" class="w-4 h-4" /></button>
					<span class="cat-nav-pos">{{ rows.length ? (selectedIndex + 1) + " / " + rows.length : "0 / 0" }}</span>
					<button type="button" class="cat-nav-btn" data-testid="cat-nav-next" :title="__('الصنف التالي')" :disabled="!canGoNext" @click="navTo('next')"><FeatherIcon name="chevron-left" class="w-4 h-4" /></button>
					<button type="button" class="cat-nav-btn" data-testid="cat-nav-last" :title="__('آخر صنف')" :disabled="!canGoNext" @click="navTo('last')"><FeatherIcon name="chevrons-left" class="w-4 h-4" /></button>
				</div>

				<div class="cat-tb-divider" />

				<!-- Search -->
				<div class="flex items-center gap-1">
					<input
						v-model.trim="searchTerm"
						type="search"
						class="cat-search-input"
						data-testid="cat-search-input"
						:placeholder="__('بحث بالاسم أو الكود أو الباركود')"
						@keydown.enter="doSearch"
					/>
					<button type="button" class="cat-tb-btn" data-testid="cat-search-btn" :title="__('بحث')" :disabled="loading" @click="doSearch">
						<span class="cat-tb-icon bg-orange-600"><FeatherIcon name="search" class="w-4 h-4 text-white" /></span>
						<span>{{ __("بحث") }}</span>
					</button>
					<button type="button" class="cat-nav-btn" :title="__('تحديث')" :disabled="loading" @click="onRefresh"><FeatherIcon name="refresh-cw" class="w-4 h-4" /></button>
				</div>
			</div>
		</div>

		<!-- Scroll body: form + grid -->
		<div class="flex-1 overflow-y-auto p-3 lg:p-4">
			<!-- Peach master form -->
			<section class="cat-form">
				<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-x-6 gap-y-3">
					<!-- Item code (read-only) -->
					<label class="cat-field">
						<span class="cat-label">{{ __("كود الصنف") }}</span>
						<input :value="form.item_code" type="text" class="cat-input" data-testid="cat-item-code" readonly :placeholder="mode === 'add' ? __('تلقائي') : ''" />
					</label>

					<!-- Item name -->
					<label class="cat-field">
						<span class="cat-label">{{ __("اسم الصنف") }} <span class="text-red-500">*</span></span>
						<input v-model="form.item_name" type="text" class="cat-input" data-testid="cat-item-name" :readonly="!isEditable" :placeholder="__('اسم الصنف')" />
					</label>

					<!-- Barcode -->
					<label class="cat-field">
						<span class="cat-label">{{ __("الباركود") }}</span>
						<input v-model.trim="form.barcode" type="text" class="cat-input" :readonly="!isEditable" :placeholder="__('اختياري')" />
					</label>

					<!-- Item group (autocomplete + add) -->
					<div class="cat-field items-start">
						<span class="cat-label mt-2">{{ __("اسم المجموعة") }} <span class="text-red-500">*</span></span>
						<div class="flex-1 min-w-0">
							<div v-if="isEditable" class="flex gap-1">
								<div class="flex-1 min-w-0">
									<AutocompleteSelect
										v-model="form.item_group"
										:options="groupOptions"
										:placeholder="__('اختر المجموعة')"
										required
									/>
								</div>
								<button type="button" class="cat-add-group" :title="__('إضافة مجموعة')" @click="showAddGroup = !showAddGroup"><FeatherIcon name="plus" class="w-4 h-4" /></button>
							</div>
							<input v-else :value="form.item_group" type="text" class="cat-input" readonly />
							<div v-if="isEditable && showAddGroup" class="mt-1 flex gap-1">
								<input v-model.trim="newGroupName" type="text" class="cat-input" :placeholder="__('اسم المجموعة الجديدة')" @keydown.enter.prevent="addGroup" />
								<button type="button" class="cat-mini-btn" :disabled="savingGroup || !newGroupName" @click="addGroup">{{ savingGroup ? __("...") : __("إضافة مجموعة") }}</button>
							</div>
						</div>
					</div>

					<!-- Stock UOM -->
					<label class="cat-field">
						<span class="cat-label">{{ __("وحدة الصنف") }}</span>
						<select v-model="form.stock_uom" class="cat-input" :disabled="!isEditable">
							<option v-for="u in uoms" :key="u" :value="u">{{ u }}</option>
						</select>
					</label>

					<!-- Serial -->
					<label class="cat-field">
						<span class="cat-label">{{ __("السريال") }}</span>
						<input v-model.trim="form.serial" type="text" class="cat-input" :readonly="!isEditable" :placeholder="__('اختياري')" />
					</label>

					<!-- Quantity -->
					<label class="cat-field">
						<span class="cat-label">{{ __("الكمية") }}</span>
						<input v-model.number="form.qty" type="number" min="0" step="1" class="cat-input" data-testid="cat-qty" :readonly="!isEditable" />
					</label>

					<!-- Available (read-only) -->
					<label class="cat-field">
						<span class="cat-label">{{ __("الكمية المتاحة") }}</span>
						<input :value="mode === 'add' ? '' : form.available" type="text" class="cat-input cat-readonly" readonly />
					</label>

					<!-- Cost price -->
					<label class="cat-field">
						<span class="cat-label">{{ __("سعر التكلفة") }}</span>
						<input v-model.number="form.cost_price" type="number" min="0" step="0.01" class="cat-input" data-testid="cat-cost" :readonly="!isEditable" />
					</label>

					<!-- Selling price -->
					<label class="cat-field">
						<span class="cat-label">{{ __("سعر البيع") }}</span>
						<input v-model.number="form.selling_price" type="number" min="0" step="0.01" class="cat-input" :readonly="!isEditable" />
					</label>

					<!-- Description (textarea) -->
					<div class="cat-field items-start xl:col-span-2">
						<span class="cat-label mt-2">{{ __("الوصف") }}</span>
						<textarea v-model="form.description" rows="2" class="cat-input" :readonly="!isEditable" :placeholder="__('وصف الصنف')"></textarea>
					</div>

					<!-- Image -->
					<div class="cat-field items-start">
						<span class="cat-label mt-2">{{ __("صورة الصنف") }}</span>
						<div class="flex-1 min-w-0 flex items-center gap-2">
							<div class="cat-thumb">
								<img v-if="form.image" :src="form.image" :alt="form.item_name || __('صورة الصنف')" />
								<FeatherIcon v-else name="image" class="w-5 h-5 text-orange-300" />
							</div>
							<div v-if="isEditable" class="flex flex-col gap-1">
								<input ref="fileInput" type="file" accept="image/*" class="hidden" @change="uploadImage" />
								<button type="button" class="cat-mini-btn" :disabled="uploading" @click="fileInput?.click()">{{ uploading ? __("جارٍ الرفع...") : __("رفع صورة") }}</button>
								<button v-if="form.image" type="button" class="cat-mini-btn cat-mini-danger" @click="form.image = ''">{{ __("إزالة الصورة") }}</button>
							</div>
						</div>
					</div>
				</div>
			</section>

			<!-- Data grid -->
			<section class="cat-grid-wrap mt-4">
				<div v-if="loading" class="cat-grid-state">{{ __("جارٍ التحميل...") }}</div>
				<div v-else-if="!rows.length" class="cat-grid-state">{{ __("لا توجد أصناف") }}</div>
				<table v-else class="cat-grid">
					<thead>
						<tr>
							<th>{{ __("الكود") }}</th>
							<th>{{ __("اسم الصنف") }}</th>
							<th>{{ __("الكمية") }}</th>
							<th>{{ __("المتاحة") }}</th>
							<th>{{ __("سعر التكلفة") }}</th>
							<th>{{ __("سعر البيع") }}</th>
							<th>{{ __("السريال") }}</th>
							<th>{{ __("الباركود") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="(row, index) in rows"
							:key="row.item_code"
							class="cat-row"
							:class="{ 'cat-row-active': index === selectedIndex, 'cat-row-disabled': row.disabled }"
							:data-testid="'cat-row-' + index"
							@click="selectRow(index)"
						>
							<td class="font-mono">{{ row.item_code }}</td>
							<td>
								{{ row.item_name }}
								<span v-if="row.disabled" class="cat-badge">{{ __("معطّل") }}</span>
							</td>
							<td>{{ row.qty }}</td>
							<td>{{ row.available }}</td>
							<td>{{ money(row.cost_price) }}</td>
							<td>{{ money(row.selling_price) }}</td>
							<td>{{ row.serial || "—" }}</td>
							<td>{{ row.barcode || "—" }}</td>
						</tr>
					</tbody>
				</table>
			</section>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue"
import { FeatherIcon } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { managerTranslate as __ } from "@/utils/managementI18n"
import { parseError } from "@/utils/errorHandler"
import { useToast } from "@/composables/useToast"
import { formatCurrency } from "@/utils/currency"
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue"

const props = defineProps({
	show: { type: Boolean, default: false },
	posProfile: { type: String, required: true },
	canManageCatalog: { type: Boolean, default: false },
})
defineEmits(["close"])

const { showSuccess, showError } = useToast()

const mode = ref("view") // 'add' | 'edit' | 'view'
const rows = ref([])
const currency = ref("")
const selectedIndex = ref(-1)
const searchTerm = ref("")
const uoms = ref([])
const itemGroups = ref([])

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const uploading = ref(false)
const savingGroup = ref(false)
const showAddGroup = ref(false)
const newGroupName = ref("")
const fileInput = ref(null)

const form = reactive({
	item_code: "",
	item_name: "",
	item_group: "",
	barcode: "",
	stock_uom: "Nos",
	serial: "",
	qty: 0,
	available: 0,
	cost_price: 0,
	selling_price: 0,
	description: "",
	image: "",
})

const isEditable = computed(() => mode.value === "add" || mode.value === "edit")
const canGoPrev = computed(() => selectedIndex.value > 0)
const canGoNext = computed(() => selectedIndex.value >= 0 && selectedIndex.value < rows.value.length - 1)
const groupOptions = computed(() => itemGroups.value.map((g) => ({ value: g, label: g })))

function money(value) {
	return formatCurrency(Number(value) || 0, currency.value)
}

watch(
	() => props.show,
	async (visible) => {
		if (!visible) return
		await Promise.all([loadDefaults(), loadGrid()])
		if (rows.value.length) selectRow(0)
		else enterAddMode()
	},
	{ immediate: true },
)

async function loadDefaults() {
	try {
		const [defaults, groups] = await Promise.all([
			call("pos_next.api.catalog.get_catalog_defaults", { pos_profile: props.posProfile }),
			call("pos_next.api.catalog.get_item_groups_for_select", { pos_profile: props.posProfile }),
		])
		uoms.value = defaults?.uoms || []
		if (!uoms.value.includes(form.stock_uom)) form.stock_uom = uoms.value[0] || "Nos"
		itemGroups.value = groups || []
	} catch (e) {
		showError(parseError(e).message)
	}
}

async function loadGrid(search = "") {
	loading.value = true
	try {
		const res = await call("pos_next.api.catalog.get_catalog_items", {
			pos_profile: props.posProfile,
			search: search || undefined,
		})
		rows.value = res?.items || []
		currency.value = res?.currency || currency.value
	} catch (e) {
		rows.value = []
		showError(parseError(e).message)
	} finally {
		loading.value = false
	}
}

function populateForm(row) {
	form.item_code = row.item_code || ""
	form.item_name = row.item_name || ""
	form.item_group = row.item_group || ""
	form.barcode = row.barcode || ""
	form.stock_uom = row.stock_uom || uoms.value[0] || "Nos"
	form.serial = row.serial || ""
	form.qty = Number(row.qty) || 0
	form.available = Number(row.available) || 0
	form.cost_price = Number(row.cost_price) || 0
	form.selling_price = Number(row.selling_price) || 0
	form.description = row.description || ""
	form.image = row.image || ""
}

function selectRow(index) {
	if (index < 0 || index >= rows.value.length) return
	selectedIndex.value = index
	mode.value = "view"
	showAddGroup.value = false
	populateForm(rows.value[index])
}

function enterAddMode() {
	mode.value = "add"
	selectedIndex.value = -1
	showAddGroup.value = false
	newGroupName.value = ""
	Object.assign(form, {
		item_code: "",
		item_name: "",
		item_group: "",
		barcode: "",
		stock_uom: uoms.value[0] || "Nos",
		serial: "",
		qty: 0,
		available: 0,
		cost_price: 0,
		selling_price: 0,
		description: "",
		image: "",
	})
}

async function onEdit() {
	if (!props.canManageCatalog || selectedIndex.value < 0) return
	const code = rows.value[selectedIndex.value].item_code
	loading.value = true
	try {
		const item = await call("pos_next.api.catalog.get_catalog_item", {
			item_code: code,
			pos_profile: props.posProfile,
		})
		populateForm(item)
		mode.value = "edit"
	} catch (e) {
		showError(parseError(e).message)
	} finally {
		loading.value = false
	}
}

function validateForm() {
	if (!form.item_name) {
		showError(__("اسم الصنف مطلوب"))
		return false
	}
	if (!form.item_group) {
		showError(__("اسم المجموعة مطلوب"))
		return false
	}
	if (Number(form.qty) > 0 && Number(form.cost_price) <= 0) {
		showError(__("أدخل سعر تكلفة للكمية المضافة"))
		return false
	}
	return true
}

async function onSave() {
	if (saving.value || !isEditable.value || !validateForm()) return
	saving.value = true
	try {
		let result
		if (mode.value === "add") {
			result = await call("pos_next.api.catalog.create_catalog_item", {
				item_name: form.item_name,
				item_group: form.item_group,
				stock_uom: form.stock_uom,
				qty: Number(form.qty) || 0,
				cost_price: Number(form.cost_price) || 0,
				selling_price: Number(form.selling_price) || 0,
				barcode: form.barcode,
				serial: form.serial,
				description: form.description,
				image: form.image,
				pos_profile: props.posProfile,
			})
		} else {
			result = await call("pos_next.api.catalog.update_catalog_item", {
				item_code: form.item_code,
				item_name: form.item_name,
				item_group: form.item_group,
				stock_uom: form.stock_uom,
				qty: Number(form.qty) || 0,
				cost_price: Number(form.cost_price) || 0,
				selling_price: Number(form.selling_price) || 0,
				barcode: form.barcode,
				serial: form.serial,
				description: form.description,
				image: form.image,
				pos_profile: props.posProfile,
			})
		}
		showSuccess(__("تم حفظ الصنف {0}", [result?.item_code || ""]))
		await loadGrid(searchTerm.value)
		const idx = rows.value.findIndex((r) => r.item_code === result?.item_code)
		if (idx >= 0) selectRow(idx)
		else if (result) populateForm(result), (mode.value = "view")
	} catch (e) {
		showError(parseError(e).message)
	} finally {
		saving.value = false
	}
}

async function onDelete() {
	if (!props.canManageCatalog || selectedIndex.value < 0 || deleting.value) return
	const row = rows.value[selectedIndex.value]
	if (!window.confirm(__("حذف الصنف {0}؟", [row.item_code]))) return
	deleting.value = true
	try {
		const res = await call("pos_next.api.catalog.delete_catalog_item", {
			item_code: row.item_code,
			pos_profile: props.posProfile,
		})
		showSuccess(res?.deleted ? __("تم حذف الصنف") : __("تم تعطيل الصنف"))
		await loadGrid(searchTerm.value)
		if (rows.value.length) selectRow(Math.min(selectedIndex.value, rows.value.length - 1))
		else enterAddMode()
	} catch (e) {
		showError(parseError(e).message)
	} finally {
		deleting.value = false
	}
}

async function doSearch() {
	await loadGrid(searchTerm.value)
	if (rows.value.length) selectRow(0)
	else {
		selectedIndex.value = -1
		mode.value = "view"
	}
}

async function onRefresh() {
	const code = form.item_code
	await loadGrid(searchTerm.value)
	const idx = rows.value.findIndex((r) => r.item_code === code)
	if (idx >= 0) selectRow(idx)
	else if (rows.value.length) selectRow(0)
}

function navTo(where) {
	if (!rows.value.length) return
	let index = selectedIndex.value
	if (where === "first") index = 0
	else if (where === "last") index = rows.value.length - 1
	else if (where === "prev") index = Math.max(0, index - 1)
	else if (where === "next") index = Math.min(rows.value.length - 1, index + 1)
	selectRow(index)
}

async function addGroup() {
	if (savingGroup.value || !newGroupName.value) return
	savingGroup.value = true
	try {
		const res = await call("pos_next.api.catalog.create_item_group", {
			group_name: newGroupName.value,
			pos_profile: props.posProfile,
		})
		const name = res?.name || newGroupName.value
		if (!itemGroups.value.includes(name)) itemGroups.value = [...itemGroups.value, name].sort()
		form.item_group = name
		newGroupName.value = ""
		showAddGroup.value = false
		showSuccess(__("تمت إضافة المجموعة"))
	} catch (e) {
		showError(parseError(e).message)
	} finally {
		savingGroup.value = false
	}
}

async function uploadImage(event) {
	const file = event.target.files?.[0]
	if (!file) return
	uploading.value = true
	try {
		const body = new FormData()
		body.append("file", file, file.name)
		body.append("is_private", "0")
		const response = await fetch("/api/method/upload_file", {
			method: "POST",
			credentials: "same-origin",
			headers: {
				"X-Frappe-CSRF-Token": window.csrf_token || "",
				"X-Frappe-Site-Name": window.location.hostname,
			},
			body,
		})
		const uploaded = await response.json()
		if (!response.ok || uploaded.exc || !uploaded.message?.file_url) {
			throw new Error(uploaded._server_messages || __("فشل رفع الصورة"))
		}
		form.image = uploaded.message.file_url
	} catch (e) {
		showError(parseError(e).message)
	} finally {
		uploading.value = false
		if (event.target) event.target.value = ""
	}
}
</script>

<style scoped>
.cat-brand-icon {
	@apply flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-orange-600 text-white shadow-sm;
}
.cat-toolbar {
	@apply border-b border-orange-200 bg-orange-50 px-3 py-2;
}
.cat-tb-btn {
	@apply flex items-center gap-2 rounded-lg px-2 py-1 text-sm font-semibold text-gray-800 transition-colors hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-40;
}
.cat-tb-icon {
	@apply flex h-9 w-9 items-center justify-center rounded-full shadow-sm;
}
.cat-tb-divider {
	@apply mx-1 h-8 w-px bg-orange-200;
}
.cat-nav-btn {
	@apply flex h-9 w-9 items-center justify-center rounded-full border border-orange-300 bg-white text-orange-700 transition-colors hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-40;
}
.cat-nav-pos {
	@apply px-1 text-xs font-semibold tabular-nums text-gray-600;
}
.cat-search-input {
	@apply h-9 w-44 rounded-lg border border-orange-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 sm:w-56;
}

.cat-form {
	@apply rounded-2xl border border-orange-200 bg-orange-50 p-4 shadow-sm;
}
.cat-field {
	@apply flex items-center gap-2;
}
.cat-label {
	@apply flex-shrink-0 text-end text-sm font-semibold text-orange-900;
	width: 6.5rem;
}
.cat-input {
	@apply h-9 w-full min-w-0 flex-1 rounded-lg border border-orange-200 bg-white px-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-400 disabled:bg-orange-50;
}
textarea.cat-input {
	@apply h-auto py-2;
}
.cat-readonly {
	@apply bg-orange-100 font-semibold;
}
.cat-add-group,
.cat-mini-btn {
	@apply flex h-9 items-center justify-center rounded-lg border border-orange-300 bg-white px-2 text-sm font-semibold text-orange-700 transition-colors hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-50;
}
.cat-mini-danger {
	@apply border-red-200 text-red-600 hover:bg-red-50;
}
.cat-thumb {
	@apply flex h-16 w-16 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg border border-orange-200 bg-white;
}
.cat-thumb img {
	@apply h-full w-full object-cover;
}

.cat-grid-wrap {
	@apply overflow-x-auto rounded-xl border border-orange-200 bg-white;
}
.cat-grid-state {
	@apply py-12 text-center text-sm text-gray-400;
}
.cat-grid {
	@apply min-w-full text-sm;
}
.cat-grid thead th {
	@apply sticky top-0 bg-orange-100 px-3 py-2.5 text-start text-xs font-bold text-orange-900;
}
.cat-grid tbody td {
	@apply px-3 py-2 text-start text-gray-800;
}
.cat-row {
	@apply cursor-pointer border-t border-orange-100 transition-colors hover:bg-orange-50;
}
.cat-row-active {
	@apply bg-orange-100 hover:bg-orange-100;
}
.cat-row-disabled {
	@apply text-gray-400;
}
.cat-badge {
	@apply ms-1 rounded bg-gray-200 px-1.5 py-0.5 text-[10px] font-semibold text-gray-600;
}
</style>
