<template>
	<!-- Full Page Overlay -->
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<!-- Main Container -->
			<div class="fixed inset-0 flex items-center justify-center p-4 md:p-6">
				<div
					class="w-full max-w-5xl max-h-[90vh] bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col"
				>
					<!-- Header -->
					<div
						class="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-white"
					>
						<div class="flex items-center gap-3">
							<div class="p-2 bg-emerald-50 rounded-lg">
								<svg
									class="w-6 h-6 text-emerald-600"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
									/>
								</svg>
							</div>
							<div>
								<h2 class="text-xl font-bold text-gray-900">
									{{ __("POS Settings") }}
								</h2>
								<p class="text-sm text-gray-600 flex items-center mt-0.5">
									<svg
										class="w-4 h-4 me-1.5"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
										/>
									</svg>
									{{ settings.pos_profile || posProfile }}
								</p>
							</div>
						</div>
						<div class="flex items-center gap-2">
							<Button
								@click="loadSettings"
								:loading="loading"
								variant="ghost"
								size="sm"
							>
								<template #prefix>
									<svg
										class="w-4 h-4"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
										/>
									</svg>
								</template>
								{{ __("Refresh") }}
							</Button>
							<Button
								@click="saveSettings"
								:loading="saving"
								variant="solid"
								theme="blue"
							>
								<template #prefix>
									<svg
										class="w-4 h-4"
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
								</template>
								{{ __("Save Changes") }}
							</Button>
							<button
								@click="handleClose"
								class="p-2 hover:bg-white/50 rounded-lg transition-colors"
							>
								<svg
									class="w-5 h-5 text-gray-600"
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
					</div>

					<!-- Main Content -->
					<div class="flex-1 overflow-y-auto bg-gray-50">
						<!-- Loading State -->
						<div
							v-if="loading"
							class="flex flex-col items-center justify-center py-16"
						>
							<div
								class="animate-spin rounded-full h-12 w-12 border-b-3 border-blue-500 mb-4"
							></div>
							<p class="text-sm font-medium text-gray-600">
								{{ __("Loading settings...") }}
							</p>
						</div>

						<!-- Settings Form -->
						<div
							v-else-if="settings.pos_profile || posProfile"
							class="p-6 flex flex-col gap-6"
						>
							<!-- Tabs Navigation -->
							<div class="flex p-1 bg-gray-200 rounded-lg self-start">
								<button
									@click="activeTab = 'stock'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'stock'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Stock Management") }}
								</button>
								<button
									@click="activeTab = 'sales'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'sales'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Sales Management") }}
								</button>
								<button
									@click="activeTab = 'customers'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'customers'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Customers") }}
								</button>
								<button
									@click="activeTab = 'display'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'display'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Display & Print") }}
								</button>
								<button
									@click="activeTab = 'branding'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'branding'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Identity") }}
								</button>
								<button
									v-if="canManageFeatureFlags"
									@click="activeTab = 'features'"
									:class="[
										'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
										activeTab === 'features'
											? 'bg-white text-gray-900 shadow-sm'
											: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
									]"
								>
									{{ __("Feature Flags") }}
								</button>
							</div>

							<!-- Brand Identity Section -->
							<BrandingSettings v-if="activeTab === 'branding'" />

							<div
								v-if="activeTab === 'features' && canManageFeatureFlags"
								class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
							>
								<div class="px-5 py-4 bg-amber-50 border-b border-amber-100">
									<h3 class="font-bold text-gray-900">{{ __("Management Feature Flags") }}</h3>
									<p class="mt-1 text-sm text-gray-700">
										{{ __("Disabled by default. Enable only after acceptance testing; every change is audited.") }}
									</p>
								</div>
								<div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-5">
									<label
										v-for="flag in featureFlagDefinitions"
										:key="flag.fieldname"
										class="min-h-32 rounded-xl border border-gray-200 p-4 flex items-start gap-3 cursor-pointer hover:border-blue-300"
										:class="{ 'opacity-60 cursor-not-allowed': flag.requires && !settings[flag.requires] }"
									>
										<input
											type="checkbox"
											class="mt-1 h-5 w-5 rounded border-gray-300 text-blue-600"
											v-model="settings[flag.fieldname]"
											:disabled="flag.requires && !settings[flag.requires]"
										/>
										<span>
											<span class="block font-semibold text-gray-900">{{ flag.label }}</span>
											<span class="block text-sm text-gray-600 mt-2">{{ flag.description }}</span>
										</span>
									</label>
								</div>
									<!-- Purchase Defaults — pre-fill purchase mode (mirrors sales default customer) -->
									<div v-if="settings.enable_purchases" class="border-t border-gray-100 p-5">
										<div class="flex items-center gap-2 mb-1">
											<svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
											</svg>
											<h3 class="font-bold text-gray-900">{{ __("Purchase Defaults") }}</h3>
										</div>
										<p class="text-sm text-gray-600 mb-4">
											{{ __("Pre-fill these when purchase mode is opened. The cashier can still change any of them.") }}
										</p>

										<div v-if="purchaseDefaultsLoading" class="text-sm text-gray-500 py-2">
											{{ __("Loading purchase options...") }}
										</div>
										<div
											v-else-if="purchaseDefaultsError"
											class="text-sm text-amber-800 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2"
										>
											{{ __("Enable Purchases and save settings first, then reopen to pick purchase defaults.") }}
										</div>
										<div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2">
											<SelectField
												v-model="settings.posa_default_supplier"
												:label="__('Default Supplier')"
												:options="supplierOptions"
												:description="__('Pre-selected supplier for new purchases.')"
											/>
											<SelectField
												v-model="settings.posa_default_purchase_warehouse"
												:label="__('Default Warehouse')"
												:options="purchaseWarehouseOptions"
												:description="__('Receiving warehouse for purchased stock.')"
											/>
											<SelectField
												v-model="settings.posa_default_purchase_tax_template"
												:label="__('Default Purchase Tax Template')"
												:options="purchaseTaxTemplateOptions"
												:description="__('Purchase taxes and charges template.')"
											/>
											<SelectField
												v-model="settings.posa_default_expense_account"
												:label="__('Default Expense Account')"
												:options="expenseAccountOptions"
												:description="__('Expense account for purchased expense items.')"
											/>
											<SelectField
												v-model="settings.posa_purchase_price_source"
												:label="__('Purchase Price Source')"
												:options="purchasePriceSourceOptions"
												:description="__('The source the buying price is fetched from in purchase mode (falls back to the other sources when unavailable).')"
											/>
										</div>
									</div>
							</div>

							<!-- Stock Settings Section - Prominent -->
							<div
								v-if="activeTab === 'stock'"
								class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
							>
								<div :class="stockSectionClasses.header">
									<div class="flex items-center justify-between">
										<div class="flex items-center gap-3">
											<div :class="stockSectionClasses.iconContainer">
												<svg
													:class="stockSectionClasses.icon"
													fill="none"
													stroke="currentColor"
													viewBox="0 0 24 24"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														:d="icons.warehouse"
													/>
												</svg>
											</div>
											<div>
												<h3 class="text-lg font-bold text-gray-900">
													{{ __("Stock Management") }}
												</h3>
												<p class="text-xs text-gray-600 mt-0.5">
													{{
														__(
															"Configure warehouse and inventory settings"
														)
													}}
												</p>
											</div>
										</div>
										<div :class="stockSectionClasses.badge">
											<svg
												:class="stockSectionClasses.badgeIcon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.checkCircle"
												/>
											</svg>
											<span :class="stockSectionClasses.badgeText">{{
												__("Stock Controls")
											}}</span>
										</div>
									</div>
								</div>
								<div class="p-6 flex flex-col gap-6">
									<!-- Warehouse Selection -->
									<div :class="warehouseSubsectionClasses.container">
										<div class="flex items-center gap-2 mb-4">
											<svg
												:class="warehouseSubsectionClasses.icon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.location"
												/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">
												{{ __("Warehouse Selection") }}
											</h4>
										</div>
										<div
											v-if="warehouseOptions.length === 0"
											class="flex items-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
										>
											<svg
												class="w-5 h-5 text-yellow-600 me-3 flex-shrink-0"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.warning"
												/>
											</svg>
											<p class="text-sm text-yellow-800 font-medium">
												{{ __("Loading warehouses...") }}
											</p>
										</div>
										<SelectField
											v-else
											v-model="selectedWarehouse"
											:label="__('Active Warehouse')"
											:options="warehouseOptions"
											:description="
												__(
													'All stock operations will use this warehouse. Stock quantities will refresh after saving.'
												)
											"
										/>
									</div>

									<!-- Stock Policy Settings -->
									<div :class="stockPolicySubsectionClasses.container">
										<div class="flex items-center gap-2 mb-4">
											<svg
												:class="stockPolicySubsectionClasses.icon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.clipboard"
												/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">
												{{ __("Stock Validation Policy") }}
											</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.allow_negative_stock"
												:label="__('Allow Negative Stock')"
												:description="
													__(
														'Enable selling items even when stock reaches zero or below. Integrates with Back Office stock settings.'
													)
												"
											/>
											<div class="mt-3 p-3 bg-blue-100 rounded-md">
												<div class="flex items-start gap-2">
													<svg
														class="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															:d="icons.info"
														/>
													</svg>
													<TranslatedHTML
														:tag="'p'"
														class="text-xs text-blue-800 leading-relaxed"
														:inner="
															__(
																'&lt;strong&gt;Note:&lt;strong&gt; When enabled, the system will allow sales even when stock quantity is zero or negative. This is useful for handling stock sync delays or backorders. All transactions are tracked in the stock ledger.'
															)
														"
													/>
												</div>
											</div>
										</div>
									</div>

									<!-- Background Stock Sync Settings -->
									<div :class="stockSyncSubsectionClasses.container">
										<div class="flex items-center gap-2 mb-4">
											<svg
												:class="stockSyncSubsectionClasses.icon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
												/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">
												{{ __("Background Stock Sync") }}
											</h4>
											<div
												v-if="stockSyncStatus.enabled"
												class="ms-auto flex items-center px-2.5 py-1 bg-green-100 border border-green-300 rounded-full"
											>
												<div
													class="w-2 h-2 bg-green-500 rounded-full animate-pulse me-2"
												></div>
												<span class="text-xs font-medium text-green-800">{{
													__("Active")
												}}</span>
											</div>
											<div
												v-else
												class="ms-auto flex items-center px-2.5 py-1 bg-gray-100 border border-gray-300 rounded-full"
											>
												<div
													class="w-2 h-2 bg-gray-400 rounded-full me-2"
												></div>
												<span class="text-xs font-medium text-gray-600">{{
													__("Inactive")
												}}</span>
											</div>
										</div>

										<div class="flex flex-col gap-4">
											<!-- Enable Sync Toggle -->
											<CheckboxField
												v-model="stockSyncEnabled"
												:label="__('Enable Automatic Stock Sync')"
												:description="
													__(
														'Periodically sync stock quantities from server in the background (runs in Web Worker)'
													)
												"
											/>

											<!-- Sync Interval -->
											<div
												v-if="stockSyncEnabled"
												class="ps-6 flex flex-col gap-3 border-s-2 border-blue-200"
											>
												<NumberField
													v-model="stockSyncIntervalSeconds"
													:label="__('Sync Interval (seconds)')"
													:description="
														__(
															'How often to check server for stock updates (minimum 10 seconds)'
														)
													"
													:min="10"
													:max="300"
													:step="10"
												/>

												<!-- Sync Status Info -->
												<div
													class="p-3 bg-blue-50 border border-blue-200 rounded-lg"
												>
													<div class="flex items-start gap-2">
														<svg
															class="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0"
															fill="none"
															stroke="currentColor"
															viewBox="0 0 24 24"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																:d="icons.info"
															/>
														</svg>
														<div
															class="text-xs text-blue-800 flex flex-col gap-1"
														>
															<TranslatedHTML
																:tag="'p'"
																:inner="
																	stockSyncStatus.enabled
																		? __(
																				'&lt;strong&gt;Status:&lt;strong&gt; Running'
																		  )
																		: __(
																				'&lt;strong&gt;Status:&lt;strong&gt; Stopped'
																		  )
																"
															/>
															<TranslatedHTML
																:tag="'p'"
																:inner="
																	__(
																		'&lt;strong&gt;Items Tracked:&lt;strong&gt; {0}',
																		[
																			stockSyncStatus.itemCount ||
																				0,
																		]
																	)
																"
															/>
															<TranslatedHTML
																:tag="'p'"
																:inner="
																	stockSyncStatus.warehouse
																		? __(
																				'&lt;strong&gt;Warehouse:&lt;strong&gt; {0}',
																				[
																					stockSyncStatus.warehouse,
																				]
																		  )
																		: __('Warehouse not set')
																"
															/>
															<TranslatedHTML
																:tag="'p'"
																:inner="
																	stockSyncStatus.lastSync
																		? __(
																				'&lt;strong&gt;Last Sync:&lt;strong&gt; {0}',
																				[
																					formatSyncTime(
																						stockSyncStatus.lastSync
																					),
																				]
																		  )
																		: __(
																				'&lt;strong&gt;Last Sync:&lt;strong&gt; Never'
																		  )
																"
															/>
														</div>
													</div>
												</div>

												<!-- Network Usage Info -->
												<div
													class="p-3 bg-gray-50 border border-gray-200 rounded-lg"
												>
													<div class="flex items-start gap-2">
														<svg
															class="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0"
															fill="none"
															stroke="currentColor"
															viewBox="0 0 24 24"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M13 10V3L4 14h7v7l9-11h-7z"
															/>
														</svg>
														<div class="text-xs text-gray-700">
															<p class="font-medium mb-1">
																{{ __("Network Usage:") }}
															</p>
															<p>
																{{ __("~15 KB per sync cycle") }}
															</p>
															<p>
																{{
																	__("~{0} MB per hour", [
																		Math.round(
																			((3600 /
																				stockSyncIntervalSeconds) *
																				15) /
																				1024
																		),
																	])
																}}
															</p>
														</div>
													</div>
												</div>
											</div>
										</div>
									</div>
								</div>
							</div>

							<!-- Sales Management Section - Prominent -->
							<div
								v-if="activeTab === 'sales'"
								class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
							>
								<div :class="salesSectionClasses.header">
									<div class="flex items-center justify-between">
										<div class="flex items-center gap-3">
											<div :class="salesSectionClasses.iconContainer">
												<svg
													:class="salesSectionClasses.icon"
													fill="none"
													stroke="currentColor"
													viewBox="0 0 24 24"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														:d="icons.shoppingCart"
													/>
												</svg>
											</div>
											<div>
												<h3 class="text-lg font-bold text-gray-900">
													{{ __("Sales Management") }}
												</h3>
												<p class="text-xs text-gray-600 mt-0.5">
													{{
														__(
															"Configure pricing, discounts, and sales operations"
														)
													}}
												</p>
											</div>
										</div>
										<div :class="salesSectionClasses.badge">
											<svg
												:class="salesSectionClasses.badgeIcon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.currency"
												/>
											</svg>
											<span :class="salesSectionClasses.badgeText">{{
												__("Sales Controls")
											}}</span>
										</div>
									</div>
								</div>
								<div class="p-6 flex flex-col gap-6">
									<!-- Pricing & Discounts -->
									<div :class="pricingSubsectionClasses.container">
										<div class="flex items-center gap-2 mb-4">
											<svg
												:class="pricingSubsectionClasses.icon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.tag"
												/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">
												{{ __("Pricing & Discounts") }}
											</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.tax_inclusive"
												:label="__('Tax Inclusive')"
												:description="
													__(
														'When enabled, displayed prices include tax. When disabled, tax is calculated separately. Changes apply immediately to your cart when you save.'
													)
												"
											/>
											<NumberField
												v-model="settings.max_discount_allowed"
												:label="__('Max Discount (%)')"
												:description="__('Maximum discount per item')"
												:min="0"
												:max="100"
											/>
											<CheckboxField
												v-model="settings.use_percentage_discount"
												:label="__('Use Percentage Discount')"
												:description="__('Show discounts as percentages')"
											/>
											<CheckboxField
												v-model="
													settings.allow_user_to_edit_additional_discount
												"
												:label="__('Allow Additional Discount')"
												:description="__('Enable invoice-level discount')"
											/>
											<CheckboxField
												v-model="settings.allow_user_to_edit_item_discount"
												:label="__('Allow Item Discount')"
												:description="
													__('Enable item-level discount in edit dialog')
												"
											/>
											<CheckboxField
												v-model="settings.allow_user_to_edit_rate"
												:label="__('Allow User To Edit Rate')"
												:description="
													__(
														'Allow editing item rate in cart. Disabled when offers are applied.'
													)
												"
											/>
											<CheckboxField
												v-model="settings.disable_rounded_total"
												:label="__('Disable Rounded Total')"
												:description="
													__('Show exact totals without rounding')
												"
											/>
										</div>
									</div>

									<!-- Sales Operations -->
									<div :class="operationsSubsectionClasses.container">
										<div class="flex items-center gap-2 mb-4">
											<svg
												:class="operationsSubsectionClasses.icon"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													:d="icons.checkCircle"
												/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">
												{{ __("Sales Operations") }}
											</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.allow_credit_sale"
												:label="__('Allow Credit Sale')"
												:description="__('Enable sales on credit')"
											/>
											<CheckboxField
												v-model="settings.allow_return"
												:label="__('Allow Return')"
												:description="__('Enable product returns')"
											/>
											<CheckboxField
												v-model="settings.allow_write_off_change"
												:label="__('Allow Write Off Change')"
												:description="__('Write off small change amounts')"
											/>
											<CheckboxField
												v-model="settings.allow_partial_payment"
												:label="__('Allow Partial Payment')"
												:description="
													__('Enable partial payment for invoices')
												"
											/>
											<CheckboxField
												v-model="settings.silent_print"
												:label="__('Silent Print')"
												:description="
													__(
														'Send receipts directly to a thermal printer via QZ Tray (no browser dialog)'
													)
												"
											/>

											<!-- QZ Tray Printer Settings (shown when silent print is enabled) -->
											<div
												v-if="settings.silent_print"
												class="ps-6 flex flex-col gap-3 border-s-2 border-teal-200"
											>
												<!-- Connection Status -->
												<div class="flex items-center gap-2">
													<div
														class="w-2.5 h-2.5 rounded-full flex-shrink-0"
														:class="
															qzConnecting
																? 'bg-yellow-500 animate-pulse'
																: qzConnected
																? 'bg-green-500'
																: 'bg-red-500'
														"
													></div>
													<span
														class="text-xs font-medium"
														:class="
															qzConnecting
																? 'text-yellow-700'
																: qzConnected
																? 'text-green-700'
																: 'text-red-700'
														"
													>
														{{
															qzConnecting
																? __("Connecting to QZ Tray...")
																: qzConnected
																? __("QZ Tray Connected")
																: __("QZ Tray Not Connected")
														}}
													</span>
													<button
														v-if="!qzConnected && !qzConnecting"
														@click="handleQzConnect"
														class="ms-auto text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition-colors"
													>
														{{ __("Retry") }}
													</button>
												</div>

												<!-- Printer Selection -->
												<div class="flex items-end gap-2">
													<div class="flex-1">
														<SelectField
															v-model="selectedPrinter"
															:label="__('Printer')"
															:options="printerOptions"
															:description="
																qzPrinters.length === 0 &&
																!loadingPrinters
																	? __(
																			'No printers found. Is QZ Tray running?'
																	  )
																	: ''
															"
														/>
													</div>
													<button
														@click="handleRefreshPrinters"
														:disabled="loadingPrinters"
														class="px-2 py-2 mb-0.5 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
														:title="__('Refresh printer list')"
													>
														<svg
															class="w-4 h-4 text-gray-600"
															:class="
																loadingPrinters
																	? 'animate-spin'
																	: ''
															"
															fill="none"
															stroke="currentColor"
															viewBox="0 0 24 24"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
															/>
														</svg>
													</button>
												</div>

												<!-- QZ Certificate Status & Setup -->
												<div
													:class="[
														'p-3 rounded-lg border',
														qzCertStatus === 'trusted'
															? 'bg-green-50 border-green-200'
															: qzCertStatus === 'untrusted'
															? 'bg-red-50 border-red-200'
															: 'bg-amber-50 border-amber-200',
													]"
												>
													<div class="flex items-start gap-2">
														<!-- Icon changes based on status -->
														<svg
															class="w-4 h-4 mt-0.5 flex-shrink-0"
															:class="
																qzCertStatus === 'trusted'
																	? 'text-green-600'
																	: qzCertStatus === 'untrusted'
																	? 'text-red-600'
																	: 'text-amber-600'
															"
															fill="none"
															stroke="currentColor"
															viewBox="0 0 24 24"
														>
															<path
																v-if="qzCertStatus === 'trusted'"
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
															/>
															<path
																v-else
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
															/>
														</svg>
														<div class="flex-1">
															<!-- Title with inline status badge -->
															<div
																class="flex items-center gap-2 mb-1"
															>
																<p
																	class="text-xs font-semibold"
																	:class="
																		qzCertStatus === 'trusted'
																			? 'text-green-900'
																			: qzCertStatus ===
																			  'untrusted'
																			? 'text-red-900'
																			: 'text-amber-900'
																	"
																>
																	{{
																		__(
																			"Silent Print Certificate"
																		)
																	}}
																</p>
																<span
																	v-if="
																		qzCertStatus === 'trusted'
																	"
																	class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-100 border border-green-300 rounded-full"
																>
																	<span
																		class="w-1.5 h-1.5 bg-green-500 rounded-full"
																	></span>
																	<span
																		class="text-[10px] font-medium text-green-800"
																		>{{
																			__("Installed")
																		}}</span
																	>
																</span>
																<span
																	v-else-if="
																		qzCertStatus ===
																		'untrusted'
																	"
																	class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-100 border border-red-300 rounded-full"
																>
																	<span
																		class="w-1.5 h-1.5 bg-red-500 rounded-full"
																	></span>
																	<span
																		class="text-[10px] font-medium text-red-800"
																		>{{
																			__("Not Installed")
																		}}</span
																	>
																</span>
																<span
																	v-else
																	class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-100 border border-amber-300 rounded-full"
																>
																	<span
																		class="w-1.5 h-1.5 bg-amber-500 rounded-full"
																	></span>
																	<span
																		class="text-[10px] font-medium text-amber-800"
																		>{{
																			__("Checking...")
																		}}</span
																	>
																</span>
															</div>

															<!-- Status message -->
															<p
																v-if="qzCertStatus === 'trusted'"
																class="text-xs text-green-800 leading-relaxed mb-2"
															>
																{{
																	__(
																		"Certificate is installed and signing is active. Print jobs will be sent silently without confirmation dialogs."
																	)
																}}
															</p>
															<p
																v-else-if="
																	qzCertStatus === 'untrusted'
																"
																class="text-xs text-red-800 leading-relaxed mb-2"
															>
																{{
																	__(
																		"Certificate is not installed on this machine. Generate a certificate, download it, and import it into QZ Tray."
																	)
																}}
															</p>
															<p
																v-else
																class="text-xs text-amber-800 leading-relaxed mb-2"
															>
																{{
																	__(
																		"To print without confirmation dialogs, generate a signing certificate and install it on each POS machine."
																	)
																}}
															</p>

															<!-- Action buttons -->
															<div
																class="flex items-center gap-2 flex-wrap"
															>
																<button
																	v-if="
																		qzCertStatus !== 'trusted'
																	"
																	@click="
																		handleSetupQzCertificate
																	"
																	:disabled="qzCertLoading"
																	class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white rounded-md transition-colors bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400"
																>
																	<svg
																		v-if="qzCertLoading"
																		class="w-3.5 h-3.5 animate-spin"
																		fill="none"
																		viewBox="0 0 24 24"
																	>
																		<circle
																			class="opacity-25"
																			cx="12"
																			cy="12"
																			r="10"
																			stroke="currentColor"
																			stroke-width="4"
																		/>
																		<path
																			class="opacity-75"
																			fill="currentColor"
																			d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
																		/>
																	</svg>
																	<svg
																		v-else
																		class="w-3.5 h-3.5"
																		fill="none"
																		stroke="currentColor"
																		viewBox="0 0 24 24"
																	>
																		<path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="2"
																			d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
																		/>
																	</svg>
																	{{
																		__("Generate Certificate")
																	}}
																</button>
																<button
																	v-if="qzCertReady"
																	@click="
																		handleDownloadQzCertificate
																	"
																	class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
																>
																	<svg
																		class="w-3.5 h-3.5"
																		fill="none"
																		stroke="currentColor"
																		viewBox="0 0 24 24"
																	>
																		<path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="2"
																			d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
																		/>
																	</svg>
																	{{
																		__("Download Certificate")
																	}}
																</button>
															</div>

															<!-- Install instructions (only when cert exists but not trusted yet) -->
															<p
																v-if="
																	qzCertReady &&
																	qzCertStatus !== 'trusted'
																"
																class="text-xs mt-2"
																:class="
																	qzCertStatus === 'untrusted'
																		? 'text-red-700'
																		: 'text-amber-700'
																"
															>
																{{
																	__(
																		"Download the certificate and import it into QZ Tray, then restart QZ Tray."
																	)
																}}
															</p>
														</div>
													</div>
												</div>

												<!-- Help text -->
												<div
													class="p-3 bg-teal-50 border border-teal-200 rounded-lg"
												>
													<div class="flex items-start gap-2">
														<svg
															class="w-4 h-4 text-teal-600 mt-0.5 flex-shrink-0"
															fill="none"
															stroke="currentColor"
															viewBox="0 0 24 24"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
															/>
														</svg>
														<p
															class="text-xs text-teal-800 leading-relaxed"
														>
															{{
																__(
																	"QZ Tray must be installed and running on this computer. Download from"
																)
															}}
															<a
																href="https://qz.io/download/"
																target="_blank"
																class="font-semibold underline"
																>qz.io</a
															>.
															{{
																__(
																	"If QZ Tray is unavailable, printing will fall back to the browser dialog."
																)
															}}
														</p>
													</div>
												</div>
											</div>
										</div>
									</div>
								</div>

								<!-- Returns Policy -->
								<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Returns Policy") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.allow_return_without_invoice"
											:label="__('Allow Return Without Invoice')"
											:description="__('Enable returning items without referencing the original invoice')"
										/>
										<NumberField
											v-model="settings.return_validity_days"
											:label="__('Return Validity (Days)')"
											:description="__('Number of days a return is allowed after the sale. 0 means no limit.')"
											:min="0"
											:max="365"
										/>
										<CheckboxField
											v-model="settings.allow_free_batch_return"
											:label="__('Allow Free Batch Return')"
											:description="__('Allow returning items from batches that were given for free')"
										/>
									</div>
								</div>

								<!-- Sales Orders -->
								<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Sales Orders") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.allow_sales_order"
											:label="__('Allow Create Sales Order')"
											:description="__('Enable creating a Sales Order from the POS instead of a direct invoice')"
										/>
										<CheckboxField
											v-model="settings.allow_select_sales_order"
											:label="__('Allow Select Sales Order')"
											:description="__('Allow selecting an existing Sales Order to convert to an invoice')"
										/>
										<CheckboxField
											v-model="settings.create_only_sales_order"
											:label="__('Create Only Sales Order')"
											:description="__('Force POS to always create a Sales Order instead of an invoice')"
										/>
									</div>
								</div>

								<!-- Delivery Charges -->
								<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Delivery Charges") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.use_delivery_charges"
											:label="__('Use Delivery Charges')"
											:description="__('Allow adding delivery charges to invoices')"
										/>
										<CheckboxField
											v-model="settings.auto_set_delivery_charges"
											:label="__('Auto Set Delivery Charges')"
											:description="__('Automatically apply delivery charges based on configured rules')"
										/>
									</div>
								</div>

								<!-- Advanced Operations -->
								<div class="bg-gray-50 rounded-xl p-5 border border-gray-200">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Advanced Operations") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.allow_customer_credit_payment"
											:label="__('Allow Customer Credit Payment')"
											:description="__('Allow customers to pay using their credit balance')"
										/>
										<CheckboxField
											v-model="settings.use_exact_amount"
											:label="__('Use Exact Amount for Non-Cash')"
											:description="__('Require exact payment amount for non-cash payment methods')"
										/>
										<CheckboxField
											v-model="settings.fetch_coupon"
											:label="__('Auto Fetch Coupon Gifts')"
											:description="__('Automatically apply coupon gifts when eligible')"
										/>
										<CheckboxField
											v-model="settings.allow_change_posting_date"
											:label="__('Allow Change Posting Date')"
											:description="__('Allow cashiers to change the invoice posting date')"
										/>
										<CheckboxField
											v-model="settings.allow_delete_offline_invoice"
											:label="__('Allow Delete Offline Invoice')"
											:description="__('Allow deleting invoices that were created while offline')"
										/>
										<CheckboxField
											v-model="settings.allow_submissions_in_background_job"
											:label="__('Allow Background Submissions')"
											:description="__('Submit invoices in background jobs for faster checkout')"
										/>
										<div class="grid grid-cols-2 gap-3 pt-1">
											<div>
												<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Sales Persons") }}</label>
												<select v-model="settings.enable_sales_persons"
													class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
												>
													<option value="Disabled">{{ __("Disabled") }}</option>
													<option value="Single">{{ __("Single") }}</option>
													<option value="Multiple">{{ __("Multiple") }}</option>
												</select>
												<p class="text-xs text-gray-400 mt-1">{{ __("Assign sales persons to invoices") }}</p>
											</div>
											<div>
												<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Input Quantity") }}</label>
												<div class="flex items-center h-10">
													<CheckboxField
														v-model="settings.input_qty"
														:label="__('Use QTY Keypad')"
													/>
												</div>
											</div>
										</div>
										<div class="flex flex-col gap-2 pt-1 border-t border-gray-200">
											<CheckboxField
												v-model="settings.use_limit_search"
												:label="__('Use Search Limit')"
												:description="__('Limit the number of items shown in search results')"
											/>
											<NumberField
												v-if="settings.use_limit_search"
												v-model="settings.search_limit"
												:label="__('Search Result Limit')"
												:description="__('Maximum number of items shown in search results')"
												:min="10"
												:max="1000"
												:step="10"
											/>
										</div>
									</div>
								</div>
							</div>
						</div>

						<!-- ===== CUSTOMERS TAB ===== -->
						<div v-if="activeTab === 'customers'" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
							<div class="px-6 py-4 bg-white border-b border-gray-100">
								<div class="flex items-center gap-3">
									<div class="p-2 bg-blue-50 rounded-lg">
										<svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
										</svg>
									</div>
									<div>
										<h3 class="text-lg font-bold text-gray-900">{{ __("Customer Settings") }}</h3>
										<p class="text-xs text-gray-600 mt-0.5">{{ __("Configure loyalty, wallet, and customer options") }}</p>
									</div>
								</div>
							</div>
							<div class="p-6 flex flex-col gap-6">

								<!-- Loyalty Program -->
								<div class="bg-amber-50/50 rounded-xl p-5 border border-amber-100">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Loyalty Program") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.enable_loyalty_program"
											:label="__('Enable Loyalty Program')"
											:description="__('Allow customers to earn and redeem loyalty points')"
										/>
										<div v-if="settings.enable_loyalty_program" class="ps-6 border-s-2 border-amber-200 flex flex-col gap-3">
											<div>
												<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Default Loyalty Program") }}</label>
												<input
													v-model="settings.default_loyalty_program"
													type="text"
													:placeholder="__('Loyalty Program name...')"
													class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
												/>
												<p class="text-xs text-gray-400 mt-1">{{ __("Enter the exact Loyalty Program name from ERPNext") }}</p>
											</div>
											<CheckboxField
												v-model="settings.loyalty_to_wallet"
												:label="__('Convert Loyalty Points to Wallet')"
												:description="__('Automatically convert redeemed loyalty points into wallet balance')"
											/>
										</div>
									</div>
								</div>

								<!-- Wallet -->
								<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Customer Wallet") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<div>
											<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Wallet Account") }}</label>
											<input
												v-model="settings.wallet_account"
												type="text"
												:placeholder="__('Account name from Chart of Accounts...')"
												class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
											/>
											<p class="text-xs text-gray-400 mt-1">{{ __("The ledger account used for customer wallet balances") }}</p>
										</div>
										<CheckboxField
											v-model="settings.auto_create_wallet"
											:label="__('Auto Create Wallet')"
											:description="__('Automatically create a wallet for new customers')"
										/>
									</div>
								</div>

								<!-- Customer Options -->
								<div class="bg-gray-50 rounded-xl p-5 border border-gray-200">
									<div class="flex items-center gap-2 mb-4">
										<svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
										</svg>
										<h4 class="text-sm font-semibold text-gray-900">{{ __("Customer Options") }}</h4>
									</div>
									<div class="flex flex-col gap-3">
										<CheckboxField
											v-model="settings.show_customer_balance"
											:label="__('Show Customer Balance')"
											:description="__('Display the customer outstanding balance in the POS')"
										/>
										<CheckboxField
											v-model="settings.allow_customer_purchase_order"
											:label="__('Allow Customer Purchase Order')"
											:description="__('Allow linking a customer PO number to the invoice')"
										/>
										<CheckboxField
											v-model="settings.allow_duplicate_customer_names"
											:label="__('Allow Duplicate Customer Names')"
											:description="__('Allow creating customers with the same name')"
										/>
									</div>
								</div>

							</div>
						</div>

						<!-- ===== DISPLAY & PRINT TAB ===== -->
						<div v-if="activeTab === 'display'" class="flex flex-col gap-6">

							<!-- Display Options Card -->
							<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
								<div class="px-6 py-4 bg-white border-b border-gray-100">
									<div class="flex items-center gap-3">
										<div class="p-2 bg-slate-100 rounded-lg">
											<svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2"/>
											</svg>
										</div>
										<div>
											<h3 class="text-lg font-bold text-gray-900">{{ __("Display Options") }}</h3>
											<p class="text-xs text-gray-600 mt-0.5">{{ __("Customize what information is shown in the POS interface") }}</p>
										</div>
									</div>
								</div>
								<div class="p-6 flex flex-col gap-6">

									<!-- Item Display -->
									<div class="bg-gray-50 rounded-xl p-5 border border-gray-200">
										<div class="flex items-center gap-2 mb-4">
											<svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">{{ __("Items Display") }}</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.default_card_view"
												:label="__('Default Card View')"
												:description="__('Show items as cards instead of a list by default')"
											/>
											<CheckboxField
												v-model="settings.display_item_code"
												:label="__('Display Item Code')"
												:description="__('Show the item code alongside the item name')"
											/>
											<CheckboxField
												v-model="settings.show_variants_as_items"
												:label="__('Show Variants as Items')"
												:description="__('Display product variants as separate items in the catalog')"
											/>
											<CheckboxField
												v-model="settings.input_qty"
												:label="__('Use QTY Input Keypad')"
												:description="__('Show a quantity keypad for faster item entry')"
											/>
											<div>
												<label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Decimal Precision") }}</label>
												<select v-model="settings.decimal_precision"
													class="w-40 h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
												>
													<option value="2">2 {{ __("decimals") }}</option>
													<option value="3">3 {{ __("decimals") }}</option>
													<option value="4">4 {{ __("decimals") }}</option>
													<option value="5">5 {{ __("decimals") }}</option>
													<option value="6">6 {{ __("decimals") }}</option>
												</select>
												<p class="text-xs text-gray-400 mt-1">{{ __("Precision for quantities and rates") }}</p>
											</div>
										</div>
									</div>

									<!-- Invoice Display -->
									<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
										<div class="flex items-center gap-2 mb-4">
											<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z"/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">{{ __("Invoice Display") }}</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.hide_expected_amount"
												:label="__('Hide Expected Amount')"
												:description="__('Hide the expected payment amount in the payment dialog')"
											/>
											<CheckboxField
												v-model="settings.display_discount_percentage"
												:label="__('Display Discount %')"
												:description="__('Show the discount percentage on invoice lines')"
											/>
											<CheckboxField
												v-model="settings.display_discount_amount"
												:label="__('Display Discount Amount')"
												:description="__('Show the discount amount on invoice lines')"
											/>
										</div>
									</div>

								</div>
							</div>

							<!-- Print Options Card -->
							<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
								<div class="px-6 py-4 bg-white border-b border-gray-100">
									<div class="flex items-center gap-3">
										<div class="p-2 bg-slate-100 rounded-lg">
											<svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
											</svg>
										</div>
										<div>
											<h3 class="text-lg font-bold text-gray-900">{{ __("Print Settings") }}</h3>
											<p class="text-xs text-gray-600 mt-0.5">{{ __("Configure receipt printing options") }}</p>
										</div>
									</div>
								</div>
								<div class="p-6 flex flex-col gap-6">
									<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
										<div class="flex items-center gap-2 mb-4">
											<svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
											</svg>
											<h4 class="text-sm font-semibold text-gray-900">{{ __("Print Options") }}</h4>
										</div>
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.allow_print_draft_invoices"
												:label="__('Allow Print Draft Invoices')"
												:description="__('Allow printing invoices that are still in draft state')"
											/>
											<CheckboxField
												v-model="settings.allow_print_last_invoice"
												:label="__('Allow Print Last Invoice')"
												:description="__('Show a button to reprint the last submitted invoice')"
											/>
										</div>
									</div>
								</div>
							</div>

							<!-- Security Card -->
							<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
								<div class="px-6 py-4 bg-white border-b border-gray-100">
									<div class="flex items-center gap-3">
										<div class="p-2 bg-red-50 rounded-lg">
											<svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
											</svg>
										</div>
										<div>
											<h3 class="text-lg font-bold text-gray-900">{{ __("Security") }}</h3>
											<p class="text-xs text-gray-600 mt-0.5">{{ __("Configure session lock and security options") }}</p>
										</div>
									</div>
								</div>
								<div class="p-6">
									<div class="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
										<div class="flex flex-col gap-3">
											<CheckboxField
												v-model="settings.enable_session_lock"
												:label="__('Enable Session Lock')"
												:description="__('Automatically lock the POS after a period of inactivity')"
											/>
											<div v-if="settings.enable_session_lock" class="ps-6 border-s-2 border-red-200">
												<NumberField
													v-model="settings.session_lock_timeout"
													:label="__('Lock Timeout (minutes)')"
													:description="__('Minutes of inactivity before the session auto-locks')"
													:min="1"
													:max="120"
												/>
											</div>
										</div>
									</div>
								</div>
							</div>

						</div>

						<!-- Empty State -->
						<div
							v-else
							class="flex flex-col items-center justify-center py-16 text-center"
						>
							<svg
								class="w-16 h-16 text-gray-400 mb-4"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
							<p class="text-gray-600 font-medium">
								{{ __("No POS Profile Selected") }}
							</p>
							<p class="text-gray-500 text-sm mt-1">
								{{ __("Please select a POS Profile to configure settings") }}
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</Transition>
</template>

