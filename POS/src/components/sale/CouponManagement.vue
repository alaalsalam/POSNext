<template>
	<!-- Split Layout matching PromotionManagement -->
	<div class="flex-1 flex overflow-hidden">
		<!-- LEFT SIDE: Coupon List & Navigation -->
		<div class="w-80 flex-shrink-0 border-e bg-gray-50 flex flex-col">
			<!-- Search & Filter -->
			<div class="p-4 bg-white border-b flex flex-col gap-3">
				<FormControl
					type="text"
					v-model="searchQuery"
					:placeholder="__('Search coupons...')"
				>
					<template #prefix>
						<FeatherIcon name="search" class="w-4 h-4 text-gray-500" />
					</template>
				</FormControl>

				<div class="grid grid-cols-2 gap-2">
					<select v-model="filterStatus"
						class="w-full h-8 px-2 rounded-lg border border-gray-200 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400">
						<option value="all">{{ __("All Status") }}</option>
						<option value="active">{{ __("Active") }}</option>
						<option value="expired">{{ __("Expired") }}</option>
						<option value="not_started">{{ __("Not Started") }}</option>
						<option value="exhausted">{{ __("Exhausted") }}</option>
						<option value="disabled">{{ __("Disabled") }}</option>
					</select>
					<select v-model="filterType"
						class="w-full h-8 px-2 rounded-lg border border-gray-200 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400">
						<option value="all">{{ __("All Types") }}</option>
						<option value="Promotional">{{ __("Promotional") }}</option>
						<option value="Gift Card">{{ __("Gift Card") }}</option>
					</select>
				</div>
			</div>

			<!-- Create New Button -->
			<div class="p-4 bg-white border-b flex flex-col gap-2">
				<Button
					v-if="permissions.create"
					@click="handleCreateNew"
					variant="solid"
					class="w-full"
				>
					<template #prefix>
						<FeatherIcon name="plus-circle" class="w-4 h-4" />
					</template>
					{{ __("Create New Coupon") }}
				</Button>
				<Button @click="loadCoupons" variant="outline" class="w-full" :loading="loading">
					<template #prefix>
						<FeatherIcon name="refresh-cw" class="w-4 h-4" />
					</template>
					{{ __("Refresh") }}
				</Button>
			</div>

			<!-- Coupons List -->
			<div class="flex-1 overflow-y-auto">
				<!-- Loading State -->
				<div
					v-if="loading && coupons.length === 0"
					class="flex items-center justify-center py-12"
				>
					<div class="text-center">
						<LoadingIndicator class="w-6 h-6 mx-auto mb-2" />
						<p class="text-sm text-gray-600">{{ __("Loading...") }}</p>
					</div>
				</div>

				<!-- Empty State -->
				<div v-else-if="filteredCoupons.length === 0" class="text-center py-12 px-4">
					<div class="text-gray-400 mb-3">
						<FeatherIcon name="gift" class="w-12 h-12 mx-auto" />
					</div>
					<p class="text-sm text-gray-600">{{ __("No coupons found") }}</p>
				</div>

				<!-- Coupon Items -->
				<div v-else class="p-2 flex flex-col gap-1">
					<button
						v-for="coupon in filteredCoupons"
						:key="coupon.name"
						@click="handleSelectCoupon(coupon)"
						:class="[
							'w-full text-start p-3 rounded-md transition-all',
							selectedCoupon?.name === coupon.name
								? 'bg-blue-50 ring-2 ring-blue-500 ring-inset'
								: 'hover:bg-gray-100',
						]"
					>
						<div class="flex items-start justify-between mb-2">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2">
									<p
										:class="[
											'text-sm font-medium truncate',
											selectedCoupon?.name === coupon.name
												? 'text-blue-900'
												: 'text-gray-900',
										]"
									>
										{{ coupon.coupon_code }}
									</p>
									<Badge
										v-if="coupon.coupon_type === 'Gift Card'"
										variant="subtle"
										theme="purple"
										size="sm"
									>
										{{ __("Gift") }}
									</Badge>
								</div>
								<p class="text-xs text-gray-500 mt-0.5 truncate">
									{{ coupon.coupon_name }}
								</p>
							</div>
							<Badge
								variant="subtle"
								:theme="getStatusTheme(coupon.status)"
								size="sm"
							>
								{{ coupon.status || __("Active") }}
							</Badge>
						</div>
						<div class="flex items-center justify-between text-xs">
							<span class="text-gray-500">
								{{
									coupon.maximum_use
										? __("Used: {0}/{1}", [coupon.used, coupon.maximum_use])
										: __("Used: {0}", [coupon.used])
								}}
							</span>
							<span class="text-gray-500">
								{{
									coupon.valid_upto
										? formatDate(coupon.valid_upto)
										: __("No expiry")
								}}
							</span>
						</div>
					</button>
				</div>
			</div>
		</div>

		<!-- RIGHT SIDE: Work Area -->
		<div class="flex-1 overflow-y-auto bg-white">

		  <!-- Empty State: No Selection -->
		  <div v-if="!selectedCoupon && !isCreating" class="flex items-center justify-center h-full">
		    <div class="text-center px-8 max-w-md">
		      <div class="w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
		        <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
		          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/>
		        </svg>
		      </div>
		      <h3 class="text-lg font-bold text-gray-900 mb-2">{{ __("Select a Coupon") }}</h3>
		      <p class="text-sm text-gray-500 mb-6">{{ __("Choose a coupon from the list, or create a new one") }}</p>
		      <button v-if="permissions.create" @click="handleCreateNew"
		        class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors">
		        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
		          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
		        </svg>
		        {{ __("Create New Coupon") }}
		      </button>
		    </div>
		  </div>

		  <!-- CREATE / EDIT FORM -->
		  <div v-else class="p-6 max-w-2xl mx-auto flex flex-col gap-5">

		    <!-- Header + Action Buttons -->
		    <div class="flex items-start justify-between pb-4 border-b border-gray-100">
		      <div>
		        <h3 class="text-lg font-bold text-gray-900">
		          {{ isCreating ? __("Create New Coupon") : __("Coupon Details") }}
		        </h3>
		        <p class="text-sm text-gray-500 mt-0.5">
		          {{ isCreating ? __("Fill in the details to create a coupon") : __("View and edit coupon information") }}
		        </p>
		      </div>
		      <div class="flex items-center gap-2 flex-shrink-0">
		        <button v-if="!isCreating && permissions.write" @click="handleToggle"
		          :class="['px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors',
		            couponDetails.disabled
		              ? 'border-green-200 text-green-700 hover:bg-green-50'
		              : 'border-orange-200 text-orange-700 hover:bg-orange-50']">
		          {{ couponDetails.disabled ? __("Enable") : __("Disable") }}
		        </button>
		        <button v-if="!isCreating && permissions.delete && selectedCoupon.used === 0"
		          @click="handleDelete"
		          class="px-3 py-1.5 text-xs font-semibold rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors">
		          {{ __("Delete") }}
		        </button>
		        <button @click="handleCancel"
		          class="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors">
		          {{ __("Cancel") }}
		        </button>
		        <button v-if="isCreating ? permissions.create : permissions.write"
		          @click="handleSubmit" :disabled="loading"
		          class="px-4 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5">
		          <div v-if="loading" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"/>
		          {{ isCreating ? __("Create Coupon") : __("Save Changes") }}
		        </button>
		      </div>
		    </div>

		    <!-- ① COUPON TYPE (create mode only) — big visual cards -->
		    <div v-if="isCreating">
		      <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">
		        {{ __("Coupon Type") }} <span class="text-red-500">*</span>
		      </p>
		      <div class="grid grid-cols-2 gap-3">
		        <button @click="form.coupon_type = 'Promotional'"
		          :class="['p-4 rounded-xl border-2 text-start transition-all',
		            form.coupon_type === 'Promotional'
		              ? 'border-blue-500 bg-blue-50'
		              : 'border-gray-200 hover:border-gray-300 bg-white']">
		          <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
		            :class="form.coupon_type === 'Promotional' ? 'bg-blue-100' : 'bg-gray-100'">
		            <svg class="w-5 h-5" :class="form.coupon_type === 'Promotional' ? 'text-blue-600' : 'text-gray-500'"
		              fill="none" stroke="currentColor" viewBox="0 0 24 24">
		              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
		                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
		            </svg>
		          </div>
		          <p class="text-sm font-bold" :class="form.coupon_type === 'Promotional' ? 'text-blue-900' : 'text-gray-900'">
		            {{ __("Promotional") }}
		          </p>
		          <p class="text-xs text-gray-500 mt-1">{{ __("Shared publicly, usable by many customers") }}</p>
		        </button>
		        <button @click="form.coupon_type = 'Gift Card'"
		          :class="['p-4 rounded-xl border-2 text-start transition-all',
		            form.coupon_type === 'Gift Card'
		              ? 'border-purple-500 bg-purple-50'
		              : 'border-gray-200 hover:border-gray-300 bg-white']">
		          <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
		            :class="form.coupon_type === 'Gift Card' ? 'bg-purple-100' : 'bg-gray-100'">
		            <svg class="w-5 h-5" :class="form.coupon_type === 'Gift Card' ? 'text-purple-600' : 'text-gray-500'"
		              fill="none" stroke="currentColor" viewBox="0 0 24 24">
		              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
		                d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/>
		            </svg>
		          </div>
		          <p class="text-sm font-bold" :class="form.coupon_type === 'Gift Card' ? 'text-purple-900' : 'text-gray-900'">
		            {{ __("Gift Card") }}
		          </p>
		          <p class="text-xs text-gray-500 mt-1">{{ __("Assigned to one specific customer only") }}</p>
		        </button>
		      </div>
		    </div>

		    <!-- Type badge (view mode) -->
		    <div v-if="!isCreating" class="flex items-center gap-2">
		      <span :class="['px-3 py-1 rounded-full text-xs font-bold',
		        couponDetails.coupon_type === 'Gift Card' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700']">
		        {{ couponDetails.coupon_type }}
		      </span>
		      <span :class="['px-3 py-1 rounded-full text-xs font-bold',
		        selectedCoupon.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600']">
		        {{ selectedCoupon.status }}
		      </span>
		      <code class="ms-auto text-sm font-mono bg-gray-100 px-2 py-1 rounded text-gray-700">
		        {{ couponDetails.coupon_code }}
		      </code>
		    </div>

		    <!-- ② CUSTOMER (Gift Card only) -->
		    <div v-if="form.coupon_type === 'Gift Card'">
		      <label class="block text-xs font-semibold text-gray-700 mb-1.5">
		        {{ __("Customer") }} <span class="text-red-500">*</span>
		      </label>
		      <div v-if="isCreating">
		        <AutocompleteSelect
		          v-model="form.customer"
		          :options="customerOptions"
		          :loading="customerLoading"
		          :placeholder="__('Search customer by name or mobile...')"
		          @search="handleCustomerSearch"
		        />
		      </div>
		      <div v-else class="px-3 py-2.5 bg-purple-50 border border-purple-100 rounded-lg">
		        <p class="text-sm font-semibold text-purple-900">{{ couponDetails.customer_name || couponDetails.customer }}</p>
		        <p class="text-xs text-purple-600">{{ couponDetails.customer }}</p>
		      </div>
		    </div>

		    <!-- ③ BASIC INFO -->
		    <div class="flex flex-col gap-3">
		      <div>
		        <label class="block text-xs font-semibold text-gray-700 mb-1.5">
		          {{ __("Coupon Name") }} <span class="text-red-500">*</span>
		        </label>
		        <input v-model="form.coupon_name" type="text"
		          :disabled="!isCreating"
		          :placeholder="__('e.g., Summer Sale Coupon 2025')"
		          class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-600"
		        />
		      </div>
		      <div>
		        <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Coupon Code") }}</label>
		        <div class="flex gap-2">
		          <input v-model="form.coupon_code" type="text"
		            :disabled="!isCreating"
		            :placeholder="__('Auto-generated if left empty')"
		            class="flex-1 h-10 px-3 rounded-lg border border-gray-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-600"
		          />
		          <button v-if="isCreating" @click="generateCouponCode"
		            class="px-4 h-10 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold rounded-lg transition-colors">
		            {{ __("Generate") }}
		          </button>
		        </div>
		        <p class="text-xs text-gray-400 mt-1">{{ __("Customers enter this code at checkout") }}</p>
		      </div>
		    </div>

		    <!-- ④ DISCOUNT SETTINGS -->
		    <div class="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
		      <p class="text-xs font-bold text-emerald-700 uppercase tracking-wide mb-4">
		        % {{ __("Discount Settings") }}
		      </p>

		      <!-- Discount Type buttons -->
		      <div class="mb-4">
		        <p class="text-xs font-semibold text-gray-600 mb-2">{{ __("Discount Type") }} <span class="text-red-500">*</span></p>
		        <div class="flex gap-2">
		          <button @click="form.discount_type = 'Percentage'"
		            :class="['flex-1 py-2.5 rounded-lg border-2 text-sm font-semibold transition-all',
		              form.discount_type === 'Percentage'
		                ? 'border-emerald-500 bg-white text-emerald-700'
		                : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300']">
		            % {{ __("Percentage") }}
		          </button>
		          <button @click="form.discount_type = 'Amount'"
		            :class="['flex-1 py-2.5 rounded-lg border-2 text-sm font-semibold transition-all',
		              form.discount_type === 'Amount'
		                ? 'border-emerald-500 bg-white text-emerald-700'
		                : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300']">
		            {{ __("Fixed Amount") }}
		          </button>
		        </div>
		      </div>

		      <!-- Discount value + Apply On -->
		      <div class="grid grid-cols-2 gap-3">
		        <div>
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">
		            {{ form.discount_type === 'Percentage' ? __("Discount Percentage (%)") : __("Discount Amount") }}
		            <span class="text-red-500">*</span>
		          </label>
		          <div class="relative">
		            <input v-if="form.discount_type === 'Percentage'"
		              v-model.number="form.discount_percentage" type="number" min="0.01" max="100" step="0.01"
		              :placeholder="__('e.g., 20')"
		              class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
		            />
		            <input v-else
		              v-model.number="form.discount_amount" type="number" min="0.01" step="0.01"
		              :placeholder="__('Amount in {0}', [currency])"
		              class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
		            />
		          </div>
		        </div>
		        <div>
		          <p class="text-xs font-semibold text-gray-700 mb-1.5">
		            {{ __("Apply Discount On") }} <span class="text-red-500">*</span>
		          </p>
		          <div class="flex gap-1.5">
		            <button @click="form.apply_on = 'Grand Total'"
		              :class="['flex-1 py-2.5 rounded-lg border-2 text-xs font-semibold transition-all',
		                form.apply_on === 'Grand Total'
		                  ? 'border-emerald-500 bg-white text-emerald-700'
		                  : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300']">
		              {{ __("Grand Total") }}
		            </button>
		            <button @click="form.apply_on = 'Net Total'"
		              :class="['flex-1 py-2.5 rounded-lg border-2 text-xs font-semibold transition-all',
		                form.apply_on === 'Net Total'
		                  ? 'border-emerald-500 bg-white text-emerald-700'
		                  : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300']">
		              {{ __("Net Total") }}
		            </button>
		          </div>
		        </div>
		        <div>
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Min Cart Amount") }}</label>
		          <input v-model.number="form.min_amount" type="number" min="0" step="0.01"
		            :placeholder="__('Optional — no minimum')"
		            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
		          />
		        </div>
		        <div>
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Max Discount Cap") }}</label>
		          <input v-model.number="form.max_amount" type="number" min="0" step="0.01"
		            :placeholder="__('Optional — no cap')"
		            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
		          />
		        </div>
		      </div>

		      <!-- Summary (view mode) -->
		      <div v-if="!isCreating" class="mt-3 p-3 bg-white rounded-lg border border-emerald-200">
		        <p class="text-sm font-semibold text-emerald-800">
		          <span v-if="couponDetails.discount_type === 'Percentage'">
		            {{ couponDetails.discount_percentage }}% {{ __("off") }} {{ couponDetails.apply_on }}
		          </span>
		          <span v-else>
		            {{ currency }} {{ couponDetails.discount_amount }} {{ __("off") }} {{ couponDetails.apply_on }}
		          </span>
		          <span v-if="couponDetails.min_amount" class="text-xs text-gray-500 ms-2">
		            · {{ __("Min: {0} {1}", [currency, couponDetails.min_amount]) }}
		          </span>
		        </p>
		      </div>
		    </div>

		    <!-- ⑤ VALIDITY & USAGE -->
		    <div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
		      <p class="text-xs font-bold text-blue-700 uppercase tracking-wide mb-4">
		        📅 {{ __("Validity & Usage Limits") }}
		      </p>
		      <div class="grid grid-cols-3 gap-3">
		        <div>
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Valid From") }}</label>
		          <input v-model="form.valid_from" type="date"
		            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
		          />
		        </div>
		        <div>
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Valid Until") }}</label>
		          <input v-model="form.valid_upto" type="date"
		            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
		          />
		        </div>
		        <div v-if="form.coupon_type === 'Promotional'">
		          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Max Uses") }}</label>
		          <input v-model.number="form.maximum_use" type="number" min="1"
		            :placeholder="__('Unlimited')"
		            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
		          />
		        </div>
		        <div v-if="!isCreating">
		          <label class="block text-xs font-semibold text-gray-500 mb-1.5">{{ __("Times Used") }}</label>
		          <div class="h-10 px-3 flex items-center bg-white rounded-lg border border-gray-200">
		            <span class="text-lg font-bold text-gray-900">{{ couponDetails.used || 0 }}</span>
		            <span v-if="couponDetails.maximum_use" class="text-xs text-gray-400 ms-1">/ {{ couponDetails.maximum_use }}</span>
		          </div>
		        </div>
		      </div>
		      <label class="flex items-center gap-2 mt-3 cursor-pointer">
		        <input type="checkbox" v-model="form.one_use"
		          class="w-4 h-4 rounded border-gray-300 text-blue-600"
		        />
		        <span class="text-sm text-gray-700">{{ __("Allow only one use per customer") }}</span>
		      </label>
		    </div>

		    <!-- Campaign (optional) -->
		    <div v-if="campaigns.length > 0">
		      <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Campaign (optional)") }}</label>
		      <select v-model="form.campaign" :disabled="!isCreating"
		        class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white disabled:bg-gray-50">
		        <option value="">{{ __("-- No Campaign --") }}</option>
		        <option v-for="c in campaigns" :key="c.name" :value="c.name">{{ c.name }}</option>
		      </select>
		    </div>

		    <!-- Referral Code (view only) -->
		    <div v-if="!isCreating && couponDetails.referral_code"
		      class="px-3 py-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
		      <svg class="w-4 h-4 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
		        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
		          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
		      </svg>
		      <div>
		        <p class="text-xs text-amber-700 font-semibold">{{ __("Generated from Referral Code") }}</p>
		        <p class="text-sm font-mono text-amber-900">{{ couponDetails.referral_code }}</p>
		      </div>
		    </div>

		    <!-- Status Info (view mode) -->
		    <div v-if="!isCreating" class="grid grid-cols-2 gap-3 text-xs text-gray-500">
		      <div>{{ __("Created:") }} {{ formatDate(couponDetails.creation) }}</div>
		      <div>{{ __("Modified:") }} {{ formatDate(couponDetails.modified) }}</div>
		    </div>

		  </div>
		</div>
	</div>

	<!-- Delete Confirmation Dialog -->
	<Transition name="fade">
		<div
			v-if="showDeleteConfirm"
			class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[400]"
			@click.self="showDeleteConfirm = false"
		>
			<div class="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 p-6">
				<div class="flex items-start gap-4">
					<div class="flex-shrink-0">
						<div
							class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center"
						>
							<FeatherIcon name="alert-triangle" class="w-6 h-6 text-red-600" />
						</div>
					</div>
					<div class="flex-1">
						<h3 class="text-lg font-semibold text-gray-900 mb-2">
							{{ __("Delete Coupon") }}
						</h3>
						<TranslatedHTML
							:tag="'p'"
							class="text-sm text-gray-600 mb-1"
							:inner="
								__(
									'Are you sure you want to delete &lt;strong&gt;&quot;{0}&quot;&lt;strong&gt;?',
									[selectedCoupon?.coupon_code]
								)
							"
						/>
						<p class="text-sm text-gray-500">
							{{ __("This action cannot be undone.") }}
						</p>
					</div>
				</div>
				<div class="flex justify-end gap-3 mt-6">
					<Button @click="showDeleteConfirm = false" variant="ghost">
						{{ __("Cancel") }}
					</Button>
					<Button @click="confirmDelete" variant="solid" theme="red" :loading="loading">
						<template #prefix>
							<FeatherIcon name="trash-2" class="w-4 h-4" />
						</template>
						{{ __("Delete Coupon") }}
					</Button>
				</div>
			</div>
		</div>
	</Transition>
