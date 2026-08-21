<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between gap-3 flex-shrink-0">
      <div class="flex items-center gap-3">
        <button @click="$emit('back')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h2 class="text-base font-bold text-gray-900">
            {{ isNew ? __("فاتورة شراء جديدة") : __("تعديل فاتورة") }}
          </h2>
          <p v-if="form.name" class="text-xs text-gray-400">{{ form.name }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <!-- Status badge -->
        <span v-if="!isNew" :class="docstatusClass" class="text-[10px] font-bold px-2 py-0.5 rounded-full">
          {{ docstatusLabel }}
        </span>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="errorMsg" data-testid="purchase-error" class="mx-3 mt-3 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2 flex-shrink-0">
      <svg class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-xs text-red-700 flex-1" v-html="errorMsg"></p>
      <button v-if="staleDraft && form.name" data-testid="purchase-reload" @click="loadInvoice(form.name)" class="text-xs font-semibold text-red-700 underline">
        {{ __("Reload Draft") }}
      </button>
      <button @click="errorMsg=''" class="text-red-400 hover:text-red-600 flex-shrink-0">×</button>
    </div>

    <!-- Form body -->
    <div class="flex-1 overflow-y-auto p-3 flex flex-col gap-3">

      <!-- Supplier section -->
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">{{ __("المورد") }}</h3>
        <div class="grid grid-cols-1 gap-3">
          <!-- Supplier autocomplete -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("المورد") }} <span class="text-red-500">*</span></label>
            <div class="relative">
              <input
                v-model="supplierSearch"
                @input="searchSuppliers"
                @focus="supplierSearch = form.supplier_name || form.supplier; showSupplierDropdown = true"
                :placeholder="__('ابحث عن مورد...')"
                :disabled="isSubmitted"
                class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:bg-gray-50"
                :class="form.supplier ? 'border-green-300 bg-green-50/30' : 'border-gray-200'"
              />
              <div v-if="showSupplierDropdown && supplierOptions.length" class="absolute top-full mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-lg z-50 max-h-48 overflow-y-auto">
                <button
                  v-for="s in supplierOptions" :key="s.name"
                  @mousedown.prevent="selectSupplier(s)"
                  class="w-full text-start px-3 py-2 text-sm hover:bg-blue-50 transition-colors"
                >
                  <span class="font-semibold">{{ s.supplier_name }}</span>
                  <span class="text-xs text-gray-400 ms-2">{{ s.supplier_group }}</span>
                </button>
                <button
                  @mousedown.prevent="showCreateSupplier = true; showSupplierDropdown = false"
                  class="w-full text-start px-3 py-2 text-xs text-blue-600 font-semibold hover:bg-blue-50 border-t border-gray-100 flex items-center gap-1"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                  {{ __("إنشاء مورد جديد: {0}", [supplierSearch]) }}
                </button>
              </div>
            </div>
            <!-- Quick create supplier -->
            <div v-if="showCreateSupplier" class="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg grid grid-cols-1 sm:grid-cols-[1fr_1fr_1fr_auto_auto] items-center gap-2">
              <input v-model="newSupplierName" :placeholder="__('اسم المورد الجديد')" class="flex-1 h-8 px-3 text-xs rounded-lg border border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <input v-model="newSupplierMobileNo" type="tel" autocomplete="tel" :placeholder="__('Mobile Number')" class="flex-1 h-8 px-3 text-xs rounded-lg border border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <select v-model="newSupplierGroup" class="h-8 px-2 text-xs rounded-lg border border-blue-300 bg-white">
                <option value="">{{ __("Supplier Group") }}</option>
                <option v-for="group in supplierGroups" :key="group.name" :value="group.name">{{ group.name }}</option>
              </select>
              <button @click="createSupplier" :disabled="!newSupplierName || !newSupplierMobileNo || !newSupplierGroup || creatingSupplier" class="h-8 px-3 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
                {{ creatingSupplier ? __("...") : __("إنشاء") }}
              </button>
              <button @click="showCreateSupplier = false" class="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
            </div>
          </div>

          <!-- Bill No + dates row -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("رقم فاتورة المورد") }}</label>
              <input v-model="form.bill_no" :disabled="isSubmitted" :placeholder="__('اختياري')"
                class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("تاريخ الفاتورة") }} <span class="text-red-500">*</span></label>
              <input type="date" v-model="form.posting_date" :disabled="isSubmitted"
                class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("تاريخ الاستحقاق") }}</label>
            <input type="date" v-model="form.due_date" :disabled="isSubmitted"
              class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
          </div>
        </div>
      </div>

      <!-- Items section -->
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("الأصناف") }}</h3>
          <button v-if="!isSubmitted" @click="addLine"
            class="flex items-center gap-1 text-xs text-blue-600 font-semibold hover:text-blue-700 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            {{ __("إضافة صنف") }}
          </button>
        </div>

        <div v-if="!form.items.length" class="py-6 text-center text-xs text-gray-400">
          {{ __("لا توجد أصناف. أضف صنفًا للبدء.") }}
        </div>

        <div class="flex flex-col gap-2">
          <div v-for="(line, idx) in form.items" :key="idx" class="border border-gray-100 rounded-xl p-3 bg-gray-50/50 relative">
            <div class="grid grid-cols-12 gap-2 items-start">
              <!-- Item search -->
              <div class="col-span-12">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("الصنف") }}</label>
                <div class="relative">
                  <input
                    v-model="line._itemSearch"
                    @input="searchItems(idx)"
                    @focus="line._showDrop = true"
                    :disabled="isSubmitted"
                    :placeholder="__('ابحث عن صنف...')"
                    class="w-full h-9 px-3 text-sm rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    :class="line.item_code ? 'border-green-300' : ''"
                  />
                  <div v-if="line._showDrop && line._options?.length" class="absolute top-full mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-lg z-50 max-h-40 overflow-y-auto">
                    <button v-for="it in line._options" :key="it.item_code" @mousedown.prevent="selectItem(idx, it)"
                      class="w-full text-start px-3 py-2 text-xs hover:bg-blue-50 transition-colors">
                      <span class="font-semibold">{{ it.item_name }}</span>
                      <span class="text-gray-400 ms-1">({{ it.item_code }})</span>
                    </button>
                  </div>
                </div>
              </div>
              <!-- Qty -->
              <div class="col-span-3">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("الكمية") }}</label>
                <input v-model.number="line.qty" type="number" min="0.001" step="0.001" :disabled="isSubmitted"
                  @change="calcLine(idx)"
                  class="w-full h-9 px-2 text-sm rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center disabled:bg-gray-100" />
              </div>
              <!-- UOM -->
              <div class="col-span-3">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("الوحدة") }}</label>
                <input v-model="line.uom" :disabled="isSubmitted"
                  class="w-full h-9 px-2 text-sm rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" />
              </div>
              <!-- Rate -->
              <div class="col-span-4">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("سعر الشراء") }}</label>
                <input v-model.number="line.rate" type="number" min="0" step="0.01" :disabled="isSubmitted"
                  @change="calcLine(idx)"
                  class="w-full h-9 px-2 text-sm rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-end disabled:bg-gray-100" />
              </div>
              <!-- Amount -->
              <div class="col-span-2 text-end">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("الإجمالي") }}</label>
                <p class="text-sm font-bold text-gray-900 h-9 flex items-center justify-end">{{ formatAmt(line.amount) }}</p>
              </div>
              <div class="col-span-12 sm:col-span-6">
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">{{ __("Expense Account") }}</label>
                <select v-model="line.expense_account" :disabled="isSubmitted"
                  class="w-full h-9 px-2 text-xs rounded-lg border border-gray-200 bg-white disabled:bg-gray-100">
                  <option value="">{{ __("Use ERPNext Default") }}</option>
                  <option v-for="account in expenseAccounts" :key="account.name" :value="account.name">
                    {{ account.account_name || account.name }}
                  </option>
                </select>
              </div>
              <!-- Delete -->
              <button v-if="!isSubmitted" @click="removeLine(idx)" class="absolute top-2 start-2 w-6 h-6 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Totals summary -->
        <div v-if="form.items.length" class="mt-3 pt-3 border-t border-gray-100 space-y-1">
          <div class="flex justify-between text-xs text-gray-500">
            <span>{{ __("المجموع قبل الضريبة") }}</span>
            <span class="font-semibold">{{ formatAmt(totals.net) }}</span>
          </div>
          <div v-if="form.taxes_and_charges || form.total_taxes_and_charges" class="flex justify-between text-xs text-gray-500">
            <span>{{ __("الضريبة") }}</span>
            <span class="font-semibold">{{ formatAmt(totals.tax) }}</span>
          </div>
          <p v-if="form.taxes_and_charges && !form.total_taxes_and_charges && !form.name" class="text-[11px] text-amber-700">
            {{ __("ERPNext calculates the selected tax template when the draft is saved.") }}
          </p>
          <div class="flex justify-between text-sm font-bold text-gray-900 pt-1 border-t border-gray-100">
            <span>{{ __("الإجمالي الكلي") }}</span>
            <span>{{ formatAmt(totals.grand) }}</span>
          </div>
        </div>
      </div>

      <!-- Additional info -->
      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">{{ __("معلومات إضافية") }}</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Currency") }}</label>
            <select v-model="form.currency" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm bg-white">
              <option v-for="currency in currencies" :key="currency.name" :value="currency.name">{{ currency.name }}</option>
            </select>
          </div>
          <div v-if="form.currency && form.currency !== form.company_currency">
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Exchange Rate") }}</label>
            <input v-model.number="form.conversion_rate" type="number" min="0.000001" step="0.000001" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm" />
          </div>
          <div v-if="form.price_list_currency && form.price_list_currency !== form.currency">
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Price List Exchange Rate") }}</label>
            <input v-model.number="form.plc_conversion_rate" type="number" min="0.000001" step="0.000001" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Supplier Invoice Date") }}</label>
            <input v-model="form.bill_date" type="date" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Purchase Tax Template") }}</label>
            <select v-model="form.taxes_and_charges" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm bg-white">
              <option :value="null">{{ __("No Tax Template") }}</option>
              <option v-for="template in taxTemplates" :key="template.name" :value="template.name">
                {{ template.title || template.name }}
              </option>
            </select>
          </div>
          <label class="col-span-2 flex items-center gap-2 min-h-10 text-xs font-semibold text-gray-700">
            <input v-model="form.update_stock" type="checkbox" :disabled="isSubmitted" class="w-5 h-5 accent-blue-600" />
            {{ __("Update Stock") }}
          </label>
          <div v-if="form.update_stock" class="col-span-2">
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("Warehouse") }}</label>
            <select v-model="form.set_warehouse" :disabled="isSubmitted" class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm bg-white">
              <option value="">{{ __("Select Warehouse") }}</option>
              <option v-for="warehouse in warehouses" :key="warehouse.name" :value="warehouse.name">{{ warehouse.warehouse_name || warehouse.name }}</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-semibold text-gray-700 mb-1">{{ __("ملاحظات") }}</label>
            <textarea v-model="form.remarks" rows="2" :disabled="isSubmitted" :placeholder="__('ملاحظات اختيارية...')"
              class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-gray-50" />
          </div>
        </div>
      </div>
    </div>

    <!-- Actions footer -->
    <div class="bg-white border-t border-gray-100 px-4 py-3 flex items-center justify-between gap-3 flex-shrink-0">
      <div class="text-sm font-bold text-gray-900">
        {{ __("الإجمالي:") }} {{ formatAmt(totals.grand) }}
      </div>
      <div class="flex items-center gap-2" v-if="!isSubmitted">
        <button v-if="isNew ? props.canCreate : props.canWrite" data-testid="purchase-save" @click="saveDraft" :disabled="saving"
          class="px-4 py-2 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50">
          {{ saving ? __("جاري الحفظ...") : __("حفظ مسودة") }}
        </button>
        <button v-if="props.canSubmit" data-testid="purchase-submit" @click="confirmSubmit" :disabled="saving || submitting || !formCanSubmit"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50">
          {{ __("اعتماد الفاتورة") }}
        </button>
      </div>
      <div v-else class="flex items-center gap-3 text-xs text-gray-400">
        <span>{{ isSubmitted ? __("الفاتورة معتمدة — للتعديل يجب الإلغاء أولاً") : "" }}</span>
        <button v-if="form.docstatus === 1 && props.canCancel" data-testid="purchase-cancel" @click="cancelInvoice" :disabled="submitting" class="px-4 py-2 rounded-lg bg-red-50 text-red-700 font-semibold disabled:opacity-50">
          {{ __("Cancel Invoice") }}
        </button>
      </div>
    </div>

    <!-- Submit confirm overlay -->
    <div v-if="showConfirm" class="absolute inset-0 bg-black/40 z-50 flex items-center justify-center p-6">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <h3 class="text-base font-bold text-gray-900 mb-2">{{ __("تأكيد الاعتماد") }}</h3>
        <p class="text-sm text-gray-600 mb-4">
          {{ __("سيتم اعتماد فاتورة الشراء وتحديث المخزون والحسابات. لا يمكن التراجع عن هذه العملية.") }}
        </p>
        <div class="bg-gray-50 rounded-xl p-3 mb-4 text-xs space-y-1">
          <div class="flex justify-between"><span class="text-gray-500">{{ __("المورد") }}</span><span class="font-semibold">{{ form.supplier_name || form.supplier }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">{{ __("الإجمالي") }}</span><span class="font-bold text-blue-700">{{ formatAmt(totals.grand) }}</span></div>
        </div>
        <div class="flex gap-3">
          <button @click="showConfirm = false" class="flex-1 py-2.5 text-sm font-semibold text-gray-600 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors">{{ __("إلغاء") }}</button>
          <button data-testid="purchase-confirm-submit" @click="doSubmit" :disabled="submitting" class="flex-1 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {{ submitting ? __("جاري الاعتماد...") : __("تأكيد الاعتماد") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { managerTranslate as __ } from "@/utils/managementI18n"

const { showSuccess } = useToast()

const props = defineProps({
	invoiceName: { type: String, default: null },
	defaults: { type: Object, default: () => ({}) },
	posProfile: { type: String, required: true },
	canCreate: { type: Boolean, default: false },
	canWrite: { type: Boolean, default: false },
	canSubmit: { type: Boolean, default: false },
	canCancel: { type: Boolean, default: false },
})
const emit = defineEmits(["back", "close", "saved", "submitted"])

const isNew = computed(() => !form.name)
const isSubmitted = computed(() => form.docstatus === 1 || form.docstatus === 2)

const form = reactive({
	name: null,
	docstatus: 0,
	supplier: "",
	supplier_name: "",
	posting_date: "",
	due_date: "",
	bill_no: "",
	bill_date: "",
	remarks: "",
	company: "",
	currency: "",
	company_currency: "",
	conversion_rate: 1,
	buying_price_list: "",
	price_list_currency: "",
	plc_conversion_rate: 1,
	// A POS purchase is a stock receipt by default.  Starting this as `false`
	// made it far too easy to submit a supplier invoice without receiving its
	// items, which looked like a sale/expense transaction to the operator and
	// left the inventory unchanged.
	update_stock: true,
	set_warehouse: "",
	items: [],
	taxes_and_charges: null,
	total_taxes_and_charges: 0,
})

const saving = ref(false)
const submitting = ref(false)
const showConfirm = ref(false)
const errorMsg = ref("")
const staleDraft = ref(false)

// Supplier autocomplete
const supplierSearch = ref("")
const supplierOptions = ref([])
const showSupplierDropdown = ref(false)
const showCreateSupplier = ref(false)
const newSupplierName = ref("")
const newSupplierMobileNo = ref("")
const newSupplierGroup = ref("")
const supplierGroups = ref([])
const warehouses = ref([])
const currencies = ref([])
const expenseAccounts = ref([])
const taxTemplates = ref([])
const creatingSupplier = ref(false)
const invoiceIdempotencyKey =
	globalThis.crypto?.randomUUID?.() ||
	`purchase-${Date.now()}-${Math.random().toString(16).slice(2)}`

let supplierTimer = null
function searchSuppliers() {
	clearTimeout(supplierTimer)
	supplierTimer = setTimeout(async () => {
		if (!supplierSearch.value) {
			supplierOptions.value = []
			return
		}
		try {
			supplierOptions.value = await call("pos_next.api.purchases.get_suppliers", {
				search: supplierSearch.value,
				limit: 10,
				pos_profile: props.posProfile,
			}) || []
			showSupplierDropdown.value = true
		} catch (error) {
			errorMsg.value = error?.message || __("فشل البحث عن الموردين")
		}
	}, 300)
}

function selectSupplier(s) {
	form.supplier = s.name
	form.supplier_name = s.supplier_name
	supplierSearch.value = s.supplier_name
	showSupplierDropdown.value = false
	supplierOptions.value = []
}

async function createSupplier() {
	if (!newSupplierName.value || !newSupplierMobileNo.value) return
	creatingSupplier.value = true
	try {
		const result = await call("pos_next.api.purchases.create_supplier", {
			supplier_name: newSupplierName.value,
			mobile_no: newSupplierMobileNo.value,
			supplier_group: newSupplierGroup.value,
			supplier_type: "Company",
			pos_profile: props.posProfile,
		})
		if (result) {
			selectSupplier(result)
			showCreateSupplier.value = false
			newSupplierName.value = ""
			newSupplierMobileNo.value = ""
		}
	} catch (error) {
		errorMsg.value = error?.message || __("فشل إنشاء المورد")
	} finally {
		creatingSupplier.value = false
	}
}

// Item lines
function addLine() {
	form.items.push({
		item_code: "",
		item_name: "",
		qty: 1,
		uom: "Nos",
		rate: 0,
		amount: 0,
		expense_account: "",
		_itemSearch: "",
		_options: [],
		_showDrop: false,
	})
}

function removeLine(idx) {
	form.items.splice(idx, 1)
}

function calcLine(idx) {
	const line = form.items[idx]
	line.amount = Number.parseFloat(
		((line.qty || 0) * (line.rate || 0)).toFixed(2),
	)
}

const itemTimers = {}
function searchItems(idx) {
	clearTimeout(itemTimers[idx])
	itemTimers[idx] = setTimeout(async () => {
		const q = form.items[idx]._itemSearch
		if (!q) {
			form.items[idx]._options = []
			return
		}
		try {
			form.items[idx]._options = await call("pos_next.api.purchases.get_purchase_items", {
				search: q,
				limit: 10,
				pos_profile: props.posProfile,
			}) || []
			form.items[idx]._showDrop = true
		} catch (error) {
			errorMsg.value = error?.message || __("فشل البحث عن الأصناف")
		}
	}, 300)
}

async function selectItem(idx, it) {
	const line = form.items[idx]
	line.item_code = it.item_code
	line.item_name = it.item_name
	line.uom = it.stock_uom || "Nos"
	line._itemSearch = it.item_name
	line._showDrop = false
	line._options = []
	// Fetch buying price (best-effort; the cashier can still type the rate).
	try {
		const priceInfo = await call("pos_next.api.purchases.get_item_buying_price", {
			item_code: it.item_code,
			buying_price_list: form.buying_price_list,
			pos_profile: props.posProfile,
		})
		if (priceInfo?.buying_price) {
			line.rate = priceInfo.buying_price
		}
	} catch (error) {
		console.error("Error loading item buying price", error)
	}
	calcLine(idx)
}

// Totals
const totals = computed(() => {
	const net = form.items.reduce((s, l) => s + (l.amount || 0), 0)
	const tax = Number.parseFloat(form.total_taxes_and_charges || 0)
	return { net, tax, grand: net + tax }
})

const formCanSubmit = computed(
	() =>
		!!form.supplier &&
		form.items.length > 0 &&
		form.items.every((l) => l.item_code && l.qty > 0) &&
		// Stock receipts need both a destination and a real cost.  ERPNext uses
		// that cost for inventory valuation and COGS, so do not defer this error
		// until after the user presses Submit.
		(!form.update_stock ||
			(!!form.set_warehouse && form.items.every((l) => Number(l.rate || 0) > 0))),
)

const docstatusLabel = computed(() => {
	const m = { 0: __("مسودة"), 1: __("معتمدة"), 2: __("ملغاة") }
	return m[form.docstatus] || ""
})
const docstatusClass = computed(() => {
	const m = {
		0: "bg-gray-100 text-gray-600",
		1: "bg-green-100 text-green-700",
		2: "bg-red-100 text-red-600",
	}
	return m[form.docstatus] || ""
})

async function saveDraft() {
	if (saving.value || submitting.value) return
	if (!form.supplier) {
		errorMsg.value = __("يرجى اختيار المورد أولاً")
		return
	}
	if (!form.items.length) {
		errorMsg.value = __("يرجى إضافة صنف واحد على الأقل")
		return
	}
	saving.value = true
	errorMsg.value = ""
	staleDraft.value = false
	try {
		const payload = buildPayload()
		const result = await call("pos_next.api.purchases.save_purchase_invoice", {
			data: payload,
			idempotency_key: invoiceIdempotencyKey,
			expected_modified: form.modified || null,
			pos_profile: props.posProfile,
		})
		if (result?.name) {
			form.name = result.name
			form.modified = result.modified
			emit("saved", result.name)
			showSuccess(__("تم الحفظ بنجاح"))
		}
	} catch (e) {
		errorMsg.value = e?.message || __("حدث خطأ أثناء الحفظ")
		staleDraft.value =
			e?.exc_type === "TimestampMismatchError" ||
			e?.name === "TimestampMismatchError"
	} finally {
		saving.value = false
	}
}

function confirmSubmit() {
	if (!formCanSubmit.value || !props.canSubmit) return
	showConfirm.value = true
}

async function doSubmit() {
	if (submitting.value || saving.value) return
	submitting.value = true
	errorMsg.value = ""
	staleDraft.value = false
	try {
		const payload = buildPayload()
		const saveResult = await call("pos_next.api.purchases.save_purchase_invoice", {
			data: payload,
			idempotency_key: invoiceIdempotencyKey,
			expected_modified: form.modified || null,
			pos_profile: props.posProfile,
		})
		if (!saveResult?.name) {
			submitting.value = false
			showConfirm.value = false
			return
		}
		form.name = saveResult.name
		form.modified = saveResult.modified
		const result = await call("pos_next.api.purchases.submit_purchase_invoice", {
			name: form.name,
			expected_modified: form.modified,
			pos_profile: props.posProfile,
		})
		if (result) {
			form.docstatus = 1
			showConfirm.value = false
			showSuccess(__("تم اعتماد الفاتورة بنجاح"))
			emit("submitted", form.name)
		}
	} catch (e) {
		errorMsg.value = e?.message || __("حدث خطأ أثناء الاعتماد")
		staleDraft.value =
			e?.exc_type === "TimestampMismatchError" ||
			e?.name === "TimestampMismatchError"
		showConfirm.value = false
	} finally {
		submitting.value = false
	}
}

async function cancelInvoice() {
	if (submitting.value) return
	if (
		!window.confirm(
			__("Cancel this Purchase Invoice using the standard reversal workflow?"),
		)
	)
		return
	submitting.value = true
	errorMsg.value = ""
	try {
		const result = await call("pos_next.api.purchases.cancel_purchase_invoice", {
			name: form.name,
			pos_profile: props.posProfile,
		})
		form.docstatus = result?.docstatus ?? 2
		emit("saved", form.name)
	} catch (error) {
		errorMsg.value =
			error?.message || __("Could not cancel the Purchase Invoice")
	} finally {
		submitting.value = false
	}
}

function buildPayload() {
	const cleanItems = form.items
		.filter((l) => l.item_code)
		.map((l) => ({
			item_code: l.item_code,
			qty: Number.parseFloat(l.qty) || 1,
			uom: l.uom || "Nos",
			rate: Number.parseFloat(l.rate) || 0,
			...(form.update_stock ? { warehouse: form.set_warehouse } : {}),
			...(l.expense_account ? { expense_account: l.expense_account } : {}),
		}))
	return {
		...(form.name ? { name: form.name } : {}),
		supplier: form.supplier,
		posting_date: form.posting_date,
		due_date: form.due_date || null,
		bill_no: form.bill_no || null,
		bill_date: form.bill_date || null,
		remarks: form.remarks || null,
		company: form.company,
		currency: form.currency,
		conversion_rate: Number(form.conversion_rate || 1),
		buying_price_list: form.buying_price_list,
		plc_conversion_rate: Number(form.plc_conversion_rate || 1),
		items: cleanItems,
		taxes_and_charges: form.taxes_and_charges || null,
		update_stock: form.update_stock ? 1 : 0,
		set_warehouse: form.update_stock ? form.set_warehouse : null,
	}
}

function formatAmt(v) {
	if (v === null || v === undefined) return "0.00"
	return Number.parseFloat(v).toLocaleString(frappe.boot?.lang || undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	})
}