<script setup>
import BrandingSettings from "@/components/settings/BrandingSettings.vue";
import CheckboxField from "@/components/settings/CheckboxField.vue";
import NumberField from "@/components/settings/NumberField.vue";
import SelectField from "@/components/settings/SelectField.vue";
import { useToast } from "@/composables/useToast";
import { Button, call, createResource } from "frappe-ui";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { getSectionHeaderClasses, getSubsectionClasses, icons } from "./settingsConfig";
import { offlineWorker } from "@/utils/offline/workerClient";
import { logger } from "@/utils/logger";
import { usePOSEvents } from "@/composables/usePOSEvents";
import TranslatedHTML from "../common/TranslatedHTML.vue";
import { useQzTray } from "@/composables/useQzTray";
import { getSetting, isOffline, setSetting } from "@/utils/offline";

const log = logger.create("POSSettings");
const { detectSettingsChanges, updateSettingsSnapshot, emitStockSyncConfigured } = usePOSEvents();
const { showSuccess, showError, showWarning } = useToast();

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	currentWarehouse: String,
	canManageFeatureFlags: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const show = ref(props.modelValue);
const settingsCacheKey = computed(() => `pos_settings_${props.posProfile || "default"}`);
const warehousesCacheKey = computed(() => `pos_warehouses_${props.posProfile || "default"}`);

