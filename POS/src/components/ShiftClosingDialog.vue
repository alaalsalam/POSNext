<template>
	<Dialog v-model="open" :options="{ title: __('Close POS Shift'), size: '4xl' }">
		<template #body-content>

			<!-- ── LOADING ── -->
			<div v-if="closingDataResource.loading" class="flex flex-col items-center justify-center py-12 gap-3">
				<div class="relative w-10 h-10">
					<div class="absolute inset-0 rounded-full border-4 border-gray-100"></div>
					<div class="absolute inset-0 rounded-full border-4 border-t-blue-600 animate-spin"></div>
				</div>
				<p class="text-sm text-gray-500">{{ __("Loading shift data...") }}</p>
			</div>

			<!-- ── LOAD ERROR ── -->
			<div v-else-if="!closingData && (closingDataResource.error || errorMessage)" class="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4">
				<FeatherIcon name="alert-circle" class="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
				<div>
					<p class="text-sm font-semibold text-red-800">{{ __("Failed to Load Shift Data") }}</p>
					<p class="text-xs text-red-600 mt-0.5">{{ errorMessage || closingDataResource.error }}</p>
				</div>
			</div>

			<!-- ── MAIN CONTENT ── -->
			<div v-else-if="closingData" class="flex flex-col gap-2.5">

				<!-- Idle Warning -->
				<div v-if="showIdleWarning" class="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
					<FeatherIcon name="clock" class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
					<p class="text-xs text-amber-800">{{ __("Open over 1 minute — close the shift or cancel.") }}</p>
				</div>

				<!-- Pending (unapproved) cash entries are NOT in the expected cash yet — warn so the
				     drawer is not mistaken for short until a manager approves them. -->
				<div v-if="closingData.pending_cash_entries > 0" class="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
					<FeatherIcon name="alert-triangle" class="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
					<p class="text-xs text-amber-800">{{ __("{0} cash entries await manager approval — not counted in the expected cash yet, so the drawer may look short until approved.", [closingData.pending_cash_entries]) }}</p>
				</div>

				<!-- ── HEADER STRIP ── -->
				<div class="flex items-center justify-between bg-slate-800 text-white px-4 py-2.5 rounded-xl gap-4">
					<div class="min-w-0">
						<p class="text-xs text-slate-400 truncate leading-none mb-0.5">{{ closingData.pos_profile }}</p>
						<p class="text-sm font-bold leading-tight">
							{{ isInEntryMode ? __("Count Your Cash") : showSuccessReport ? __("✓ Shift Closed") : __("Shift Summary") }}
						</p>
						<p class="text-xs text-slate-400 truncate leading-none mt-0.5">
							{{ __("Cashier: {0}", [userName]) }}
						</p>
					</div>

					<!-- Entry mode: progress pills -->
					<div v-if="isInEntryMode" class="flex items-center gap-1 flex-1 max-w-28">
						<div
							v-for="(p, i) in activeMethods"
							:key="i"
							:class="['h-1 flex-1 rounded-full transition-all', p._touched ? 'bg-blue-400' : 'bg-slate-600']"
						></div>
					</div>

					<div class="text-end flex-shrink-0">
						<p class="text-sm font-semibold tabular-nums leading-none">{{ getShiftDuration() }}</p>
						<p class="text-xs text-slate-500 mt-0.5">{{ formatDateTime(closingData.period_start_date) }}</p>
					</div>
				</div>

				<!-- ══════════════════════════════════════════
				     ENTRY MODE
				     ══════════════════════════════════════════ -->
				<template v-if="isInEntryMode">

					<!-- Active payment methods -->
					<div class="border border-gray-200 rounded-xl overflow-hidden divide-y divide-gray-100">
						<div
							v-for="(payment, idx) in activeMethods"
							:key="idx"
							:class="['flex items-center gap-3 px-4 py-2.5 transition-colors', payment._touched ? 'bg-blue-50' : 'bg-white hover:bg-gray-50']"
						>
							<div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0', getPaymentIcon(payment.mode_of_payment).color]">
								{{ getPaymentIcon(payment.mode_of_payment).icon }}
							</div>
							<div class="flex-1 min-w-0">
								<label :for="`entry-${idx}`" class="block text-sm font-semibold text-gray-900 cursor-pointer truncate">
									{{ payment.mode_of_payment }}
								</label>
								<p v-if="payment._touched && payment.closing_amount !== null" class="text-xs text-blue-600 font-medium leading-none mt-0.5">
									{{ formatCurrency(payment.closing_amount) }}
								</p>
								<p v-else class="text-xs text-gray-400 leading-none mt-0.5">{{ __("Tap to enter") }}</p>
							</div>
							<div class="w-36 flex-shrink-0">
								<Input
									:id="`entry-${idx}`"
									:modelValue="payment.closing_amount"
									@update:modelValue="(v) => updateClosingAmount(payment, v)"
									type="number" step="10" min="0" placeholder="0.00"
									:disabled="submitResource.loading"
									class="text-base font-bold text-center"
								/>
							</div>
						</div>

						<!-- "Show unused" toggle row -->
						<button
							v-if="unusedMethodsCount > 0"
							@click="showAllMethods = !showAllMethods"
							class="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-start"
						>
							<span class="text-xs text-gray-500">
								<span v-if="showAllMethods">{{ __("Hide {0} unused methods", [unusedMethodsCount]) }}</span>
								<span v-else>{{ __("+ {0} unused methods (0.00)", [unusedMethodsCount]) }}</span>
							</span>
							<FeatherIcon :name="showAllMethods ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5 text-gray-400" />
						</button>

						<!-- Unused methods (shown when expanded) -->
						<template v-if="showAllMethods">
							<div
								v-for="(payment, idx) in unusedMethods"
								:key="`unused-${idx}`"
								class="flex items-center gap-3 px-4 py-2.5 bg-gray-50 opacity-70"
							>
								<div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0', getPaymentIcon(payment.mode_of_payment).color]">
									{{ getPaymentIcon(payment.mode_of_payment).icon }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-gray-600 truncate">{{ payment.mode_of_payment }}</p>
									<p class="text-xs text-gray-400 leading-none mt-0.5">{{ __("No activity this shift") }}</p>
								</div>
								<div class="w-36 flex-shrink-0">
									<Input
										:modelValue="payment.closing_amount"
										@update:modelValue="(v) => updateClosingAmount(payment, v)"
										type="number" step="10" min="0" placeholder="0.00"
										:disabled="submitResource.loading"
										class="text-base font-bold text-center"
									/>
								</div>
							</div>
						</template>
					</div>

					<!-- All entered total -->
					<div v-if="allRequiredAmountsEntered" class="flex items-center justify-between bg-green-50 border border-green-200 rounded-xl px-4 py-2.5">
						<div class="flex items-center gap-1.5">
							<FeatherIcon name="check-circle" class="w-4 h-4 text-green-600" />
							<span class="text-sm font-semibold text-green-800">{{ __("All amounts entered") }}</span>
						</div>
						<span class="text-base font-bold text-green-900 tabular-nums">{{ formatCurrency(getTotalActual) }}</span>
					</div>

					<!-- Variance confirmation -->
					<div v-if="hasUnconfirmedVariance" class="flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 px-4 py-2.5">
						<FeatherIcon name="alert-triangle" class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
						<label class="flex cursor-pointer items-start gap-2 text-sm text-amber-900">
							<input v-model="varianceConfirmed" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-amber-400" />
							<span class="text-xs">{{ __("Variance detected — I reviewed and approve closing this shift.") }}</span>
						</label>
					</div>
				</template>

				<!-- ══════════════════════════════════════════
				     REVIEW / REPORT MODE
				     ══════════════════════════════════════════ -->
				<template v-else>

					<!-- Success bar -->
					<div v-if="showSuccessReport" class="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-2.5">
						<FeatherIcon name="check-circle" class="w-4 h-4 text-green-600 flex-shrink-0" />
						<p class="text-sm font-semibold text-green-800">{{ __("Shift closed successfully") }}</p>
					</div>

					<!-- KPI strip -->
					<div v-if="shouldShowSummary" class="grid grid-cols-4 gap-2">
						<div class="bg-blue-50 border border-blue-100 rounded-xl px-3 py-2 text-center">
							<p class="text-xs text-blue-500 font-medium leading-none mb-1">{{ __("Gross") }}</p>
							<p class="text-sm font-bold text-blue-900 tabular-nums">{{ formatCurrency(grossSales) }}</p>
							<p class="text-xs text-blue-400 mt-0.5 leading-none">{{ closingData.sales_count || salesInvoiceCount }} {{ __("inv.") }}</p>
						</div>
						<div v-if="hasReturns" class="bg-red-50 border border-red-100 rounded-xl px-3 py-2 text-center">
							<p class="text-xs text-red-500 font-medium leading-none mb-1">{{ __("Returns") }}</p>
							<p class="text-sm font-bold text-red-800 tabular-nums">-{{ formatCurrency(closingData.returns_total) }}</p>
							<p class="text-xs text-red-400 mt-0.5 leading-none">{{ closingData.returns_count }}</p>
						</div>
						<div :class="['bg-green-50 border border-green-100 rounded-xl px-3 py-2 text-center', !hasReturns ? 'col-span-2' : '']">
							<p class="text-xs text-green-600 font-medium leading-none mb-1">{{ __("Net Sales") }}</p>
							<p class="text-sm font-bold text-green-900 tabular-nums">{{ formatCurrency(closingData.grand_total) }}</p>
							<p class="text-xs text-green-400 mt-0.5 leading-none">{{ __("after returns") }}</p>
						</div>
						<div class="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-center">
							<p class="text-xs text-gray-500 font-medium leading-none mb-1">{{ __("Tax") }}</p>
							<p class="text-sm font-bold text-gray-900 tabular-nums">{{ formatCurrency(totalTax) }}</p>
							<p class="text-xs text-gray-400 mt-0.5 leading-none">{{ __("collected") }}</p>
						</div>
					</div>

					<!-- No sales -->
					<div v-if="invoiceCount === 0" class="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-3 py-2">
						<FeatherIcon name="info" class="w-3.5 h-3.5 text-yellow-600 flex-shrink-0" />
						<p class="text-xs text-yellow-800">{{ __("No invoices this shift — closing amounts should match opening amounts.") }}</p>
					</div>

					<!-- ── Payment Reconciliation ── -->
					<div class="border border-gray-200 rounded-xl overflow-hidden">
						<div class="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
							<p class="text-sm font-bold text-gray-800">{{ __("Payment Reconciliation") }}</p>
							<div v-if="shouldShowSummary">
								<span v-if="getTotalDifference !== 0" :class="['text-xs font-bold tabular-nums', getTotalDifference > 0 ? 'text-blue-600' : 'text-red-600']">
									{{ getTotalDifference > 0 ? "+" : "" }}{{ formatCurrency(getTotalDifference) }} {{ __("variance") }}
								</span>
								<span v-else class="text-xs font-semibold text-green-600">✓ {{ __("Balanced") }}</span>
							</div>
						</div>

						<!-- Active rows -->
						<div class="divide-y divide-gray-100">
							<div
								v-for="(payment, idx) in activeMethods"
								:key="idx"
								class="flex items-center gap-3 px-4 py-2.5 bg-white"
							>
								<div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0', getPaymentIcon(payment.mode_of_payment).color]">
									{{ getPaymentIcon(payment.mode_of_payment).icon }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-gray-900 truncate">{{ payment.mode_of_payment }}</p>
									<p class="text-xs text-gray-400 leading-none mt-0.5">
										{{ __("Opening {0} · Expected {1}", [formatCurrency(payment.opening_amount), formatCurrency(payment.expected_amount)]) }}
									</p>
								</div>
								<!-- Negative expected -->
								<span v-if="isNegativeExpected(payment)" class="text-xs font-semibold bg-amber-100 text-amber-700 px-2 py-1 rounded-lg flex-shrink-0">
									{{ __("Disbursed: {0}", [formatCurrency(Math.abs(payment.expected_amount))]) }}
								</span>
								<!-- Normal input -->
								<template v-else>
									<div class="w-28 flex-shrink-0">
										<Input
											:modelValue="payment.closing_amount"
											@update:modelValue="(v) => updateClosingAmount(payment, v)"
											type="number" step="0.01" min="0" placeholder="0.00"
											:disabled="showSuccessReport || submitResource.loading"
											class="text-sm text-center"
										/>
									</div>
									<div class="w-20 text-end flex-shrink-0">
										<span
											v-if="payment.closing_amount !== null && payment.closing_amount !== undefined"
											:class="[
												'px-2 py-0.5 rounded-full text-xs font-bold',
												payment.difference === 0 ? 'bg-green-100 text-green-700'
												: payment.difference > 0 ? 'bg-blue-100 text-blue-700'
												: 'bg-red-100 text-red-700',
											]"
										>
											{{
												payment.difference === 0 ? "✓"
												: (payment.difference > 0 ? "+" : "") + formatCurrency(payment.difference)
											}}
										</span>
									</div>
								</template>
							</div>
						</div>

						<!-- "Show unused" toggle row -->
						<button
							v-if="unusedMethodsCount > 0"
							@click="showAllMethods = !showAllMethods"
							class="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 transition-colors border-t border-gray-100"
						>
							<span class="text-xs text-gray-500">
								{{ showAllMethods ? __("Hide {0} unused methods", [unusedMethodsCount]) : __("+ {0} unused methods (0.00 each)", [unusedMethodsCount]) }}
							</span>
							<FeatherIcon :name="showAllMethods ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5 text-gray-400" />
						</button>

						<!-- Unused methods (expanded) -->
						<div v-if="showAllMethods" class="divide-y divide-gray-100 border-t border-gray-100">
							<div
								v-for="(payment, idx) in unusedMethods"
								:key="`unused-${idx}`"
								class="flex items-center gap-3 px-4 py-2.5 bg-gray-50 opacity-75"
							>
								<div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0', getPaymentIcon(payment.mode_of_payment).color]">
									{{ getPaymentIcon(payment.mode_of_payment).icon }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-gray-500 truncate">{{ payment.mode_of_payment }}</p>
									<p class="text-xs text-gray-400 leading-none mt-0.5">{{ __("No activity this shift") }}</p>
								</div>
								<div class="w-28 flex-shrink-0">
									<Input
										:modelValue="payment.closing_amount"
										@update:modelValue="(v) => updateClosingAmount(payment, v)"
										type="number" step="0.01" min="0" placeholder="0.00"
										:disabled="showSuccessReport || submitResource.loading"
										class="text-sm text-center"
									/>
								</div>
								<div class="w-20 text-end flex-shrink-0">
									<span
										v-if="payment.closing_amount !== null && payment.closing_amount !== undefined && Number(payment.closing_amount) !== 0"
										class="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-700"
									>
										{{ formatCurrency(payment.closing_amount) }}
									</span>
									<span v-else class="text-xs text-gray-400">—</span>
								</div>
							</div>
						</div>

						<!-- Totals footer -->
						<div v-if="shouldShowSummary" class="grid grid-cols-3 border-t border-gray-200 bg-gray-50 divide-x divide-gray-200 text-center">
							<div class="px-3 py-2">
								<p class="text-xs text-gray-400 leading-none mb-1">{{ __("Expected") }}</p>
								<p class="text-sm font-bold text-gray-900 tabular-nums">{{ formatCurrency(getTotalExpected) }}</p>
							</div>
							<div class="px-3 py-2">
								<p class="text-xs text-gray-400 leading-none mb-1">{{ __("Actual") }}</p>
								<p class="text-sm font-bold text-gray-900 tabular-nums">{{ formatCurrency(getTotalActual) }}</p>
							</div>
							<div class="px-3 py-2">
								<p class="text-xs text-gray-400 leading-none mb-1">{{ __("Variance") }}</p>
								<p :class="['text-sm font-bold tabular-nums', getTotalDifference === 0 ? 'text-green-600' : getTotalDifference > 0 ? 'text-blue-600' : 'text-red-600']">
									{{ getTotalDifference === 0 ? "✓ 0.00" : (getTotalDifference > 0 ? "+" : "") + formatCurrency(getTotalDifference) }}
								</p>
							</div>
						</div>
					</div>

					<!-- Variance confirmation -->
					<div v-if="hasUnconfirmedVariance" class="flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 px-4 py-2.5">
						<FeatherIcon name="alert-triangle" class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
						<label class="flex cursor-pointer items-start gap-2">
							<input v-model="varianceConfirmed" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-amber-400" />
							<span class="text-xs text-amber-900">{{ __("Variance detected — I reviewed and approve closing this shift.") }}</span>
						</label>
					</div>

					<!-- Post cash variance to accounting (optional, capped) -->
					<div v-if="!showSuccessReport && combinedAbsoluteVariance >= 0.005" class="flex items-start gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5">
						<FeatherIcon name="file-text" class="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
						<label class="flex cursor-pointer items-start gap-2">
							<input v-model="postVariance" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-blue-400" />
							<span class="text-xs text-blue-900">{{ __("Post cash variances within the allowed cap to accounting.") }}</span>
						</label>
					</div>

					<!-- Cash variance posting result -->
					<div v-if="variancePostResult" class="flex items-start gap-2 rounded-xl border px-4 py-2.5"
						:class="variancePostResult.posted ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'">
						<FeatherIcon :name="variancePostResult.posted ? 'check-circle' : 'alert-circle'"
							class="w-4 h-4 flex-shrink-0 mt-0.5" :class="variancePostResult.posted ? 'text-green-600' : 'text-amber-600'" />
						<div class="text-xs" :class="variancePostResult.posted ? 'text-green-900' : 'text-amber-900'">
							<p v-if="variancePostResult.posted">
								{{ __("Cash variance posted: {0}", [variancePostResult.journal_entry]) }}
							</p>
							<p v-else-if="variancePostResult.reason === 'over_cap'">
								{{ __("Not posted — combined variance {0} exceeds the allowed cap {1}.", [formatCurrency(variancePostResult.combined_total), formatCurrency(variancePostResult.max_variance)]) }}
							</p>
							<p v-else-if="variancePostResult.reason === 'nothing_postable'">
								{{ __("Not posted — no account is configured (cashier shortage account or surplus account).") }}
							</p>
							<p v-else>
								{{ __("Cash variance could not be posted. It can still be handled manually.") }}
							</p>
						</div>
					</div>

					<!-- Returns disbursed note -->
					<div v-if="getTotalReturnsDisbursed > 0" class="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
						<FeatherIcon name="info" class="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
						<p class="text-xs text-amber-800">
							{{ __("Cash disbursed for returns:") }} <span class="font-bold ms-1">{{ formatCurrency(getTotalReturnsDisbursed) }}</span>
						</p>
					</div>

					<!-- ── Transactions (collapsible) ── -->
					<div v-if="invoiceCount > 0 && shouldShowSummary" class="border border-gray-200 rounded-xl overflow-hidden">
						<button @click="showInvoiceDetails = !showInvoiceDetails" :aria-expanded="showInvoiceDetails"
							class="w-full flex items-center justify-between px-4 py-2.5 bg-white hover:bg-gray-50 transition-colors">
							<span class="text-sm font-semibold text-gray-700">
								{{ __("Transactions") }}
								<span class="ms-2 text-gray-400 font-normal text-xs">{{ invoiceCount }} · {{ formatCurrency(closingData.grand_total) }}</span>
							</span>
							<FeatherIcon :name="showInvoiceDetails ? 'chevron-up' : 'chevron-down'" class="w-4 h-4 text-gray-400" />
						</button>
						<div v-show="showInvoiceDetails" class="border-t border-gray-100 max-h-52 overflow-y-auto">
							<table class="min-w-full divide-y divide-gray-100 text-sm">
								<thead class="bg-gray-50 sticky top-0">
									<tr>
										<th class="px-4 py-2 text-start text-xs font-semibold text-gray-500 uppercase">{{ __("Invoice") }}</th>
										<th class="px-4 py-2 text-start text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">{{ __("Customer") }}</th>
										<th class="px-4 py-2 text-start text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">{{ __("Time") }}</th>
										<th class="px-4 py-2 text-end text-xs font-semibold text-gray-500 uppercase">{{ __("Amount") }}</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-100 bg-white">
									<tr v-for="(inv, i) in closingData.pos_transactions" :key="i"
										:class="inv.is_return ? 'bg-red-50' : 'hover:bg-gray-50'">
										<td class="px-4 py-2">
											<span :class="['text-xs font-medium', inv.is_return ? 'text-red-700' : 'text-gray-900']">
												{{ inv.pos_invoice || inv.sales_invoice || __("N/A") }}
											</span>
											<span v-if="inv.is_return" class="ms-1 px-1 py-0.5 text-xs bg-red-100 text-red-700 rounded">{{ __("Ret.") }}</span>
										</td>
										<td class="px-4 py-2 text-xs text-gray-500 hidden sm:table-cell truncate max-w-xs">{{ inv.customer }}</td>
										<td class="px-4 py-2 text-xs text-gray-400 tabular-nums hidden sm:table-cell">{{ formatTime(inv.posting_date) }}</td>
										<td :class="['px-4 py-2 text-end text-xs font-bold tabular-nums', inv.is_return ? 'text-red-700' : 'text-gray-900']">
											{{ formatCurrency(inv.grand_total) }}
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>

					<!-- ── Tax Summary (collapsible) ── -->
					<div v-if="shouldShowSummary && closingData.taxes && closingData.taxes.length > 0" class="border border-gray-200 rounded-xl overflow-hidden">
						<button @click="showTaxDetails = !showTaxDetails" :aria-expanded="showTaxDetails"
							class="w-full flex items-center justify-between px-4 py-2.5 bg-white hover:bg-gray-50 transition-colors">
							<span class="text-sm font-semibold text-gray-700">
								{{ __("Tax Summary") }}
								<span class="ms-2 text-gray-400 font-normal text-xs">{{ formatCurrency(totalTax) }}</span>
							</span>
							<FeatherIcon :name="showTaxDetails ? 'chevron-up' : 'chevron-down'" class="w-4 h-4 text-gray-400" />
						</button>
						<div v-show="showTaxDetails" class="border-t border-gray-100 divide-y divide-gray-100">
							<div v-for="(tax, i) in closingData.taxes" :key="i" class="flex items-center justify-between px-4 py-2">
								<div>
									<p class="text-xs font-medium text-gray-800">{{ tax.account_head }}</p>
									<p class="text-xs text-gray-400">{{ formatQuantity(tax.rate) }}%</p>
								</div>
								<p class="text-sm font-bold text-gray-900 tabular-nums">{{ formatCurrency(tax.amount) }}</p>
							</div>
						</div>
					</div>
				</template>

				<!-- Submit error -->
				<div v-if="submitResource.error || (errorMessage && !closingDataResource.error)" class="flex items-start gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3">
					<FeatherIcon name="alert-circle" class="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
					<div class="flex-1">
						<p class="text-sm font-semibold text-red-800">{{ __("Error Closing Shift") }}</p>
						<p class="text-xs text-red-600 mt-0.5">{{ errorMessage || submitResource.error }}</p>
						<button v-if="errorMessage" @click="errorMessage = ''" class="mt-1 text-xs text-red-500 underline">{{ __("Dismiss") }}</button>
					</div>
				</div>

			</div>
		</template>

		<!-- ── ACTIONS BAR ── -->
		<template #actions>
			<div class="flex items-center justify-between w-full gap-3">
				<Button variant="subtle" @click="closeDialog" :disabled="submitResource.loading">
					{{ showSuccessReport ? __("Close") : __("Cancel") }}
				</Button>
				<div class="flex items-center gap-2.5 flex-wrap justify-end">
					<p v-if="!canSubmit && closingData && !showSuccessReport" class="text-xs text-amber-600 font-medium">
						{{ hasUnconfirmedVariance ? __("Confirm variance first") : __("Enter all amounts first") }}
					</p>
					<p v-if="showSuccessReport" class="text-xs text-green-600 font-semibold">{{ __("✓ Shift closed") }}</p>
					<p v-if="eodPrintFailed" class="text-xs text-amber-600">{{ __("Print is optional — you can finish without printing.") }}</p>
					<Button v-if="showSuccessReport && closingShiftName" variant="subtle" theme="blue" @click="printEOD" :loading="printLoading">
						{{ printLoading ? __("Printing...") : __("Print EOD Report") }}
					</Button>
					<Button v-if="showSuccessReport" variant="solid" theme="green" @click="closeDialog">
						{{ __("Finish") }}
					</Button>
					<Button v-if="!showSuccessReport" variant="solid" theme="blue" @click="submitClosing" :loading="submitResource.loading" :disabled="!canSubmit">
						{{ submitResource.loading ? __("Closing...") : __("Close Shift") }}
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog, FeatherIcon, Input } from "frappe-ui";
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useShift, shiftState } from "../composables/useShift";
import { useFormatters } from "../composables/useFormatters";
import { useToast } from "../composables/useToast";
import { usePOSSettingsStore } from "../stores/posSettings";
import { usePOSShiftStore } from "../stores/posShift";
import { printEODReport } from "../utils/printEod";
import { useUserData } from "@/data/user";

