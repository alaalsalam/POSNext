<template>
	<div v-if="show" class="pos-management-screen absolute inset-0 z-[300] flex flex-col bg-white">
		<header class="pos-management-header flex items-center justify-between flex-shrink-0">
			<div class="flex items-center gap-3">
				<div class="pos-management-brand-icon"><FeatherIcon name="clipboard" class="w-5 h-5 text-white" /></div>
				<div>
					<h2 class="text-base font-bold text-gray-900">{{ __('Inventory Count & Adjustment') }}</h2>
					<p class="text-xs text-gray-500">{{ __('Count stock and update POS buying and selling prices') }}</p>
				</div>
			</div>
			<button type="button" class="pos-management-close" :title="__('Close')" @click="$emit('close')"><FeatherIcon name="x" class="w-5 h-5" /></button>
		</header>

		<div class="flex-1 overflow-y-auto p-4 lg:p-6">
			<div class="max-w-6xl mx-auto space-y-5">
				<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
					<label class="pos-field"><span>{{ __('Adjustment Type') }}</span>
						<select v-model="purpose"><option value="Opening Stock">{{ __('Opening Stock') }}</option><option value="Stock Reconciliation">{{ __('Stock Reconciliation') }}</option></select>
					</label>
					<label class="pos-field"><span>{{ __('Posting Date') }}</span><input v-model="postingDate" type="date" /></label>
					<div class="rounded-xl border border-blue-100 bg-blue-50 px-3 py-2.5 text-xs text-blue-800">
						<div class="font-semibold">{{ context.company || __('Loading...') }}</div>
						<div>{{ context.warehouse || __('Loading warehouse...') }}</div>
					</div>
				</div>

				<div class="rounded-xl border border-gray-200 bg-gray-50 p-3 relative">
					<label class="text-xs font-semibold text-gray-700">{{ __('Search and add item') }}</label>
					<div class="mt-1 flex gap-2"><input v-model.trim="searchTerm" class="pos-input" :placeholder="__('Search by item name or code')" @input="scheduleSearch" /><button class="pos-management-secondary" :disabled="searching" @click="searchItems">{{ searching ? __('Searching...') : __('Search') }}</button></div>
					<div v-if="searchResults.length" class="mt-2 rounded-lg bg-white border border-gray-200 overflow-hidden max-h-48 overflow-y-auto">
						<button v-for="item in searchResults" :key="item.item_code" class="w-full px-3 py-2 text-start text-sm hover:bg-blue-50 flex justify-between gap-3" @click="addItem(item)"><span>{{ item.item_name }} <small class="text-gray-400">{{ item.item_code }}</small></span><span class="text-gray-500">{{ item.actual_qty ?? 0 }}</span></button>
					</div>
				</div>

				<div v-if="errorMessage" class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ errorMessage }}</div>
				<div v-if="successMessage" class="rounded-xl border border-green-200 bg-green-50 p-3 text-sm text-green-700">{{ successMessage }}</div>

				<div class="rounded-xl border border-gray-200 overflow-x-auto">
					<table class="min-w-full text-sm"><thead class="bg-gray-50 text-gray-500 text-xs"><tr><th>{{ __('Item') }}</th><th>{{ __('Current Qty') }}</th><th>{{ __('Counted Qty') }}</th><th>{{ __('Buying Rate') }}</th><th>{{ __('Selling Rate') }}</th><th></th></tr></thead>
						<tbody><tr v-for="(row, index) in rows" :key="row.item_code" class="border-t border-gray-100"><td><div class="font-medium">{{ row.item_name }}</div><small class="text-gray-400">{{ row.item_code }}</small></td><td>{{ row.current_qty }}</td><td><input v-model.number="row.qty" min="0" step="0.001" type="number" class="pos-table-input" /></td><td><input v-model.number="row.buying_rate" min="0" step="0.01" type="number" class="pos-table-input" /></td><td><input v-model.number="row.selling_rate" min="0" step="0.01" type="number" class="pos-table-input" /></td><td><button class="text-red-500 hover:text-red-700" :title="__('Remove')" @click="rows.splice(index, 1)"><FeatherIcon name="trash-2" class="w-4 h-4" /></button></td></tr>
						<tr v-if="!rows.length"><td colspan="6" class="py-10 text-center text-gray-400">{{ __('Search for an item to begin the count') }}</td></tr></tbody>
					</table>
				</div>
				<p class="text-xs text-gray-500">{{ purpose === 'Opening Stock' ? __('Use Opening Stock only for initial balances.') : __('Use Stock Reconciliation to correct a physical count. Submitted rows update inventory and optional POS prices.') }}</p>
			</div>
		</div>

		<footer class="border-t border-gray-200 bg-white px-4 py-3 flex justify-end gap-2"><button class="pos-management-secondary" @click="$emit('close')">{{ __('Cancel') }}</button><button class="pos-management-primary" :disabled="submitting || !rows.length" @click="submit">{{ submitting ? __('Submitting...') : __('Submit Inventory Adjustment') }}</button></footer>
	</div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { call } from '@/utils/apiWrapper'