// State
const activeTab = ref("stock");
const loading = ref(true);
const saving = ref(false);
const warehousesList = ref([]);
const selectedWarehouse = ref(props.currentWarehouse || "");
const settings = ref({
	pos_profile: props.posProfile || "",
	enabled: 1,
	// Core Settings
	max_discount_allowed: 0,
	use_percentage_discount: 0,
	allow_user_to_edit_additional_discount: 0,
	allow_user_to_edit_item_discount: 1,
	allow_user_to_edit_rate: 0,
	disable_rounded_total: 1,
	allow_credit_sale: 0,
	allow_return: 0,
	allow_write_off_change: 0,
	allow_partial_payment: 0,
	silent_print: 0,
	allow_negative_stock: 0,
	tax_inclusive: 0,
	// Returns Policy
	allow_return_without_invoice: 0,
	return_validity_days: 0,
	allow_free_batch_return: 0,
	// Sales Orders
	allow_sales_order: 0,
	allow_select_sales_order: 0,
	create_only_sales_order: 0,
	// Delivery Charges
	use_delivery_charges: 0,
	auto_set_delivery_charges: 0,
	// Advanced Operations
	allow_customer_credit_payment: 0,
	use_exact_amount: 0,
	fetch_coupon: 0,
	allow_change_posting_date: 0,
	allow_delete_offline_invoice: 0,
	allow_submissions_in_background_job: 0,
	enable_sales_persons: "Disabled",
	input_qty: 0,
	use_limit_search: 0,
	search_limit: 100,
	// Customers — Loyalty
	enable_loyalty_program: 0,
	default_loyalty_program: "",
	loyalty_to_wallet: 0,
	// Customers — Wallet
	wallet_account: "",
	auto_create_wallet: 0,
	// Customers — Options
	show_customer_balance: 0,
	allow_customer_purchase_order: 0,
	allow_duplicate_customer_names: 0,
	// Display — Items
	default_card_view: 0,
	display_item_code: 0,
	show_variants_as_items: 0,
	decimal_precision: "2",
	// Display — Invoice
	hide_expected_amount: 0,
	display_discount_percentage: 0,
	display_discount_amount: 0,
	// Print
	allow_print_draft_invoices: 0,
	allow_print_last_invoice: 0,
	// Security
	enable_session_lock: 0,
	session_lock_timeout: 5,
	// Manager-controlled capabilities (secure-off defaults)
	enable_catalog_management: 0,
	enable_purchases: 0,
	enable_supplier_payments: 0,
	enable_pos_reports: 0,
	enable_cash_management: 0,
	// Purchase defaults (mirror the sales default customer) — pre-fill purchase mode
	posa_default_supplier: "",
	posa_default_purchase_warehouse: "",
	posa_default_purchase_tax_template: "",
	posa_default_expense_account: "",
	// Which source purchase-mode buying prices are fetched from (backend expects the
	// exact English string; falls back through the other sources).
	posa_purchase_price_source: "Buying Price List",
});