const props = defineProps({
	modelValue: { type: Boolean, required: true },
	openingShift: { type: String, required: true, validator: (v) => v && v.length > 0 },
});
const emit = defineEmits(["update:modelValue", "shift-closed"]);

const open = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
});

const { getClosingShiftData, submitClosingShift, postCashVariance } = useShift();
const { formatCurrency, formatQuantity, formatDateTime, formatTime } = useFormatters();
const { showSuccess } = useToast();
const { userName } = useUserData();
const posSettingsStore = usePOSSettingsStore();
const { hideExpectedAmount } = storeToRefs(posSettingsStore);
const shiftStore = usePOSShiftStore();

const closingData        = ref(null);
const closingDataResource = getClosingShiftData;
const submitResource     = submitClosingShift;
const showInvoiceDetails = ref(false);
const showTaxDetails     = ref(false);
const showAllMethods     = ref(false);   // ← toggle for unused payment methods
const showSuccessReport  = ref(false);
const errorMessage       = ref("");
const eodPrintFailed     = ref(null);
const closingShiftName   = ref(null);
const printLoading       = ref(false);
const showIdleWarning    = ref(false);
const varianceConfirmed  = ref(false);
const postVariance       = ref(false);
const variancePostResult = ref(null);
let _idleWarningTimer    = null;