async function loadInvoice(name) {
	staleDraft.value = false
	errorMsg.value = ""
	let d
	try {
		d = await call("pos_next.api.purchases.get_purchase_invoice", {
			name,
			pos_profile: props.posProfile,
		})
	} catch (error) {
		errorMsg.value = error?.message || __("فشل تحميل الفاتورة")
		return
	}
	if (!d) return
	Object.assign(form, {
		name: d.name,
		docstatus: d.docstatus,
		supplier: d.supplier,
		supplier_name: d.supplier_name,
		posting_date: d.posting_date,
		due_date: d.due_date,
		bill_no: d.bill_no,
		bill_date: d.bill_date,
		remarks: d.remarks,
		company: d.company,
		currency: d.currency,
		company_currency: d.company_currency || form.company_currency,
		conversion_rate: d.conversion_rate || 1,
		buying_price_list: d.buying_price_list,
		price_list_currency: d.price_list_currency || form.price_list_currency,
		plc_conversion_rate: d.plc_conversion_rate || 1,
		update_stock: Boolean(d.update_stock),
		set_warehouse: d.set_warehouse || "",
		modified: d.modified,
		taxes_and_charges: d.taxes_and_charges,
		total_taxes_and_charges: d.total_taxes_and_charges || 0,
		items: (d.items || []).map((l) => ({
			...l,
			_itemSearch: l.item_name || l.item_code,
			_options: [],
			_showDrop: false,
		})),
	})
	supplierSearch.value = d.supplier_name || d.supplier
}