const featureFlagDefinitions = computed(() => [
	{
		fieldname: "enable_catalog_management",
		label: __("Catalog Management"),
		description: __("Create and update item groups, items, and prices inside POS."),
	},
	{
		fieldname: "enable_purchases",
		label: __("Purchases"),
		description: __("Manage Purchase Invoices from the manager workspace."),
	},
	{
		fieldname: "enable_supplier_payments",
		requires: "enable_purchases",
		label: __("Supplier Payments"),
		description: __("Create, submit, and cancel supplier Payment Entries. Requires Purchases."),
	},
	{
		fieldname: "enable_pos_reports",
		label: __("In-POS Reports"),
		description: __("Show operational reports to authorized managers inside POS."),
	},
	{
		fieldname: "enable_cash_management",
		label: __("Enable Cash Management (Expenses / Receipts)"),
		description: __("Let cashiers record drawer cash movements (expense / receipt / payment) during a shift."),
	},
]);

// Purchase defaults option lists (loaded lazily when the section is visible).
const purchaseSuppliers = ref([]);
const purchaseWarehouses = ref([]);
const purchaseTaxTemplates = ref([]);
const purchaseExpenseAccounts = ref([]);
const purchaseDefaultsLoading = ref(false);
const purchaseDefaultsError = ref(false);
let purchaseDefaultsLoaded = false;

