<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ layout: false, middleware: "auth" });

const auth = useAuthStore();

// If already authenticated, redirect to inicio
if (auth.isAuthenticated) {
  await navigateTo("/inicio", { replace: true });
}
</script>

<template>
  <div class="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-panel">

    <!-- Subtle background gradient -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div
        class="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full opacity-[0.04]"
        style="background: radial-gradient(circle, #c9a84c, transparent 70%)"
      />
      <div
        class="absolute -bottom-32 -right-32 w-[500px] h-[500px] rounded-full opacity-[0.03]"
        style="background: radial-gradient(circle, #0071e3, transparent 70%)"
      />
    </div>

    <!-- Content -->
    <div class="relative z-10 flex flex-col items-center gap-10 animate-scale-in">
      <!-- Logo -->
      <img
        src="~/assets/images/stimada_logo.png"
        alt="Stimada"
        class="w-64 drop-shadow-sm"
      />

      <!-- Tagline -->
      <p class="text-muted text-center text-lg tracking-wide max-w-xs">
        Plataforma de gestión de contenidos
      </p>

      <!-- CTA Button -->
      <NuxtLink
        to="/login"
        class="px-8 py-3 rounded-xl bg-gold text-white font-semibold text-base shadow-md hover:shadow-lg hover:brightness-110 transition-all duration-200"
      >
        Iniciar sesión
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.animate-scale-in {
  animation: scale-in 0.5s ease-out both;
}
</style>