watch(open, async (isOpen) => {
	if (isOpen && props.openingShift) {
		shiftStore.shiftTimerPaused = true;
		showIdleWarning.value = false;
		showAllMethods.value = false;
		postVariance.value = false;
		variancePostResult.value = null;
		_idleWarningTimer = setTimeout(() => { showIdleWarning.value = true; }, 60_000);
		await posSettingsStore.reloadSettings();
		loadClosingData();
	} else {
		shiftStore.shiftTimerPaused = false;
		showIdleWarning.value = false;
		if (_idleWarningTimer) { clearTimeout(_idleWarningTimer); _idleWarningTimer = null; }
		eodPrintFailed.value = null;
		closingShiftName.value = null;
	}
});

onBeforeUnmount(() => {
	shiftStore.shiftTimerPaused = false;
	if (_idleWarningTimer) { clearTimeout(_idleWarningTimer); _idleWarningTimer = null; }
});

async function loadClosingData() {
	try {
		errorMessage.value = "";
		varianceConfirmed.value = false;

		const data = await closingDataResource.submit({ opening_shift: props.openingShift });

		if (data.payment_reconciliation) {
			data.payment_reconciliation = data.payment_reconciliation.map((payment) => {
				const noBalance = hasNoExpectedBalance(payment);
				const negExp   = Number.parseFloat(payment.expected_amount) < -0.005;
				return reactive({
					...payment,
					closing_amount: payment.closing_amount ?? (noBalance || negExp ? 0 : null),
					difference: 0,
					_touched: noBalance || negExp,
				});
			});
			data.payment_reconciliation.forEach((p) => calculateDifference(p));
		}

		closingData.value   = data;
		showInvoiceDetails.value = false;
		showTaxDetails.value     = false;
	} catch (error) {
		console.error("Error loading closing data:", error);
		errorMessage.value = __("Unable to load shift data. Please check your connection and try again.");
	}
}