</template>

<script setup>
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue";
import { useToast } from "@/composables/useToast";
import { useCustomerSearchStore } from "@/stores/customerSearch";
import { usePOSSettingsStore } from "@/stores/posSettings";
import { DEFAULT_CURRENCY, DEFAULT_LOCALE } from "@/utils/currency";
import { Badge, Button, Card, FormControl, LoadingIndicator, createResource } from "frappe-ui";
import { FeatherIcon } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, onMounted, ref, watch } from "vue";
import TranslatedHTML from "../common/TranslatedHTML.vue";

const { showSuccess, showError, showWarning } = useToast();
const customerStore = useCustomerSearchStore();
const { filteredCustomers, loading: customerLoading } = storeToRefs(customerStore);
const posSettingsStore = usePOSSettingsStore();

const props = defineProps({
	company: String,
	currency: {
		type: String,
		default: DEFAULT_CURRENCY,
	},
	permissions: {
		type: Object,
		default: () => ({
			create: true,
			write: true,
			delete: true,
		}),
	},
});

const emit = defineEmits(["coupon-saved", "refresh-requested"]);

const loading = ref(false);
const coupons = ref([]);
const selectedCoupon = ref(null);
const couponDetails = ref({});
const isCreating = ref(false);
const showDeleteConfirm = ref(false);