/**
 * Build SelectField options ([{value,label}]) from a fetched list. Ensures the
 * currently-saved value is always present as an option even when it falls outside
 * the fetched set (e.g. supplier list capped at 100, or a value now disabled),
 * so the <select> never renders blank while a value is silently set.
 */
function toPurchaseOptions(list, valueKey, labelKey, savedValue) {
	const options = (list || []).map((row) => ({
		value: row[valueKey],
		label: row[labelKey] || row[valueKey],
	}));
	if (savedValue && !options.some((o) => o.value === savedValue)) {
		options.unshift({ value: savedValue, label: savedValue });
	}
	return options;
}

const supplierOptions = computed(() =>
	toPurchaseOptions(
		purchaseSuppliers.value,
		"name",
		"supplier_name",
		settings.value.posa_default_supplier
	)
);
const purchaseWarehouseOptions = computed(() =>
	toPurchaseOptions(
		purchaseWarehouses.value,
		"name",
		"warehouse_name",
		settings.value.posa_default_purchase_warehouse
	)
);
const purchaseTaxTemplateOptions = computed(() =>
	toPurchaseOptions(
		purchaseTaxTemplates.value,
		"name",
		"title",
		settings.value.posa_default_purchase_tax_template
	)
);
const expenseAccountOptions = computed(() =>
	toPurchaseOptions(
		purchaseExpenseAccounts.value,
		"name",
		"account_name",
		settings.value.posa_default_expense_account
	)
);
// Fixed list; the stored value MUST be the exact English string the backend expects.
const purchasePriceSourceOptions = computed(() => [
	{ value: "Buying Price List", label: __("Buying Price List") },
	{ value: "Last Purchase Rate", label: __("Last Purchase Rate") },
	{ value: "Valuation Rate", label: __("Valuation Rate") },
]);

