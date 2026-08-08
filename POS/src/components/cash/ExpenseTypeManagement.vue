<!--
  ExpenseTypeManagement — manager-only CRUD for POS Expense Types (Cash Management v2, Screen 2).
  Lets a manager define expense types (and the account each posts to) from the POS so cashiers can
  record expenses without touching Desk or the full chart of accounts. Nested overlay opened from
  CashManagement (the header link + the Expense empty-state). Same design language (teal, rounded-xl).
-->
<template>
  <div class="absolute inset-0 z-[310] bg-white flex flex-col">
    <!-- Header -->
    <div class="border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-gray-900">{{ __("إدارة أنواع المصاريف") }}</h2>
          <p class="text-xs text-gray-500">{{ __("تعريف أنواع المصاريف والحساب المرتبط بكل نوع") }}</p>
        </div>
      </div>
      <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 max-w-5xl mx-auto">

        <!-- LEFT: add / edit form -->
        <div class="flex flex-col gap-3">
          <div v-if="errorMsg" class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
            {{ errorMsg }}
          </div>

          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">
            {{ editing ? __("تعديل نوع المصروف") : __("إضافة نوع مصروف") }}
          </h3>

          <div>
            <label class="label">{{ __("نوع المصروف") }} <span class="text-red-500">*</span></label>
            <input
              v-model="form.expense_type_name"
              data-testid="expense-type-name"
              type="text"
              :placeholder="__('مثال: كهرباء، ماء، صيانة')"
              class="field"
            />
          </div>

          <div>
            <label class="label">{{ __("حساب المصروف") }} <span class="text-red-500">*</span></label>
            <select v-model="form.expense_account" data-testid="expense-account-select" :disabled="accountsLoading" class="field bg-white">
              <option value="">{{ accountsLoading ? __("جاري التحميل...") : __("اختر الحساب...") }}</option>
              <option v-for="a in accounts" :key="a.name" :value="a.name">
                {{ a.account_name || a.name }}
              </option>
            </select>
          </div>

          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.enabled" data-testid="enabled-checkbox" type="checkbox" class="h-5 w-5 rounded border-gray-300 text-teal-600" />
            <span class="text-sm text-gray-700">{{ __("مُفعّل") }}</span>
          </label>

          <div class="flex gap-2">
            <button
              type="button"
              data-testid="save-expense-type"
              @click="save"
              :disabled="!canSave || saving"
              class="flex-1 py-3 rounded-xl bg-teal-600 text-white text-sm font-bold hover:bg-teal-700 disabled:opacity-50"
            >
              {{ saving ? __("جاري الحفظ...") : editing ? __("حفظ التعديل") : __("إضافة") }}
            </button>
            <button
              v-if="editing"
              type="button"
              data-testid="cancel-edit"
              @click="resetForm"
              class="py-3 px-4 rounded-xl bg-gray-100 text-gray-700 text-sm font-bold hover:bg-gray-200"
            >
              {{ __("إلغاء") }}
            </button>
          </div>
        </div>

        <!-- RIGHT: existing types -->
        <div class="flex flex-col gap-3">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("أنواع المصاريف") }}</h3>

          <div v-if="listLoading" class="flex flex-col gap-2">
            <div v-for="i in 3" :key="i" class="h-16 bg-gray-50 rounded-xl animate-pulse" />
          </div>
          <div v-else-if="!expenseTypes.length" class="text-center py-10 text-xs text-gray-400">
            {{ __("لا توجد أنواع مصاريف") }}
          </div>
          <div v-else class="flex flex-col gap-2">
            <div
              v-for="t in expenseTypes"
              :key="t.name"
              :data-testid="`type-row-${t.name}`"
              class="flex items-center gap-3 p-3 rounded-xl border border-gray-100"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-gray-900 truncate">{{ t.expense_type_name }}</p>
                <p class="text-[11px] text-gray-500 truncate">{{ t.account_name || t.expense_account }}</p>
              </div>
              <span
                :class="['text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0', t.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500']"
              >
                {{ t.enabled ? __("مُفعّل") : __("مُعطّل") }}
              </span>
              <button
                type="button"
                :data-testid="`edit-${t.name}`"
                @click="startEdit(t)"
                class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                type="button"
                :data-testid="`delete-${t.name}`"
                @click="remove(t)"
                :disabled="deletingName === t.name"
                class="w-8 h-8 rounded-lg flex items-center justify-center text-red-400 hover:bg-red-50 disabled:opacity-50"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { parseError } from "@/utils/errorHandler"
import { useToast } from "@/composables/useToast"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	posProfile: { type: String, required: true },
})
defineEmits(["close"])

const { showSuccess, showError } = useToast()

const expenseTypes = ref([])
const accounts = ref([])
const listLoading = ref(false)
const accountsLoading = ref(false)
const saving = ref(false)
const deletingName = ref("")
const errorMsg = ref("")

const form = reactive({
	name: "",
	expense_type_name: "",
	expense_account: "",
	enabled: true,
})

const editing = computed(() => !!form.name)
const canSave = computed(
	() => form.expense_type_name.trim().length > 0 && !!form.expense_account,
)

async function loadTypes() {
	listLoading.value = true
	try {
		const res = await call("pos_next.api.cash_management.get_expense_types", {
			pos_profile: props.posProfile,
		})
		expenseTypes.value = res?.expense_types || []
	} catch (error) {
		errorMsg.value = parseError(error).message
		showError(errorMsg.value)
	} finally {
		listLoading.value = false
	}
}

async function loadAccounts() {
	accountsLoading.value = true
	try {
		const res = await call(
			"pos_next.api.cash_management.get_expense_accounts",
			{
				pos_profile: props.posProfile,
			},
		)
		accounts.value = res?.accounts || []
	} catch (error) {
		errorMsg.value = parseError(error).message
	} finally {
		accountsLoading.value = false
	}
}

function resetForm() {
	form.name = ""
	form.expense_type_name = ""
	form.expense_account = ""
	form.enabled = true
}

function startEdit(t) {
	form.name = t.name
	form.expense_type_name = t.expense_type_name || ""
	form.expense_account = t.expense_account || ""
	form.enabled = !!t.enabled
}

async function save() {
	if (!canSave.value || saving.value) return
	errorMsg.value = ""
	saving.value = true
	try {
		await call("pos_next.api.cash_management.save_expense_type", {
			name: form.name || null,
			expense_type_name: form.expense_type_name.trim(),
			expense_account: form.expense_account,
			enabled: form.enabled ? 1 : 0,
			pos_profile: props.posProfile,
		})
		showSuccess(__("تم الحفظ بنجاح"))
		resetForm()
		await loadTypes()
	} catch (error) {
		errorMsg.value = parseError(error).message
		showError(errorMsg.value)
	} finally {
		saving.value = false
	}
}

async function remove(t) {
	if (deletingName.value) return
	if (!globalThis.confirm(__("حذف نوع المصروف؟"))) return
	deletingName.value = t.name
	try {
		await call("pos_next.api.cash_management.delete_expense_type", {
			name: t.name,
			pos_profile: props.posProfile,
		})
		showSuccess(__("تم الحذف"))
		if (form.name === t.name) resetForm()
		await loadTypes()
	} catch (error) {
		showError(parseError(error).message)
	} finally {
		deletingName.value = ""
	}
}

onMounted(async () => {
	await Promise.all([loadTypes(), loadAccounts()])
})
</script>

<style scoped>
.label {
  @apply block text-xs font-semibold text-gray-700 mb-1;
}
.field {
  @apply w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400;
}
</style>