const props = defineProps({ show: Boolean, posProfile: { type: String, required: true } })
defineEmits(['close'])
const context = ref({})
const purpose = ref('Stock Reconciliation')
const postingDate = ref(new Date().toISOString().slice(0, 10))
const searchTerm = ref('')
const searchResults = ref([])
const rows = ref([])
const searching = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
let timer

watch(() => props.show, async (visible) => {
	if (!visible) return
	errorMessage.value = ''; successMessage.value = ''; searchResults.value = []
	try { context.value = await call('pos_next.api.inventory.get_stock_reconciliation_context', { pos_profile: props.posProfile }) || {} }
	catch (error) { errorMessage.value = error?.message || __('Unable to load inventory context.') }
})

function scheduleSearch() { clearTimeout(timer); timer = setTimeout(searchItems, 250) }
async function searchItems() {
	if (!searchTerm.value || searchTerm.value.length < 2) { searchResults.value = []; return }
	searching.value = true
	try { searchResults.value = await call('pos_next.api.items.get_items', { pos_profile: props.posProfile, search_term: searchTerm.value, limit: 10 }) || [] }
	catch (error) { errorMessage.value = error?.message || __('Unable to search items.') }
	finally { searching.value = false }
}
function addItem(item) {
	if (rows.value.some((row) => row.item_code === item.item_code)) return
	rows.value.push({ item_code: item.item_code, item_name: item.item_name, current_qty: item.actual_qty ?? 0, qty: item.actual_qty ?? 0, buying_rate: 0, selling_rate: item.rate || item.price_list_rate || 0 })
	searchTerm.value = ''; searchResults.value = []
}
async function submit() {
	if (submitting.value || !rows.value.length) return
	errorMessage.value = ''; successMessage.value = ''; submitting.value = true
	try {
		const result = await call('pos_next.api.inventory.submit_pos_stock_reconciliation', { pos_profile: props.posProfile, purpose: purpose.value, posting_date: postingDate.value, rows: rows.value })
		successMessage.value = result?.message || __('Inventory adjustment submitted successfully.')
		rows.value = []
	} catch (error) { errorMessage.value = error?.message || __('Unable to submit inventory adjustment.') }
	finally { submitting.value = false }
}
</script>

<style scoped>
.pos-field span { display:block; margin-bottom:.35rem; font-size:.75rem; font-weight:600; color:#374151 }.pos-field select,.pos-field input,.pos-input { width:100%; height:2.5rem; border:1px solid #d1d5db; border-radius:.5rem; padding:0 .75rem; background:#fff }.pos-table-input { width:7rem; height:2rem; border:1px solid #d1d5db; border-radius:.4rem; padding:0 .45rem } th,td { padding:.7rem .8rem; text-align:start }
</style>