// Filters
const searchQuery = ref("");
const filterStatus = ref("all");
const filterType = ref("all");

// Data for dropdowns
const campaigns = ref([]);

// Form
const form = ref({
	coupon_name: "",
	coupon_type: "Promotional",
	coupon_code: "",
	discount_type: "Percentage",
	discount_percentage: null,
	discount_amount: null,
	min_amount: null,
	max_amount: null,
	apply_on: "Grand Total",
	customer: "",
	campaign: "",
	valid_from: "",
	valid_upto: "",
	maximum_use: null,
	one_use: 0,
	company: props.company,
});

// Computed
const filteredCoupons = computed(() => {
	let filtered = coupons.value;

	// Filter by search query
	if (searchQuery.value) {
		const term = searchQuery.value.toLowerCase();
		filtered = filtered.filter(
			(c) =>
				c.coupon_code?.toLowerCase().includes(term) ||
				c.coupon_name?.toLowerCase().includes(term) ||
				c.customer_name?.toLowerCase().includes(term)
		);
	}

	// Filter by status
	if (filterStatus.value !== "all") {
		filtered = filtered.filter((c) => {
			const status = (c.status || "").toLowerCase().replace(" ", "_");
			return status === filterStatus.value;
		});
	}

	// Filter by type
	if (filterType.value !== "all") {
		filtered = filtered.filter((c) => c.coupon_type === filterType.value);
	}

	return filtered;
});

