<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useProjectsStore } from "~/stores/projects";

definePageMeta({
  layout: "app",
  middleware: ["auth"],
});

const auth = useAuthStore();
const store = useProjectsStore();
const router = useRouter();
const showCreateWizard = ref(false);

const canCreate = computed(() =>
  auth.user?.role === "admin" || auth.user?.role === "stimada_employee"
);

const isClient = computed(() => auth.user?.role === "client");

// Filters
const search = ref("");
const filterStatus = ref("");
const filterType = ref("");
const currentPage = ref(1);

async function loadProjects() {
  const params: Record<string, string> = {};
  if (search.value) params.search = search.value;
  if (filterStatus.value) params.status = filterStatus.value;
  if (filterType.value) params.service_type = filterType.value;
  await store.fetchList(params, currentPage.value);
}

watch([search, filterStatus, filterType], () => {
  currentPage.value = 1;
  loadProjects();
});

function goToPage(page: number) {
  currentPage.value = page;
  loadProjects();
}

const totalPages = computed(() => Math.ceil(store.count / 20));

function onProjectCreated() {
  showCreateWizard.value = false;
  loadProjects();
}

onMounted(() => {
  store.fetchFilters();
  loadProjects();
});

function formatDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-8 py-10 space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Proyectos</h1>
        <p class="text-sm text-muted mt-1">Gestión de proyectos con clientes y content makers</p>
      </div>
      <button
        v-if="canCreate"
        class="group inline-flex items-center gap-2 h-10 px-5 rounded-xl text-sm font-medium bg-gold text-white shadow-gold-sm hover:shadow-gold-md active:scale-[0.97] transition-all duration-200"
        @click="showCreateWizard = true"
      >
        <svg class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Crear nuevo proyecto
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="relative flex-1 min-w-[260px] max-w-md group/search">
        <div class="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-all duration-300 group-focus-within/search:scale-90 group-focus-within/search:text-gold">
          <svg class="w-4 h-4 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>
        <input
          v-model="search"
          type="text"
          placeholder="Buscar por nombre, ID o cliente…"
          class="input-field !pl-12"
        />
      </div>

      <select v-model="filterStatus" class="select-field min-w-[170px] max-w-[200px]">
        <option value="">Todos los estados</option>
        <option v-for="s in store.filters.statuses" :key="s.id" :value="s.nombre">{{ s.nombre }}</option>
      </select>

      <select v-model="filterType" class="select-field min-w-[170px] max-w-[200px]">
        <option value="">Todos los tipos</option>
        <option v-for="t in store.filters.service_types" :key="t.id" :value="t.nombre">{{ t.nombre }}</option>
      </select>

      <button
        v-if="search || filterStatus || filterType"
        class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
        @click="search = ''; filterStatus = ''; filterType = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden">
      <div v-if="store.isLoading" class="flex justify-center items-center h-48">
        <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
      </div>
      <template v-else-if="store.list.length">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border/60 bg-panel/50">
              <th v-for="col in (isClient ? ['Proyecto', 'Servicio', 'Estado', 'Total', 'Fecha venta', 'CM'] : ['ID', 'Proyecto', 'Cliente', 'Servicio', 'Estado', 'Total', 'Fecha venta', 'CM'])"
                  :key="col"
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider">
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in store.list"
              :key="p.id"
              class="border-b border-border/30 last:border-0 table-row-hover cursor-pointer"
              @click="router.push(`/proyectos/${p.id}`)"
            >
              <td v-if="!isClient" class="px-5 py-3.5 text-xs font-mono text-muted">{{ formatProjectId(p.project_id) }}</td>
              <td class="px-5 py-3.5 font-medium text-ink">{{ p.nombre }}</td>
              <td v-if="!isClient" class="px-5 py-3.5 text-muted">{{ p.client_name }}</td>
              <td class="px-5 py-3.5">
                <span v-if="p.service_type_name" class="px-2 py-0.5 rounded-md text-xs bg-blue-50 text-blue-700 font-medium">{{ p.service_type_name }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  class="px-2 py-0.5 rounded-md text-xs font-medium"
                  :class="{
                    'bg-emerald-50 text-emerald-700': p.status_name === 'Activo',
                    'bg-amber-50 text-amber-700': p.status_name === 'Pendiente',
                    'bg-blue-50 text-blue-700': p.status_name === 'Briefing',
                    'bg-gray-100 text-gray-600': p.status_name === 'Finalizado',
                    'bg-slate-50 text-slate-500 border border-dashed border-slate-300': p.status_name === 'Borrador',
                  }"
                >{{ p.status_name || '—' }}</span>
              </td>
              <td class="px-5 py-3.5 font-medium text-ink">{{ p.precio_total }} €</td>
              <td class="px-5 py-3.5 text-muted text-xs">{{ formatDate(p.fecha_venta) }}</td>
              <td class="px-5 py-3.5 text-xs">
                <span v-if="p.content_maker_name" class="text-muted">{{ p.content_maker_name }}</span>
                <span v-else class="px-2 py-0.5 rounded-md text-xs font-medium bg-red-50 text-red-600">Sin content maker</span>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
      <div v-else class="px-8 py-16 text-center">
        <div class="w-12 h-12 rounded-2xl bg-panel border border-border/60 flex items-center justify-center mx-auto mb-4">
          <svg class="w-6 h-6 text-muted/40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
          </svg>
        </div>
        <h3 class="text-sm font-medium text-ink mb-1">Sin proyectos</h3>
        <p class="text-xs text-muted">Crea tu primer proyecto para empezar</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center gap-1.5">
      <button
        v-for="page in totalPages"
        :key="page"
        class="w-8 h-8 rounded-lg text-xs font-medium transition-all duration-200"
        :class="page === currentPage ? 'bg-gold text-white shadow-gold-sm' : 'text-muted hover:text-ink hover:bg-panel'"
        @click="goToPage(page)"
      >
        {{ page }}
      </button>
    </div>

    <!-- Create Wizard -->
    <ProjectsCreateProjectWizard
      v-if="showCreateWizard"
      @close="showCreateWizard = false"
      @created="onProjectCreated"
    />
  </div>
</template>
