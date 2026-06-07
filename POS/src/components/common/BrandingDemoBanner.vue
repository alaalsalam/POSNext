<template>
	<div
		v-if="branding.demoBannerEnabled && branding.demoBannerText"
		class="fixed inset-x-0 top-0 z-[300] bg-amber-500 px-3 py-1.5 text-center text-xs font-semibold text-amber-950 shadow"
	>
		{{ branding.demoBannerText }}
	</div>
</template>

<script setup>
import { useBrandingStore } from "@/stores/branding"

const branding = useBrandingStore()
</script>
