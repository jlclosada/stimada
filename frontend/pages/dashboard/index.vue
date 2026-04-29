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
  stimada_employee: "text-blue-600 border-blue-200 bg-blue-50",
  client: "text-emerald-600 border-emerald-200 bg-emerald-50",
  content_maker: "text-orange-600 border-orange-200 bg-orange-50",
};
</script>

<template>
  <div class="space-y-8 animate-fade-up">
    <!-- Welcome section -->
    <div class="relative overflow-hidden rounded-2xl border border-border/60 bg-white p-8 shadow-card">
      <!-- Decorative -->
      <div class="absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-[0.06] pointer-events-none" style="background: radial-gradient(circle, #c9a84c, transparent 70%)" />

      <div class="relative">
        <p class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold mb-2">
          Panel principal
        </p>
        <h1 class="text-3xl font-semibold tracking-tight text-ink leading-tight">
          Hola, {{ auth.user?.full_name?.split(" ")[0] }}
        </h1>
        <p class="text-sm text-muted mt-1.5">Bienvenido de vuelta a tu espacio de trabajo</p>
      </div>
    </div>

    <!-- Info cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="group glass-card p-6 space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl bg-gold/10 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
            <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <p class="text-[11px] text-muted uppercase tracking-widest font-medium">Tu rol</p>
        </div>
        <span
          class="inline-block text-xs px-3 py-1.5 border rounded-lg font-medium"
          :class="ROLE_COLORS[auth.user?.role ?? ''] ?? 'text-ink border-border'"
        >
          {{ ROLE_LABELS[auth.user?.role ?? ""] ?? auth.user?.role }}
        </span>
      </div>

      <div class="group glass-card p-6 space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
            <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
          </div>
          <p class="text-[11px] text-muted uppercase tracking-widest font-medium">Email</p>
        </div>
        <p class="text-sm text-ink font-medium truncate">{{ auth.user?.email }}</p>
      </div>

      <div class="group glass-card p-6 space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
            <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-[11px] text-muted uppercase tracking-widest font-medium">Estado</p>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <p class="text-sm text-emerald-600 font-medium">Activo</p>
        </div>
      </div>
    </div>

    <!-- Metrics placeholder -->
    <div>
      <p class="text-[11px] text-muted uppercase tracking-[0.15em] font-medium mb-4">
        Métricas
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          v-for="i in 3"
          :key="i"
          class="glass-card border-dashed p-8 flex flex-col items-center justify-center gap-3 min-h-[140px]"
        >
          <div class="w-8 h-8 rounded-full bg-panel border border-border/40 flex items-center justify-center">
            <div class="w-1.5 h-1.5 rounded-full bg-muted/30" />
          </div>
          <p class="text-[10px] text-muted/40 tracking-[0.15em] uppercase font-medium">
            Próximamente
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