const campaignOptions = computed(() => {
	return [
		{ label: __("-- No Campaign --"), value: "" },
		...campaigns.value.map((c) => ({ label: c.name, value: c.name })),
	];
});

const customerOptions = computed(() => {
	return filteredCustomers.value.map((c) => ({
		label: c.customer_name,
		value: c.name,
		subtitle: c.mobile_no || c.email_id,
	}));
});

// Resources
const couponsResource = createResource({
	url: "pos_next.api.promotions.get_coupons",
	makeParams() {
		return {
			company: props.company,
			include_disabled: true,
		};
	},
	auto: false,
	onSuccess(data) {
		coupons.value = data || [];
		loading.value = false;
	},
	onError(error) {
		loading.value = false;
		handleError(error, __("Failed to load coupons"));
	},
});

const couponDetailsResource = createResource({
	url: "pos_next.api.promotions.get_coupon_details",
	makeParams() {
		return { coupon_name: selectedCoupon.value?.name };
	},
	auto: false,
	onSuccess(data) {
		couponDetails.value = data || {};
		populateFormFromCoupon(data);
		loading.value = false;
	},
	onError(error) {
		loading.value = false;
		handleError(error, __("Failed to load coupon details"));
	},
});

const campaignsResource = createResource({
	url: "frappe.client.get_list",
	makeParams() {
		return {
			doctype: "Campaign",
			fields: ["name"],
			filters: { disabled: 0 },
			limit_page_length: 999,
		};
	},
	auto: false,
	onSuccess(data) {
		campaigns.value = data || [];
	},
});