function hasNoExpectedBalance(payment) {
	const opening  = Number.parseFloat(payment.opening_amount) || 0;
	const expected = Number.parseFloat(payment.expected_amount) || 0;
	return Math.abs(opening) < 0.005 && Math.abs(expected) < 0.005;
}

function isNegativeExpected(payment) {
	return Number.parseFloat(payment.expected_amount) < -0.005;
}

function calculateDifference(payment) {
	const closing   = Number.parseFloat(payment.closing_amount) || 0;
	const effective = isNegativeExpected(payment) ? 0 : Number.parseFloat(payment.expected_amount) || 0;
	payment.difference = closing - effective;
}

function updateClosingAmount(payment, value) {
	payment.closing_amount = value;
	payment._touched = true;
	varianceConfirmed.value = false;
	calculateDifference(payment);
}

// ── Derived payment method lists ─────────────────────────
/** Methods with actual activity this shift (show by default). */
const activeMethods = computed(() => {
	if (!closingData.value?.payment_reconciliation) return [];
	return closingData.value.payment_reconciliation.filter(
		(p) => !hasNoExpectedBalance(p)
	);
});

/** Methods with zero opening AND zero expected (truly unused). */
const unusedMethods = computed(() => {
	if (!closingData.value?.payment_reconciliation) return [];
	return closingData.value.payment_reconciliation.filter(
		(p) => hasNoExpectedBalance(p) && !isNegativeExpected(p)
	);
});

