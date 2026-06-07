<template>
  <div>
    <BrandingDemoBanner />
    <router-view :key="translationVersion" />
    <Toast />
  </div>
</template>

<script setup>
import BrandingDemoBanner from "@/components/common/BrandingDemoBanner.vue"
import Toast from "@/components/common/Toast.vue"
import { translationVersion } from "@/utils/translation"
</script>
