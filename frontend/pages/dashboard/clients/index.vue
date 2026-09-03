<script setup lang="ts">
import { useBrandsStore } from '~/stores/brands';
import { useClientsStore } from '~/stores/clients';
import { formatBrandId, formatClientId } from '~/utils/formatId';

definePageMeta({ middleware: ['auth', 'role'] });

// Tab state
const activeTab = ref<'clientes' | 'marcas'>('clientes');

// ---------- CLIENTES ----------
const store = useClientsStore();
const search = ref('');
const filterTipo = ref('');
const filterContrato = ref('');
const filterCuenta = ref('');
const sortBy = ref<string>('');
const sortDir = ref<'asc' | 'desc'>('asc');

let searchTimer: ReturnType<typeof setTimeout>;
const debouncedSearch = ref('');
watch(search, (val) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    debouncedSearch.value = val;
  }, 300);
});

const params = computed(() => {
  const p: Record<string, string> = {};
  if (debouncedSearch.value) p.q = debouncedSearch.value;
  if (filterTipo.value) p.type = filterTipo.value;
  if (filterContrato.value) p.contract = filterContrato.value;
  if (filterCuenta.value) p.account = filterCuenta.value;
  if (sortBy.value)
    p.ordering = (sortDir.value === 'desc' ? '-' : '') + sortBy.value;
  return p;
});

watch(
  params,
  () => {
    store.currentPage = 1;
    store.fetchList(params.value, 1);
  },
  { immediate: true },
);

function toggleSort(field: string) {
  if (sortBy.value === field) {
    if (sortDir.value === 'asc') {
      sortDir.value = 'desc';
    } else {
      // 3rd click → clear sort
      sortBy.value = '';
      sortDir.value = 'asc';
    }
  } else {
    sortBy.value = field;
    sortDir.value = 'asc';
  }
}

function sortIcon(field: string): string {
  if (sortBy.value !== field) return '';
  return sortDir.value === 'asc' ? '▲' : '▼';
}

function clearFilters() {
  search.value = '';
  filterTipo.value = '';
  filterContrato.value = '';
  filterCuenta.value = '';
  sortBy.value = '';
  sortDir.value = 'asc';
}

const hasActiveFilters = computed(() =>
  Boolean(
    search.value ||
    filterTipo.value ||
    filterContrato.value ||
    filterCuenta.value ||
    sortBy.value,
  ),
);

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
    if (current > 3) pages.push('...');
    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (current < total - 2) pages.push('...');
    pages.push(total);
  }
  return pages;
});

// ---------- MARCAS ----------
const brandsStore = useBrandsStore();
const brandSearch = ref('');

let brandSearchTimeout: ReturnType<typeof setTimeout> | null = null;
function onBrandSearch() {
  if (brandSearchTimeout) clearTimeout(brandSearchTimeout);
  brandSearchTimeout = setTimeout(() => loadBrands(1), 300);
}

function loadBrands(page?: number) {
  const params: Record<string, string> = {};
  if (brandSearch.value) params.q = brandSearch.value;
  brandsStore.fetchList(params, page ?? 1);
}

function goToBrandPage(page: number) {
  if (page < 1 || page > brandsStore.totalPages) return;
  loadBrands(page);
}

// Load on mount
onMounted(() => {
  store.fetchTypes();
  loadBrands();
});
</script>