const unusedMethodsCount = computed(() => unusedMethods.value.length);

// ── Validation ────────────────────────────────────────────
const allRequiredAmountsEntered = computed(() => {
	if (!closingData.value?.payment_reconciliation) return false;
	return closingData.value.payment_reconciliation.every(
		(p) =>
			hasNoExpectedBalance(p) ||
			(p._touched && p.closing_amount !== null && p.closing_amount !== undefined && p.closing_amount !== "")
	);
});

const hasUnconfirmedVariance = computed(
	() => allRequiredAmountsEntered.value && Math.abs(getTotalDifference.value) >= 0.005 && !varianceConfirmed.value
);

const canSubmit = computed(() => allRequiredAmountsEntered.value && !hasUnconfirmedVariance.value);

// ── Submit ────────────────────────────────────────────────
async function submitClosing() {
	if (!closingData.value) return;
	try {
		errorMessage.value = "";
		closingData.value.payment_reconciliation?.forEach((p) => calculateDifference(p));
		const result = await submitResource.submit({ closing_shift: closingData.value });
		closingShiftName.value = result?.name ?? submitResource.data?.name ?? null;
		// Keep the report visible after submission. Printing is an explicit,
		// optional action and must never block finishing or signing out.
		showSuccessReport.value = true;

		// Posting the cash variance is best-effort and happens after the shift is
		// already safely closed — a failure here must never look like the shift
		// itself failed to close.
		if (postVariance.value && closingShiftName.value) {
			try {
				variancePostResult.value = await postCashVariance.submit({
					closing_shift: closingShiftName.value,
				});
			} catch (varianceError) {
				console.error("Error posting cash variance:", varianceError);
				variancePostResult.value = { posted: false, reason: "error" };
			}
		}
	} catch (error) {
		console.error("Error submitting closing shift:", error);
		errorMessage.value = __("Failed to close shift. Please verify all amounts and try again.");
	}
}

