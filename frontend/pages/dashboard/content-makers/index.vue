<script setup lang="ts">
import { useContentMakersStore } from "~/stores/contentMakers";

definePageMeta({ middleware: ["auth", "role"] });

const store = useContentMakersStore();

const search = ref("");
const filterStatus = ref("");
const filterTipo = ref("");
const filterCuenta = ref("");

onMounted(() => store.fetchFilters());

const debouncedSearch = ref("");
let searchTimer: ReturnType<typeof setTimeout>;
watch(search, (val) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { debouncedSearch.value = val; }, 300);
});

const params = computed(() => {
  const p: Record<string, string> = {};
  if (debouncedSearch.value) p.q = debouncedSearch.value;
  if (filterStatus.value) p.status = filterStatus.value;
  if (filterTipo.value) p.tipo = filterTipo.value;
  if (filterCuenta.value) p.tiene_cuenta = filterCuenta.value;
  return p;
});

// Reset to page 1 when filters change
watch(params, () => {
  store.currentPage = 1;
  store.fetchList(params.value, 1);
}, { immediate: true });

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

const STATUS_COLOR: Record<string, string> = {
  Alta: "text-emerald-700 bg-emerald-50 border-emerald-200",
  Out: "text-red-600 bg-red-50 border-red-200",
  "Dar de baja": "text-red-600 bg-red-50 border-red-200",
  Descartada: "text-zinc-500 bg-zinc-100 border-zinc-200",
  Potencial: "text-blue-600 bg-blue-50 border-blue-200",
};

function statusColor(s: string) {
  return STATUS_COLOR[s] ?? "text-muted bg-gray-50 border-border";
}

function fmt(n: number | null) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}
</script>

<template>
  <div class="space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Content Makers</h1>
        <p class="text-sm text-muted mt-0.5">Gestiona tu comunidad de creadoras</p>
      </div>
      <NuxtLink
        to="/dashboard/content-makers/nuevo"
        class="group flex items-center gap-2 h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium
               hover:bg-ink/80 hover:shadow-soft active:scale-[0.97] transition-all duration-200"
      >
        <svg class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Dar de alta
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
        <input
          v-model="search"
          type="text"
          placeholder="Buscar por nombre o email…"
          class="input-field !pl-12"
        />
      </div>

      <select v-model="filterStatus" class="select-field min-w-[180px] max-w-[200px]">
        <option value="">Todos los estados</option>
        <option v-for="s in store.filterOptions.statuses" :key="s" :value="s">{{ s }}</option>
      </select>

      <select v-model="filterTipo" class="select-field min-w-[180px] max-w-[200px]">
        <option value="">Todos los tipos</option>
        <option v-for="t in store.filterOptions.tipos" :key="t" :value="t">{{ t }}</option>
      </select>

      <select v-model="filterCuenta" class="select-field min-w-[150px] max-w-[170px]">
        <option value="">Cuenta</option>
        <option value="true">Con cuenta</option>
        <option value="false">Sin cuenta</option>
      </select>

      <button
        v-if="filterStatus || filterTipo || filterCuenta || search"
        class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
        @click="search = ''; filterStatus = ''; filterTipo = ''; filterCuenta = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden">
      <!-- Loading -->
      <div v-if="store.isLoading" class="flex justify-center items-center h-48">
        <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
      </div>

      <template v-else>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border/60 bg-panel/50">
              <th class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider">Nombre</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden md:table-cell">Instagram</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden lg:table-cell">TikTok</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden lg:table-cell">Contenido</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider">Estado</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider">Cuenta</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.list.length === 0">
              <td colspan="6" class="text-center py-16 text-sm text-muted">Sin resultados con estos filtros.</td>
            </tr>
            <tr
              v-for="cm in store.list"
              :key="cm.id"
              class="border-b border-border/30 table-row-hover cursor-pointer group"
              @click="navigateTo(`/dashboard/content-makers/${cm.id}`)"
            >
              <td class="px-5 py-3.5">
                <div>
                  <p class="text-sm text-ink font-medium group-hover:text-gold transition-colors duration-150">
                    {{ cm.nombre_completo }}
                  </p>
                  <p class="text-xs text-muted mt-0.5">{{ cm.stimada_id }}</p>
                </div>
              </td>
              <td class="px-4 py-3.5 hidden md:table-cell">
                <div v-if="cm.instagram_handle">
                  <p class="text-sm text-ink/80">@{{ cm.instagram_handle }}</p>
                  <p class="text-xs text-muted">{{ fmt(cm.seguidores_instagram) }}</p>
                </div>
                <span v-else class="text-xs text-muted/60">—</span>
              </td>
              <td class="px-4 py-3.5 hidden lg:table-cell">
                <div v-if="cm.tiktok_handle">
                  <p class="text-sm text-ink/80">{{ cm.tiktok_handle }}</p>
                  <p class="text-xs text-muted">{{ fmt(cm.seguidores_tiktok) }}</p>
                </div>
                <span v-else class="text-xs text-muted/60">—</span>
              </td>
              <td class="px-4 py-3.5 hidden lg:table-cell">
                <p class="text-sm text-muted truncate max-w-[150px]">{{ cm.categorias_contenido || "—" }}</p>
              </td>
              <td class="px-4 py-3.5">
                <span
                  class="inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-lg border"
                  :class="statusColor(cm.status)"
                >
                  {{ cm.status || "—" }}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <span
                  v-if="cm.tiene_cuenta"
                  class="inline-flex items-center gap-1.5 text-xs text-emerald-600 font-medium"
                >
                  <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Activa
                </span>
                <span v-else class="text-xs text-muted/60">Sin cuenta</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="flex items-center justify-between px-5 py-4 border-t border-border/40 bg-panel/30">
          <p class="text-sm text-muted">
            Mostrando <span class="font-medium text-ink">{{ (store.currentPage - 1) * store.pageSize + 1 }}</span>–<span class="font-medium text-ink">{{ Math.min(store.currentPage * store.pageSize, store.total) }}</span> de <span class="font-medium text-ink">{{ store.total }}</span>
          </p>

          <div class="flex items-center gap-1">
            <!-- Prev -->
            <button
              :disabled="store.currentPage <= 1"
              class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
              @click="goToPage(store.currentPage - 1)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>

            <!-- Page numbers -->
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

            <!-- Next -->
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