const createCouponResource = createResource({
	url: "pos_next.api.promotions.create_coupon",
	makeParams() {
		return { data: JSON.stringify(form.value) };
	},
	auto: false,
	onSuccess(data) {
		loading.value = false;
		const responseData = data?.message || data;
		showSuccess(responseData?.message || __("Coupon created successfully"));
		loadCoupons();
		handleCancel();
		emit("coupon-saved", responseData);
	},
	onError(error) {
		loading.value = false;
		handleError(error, __("Failed to create coupon"));
	},
});

const updateCouponResource = createResource({
	url: "pos_next.api.promotions.update_coupon",
	makeParams() {
		return {
			coupon_name: selectedCoupon.value?.name,
			data: JSON.stringify({
				discount_type: form.value.discount_type,
				discount_percentage: form.value.discount_percentage,
				discount_amount: form.value.discount_amount,
				min_amount: form.value.min_amount,
				max_amount: form.value.max_amount,
				apply_on: form.value.apply_on,
				valid_from: form.value.valid_from,
				valid_upto: form.value.valid_upto,
				maximum_use: form.value.maximum_use,
				one_use: form.value.one_use,
			}),
		};
	},
	auto: false,
	onSuccess(data) {
		loading.value = false;
		const responseData = data?.message || data;
		showSuccess(responseData?.message || __("Coupon updated successfully"));
		loadCoupons();
		// Reload details to show updated info
		couponDetailsResource.reload();
	},
	onError(error) {
		loading.value = false;
		handleError(error, __("Failed to update coupon"));
	},
});