/**
 * Lazily load the purchase-defaults option lists. Runs only when the Feature Flags
 * tab is open with purchases enabled. The endpoints are feature-gated server-side,
 * so if the manager just toggled purchases ON but hasn't saved yet, the load fails
 * — surface a graceful inline note instead of a raw error.
 */
async function loadPurchaseDefaultOptions() {
	if (purchaseDefaultsLoaded || purchaseDefaultsLoading.value) return;
	if (!props.posProfile) return;
	purchaseDefaultsLoading.value = true;
	purchaseDefaultsError.value = false;
	try {
		const [suppliers, warehouses, taxTemplates, expenseAccounts] = await Promise.all([
			call("pos_next.api.purchases.get_suppliers", {
				limit: 100,
				pos_profile: props.posProfile,
			}),
			call("pos_next.api.purchases.get_warehouses", { pos_profile: props.posProfile }),
			call("pos_next.api.purchases.get_purchase_tax_templates", {
				pos_profile: props.posProfile,
			}),
			call("pos_next.api.purchases.get_expense_accounts", {
				pos_profile: props.posProfile,
			}),
		]);
		purchaseSuppliers.value = suppliers || [];
		purchaseWarehouses.value = warehouses || [];
		purchaseTaxTemplates.value = taxTemplates || [];
		purchaseExpenseAccounts.value = expenseAccounts || [];
		purchaseDefaultsLoaded = true;
	} catch (error) {
		log.error("Error loading purchase default options:", error);
		purchaseDefaultsError.value = true;
	} finally {
		purchaseDefaultsLoading.value = false;
	}
}

