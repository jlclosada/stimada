<script setup lang="ts">
import { useBrandsStore } from "~/stores/brands";
import { useClientsStore } from "~/stores/clients";
import { formatBrandId } from "~/utils/formatId";

definePageMeta({ middleware: ["auth", "role"] });

const store = useBrandsStore();
const clientStore = useClientsStore();

const searchQuery = ref("");
const filterClient = ref("");

async function loadBrands(page?: number) {
  const params: Record<string, string> = {};
  if (searchQuery.value) params.q = searchQuery.value;
  if (filterClient.value) params.client = filterClient.value;
  await store.fetchList(params, page ?? 1);
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null;
function onSearch() {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => loadBrands(1), 300);
}

onMounted(() => {
  loadBrands();
  clientStore.fetchTypes();
});
</script>

<template>
  <div class="max-w-5xl animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between mb-7">
      <div>
        <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Dashboard</p>
        <h1 class="text-3xl font-semibold tracking-tight text-ink">Marcas</h1>
      </div>
      <NuxtLink
        to="/dashboard/marcas/nuevo"
        class="h-9 px-5 rounded-xl bg-gold text-ink text-xs font-semibold inline-flex items-center gap-2 hover:bg-gold/90 active:scale-[0.98] transition-all"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Nueva marca
      </NuxtLink>
    </div>

    <!-- Search -->
    <div class="flex gap-3 mb-5">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Buscar por nombre…"
        class="input-field flex-1"
        @input="onSearch"
      />
    </div>

    <!-- Loading -->
    <div v-if="store.isLoading" class="flex justify-center py-20">
      <div class="w-7 h-7 rounded-full border-2 border-gold/20 border-t-gold animate-spin" />
    </div>

    <!-- Table -->
    <div v-else-if="store.list.length" class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden">
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-border/40">
            <th class="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted/70">Marca</th>
            <th class="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted/70">Cliente</th>
            <th class="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted/70">Tipo</th>
            <th class="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted/70">Estado</th>
          </tr>
        </thead>
        <tbody>
          <NuxtLink
            v-for="brand in store.list"
            :key="brand.id"
            :to="`/dashboard/marcas/${brand.id}`"
            custom
            v-slot="{ navigate }"
          >
            <tr class="border-b border-border/20 last:border-0 hover:bg-panel/40 cursor-pointer transition-colors" @click="navigate">
              <td class="px-5 py-3.5">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                    <span class="text-[11px] font-bold text-indigo-400">{{ brand.nombre.charAt(0) }}</span>
                  </div>
                  <div>
                    <p class="text-sm font-medium text-ink">{{ brand.nombre }}</p>
                    <p class="text-[10px] text-muted/60 font-mono">{{ formatBrandId(brand.brand_id) }}</p>
                  </div>
                </div>
              </td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ brand.client_name }}</td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ brand.tipo_marca_nombre || "—" }}</td>
              <td class="px-5 py-3.5">
                <span
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border"
                  :class="brand.estado === 'activa' ? 'text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15' : 'text-muted/60 bg-panel border-border/40'"
                >
                  {{ brand.estado === 'activa' ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
            </tr>
          </NuxtLink>
        </tbody>
      </table>
    </div>

    <!-- Empty -->
    <div v-else class="text-center py-20">
      <p class="text-sm text-muted">No hay marcas registradas.</p>
      <NuxtLink to="/dashboard/marcas/nuevo" class="inline-flex items-center gap-1.5 text-xs text-gold mt-3 hover:text-gold/80">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Crear primera marca
      </NuxtLink>
    </div>

    <!-- Pagination -->
    <div v-if="store.totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
      <button
        :disabled="store.currentPage <= 1"
        class="px-3 py-1.5 rounded-lg border border-border/60 text-xs text-muted hover:text-ink disabled:opacity-40 transition-colors"
        @click="loadBrands(store.currentPage - 1)"
      >
        ← Anterior
      </button>
      <span class="text-xs text-muted">{{ store.currentPage }} / {{ store.totalPages }}</span>
      <button
        :disabled="store.currentPage >= store.totalPages"
        class="px-3 py-1.5 rounded-lg border border-border/60 text-xs text-muted hover:text-ink disabled:opacity-40 transition-colors"
        @click="loadBrands(store.currentPage + 1)"
      >
        Siguiente →
      </button>
    </div>
  </div>
</template>