const toggleCouponResource = createResource({
	url: "pos_next.api.promotions.toggle_coupon",
	makeParams() {
		return { coupon_name: selectedCoupon.value?.name };
	},
	auto: false,
	onSuccess(data) {
		loading.value = false;
		const responseData = data?.message || data;
		showSuccess(responseData?.message || __("Coupon status updated successfully"));
		loadCoupons();
		// Reload details to get updated disabled status
		if (selectedCoupon.value) {
			couponDetailsResource.reload();
		}
	},
	onError(error) {
		loading.value = false;
		handleError(error, __("Failed to toggle coupon status"));
	},
});

const deleteCouponResource = createResource({
	url: "pos_next.api.promotions.delete_coupon",
	makeParams() {
		return { coupon_name: selectedCoupon.value?.name };
	},
	auto: false,
	onSuccess(data) {
		loading.value = false;
		showDeleteConfirm.value = false;
		const responseData = data?.message || data;
		showSuccess(responseData?.message || __("Coupon deleted successfully"));
		loadCoupons();
		handleCancel();
	},
	onError(error) {
		loading.value = false;
		showDeleteConfirm.value = false;
		handleError(error, __("Failed to delete coupon"));
	},
});

// Watchers
watch(
	() => selectedCoupon.value,
	(val) => {
		if (val && !isCreating.value) {
			loading.value = true;
			couponDetailsResource.reload();
		}
	}
);