async function printEOD() {
	if (!closingShiftName.value || printLoading.value) return;
	printLoading.value = true;
	eodPrintFailed.value = null;
	try {
		await printEODReport(closingShiftName.value);
		eodPrintFailed.value = null;
		showSuccess(__("EOD report printed successfully"));
	} catch (err) {
		console.warn("[eod] retry print failed", err);
		eodPrintFailed.value = { closingShiftName: closingShiftName.value };
	} finally {
		printLoading.value = false;
	}
}

function closeDialog() {
	if (showSuccessReport.value) emit("shift-closed");
	open.value           = false;
	closingData.value    = null;
	showInvoiceDetails.value = false;
	showTaxDetails.value     = false;
	showAllMethods.value     = false;
	showSuccessReport.value  = false;
	errorMessage.value       = "";
	eodPrintFailed.value     = null;
	closingShiftName.value   = null;
	printLoading.value       = false;
	postVariance.value       = false;
	variancePostResult.value = null;
}

// ── UI State ──────────────────────────────────────────────
const shouldShowSummary = computed(() => !hideExpectedAmount.value || showSuccessReport.value);
const isInEntryMode     = computed(() => hideExpectedAmount.value && !showSuccessReport.value);

const invoiceCount = computed(() => (closingData.value?.pos_transactions || []).length);
const hasReturns   = computed(() => (closingData.value?.returns_count || 0) > 0);

