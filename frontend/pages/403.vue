<script setup lang="ts">
definePageMeta({ layout: false });
</script>

<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center grain px-8"
    style="background-color: #0a0a0a"
  >
    <div class="text-center fade-enter max-w-sm">
      <p class="font-sans text-xs tracking-editorial uppercase text-gold/50 mb-6">
        Error 403
      </p>
      <h1 class="font-display text-6xl font-light text-cream mb-4">
        Acceso<br />denegado
      </h1>
      <div class="w-8 h-px bg-gold/40 mx-auto my-6" />
      <p class="font-sans text-sm text-gray-muted leading-relaxed mb-10">
        No tienes permiso para acceder a esta sección.<br />
        Si crees que es un error, contacta con tu administrador.
      </p>
      <NuxtLink
        to="/dashboard"
        class="inline-block font-sans text-xs tracking-editorial uppercase text-gold border border-gold/30 px-8 py-3 hover:bg-gold/10 transition-colors duration-200"
      >
        Volver al inicio
      </NuxtLink>
    </div>
  </div>
</template>
