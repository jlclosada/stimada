<script setup lang="ts">
definePageMeta({ middleware: ["auth", "role"] });
</script>

<template>
  <div class="fade-enter space-y-6">
    <div>
      <p class="font-sans text-xs tracking-editorial uppercase text-gold/50 mb-1">
        Cliente
      </p>
      <h1 class="font-display text-4xl font-light text-cream">Mis proyectos</h1>
    </div>
    <div class="border border-dashed border-border rounded-sm p-16 flex flex-col items-center gap-4">
      <div class="w-8 h-px bg-gold/20" />
      <p class="font-display text-sm text-gray-muted/50 tracking-editorial uppercase">
        Próximamente
      </p>
      <div class="w-8 h-px bg-gold/20" />
    </div>
  </div>
</template>