const salesInvoiceCount = computed(() =>
	(closingData.value?.pos_transactions || []).filter((t) => !t.is_return).length
);

const totalTax = computed(() =>
	(closingData.value?.taxes || []).reduce((s, t) => s + Number.parseFloat(t.amount || 0), 0)
);

const grossSales = computed(() =>
	closingData.value ? (closingData.value.sales_total ?? closingData.value.grand_total ?? 0) : 0
);

const getTotalExpected = computed(() => {
	if (!closingData.value?.payment_reconciliation) return 0;
	return closingData.value.payment_reconciliation.reduce((sum, p) => {
		const exp = Number.parseFloat(p.expected_amount || 0);
		return sum + (exp < -0.005 ? 0 : exp);
	}, 0);
});

const getTotalActual = computed(() => {
	if (!closingData.value?.payment_reconciliation) return 0;
	return closingData.value.payment_reconciliation.reduce((sum, p) => {
		if (Number.parseFloat(p.expected_amount) < -0.005) return sum;
		return sum + Number.parseFloat(p.closing_amount || 0);
	}, 0);
});

const getTotalDifference = computed(() => getTotalActual.value - getTotalExpected.value);

// Sum of the ABSOLUTE difference per payment method — a Cash shortage and a Card surplus
// don't cancel out here the way they do in getTotalDifference's net total. This matches the
// backend's combined-cap check for posting cash variances (post_cash_variance in
// pos_closing_shift.py), which is checked against this same sum, not the net total.
const combinedAbsoluteVariance = computed(() => {
	if (!closingData.value?.payment_reconciliation) return 0;
	return closingData.value.payment_reconciliation.reduce(
		(sum, p) => sum + Math.abs(Number.parseFloat(p.difference) || 0),
		0
	);
});