// Load lazily when the Purchase Defaults section becomes visible.
watch(
	() => activeTab.value === "features" && !!settings.value.enable_purchases,
	(visible) => {
		if (visible) loadPurchaseDefaultOptions();
	}
);

// Stock Sync Settings (localStorage persisted)
const stockSyncEnabled = ref(false);
const stockSyncIntervalSeconds = ref(60); // Default 60 seconds
const stockSyncStatus = ref({
	enabled: false,
	warehouse: null,
	itemCount: 0,
	intervalMs: 60000,
	lastSync: null,
	running: false,
});

// QZ Tray composable
const {
	qzConnected,
	qzConnecting,
	qzCertStatus,
	printers: qzPrinters,
	selectedPrinter,
	loadingPrinters,
	printerOptions,
	certLoading: qzCertLoading,
	certReady: qzCertReady,
	handleConnect: handleQzConnect,
	refreshPrinters: handleRefreshPrinters,
	generateCertificate: handleSetupQzCertificate,
	downloadCertificate: handleDownloadQzCertificate,
} = useQzTray();

// Warehouse options
const warehouseOptions = computed(() => {
	if (warehousesList.value.length === 0) return [];
	return warehousesList.value.map((w) => ({
		label: w.warehouse_name || w.name,
		value: w.name,
	}));
});

// Dynamic classes using configuration helpers (DRY principle)
const stockSectionClasses = computed(() => getSectionHeaderClasses("purple"));
const salesSectionClasses = computed(() => getSectionHeaderClasses("green"));
const warehouseSubsectionClasses = computed(() => getSubsectionClasses("gray"));
const stockPolicySubsectionClasses = computed(() => getSubsectionClasses("blue"));
const stockSyncSubsectionClasses = computed(() => getSubsectionClasses("indigo"));
const pricingSubsectionClasses = computed(() => getSubsectionClasses("emerald"));
const operationsSubsectionClasses = computed(() => getSubsectionClasses("teal"));

// Resources
const warehousesResource = createResource({
	url: "pos_next.api.pos_profile.get_warehouses",
	makeParams() {
		return {
			pos_profile: props.posProfile,
		};
	},
	auto: false,
	onSuccess(data) {
		const warehouses = data?.message || data || [];
		warehousesList.value = warehouses;
		setSetting(warehousesCacheKey.value, warehouses).catch(() => {});
	},
	async onError(error) {
		warehousesList.value = (await getSetting(warehousesCacheKey.value)) || [];
	},
});

// Track original allow_negative_stock value for detecting changes
const originalAllowNegativeStock = ref(null);

const settingsResource = createResource({
	url: "pos_next.pos_next.doctype.pos_settings.pos_settings.get_pos_settings",
	makeParams() {
		return {
			pos_profile: props.posProfile,
		};
	},
	onSuccess(data) {
		if (data) {
			Object.assign(settings.value, data);
			setSetting(settingsCacheKey.value, data).catch(() => {});
			settings.value.pos_profile = props.posProfile;
			// Store original value
			originalAllowNegativeStock.value = data.allow_negative_stock;
			// Update event system snapshot
			updateSettingsSnapshot(settings.value);
		}
		loading.value = false;
	},
	async onError(error) {
		const cached = await getSetting(settingsCacheKey.value);
		if (cached) {
			Object.assign(settings.value, cached);
			settings.value.pos_profile = props.posProfile;
			originalAllowNegativeStock.value = cached.allow_negative_stock;
			updateSettingsSnapshot(settings.value);
			showWarning(__("Showing cached settings while offline"));
			loading.value = false;
			return;
		}
		loading.value = false;
		showError(__("Failed to load settings"));
	},
});

// Watchers
watch(
	() => props.modelValue,
	(val) => {
		show.value = val;
		if (val) {
			loadSettings();
		}
	}
);

watch(show, (val) => {
	emit("update:modelValue", val);
});

// Watch for currentWarehouse prop changes and always sync
watch(
	() => props.currentWarehouse,
	(newWarehouse) => {
		if (newWarehouse) {
			selectedWarehouse.value = newWarehouse;
		}
	},
	{ immediate: true }
);

// Watch for tax_inclusive changes to provide immediate feedback
const originalTaxInclusive = ref(null);
watch(
	() => settings.value.tax_inclusive,
	(newValue, oldValue) => {
		// Store original value on first load
		if (originalTaxInclusive.value === null && oldValue !== undefined) {
			originalTaxInclusive.value = oldValue;
		}

		// Only show feedback if value actually changed from original
		if (originalTaxInclusive.value !== null && newValue !== originalTaxInclusive.value) {
			const mode = newValue ? "inclusive" : "exclusive";
			log.info(`Tax mode toggled to: ${mode}`);
		}
	}
);

watch(
	() => settings.value.enable_purchases,
	(enabled) => {
		if (!enabled) settings.value.enable_supplier_payments = 0;
	}
);

// Methods
function handleClose() {
	show.value = false;
}

async function loadSettings() {
	if (!props.posProfile) return;
	loading.value = true;
	settings.value.pos_profile = props.posProfile;

	// Always set the current warehouse from props (from current shift/profile)
	selectedWarehouse.value = props.currentWarehouse || "";

	if (isOffline()) {
		const [cachedWarehouses, cachedSettings] = await Promise.all([
			getSetting(warehousesCacheKey.value),
			getSetting(settingsCacheKey.value),
		]);
		warehousesList.value = cachedWarehouses || [];
		if (cachedSettings) {
			Object.assign(settings.value, cachedSettings);
			settings.value.pos_profile = props.posProfile;
			originalAllowNegativeStock.value = cachedSettings.allow_negative_stock;
			updateSettingsSnapshot(settings.value);
		}
		loading.value = false;
		showWarning(__("Settings are read-only while offline"));
		return;
	}

	try {
		// Load warehouses first using call API directly
		const warehousesData = await call("pos_next.api.pos_profile.get_warehouses", {
			pos_profile: props.posProfile,
		});

		// Handle frappe-ui call response format { message: [...] }
		warehousesList.value = warehousesData?.message || warehousesData || [];
		await setSetting(warehousesCacheKey.value, warehousesList.value);

		// Load settings
		settingsResource.reload();
	} catch (error) {
		log.error("Error loading warehouses:", error);
		warehousesList.value = (await getSetting(warehousesCacheKey.value)) || [];
		// Still load settings even if warehouses fail
		settingsResource.reload();
	}
}

