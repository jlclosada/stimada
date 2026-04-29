<script setup lang="ts">
import { useClientsStore } from "~/stores/clients";

definePageMeta({ middleware: ["auth", "role"] });

const store = useClientsStore();
const search = ref("");
const filterTipo = ref("");

let searchTimer: ReturnType<typeof setTimeout>;
const debouncedSearch = ref("");
watch(search, (val) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { debouncedSearch.value = val; }, 300);
});

const params = computed(() => {
  const p: Record<string, string> = {};
  if (debouncedSearch.value) p.q = debouncedSearch.value;
  if (filterTipo.value) p.tipo = filterTipo.value;
  return p;
});

watch(params, () => {
  store.currentPage = 1;
  store.fetchList(params.value, 1);
}, { immediate: true });
onMounted(() => store.fetchTypes());

function goToPage(page: number) {
  if (page < 1 || page > store.totalPages) return;
  store.fetchList(params.value, page);
}

const visiblePages = computed(() => {
  const total = store.totalPages;
  const current = store.currentPage;
  const pages: (number | string)[] = [];
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    if (current > 3) pages.push("...");
    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (current < total - 2) pages.push("...");
    pages.push(total);
  }
  return pages;
});
</script>

<template>
  <div class="space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Clientes</h1>
        <p class="text-sm text-muted mt-0.5">Directorio de clientes</p>
      </div>
      <NuxtLink
        to="/dashboard/clientes/nuevo"
        class="group flex items-center gap-2 h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium
               hover:bg-ink/80 hover:shadow-soft active:scale-[0.97] transition-all duration-200"
      >
        <svg class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Dar de alta cliente
      </NuxtLink>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 animate-fade-up delay-100">
      <div class="relative flex-1 min-w-[260px] max-w-md group/search">
        <div class="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-all duration-300 group-focus-within/search:scale-90 group-focus-within/search:text-gold">
          <svg class="w-4 h-4 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>
        <input v-model="search" type="text" placeholder="Buscar cliente o ID…" class="input-field !pl-12" />
      </div>

      <select v-model="filterTipo" class="select-field min-w-[180px] max-w-[200px]">
        <option value="">Todos los tipos</option>
        <option v-for="t in store.types" :key="t.slug" :value="t.slug">{{ t.nombre }}</option>
      </select>

      <button
        v-if="search || filterTipo"
        class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
        @click="search = ''; filterTipo = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden">
      <div v-if="store.isLoading" class="flex justify-center items-center h-48">
        <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
      </div>
      <template v-else>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border/60 bg-panel/50">
              <th v-for="col in ['Cliente', 'ID', 'Tipo', 'Ciudad', 'Contrato', 'Alta por', 'Fecha']"
                  :key="col"
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider">
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!store.list.length">
              <td colspan="7" class="text-center py-16 text-sm text-muted">
                No hay clientes registrados aún.
              </td>
            </tr>
            <tr
              v-for="client in store.list"
              :key="client.id"
              class="border-b border-border/30 table-row-hover cursor-pointer group"
              @click="navigateTo(`/dashboard/clientes/${client.id}`)"
            >
              <td class="px-5 py-3.5">
                <p class="text-sm text-ink font-medium group-hover:text-gold transition-colors duration-150">{{ client.nombre_cliente }}</p>
              </td>
              <td class="px-5 py-3.5 text-xs text-muted">{{ client.cliente_id }}</td>
              <td class="px-5 py-3.5">
                <span v-if="client.tipo_nombre" class="text-xs px-2.5 py-1 rounded-lg border border-blue-200 text-blue-600 bg-blue-50 font-medium">
                  {{ client.tipo_nombre }}
                </span>
                <span v-else class="text-xs text-muted/60">—</span>
              </td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ client.ciudad || '—' }}</td>
              <td class="px-5 py-3.5">
                <span v-if="client.contrato_firmado" class="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
                  <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Firmado
                </span>
                <span v-else class="flex items-center gap-1.5 text-xs text-muted">
                  <div class="w-1.5 h-1.5 rounded-full bg-muted/40" />
                  Pendiente
                </span>
              </td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ client.created_by_name || '—' }}</td>
              <td class="px-5 py-3.5 text-sm text-muted">
                {{ new Date(client.created_at).toLocaleDateString('es-ES', { day:'2-digit', month:'short', year:'numeric' }) }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div v-if="store.totalPages > 1" class="flex items-center justify-between px-5 py-4 border-t border-border/40 bg-panel/30">
          <p class="text-sm text-muted">
            Mostrando <span class="font-medium text-ink">{{ (store.currentPage - 1) * store.pageSize + 1 }}</span>–<span class="font-medium text-ink">{{ Math.min(store.currentPage * store.pageSize, store.total) }}</span> de <span class="font-medium text-ink">{{ store.total }}</span>
          </p>
          <div class="flex items-center gap-1">
            <button
              :disabled="store.currentPage <= 1"
              class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
              @click="goToPage(store.currentPage - 1)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="w-9 h-9 flex items-center justify-center text-xs text-muted">…</span>
              <button
                v-else
                class="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-medium transition-all duration-150"
                :class="p === store.currentPage
                  ? 'bg-ink text-white shadow-sm'
                  : 'text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border'"
                @click="goToPage(p as number)"
              >
                {{ p }}
              </button>
            </template>
            <button
              :disabled="store.currentPage >= store.totalPages"
              class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
              @click="goToPage(store.currentPage + 1)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
