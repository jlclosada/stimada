<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import { useContentMakersStore } from '~/stores/contentMakers';
import { formatContentMakerId } from '~/utils/formatId';

definePageMeta({ middleware: ['auth', 'role'] });

const auth = useAuthStore();
const store = useContentMakersStore();

const isAdminOrEmployee = computed(
  () => auth.user?.role === 'admin' || auth.user?.role === 'stimada_employee',
);

const isClient = computed(() => auth.user?.role === 'client');

const search = ref('');
const filterStatus = ref('');
const filterTypeBase = ref('');
const filterCmType = ref('');
const filterAccount = ref('');

onMounted(() => store.fetchFilters());

const debouncedSearch = ref('');
let searchTimer: ReturnType<typeof setTimeout>;
watch(search, (val) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    debouncedSearch.value = val;
  }, 300);
});

const params = computed(() => {
  const p: Record<string, string> = {};
  if (debouncedSearch.value) p.q = debouncedSearch.value;
  if (filterStatus.value) p.status = filterStatus.value;
  if (filterTypeBase.value) p.type = filterTypeBase.value;
  if (filterCmType.value) p.cm_type = filterCmType.value;
  if (filterAccount.value) p.has_account = filterAccount.value;
  return p;
});

// Reset to page 1 when filters change
watch(
  params,
  () => {
    store.currentPage = 1;
    store.fetchList(params.value, 1);
  },
  { immediate: true },
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

const STATUS_COLOR: Record<string, string> = {
  Alta: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  Out: 'text-red-600 bg-red-50 border-red-200',
  'Dar de baja': 'text-red-600 bg-red-50 border-red-200',
  Descartada: 'text-zinc-500 bg-zinc-100 border-zinc-200',
  Potencial: 'text-blue-600 bg-blue-50 border-blue-200',
};

function statusColor(s: string) {
  return STATUS_COLOR[s] ?? 'text-muted bg-gray-50 border-border';
}

function fmt(n: number | null) {
  if (n == null) return '—';
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
        <h1 class="text-2xl font-semibold tracking-tight text-ink">
          Content Makers
        </h1>
        <p class="text-sm text-muted mt-0.5">
          Gestiona tu comunidad de creadoras
        </p>
      </div>
      <NuxtLink
        v-if="isAdminOrEmployee"
        to="/dashboard/content-makers/new"
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
        Dar de alta
      </NuxtLink>
    </div>

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
          placeholder="Buscar por nombre o email…"
          class="input-field !pl-12"
        />
      </div>

      <BaseSelect
        v-if="isAdminOrEmployee"
        v-model="filterStatus"
        class="min-w-[180px] max-w-[200px]"
        :options="[
          { value: '', label: 'Todos los estados' },
          ...store.filterOptions.statuses.map((s) => ({ value: s, label: s })),
        ]"
      />

      <BaseSelect
        v-model="filterTypeBase"
        class="min-w-[180px] max-w-[200px]"
        :options="[
          { value: '', label: 'Todos (CM y Colab.)' },
          ...store.filterOptions.type_choices.map((t) => ({
            value: t.value,
            label: t.label,
          })),
        ]"
      />

      <BaseSelect
        v-model="filterCmType"
        class="min-w-[180px] max-w-[200px]"
        :options="[
          { value: '', label: 'Todos los subtipos' },
          ...store.filterOptions.types.map((t) => ({ value: t, label: t })),
        ]"
      />

      <BaseSelect
        v-if="isAdminOrEmployee"
        v-model="filterAccount"
        class="min-w-[150px] max-w-[170px]"
        :options="[
          { value: '', label: 'Cuenta' },
          { value: 'true', label: 'Con cuenta' },
          { value: 'false', label: 'Sin cuenta' },
        ]"
      />

      <button
        v-if="
          filterStatus ||
          filterTypeBase ||
          filterCmType ||
          filterAccount ||
          search
        "
        class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
        @click="
          search = '';
          filterStatus = '';
          filterTypeBase = '';
          filterCmType = '';
          filterAccount = '';
        "
      >
        Limpiar
      </button>
    </div>

    <!-- Table (admin/employee view) -->
    <div
      v-if="isAdminOrEmployee"
      class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden"
    >
      <!-- Loading -->
      <div v-if="store.isLoading" class="flex justify-center items-center h-48">
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
                Nombre
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden md:table-cell"
              >
                Instagram
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden lg:table-cell"
              >
                TikTok
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider hidden lg:table-cell"
              >
                Contenido
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider"
              >
                Estado
              </th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-wider"
              >
                Cuenta
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.list.length === 0">
              <td colspan="6" class="text-center py-16 text-sm text-muted">
                Sin resultados con estos filtros.
              </td>
            </tr>
            <tr
              v-for="cm in store.list"
              :key="cm.id"
              class="border-b border-border/30 table-row-hover cursor-pointer group"
              @click="navigateTo(`/dashboard/content-makers/${cm.id}`)"
            >
              <td class="px-5 py-3.5">
                <div>
                  <div class="flex items-center gap-2">
                    <p
                      class="text-sm text-ink font-medium group-hover:text-gold transition-colors duration-150"
                    >
                      {{ cm.full_name }}
                    </p>
                    <span
                      v-if="cm.type === 'colaborador'"
                      class="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded border text-indigo-600 bg-indigo-50 border-indigo-200"
                    >
                      Colaborador
                    </span>
                  </div>
                  <p class="text-xs text-muted mt-0.5">
                    {{ formatContentMakerId(cm.stimada_id) }}
                  </p>
                </div>
              </td>
              <td class="px-4 py-3.5 hidden md:table-cell">
                <div v-if="cm.instagram_handle">
                  <p class="text-sm text-ink/80">@{{ cm.instagram_handle }}</p>
                  <p class="text-xs text-muted">
                    {{ fmt(cm.instagram_followers) }}
                  </p>
                </div>
                <span v-else class="text-xs text-muted/60">—</span>
              </td>
              <td class="px-4 py-3.5 hidden lg:table-cell">
                <div v-if="cm.tiktok_handle">
                  <p class="text-sm text-ink/80">{{ cm.tiktok_handle }}</p>
                  <p class="text-xs text-muted">
                    {{ fmt(cm.tiktok_followers) }}
                  </p>
                </div>
                <span v-else class="text-xs text-muted/60">—</span>
              </td>
              <td class="px-4 py-3.5">
                <p class="text-sm text-muted truncate max-w-[150px]">
                  {{ cm.content_categories || '—' }}
                </p>
              </td>
              <td class="px-4 py-3.5">
                <span
                  class="inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-lg border"
                  :class="statusColor(cm.status)"
                >
                  {{ cm.status || '—' }}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <span
                  v-if="cm.has_account"
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
        <div
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
            <!-- Prev -->
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

            <!-- Page numbers -->
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

            <!-- Next -->
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

    <!-- Gallery (client view) -->
    <div v-else>
      <!-- Loading -->
      <div v-if="store.isLoading" class="flex justify-center items-center h-48">
        <div
          class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin"
        />
      </div>

      <template v-else>
        <!-- Photo Grid -->
        <div
          v-if="store.list.length > 0"
          class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3"
        >
          <NuxtLink
            v-for="cm in store.list"
            :key="cm.id"
            :to="`/dashboard/content-makers/${cm.id}`"
            class="group block"
          >
            <div
              class="relative aspect-[3/4] rounded-xl overflow-hidden border border-border/40 group-hover:border-gold/60 group-hover:shadow-lg transition-all duration-300"
            >
              <!-- Photo -->
              <img
                v-if="cm.photo_url"
                :src="cm.photo_url"
                :alt="cm.full_name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div
                v-else
                class="w-full h-full bg-gradient-to-br from-gold/10 to-gold/5 flex items-center justify-center"
              >
                <span class="text-3xl font-bold text-gold/40"
                  >{{ cm.first_name?.charAt(0)
                  }}{{ cm.last_name?.charAt(0) }}</span
                >
              </div>

              <!-- Hover overlay with social info -->
              <div
                class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-3"
              >
                <div class="space-y-1">
                  <div
                    v-if="cm.instagram_handle"
                    class="flex items-center gap-1.5"
                  >
                    <svg
                      class="w-3.5 h-3.5 text-white/80"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"
                      />
                    </svg>
                    <span class="text-[11px] text-white/90 font-medium"
                      >@{{ cm.instagram_handle }}</span
                    >
                    <span
                      v-if="cm.instagram_followers"
                      class="text-[10px] text-white/60"
                      >· {{ fmt(cm.instagram_followers) }}</span
                    >
                  </div>
                  <div
                    v-if="cm.tiktok_handle"
                    class="flex items-center gap-1.5"
                  >
                    <svg
                      class="w-3.5 h-3.5 text-white/80"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"
                      />
                    </svg>
                    <span class="text-[11px] text-white/90 font-medium">{{
                      cm.tiktok_handle
                    }}</span>
                    <span
                      v-if="cm.tiktok_followers"
                      class="text-[10px] text-white/60"
                      >· {{ fmt(cm.tiktok_followers) }}</span
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- Name below -->
            <p
              class="mt-2 text-sm font-medium text-ink text-center truncate group-hover:text-gold transition-colors duration-200"
            >
              {{ cm.full_name }}
            </p>
          </NuxtLink>
        </div>

        <!-- No results -->
        <div v-else class="text-center py-16">
          <p class="text-sm text-muted">Sin resultados con estos filtros.</p>
        </div>

        <!-- Pagination -->
        <div
          v-if="store.list.length > 0"
          class="flex items-center justify-between mt-6"
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
  </div>
</template>