onMounted(async () => {
	try {
		const def = (await call("pos_next.api.purchases.get_new_purchase_invoice_defaults", {
			pos_profile: props.posProfile,
		})) || {}
		form.posting_date = def.posting_date || new Date().toISOString().slice(0, 10)
		form.due_date = def.due_date || ""
		form.company = def.company || props.defaults?.company || ""
		form.currency = def.currency || ""
		form.company_currency = def.company_currency || def.currency || ""
		form.buying_price_list = def.buying_price_list || ""
		form.price_list_currency = def.price_list_currency || def.currency || ""
		form.bill_date = def.posting_date || ""
		form.taxes_and_charges = props.defaults?.taxes_and_charges || null
		// Keep the full purchase form aligned with the quick purchase flow: the
		// configured receiving warehouse is preselected when opening a new invoice.
		form.set_warehouse = def.default_warehouse || ""

		const [groups, whs, curr, expenses, taxes] = await Promise.all([
			call("pos_next.api.purchases.get_supplier_groups", { pos_profile: props.posProfile }),
			call("pos_next.api.purchases.get_warehouses", { pos_profile: props.posProfile }),
			call("pos_next.api.purchases.get_purchase_currencies", { pos_profile: props.posProfile }),
			call("pos_next.api.purchases.get_expense_accounts", { pos_profile: props.posProfile }),
			call("pos_next.api.purchases.get_purchase_tax_templates", { pos_profile: props.posProfile }),
		])
		supplierGroups.value = groups || []
		newSupplierGroup.value = supplierGroups.value[0]?.name || ""
		warehouses.value = whs || []
		currencies.value = curr || []
		expenseAccounts.value = expenses || []
		taxTemplates.value = taxes || []
	} catch (error) {
		errorMsg.value = error?.message || __("فشل تحميل بيانات الفاتورة")
	}

	if (props.invoiceName) {
		await loadInvoice(props.invoiceName)
	}
})
</script>
