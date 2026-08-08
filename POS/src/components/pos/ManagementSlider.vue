<template>
	<!-- Icon-Only Sidebar - Hidden on Mobile, Visible on Desktop -->
	<div
		class="hidden lg:flex w-16 flex-shrink-0 bg-white border-e border-gray-200 flex-col items-center py-4 flex flex-col gap-2"
	>
		<!-- Promotions -->
		<button
			@click="handleMenuClick('promotions')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'promotions'
					? 'bg-green-100 text-green-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('Promotions')"
		>
			<FeatherIcon name="tag" class="w-5 h-5" />
			<div
				class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
			>
				{{ __("Promotions") }}
			</div>
		</button>

		<!-- Products -->
		<button
			@click="handleMenuClick('products')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'products'
					? 'bg-emerald-100 text-emerald-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('Products')"
		>
			<FeatherIcon name="package" class="w-5 h-5" />
			<div
				class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
			>
				{{ __("Products") }}
			</div>
		</button>

		<!-- Invoices -->
		<button
			@click="handleMenuClick('invoices')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'invoices'
					? 'bg-indigo-100 text-indigo-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('Invoice Management')"
		>
			<FeatherIcon name="file-text" class="w-5 h-5" />
			<div
				class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
			>
				{{ __("Invoice Management") }}
			</div>
		</button>

		<!-- Purchase mode toggle: activates/deactivates purchase mode on the main screen -->
		<button
			v-if="canManagePurchases"
			data-testid="rail-purchase-mode-toggle"
			@click="handleMenuClick('purchases')"
			:aria-pressed="purchaseModeActive"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				purchaseModeActive
					? 'bg-orange-600 text-white shadow-sm ring-2 ring-orange-300'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="purchaseModeActive ? __('Exit purchase mode') : __('Activate purchase mode')"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
			</svg>
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ purchaseModeActive ? __("Exit purchase mode") : __("Activate purchase mode") }}
			</div>
		</button>

		<!-- Reports -->
		<button
			v-if="canViewReports"
			@click="handleMenuClick('reports')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'reports'
					? 'bg-emerald-100 text-emerald-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('التقارير')"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
			</svg>
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __("التقارير") }}
			</div>
		</button>

		<!-- Cash Management — cashier drawer movements (gated by feature flag) -->
		<button
			v-if="canManageCash"
			data-testid="rail-cash-button"
			@click="handleMenuClick('cash')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'cash'
					? 'bg-teal-100 text-teal-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('إدارة الصندوق')"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
			</svg>
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __("إدارة الصندوق") }}
			</div>
		</button>

		<!-- Expense Types — manager-only screen (gated by the enable_expense_types flag) -->
		<button
			v-if="canManageExpenseTypes"
			data-testid="rail-expense-types-button"
			@click="handleMenuClick('expense_types')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'expense_types'
					? 'bg-purple-100 text-purple-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('أنواع المصاريف')"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-5 5a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 8V3a2 2 0 012-2z" />
			</svg>
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __("أنواع المصاريف") }}
			</div>
		</button>

		<!-- Catalog Management — only shown to authorized users -->
		<button
			v-if="canManageCatalog"
			@click="handleMenuClick('catalog')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'catalog'
					? 'bg-blue-100 text-blue-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('Catalog Management')"
		>
			<!-- plus icon -->
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 4v16m8-8H4"
				/>
			</svg>
			<div
				class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
			>
				{{ __("Catalog Management") }}
			</div>
		</button>

		<!-- Spacer to push settings to bottom -->
		<div class="flex-1"></div>

		<!-- Divider -->
		<div class="w-8 border-t border-gray-200 my-2"></div>

		<!-- Settings -->
		<button
			v-if="canManageSettings"
			@click="handleMenuClick('settings')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'settings'
					? 'bg-gray-100 text-gray-900'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
			]"
			:title="__('Settings')"
		>
			<FeatherIcon name="settings" class="w-5 h-5" />
			<div
				class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
			>
				{{ __("Settings") }}
			</div>
		</button>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";
import { ref } from "vue";

const props = defineProps({
	canManageCatalog: { type: Boolean, default: false },
	canManagePurchases: { type: Boolean, default: false },
	canViewReports: { type: Boolean, default: false },
	canManageSettings: { type: Boolean, default: false },
	// Cashier cash-drawer management (gated by the enable_cash_management flag).
	canManageCash: { type: Boolean, default: false },
	// Expense-type management screen (gated by the enable_expense_types flag + manager).
	canManageExpenseTypes: { type: Boolean, default: false },
	// True while the cart is in purchase mode — highlights the purchase toggle.
	purchaseModeActive: { type: Boolean, default: false },
});

const emit = defineEmits(["menu-clicked"]);

const activeMenu = ref("");

function handleMenuClick(menuItem) {
	// "purchases" is a mode toggle, not a panel — its highlight is driven by the
	// purchaseModeActive prop, so it must not claim the transient activeMenu state.
	if (menuItem !== "purchases") {
		activeMenu.value = menuItem;
	}
	emit("menu-clicked", menuItem);
}

defineExpose({ resetActiveMenu: () => { activeMenu.value = ""; } });
</script>