onMounted(() => {
	loadCoupons();
	loadCampaigns();
	if (posSettingsStore.settings.pos_profile) {
		customerStore.loadAllCustomers(posSettingsStore.settings.pos_profile);
	}
});

// Methods
function handleCustomerSearch(query) {
	customerStore.setSearchTerm(query);
}

function loadCoupons() {
	loading.value = true;
	couponsResource.reload();
}

function loadCampaigns() {
	campaignsResource.reload();
}

function handleCreateNew() {
	resetForm();
	isCreating.value = true;
	selectedCoupon.value = null;
}

function handleSelectCoupon(coupon) {
	if (isCreating.value) return;
	selectedCoupon.value = coupon;
}

function handleCancel() {
	isCreating.value = false;
	selectedCoupon.value = null;
	resetForm();
}

function handleSubmit() {
	// Validate
	if (!form.value.coupon_name) {
		showWarning(__("Please enter a coupon name"));
		return;
	}
	if (!form.value.discount_type) {
		showWarning(__("Please select a discount type"));
		return;
	}
	if (form.value.discount_type === "Percentage") {
		if (
			!form.value.discount_percentage ||
			form.value.discount_percentage <= 0 ||
			form.value.discount_percentage > 100
		) {
			showWarning(__("Please enter a valid discount percentage (1-100)"));
			return;
		}
	} else if (form.value.discount_type === "Amount") {
		if (!form.value.discount_amount || form.value.discount_amount <= 0) {
			showWarning(__("Please enter a valid discount amount"));
			return;
		}
	}
	if (form.value.coupon_type === "Gift Card" && !form.value.customer) {
		showWarning(__("Please select a customer for gift card"));
		return;
	}

	loading.value = true;

	if (isCreating.value) {
		createCouponResource.reload();
	} else {
		updateCouponResource.reload();
	}
}