<template>
  <div class="space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">
          Clientes y Marcas
        </h1>
        <p class="text-sm text-muted mt-0.5">
          Directorio de clientes y marcas asociadas
        </p>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink
          v-if="activeTab === 'clientes'"
          to="/dashboard/clients/new"
          class="group flex items-center gap-2 h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium hover:bg-ink/80 hover:shadow-soft active:scale-[0.97] transition-all duration-200"
        >
          <svg
            class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          Dar de alta cliente
        </NuxtLink>
        <NuxtLink
          v-else
          to="/dashboard/brands/new"
          class="group flex items-center gap-2 h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium hover:bg-ink/80 hover:shadow-soft active:scale-[0.97] transition-all duration-200"
        >
          <svg
            class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          Añadir marca
        </NuxtLink>
      </div>
    </div>

    <!-- Tabs -->
    <div
      class="flex gap-1 p-1 rounded-xl border border-border/60 bg-white w-fit"
    >
      <button
        class="px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        :class="
          activeTab === 'clientes'
            ? 'bg-ink text-white shadow-sm'
            : 'text-muted hover:text-ink'
        "
        @click="activeTab = 'clientes'"
      >
        Clientes
      </button>
      <button
        class="px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        :class="
          activeTab === 'marcas'
            ? 'bg-ink text-white shadow-sm'
            : 'text-muted hover:text-ink'
        "
        @click="activeTab = 'marcas'"
      >
        Marcas
      </button>
    </div>

    <!-- ==================== CLIENTES TAB ==================== -->
    <template v-if="activeTab === 'clientes'">
      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-3 animate-fade-up delay-100">
        <div class="relative flex-1 min-w-[260px] max-w-md group/search">
          <div
            class="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-all duration-300 group-focus-within/search:scale-90 group-focus-within/search:text-gold"
          >
            <svg
              class="w-4 h-4 text-muted/50"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
              />
            </svg>
          </div>
          <input
            v-model="search"
            type="text"
            placeholder="Buscar cliente o ID…"
            class="input-field !pl-12"
          />
        </div>

        <BaseSelect
          v-model="filterTipo"
          class="min-w-[180px] max-w-[200px]"
          :options="[
            { value: '', label: 'Todos los tipos' },
            ...store.types.map((t) => ({ value: t.slug, label: t.name })),
          ]"
        />

        <BaseSelect
          v-model="filterContrato"
          class="min-w-[160px] max-w-[180px]"
          :options="[
            { value: '', label: 'Contrato (todos)' },
            { value: 'firmado', label: 'Firmado' },
            { value: 'pendiente', label: 'Pendiente' },
          ]"
        />

        <BaseSelect
          v-model="filterCuenta"
          class="min-w-[170px] max-w-[190px]"
          :options="[
            { value: '', label: 'Cuenta (todas)' },
            { value: 'activa', label: 'Con cuenta activa' },
            { value: 'sin_cuenta', label: 'Sin cuenta' },
          ]"
        />

        <button
          v-if="hasActiveFilters"
          class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
          @click="clearFilters"
        >
          Limpiar
        </button>
      </div>

      <!-- Table -->
      <div
        class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden"
      >
        <div
          v-if="store.isLoading"
          class="flex justify-center items-center h-48"
        >
          <div
            class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin"
          />
        </div>
        <template v-else>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border/60 bg-panel/50">
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('name')"
                >
                  Cliente
                  <span class="ml-1 text-[10px]">{{ sortIcon('name') }}</span>
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('client_id')"
                >
                  ID
                  <span class="ml-1 text-[10px]">{{
                    sortIcon('client_id')
                  }}</span>
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('client_type__name')"
                >
                  Tipo
                  <span class="ml-1 text-[10px]">{{
                    sortIcon('client_type__name')
                  }}</span>
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('city')"
                >
                  Ciudad
                  <span class="ml-1 text-[10px]">{{ sortIcon('city') }}</span>
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('contract_signed')"
                >
                  Contrato
                  <span class="ml-1 text-[10px]">{{
                    sortIcon('contract_signed')
                  }}</span>
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Cuenta
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Alta por
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider cursor-pointer select-none hover:text-ink transition-colors"
                  @click="toggleSort('created_at')"
                >
                  Fecha
                  <span class="ml-1 text-[10px]">{{
                    sortIcon('created_at')
                  }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!store.list.length">
                <td colspan="8" class="text-center py-16 text-sm text-muted">
                  No hay clientes registrados aún.
                </td>
              </tr>
              <tr
                v-for="client in store.list"
                :key="client.id"
                class="border-b border-border/30 table-row-hover cursor-pointer group"
                @click="navigateTo(`/dashboard/clients/${client.id}`)"
              >
                <td class="px-5 py-3.5">
                  <p
                    class="text-sm text-ink font-medium group-hover:text-gold transition-colors duration-150"
                  >
                    {{ client.name }}
                  </p>
                </td>
                <td class="px-5 py-3.5 text-xs text-muted">
                  {{ formatClientId(client.client_id) }}
                </td>
                <td class="px-5 py-3.5">
                  <span
                    v-if="client.type_name"
                    class="text-xs px-2.5 py-1 rounded-lg border border-blue-200 text-blue-600 bg-blue-50 font-medium"
                  >
                    {{ client.type_name }}
                  </span>
                  <span v-else class="text-xs text-muted/60">—</span>
                </td>
                <td class="px-5 py-3.5 text-sm text-muted">
                  {{ client.city || '—' }}
                </td>
                <td class="px-5 py-3.5">
                  <span
                    v-if="client.contract_signed"
                    class="flex items-center gap-1.5 text-xs text-emerald-600 font-medium"
                  >
                    <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Firmado
                  </span>
                  <span
                    v-else
                    class="flex items-center gap-1.5 text-xs text-muted"
                  >
                    <div class="w-1.5 h-1.5 rounded-full bg-muted/40" />
                    Pendiente
                  </span>
                </td>
                <td class="px-5 py-3.5">
                  <span
                    v-if="client.has_account"
                    class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium"
                  >
                    <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Activa
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-md bg-panel/60 text-muted border border-border/60"
                  >
                    <div class="w-1.5 h-1.5 rounded-full bg-muted/40" />
                    Sin cuenta
                  </span>
                </td>
                <td class="px-5 py-3.5 text-sm text-muted">
                  {{ client.created_by_name || '—' }}
                </td>
                <td class="px-5 py-3.5 text-sm text-muted">
                  {{
                    new Date(client.created_at).toLocaleDateString('es-ES', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                    })
                  }}
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div
            v-if="store.totalPages > 1"
            class="flex items-center justify-between px-5 py-4 border-t border-border/40 bg-panel/30"
          >
            <p class="text-sm text-muted">
              Mostrando
              <span class="font-medium text-ink">{{
                (store.currentPage - 1) * store.pageSize + 1
              }}</span
              >–<span class="font-medium text-ink">{{
                Math.min(store.currentPage * store.pageSize, store.total)
              }}</span>
              de <span class="font-medium text-ink">{{ store.total }}</span>
            </p>
            <div class="flex items-center gap-1">
              <button
                :disabled="store.currentPage <= 1"
                class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
                @click="goToPage(store.currentPage - 1)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.75 19.5L8.25 12l7.5-7.5"
                  />
                </svg>
              </button>
              <template v-for="p in visiblePages" :key="p">
                <span
                  v-if="p === '...'"
                  class="w-9 h-9 flex items-center justify-center text-xs text-muted"
                  >…</span
                >
                <button
                  v-else
                  class="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-medium transition-all duration-150"
                  :class="
                    p === store.currentPage
                      ? 'bg-ink text-white shadow-sm'
                      : 'text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border'
                  "
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
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M8.25 4.5l7.5 7.5-7.5 7.5"
                  />
                </svg>
              </button>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- ==================== MARCAS TAB ==================== -->
    <template v-if="activeTab === 'marcas'">
      <!-- Search -->
      <div class="flex flex-wrap items-center gap-3 animate-fade-up delay-100">
        <div class="relative flex-1 min-w-[260px] max-w-md group/search">
          <div
            class="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-all duration-300 group-focus-within/search:scale-90 group-focus-within/search:text-gold"
          >
            <svg
              class="w-4 h-4 text-muted/50"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
              />
            </svg>
          </div>
          <input
            v-model="brandSearch"
            type="text"
            placeholder="Buscar marca…"
            class="input-field !pl-12"
            @input="onBrandSearch"
          />
        </div>

        <button
          v-if="brandSearch"
          class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
          @click="
            brandSearch = '';
            loadBrands(1);
          "
        >
          Limpiar
        </button>
      </div>

      <!-- Table -->
      <div
        class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden"
      >
        <div
          v-if="brandsStore.isLoading"
          class="flex justify-center items-center h-48"
        >
          <div
            class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin"
          />
        </div>
        <template v-else>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border/60 bg-panel/50">
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Marca
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Cliente
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Tipo
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider"
                >
                  Estado
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!brandsStore.list.length">
                <td colspan="4" class="text-center py-16 text-sm text-muted">
                  No hay marcas registradas aún.
                </td>
              </tr>
              <tr
                v-for="brand in brandsStore.list"
                :key="brand.id"
                class="border-b border-border/30 table-row-hover cursor-pointer group"
                @click="navigateTo(`/dashboard/brands/${brand.id}`)"
              >
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0"
                    >
                      <span class="text-[11px] font-bold text-indigo-400">{{
                        brand.name.charAt(0)
                      }}</span>
                    </div>
                    <div>
                      <p
                        class="text-sm font-medium text-ink group-hover:text-gold transition-colors duration-150"
                      >
                        {{ brand.name }}
                      </p>
                      <p class="text-[10px] text-muted/60 font-mono">
                        {{ formatBrandId(brand.brand_id) }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-3.5 text-sm text-muted">
                  {{ brand.client_name }}
                </td>
                <td class="px-5 py-3.5">
                  <span
                    v-if="brand.brand_type_name"
                    class="text-xs px-2.5 py-1 rounded-lg border border-blue-200 text-blue-600 bg-blue-50 font-medium"
                  >
                    {{ brand.brand_type_name }}
                  </span>
                  <span v-else class="text-xs text-muted/60">—</span>
                </td>
                <td class="px-5 py-3.5">
                  <span
                    class="flex items-center gap-1.5 text-xs font-medium"
                    :class="
                      brand.status === 'activa'
                        ? 'text-emerald-600'
                        : 'text-muted'
                    "
                  >
                    <div
                      class="w-1.5 h-1.5 rounded-full"
                      :class="
                        brand.status === 'activa'
                          ? 'bg-emerald-500'
                          : 'bg-muted/40'
                      "
                    />
                    {{ brand.status === 'activa' ? 'Activa' : 'Inactiva' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div
            v-if="brandsStore.totalPages > 1"
            class="flex items-center justify-between px-5 py-4 border-t border-border/40 bg-panel/30"
          >
            <p class="text-sm text-muted">
              Mostrando
              <span class="font-medium text-ink">{{
                (brandsStore.currentPage - 1) * brandsStore.pageSize + 1
              }}</span
              >–<span class="font-medium text-ink">{{
                Math.min(
                  brandsStore.currentPage * brandsStore.pageSize,
                  brandsStore.total,
                )
              }}</span>
              de
              <span class="font-medium text-ink">{{ brandsStore.total }}</span>
            </p>
            <div class="flex items-center gap-1">
              <button
                :disabled="brandsStore.currentPage <= 1"
                class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
                @click="goToBrandPage(brandsStore.currentPage - 1)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.75 19.5L8.25 12l7.5-7.5"
                  />
                </svg>
              </button>
              <span class="text-xs text-muted px-2"
                >{{ brandsStore.currentPage }} /
                {{ brandsStore.totalPages }}</span
              >
              <button
                :disabled="brandsStore.currentPage >= brandsStore.totalPages"
                class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
                @click="goToBrandPage(brandsStore.currentPage + 1)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M8.25 4.5l7.5 7.5-7.5 7.5"
                  />
                </svg>
              </button>
            </div>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>