async function saveSettings() {
	if (!props.posProfile) {
		showError(__("POS Profile not found"));
		return;
	}
	if (isOffline()) {
		showWarning(__("Settings cannot be changed while offline"));
		return;
	}

	saving.value = true;
	const oldWarehouse = props.currentWarehouse;
	const warehouseChanged = selectedWarehouse.value !== oldWarehouse;
	const negativeStockChanged =
		originalAllowNegativeStock.value !== settings.value.allow_negative_stock;
	const taxInclusiveChanged =
		originalTaxInclusive.value !== null &&
		originalTaxInclusive.value !== settings.value.tax_inclusive;

	// Capture old settings for change detection
	const oldSettings = {
		...settings.value,
		warehouse: oldWarehouse, // Include warehouse in change detection
	};

	try {
		// Save POS Settings (without warehouse)
		const result = await call(
			"pos_next.pos_next.doctype.pos_settings.pos_settings.update_pos_settings",
			{
				pos_profile: props.posProfile,
				settings: settings.value,
			}
		);

		if (result) {
			Object.assign(settings.value, result);
			settings.value.pos_profile = props.posProfile;
			// Update original values after successful save
			originalAllowNegativeStock.value = result.allow_negative_stock;
			originalTaxInclusive.value = result.tax_inclusive;
		}

		// Update warehouse in POS Profile if changed
		if (warehouseChanged && selectedWarehouse.value) {
			const warehouseResult = await call("pos_next.api.pos_profile.update_warehouse", {
				pos_profile: props.posProfile,
				warehouse: selectedWarehouse.value,
			});

			if (warehouseResult && warehouseResult.success) {
				// Add warehouse to new settings for change detection
				// (detectSettingsChanges below will emit settings:warehouse-changed via event bus)
				settings.value.warehouse = selectedWarehouse.value;
			}
		}

		// Detect and emit settings changes through event system
		// This will notify all listeners (POSSale, stock store, cart store, etc.)
		detectSettingsChanges(settings.value, oldSettings);

		// IMPORTANT: Page reload for critical stock policy change
		// The allow_negative_stock setting affects deep stock validation logic
		// throughout the app, including:
		// - Stock validation in cart operations (posCart.js:59)
		// - Stock enforcement checks (posSettings.js:268)
		// - Item addition logic and error handling
		// A page reload ensures all components get the fresh setting and
		// prevents inconsistent state. Event listeners are still notified
		// before reload for any cleanup needed.
		if (negativeStockChanged) {
			log.info("Stock policy changed, reloading page for consistency...");
			window.location.reload();
			return;
		}

		// Show success toast for other changes
		let successMessage = __("Settings saved successfully");
		if (warehouseChanged && taxInclusiveChanged) {
			successMessage = __(
				"Settings saved, warehouse updated, and tax mode changed. Cart will be recalculated."
			);
		} else if (warehouseChanged) {
			successMessage = __("Settings saved and warehouse updated. Reloading stock...");
		} else if (taxInclusiveChanged) {
			successMessage = settings.value.tax_inclusive
				? __('Settings saved. Tax mode is now "inclusive". Cart will be recalculated.')
				: __('Settings saved. Tax mode is now "exclusive". Cart will be recalculated.');
		}

		showSuccess(successMessage);

		// If purchases was just enabled (or the earlier option load failed because the
		// flag wasn't saved yet), the feature-gated purchase-default endpoints now pass
		// — load the option lists so the section is usable without a manual reopen.
		if (settings.value.enable_purchases && !purchaseDefaultsLoaded) {
			purchaseDefaultsError.value = false;
			loadPurchaseDefaultOptions();
		}
	} catch (error) {
		log.error("Error saving settings:", error);
		showError(error.message || __("Failed to save settings"));
	} finally {
		saving.value = false;
	}
}

// Auto-connect and discover printers when silent_print is toggled on
watch(
	() => settings.value.silent_print,
	async (enabled) => {
		if (enabled) {
			await handleQzConnect();
		}
	}
);

// ============================================================================
// STOCK SYNC FUNCTIONS
// ============================================================================

// Load stock sync settings from localStorage
function loadStockSyncSettings() {
	try {
		const saved = localStorage.getItem("pos_stock_sync_settings");
		if (saved) {
			const parsed = JSON.parse(saved);
			stockSyncEnabled.value = parsed.enabled ?? false;
			stockSyncIntervalSeconds.value = parsed.intervalSeconds ?? 60;
		}
	} catch (error) {
		log.error("Failed to load stock sync settings:", error);
	}
}

// Save stock sync settings to localStorage
function saveStockSyncSettings() {
	try {
		localStorage.setItem(
			"pos_stock_sync_settings",
			JSON.stringify({
				enabled: stockSyncEnabled.value,
				intervalSeconds: stockSyncIntervalSeconds.value,
			})
		);
	} catch (error) {
		log.error("Failed to save stock sync settings:", error);
	}
}

// Update stock sync status
async function updateStockSyncStatus() {
	try {
		const status = await offlineWorker.getStockSyncStatus();
		stockSyncStatus.value = status;
	} catch (error) {
		log.error("Failed to get stock sync status:", error);
	}
}

// Apply stock sync configuration to worker
async function applyStockSyncConfig() {
	try {
		const intervalMs = stockSyncIntervalSeconds.value * 1000;

		if (stockSyncEnabled.value) {
			// Configure and start sync
			await offlineWorker.configureStockSync({
				intervalMs,
			});
			await offlineWorker.startStockSync();
		} else {
			// Stop sync
			await offlineWorker.stopStockSync();
		}

		// Update status
		await updateStockSyncStatus();

		// Save to localStorage
		saveStockSyncSettings();

		// Emit sync configuration change event
		emitStockSyncConfigured({
			enabled: stockSyncEnabled.value,
			intervalMs: intervalMs,
		});
	} catch (error) {
		log.error("Failed to apply stock sync config:", error);
	}
}

// Format sync time for display
function formatSyncTime(timestamp) {
	if (!timestamp) return __("Never");

	const now = Date.now();
	const diff = now - timestamp;

	if (diff < 60000) {
		return __("{0}s ago", [Math.floor(diff / 1000)]);
	} else if (diff < 3600000) {
		return __("{0}m ago", [Math.floor(diff / 60000)]);
	} else {
		const date = new Date(timestamp);
		return date.toLocaleTimeString();
	}
}

// Watch for changes and apply
watch(stockSyncEnabled, () => {
	applyStockSyncConfig();
});

watch(stockSyncIntervalSeconds, () => {
	if (stockSyncEnabled.value) {
		applyStockSyncConfig();
	}
});

// Lifecycle hooks
onMounted(async () => {
	// Load settings
	loadStockSyncSettings();

	// Update status initially
	await updateStockSyncStatus();

	// Poll status every 5 seconds
	const statusInterval = setInterval(() => {
		updateStockSyncStatus();
	}, 5000);

	// Cleanup on unmount
	onUnmounted(() => {
		clearInterval(statusInterval);
	});
});
</script>

<style scoped>
/* Fade transition for overlay */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