function handleToggle() {
	loading.value = true;
	toggleCouponResource.reload();
}

function handleDelete() {
	if (selectedCoupon.value.used > 0) {
		showWarning(
			__("Cannot delete coupon as it has been used {0} times", [selectedCoupon.value.used])
		);
		return;
	}
	showDeleteConfirm.value = true;
}

function confirmDelete() {
	loading.value = true;
	deleteCouponResource.reload();
}

function generateCouponCode() {
	const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	let code = "";
	for (let i = 0; i < 8; i++) {
		code += chars.charAt(Math.floor(Math.random() * chars.length));
	}
	form.value.coupon_code = code;
}

function resetForm() {
	form.value = {
		coupon_name: "",
		coupon_type: "Promotional",
		coupon_code: "",
		discount_type: "Percentage",
		discount_percentage: null,
		discount_amount: null,
		min_amount: null,
		max_amount: null,
		apply_on: "Grand Total",
		customer: "",
		campaign: "",
		valid_from: "",
		valid_upto: "",
		maximum_use: null,
		one_use: 0,
		company: props.company,
	};
}

function populateFormFromCoupon(coupon) {
	form.value = {
		coupon_name: coupon.coupon_name || "",
		coupon_type: coupon.coupon_type || "Promotional",
		coupon_code: coupon.coupon_code || "",
		discount_type: coupon.discount_type || "Percentage",
		discount_percentage: coupon.discount_percentage || null,
		discount_amount: coupon.discount_amount || null,
		min_amount: coupon.min_amount || null,
		max_amount: coupon.max_amount || null,
		apply_on: coupon.apply_on || "Grand Total",
		customer: coupon.customer || "",
		campaign: coupon.campaign || "",
		valid_from: coupon.valid_from || "",
		valid_upto: coupon.valid_upto || "",
		maximum_use: coupon.maximum_use || null,
		one_use: coupon.one_use || 0,
		company: coupon.company || props.company,
	};
}

function formatDate(dateStr) {
	if (!dateStr) return "";
	const date = new Date(dateStr);
	return date.toLocaleDateString(DEFAULT_LOCALE, {
		month: "short",
		day: "numeric",
		year: "numeric",
	});
}

function formatCurrency(amount) {
	return new Intl.NumberFormat(DEFAULT_LOCALE, {
		style: "currency",
		currency: props.currency,
	}).format(amount || 0);
}

function getStatusTheme(status) {
	switch (status) {
		case "Active":
			return "green";
		case "Expired":
			return "red";
		case "Not Started":
			return "orange";
		case "Exhausted":
			return "gray";
		case "Disabled":
			return "red";
		default:
			return "gray";
	}
}

function parseErrorMessage(error) {
	try {
		if (error._server_messages) {
			const messages = JSON.parse(error._server_messages);
			if (Array.isArray(messages) && messages.length > 0) {
				const firstMessage =
					typeof messages[0] === "string" ? JSON.parse(messages[0]) : messages[0];
				return firstMessage.message || error.message || __("An error occurred");
			}
		}
		return error.message || __("An error occurred");
	} catch (e) {
		return error.message || __("An error occurred");
	}
}

function handleError(error, defaultMessage = __("An error occurred")) {
	const errorMessage = parseErrorMessage(error);
	showError(errorMessage || defaultMessage);
}

// Expose methods for parent component
defineExpose({
	loadCoupons,
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