const getTotalReturnsDisbursed = computed(() => {
	if (!closingData.value?.payment_reconciliation) return 0;
	return closingData.value.payment_reconciliation.reduce((sum, p) => {
		const exp = Number.parseFloat(p.expected_amount || 0);
		return exp < -0.005 ? sum + Math.abs(exp) : sum;
	}, 0);
});

function getShiftDuration() {
	if (!closingData.value?.period_start_date) return __("N/A");
	const { _initialElapsedMs, _receivedAt } = shiftState.value;
	const diff = _initialElapsedMs + (Date.now() - (_receivedAt || Date.now()));
	if (diff < 0) return __("N/A");
	const days    = Math.floor(diff / 86400000);
	const hours   = Math.floor((diff % 86400000) / 3600000);
	const minutes = Math.floor((diff % 3600000) / 60000);
	if (days > 0)  return __("{0}d {1}h {2}m", [days, hours, minutes]);
	if (hours > 0) return __("{0}h {1}m", [hours, minutes]);
	return __("{0}m", [minutes]);
}

function getPaymentIcon(method) {
	const m = String(method || "").toLowerCase();
	if (m.includes("cash"))                                                    return { icon: "💵", color: "bg-green-500" };
	if (m.includes("card") || m.includes("credit") || m.includes("debit"))    return { icon: "💳", color: "bg-blue-500" };
	if (m.includes("mobile") || m.includes("wallet") || m.includes("phone"))  return { icon: "📱", color: "bg-purple-500" };
	if (m.includes("bank") || m.includes("transfer"))                          return { icon: "🏦", color: "bg-indigo-500" };
	if (m.includes("cheque") || m.includes("check"))                           return { icon: "📝", color: "bg-yellow-500" };
	return { icon: "💰", color: "bg-gray-500" };
}
</script>
