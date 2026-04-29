<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth", "role"] });

const auth = useAuthStore();

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  stimada_employee: "Empleado Stimada",
  client: "Cliente",
  content_maker: "Content Maker",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "text-gold border-gold/30 bg-gold/10",
  stimada_employee: "text-blue-400 border-blue-400/30 bg-blue-400/10",
  client: "text-green-400 border-green-400/30 bg-green-400/10",
  content_maker: "text-orange-400 border-orange-400/30 bg-orange-400/10",
};
</script>

<template>
  <div class="fade-enter space-y-8">
    <!-- Bienvenida -->
    <div>
      <p class="font-sans text-xs tracking-editorial uppercase text-gold/50 mb-2">
        Panel principal
      </p>
      <h1 class="font-display text-5xl font-light text-cream">
        Hola, {{ auth.user?.full_name?.split(" ")[0] }}
      </h1>
    </div>

    <!-- Card de rol -->
    <div class="flex gap-4 flex-wrap">
      <div
        class="border border-border rounded-sm p-5 min-w-[220px]"
        style="background-color: #141414"
      >
        <p class="font-sans text-xs text-gray-muted mb-3 uppercase tracking-widest">
          Tu rol
        </p>
        <span
          class="inline-block font-sans text-xs px-3 py-1 border rounded-sm"
          :class="ROLE_COLORS[auth.user?.role ?? ''] ?? 'text-cream border-border'"
        >
          {{ ROLE_LABELS[auth.user?.role ?? ""] ?? auth.user?.role }}
        </span>
      </div>

      <div
        class="border border-border rounded-sm p-5 min-w-[220px]"
        style="background-color: #141414"
      >
        <p class="font-sans text-xs text-gray-muted mb-3 uppercase tracking-widest">
          Email
        </p>
        <p class="font-sans text-sm text-cream">{{ auth.user?.email }}</p>
      </div>
    </div>

    <!-- Coming soon widgets -->
    <div>
      <p class="font-sans text-xs text-gray-muted uppercase tracking-widest mb-4">
        Métricas
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          v-for="i in 3"
          :key="i"
          class="border border-border border-dashed rounded-sm p-6 flex flex-col items-center justify-center gap-3 min-h-[120px]"
          style="background-color: #141414"
        >
          <div class="w-6 h-px bg-gold/20" />
          <p class="font-display text-xs text-gray-muted/50 tracking-editorial uppercase">
            Próximamente
          </p>
          <div class="w-6 h-px bg-gold/20" />
        </div>
      </div>
    </div>
  </div>
</template>
