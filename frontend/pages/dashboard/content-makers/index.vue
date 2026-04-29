<script setup lang="ts">
import { useContentMakersStore } from "~/stores/contentMakers";

definePageMeta({ middleware: ["auth", "role"] });

const store = useContentMakersStore();

const search = ref("");
const filterStatus = ref("");
const filterTipo = ref("");
const filterCuenta = ref("");

const STATUS_OPTIONS = ["Alta", "Contactada", "Aceptada", "Mail Alta enviado", "Entrevista hecha", "Agendada", "Encontrada", "Out", "Dar de baja", "Descartada"];
const TIPO_OPTIONS = ["Content Maker", "Potencial", "Colaborador/a"];

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

watch(params, () => store.fetchList(params.value), { immediate: true });

const STATUS_COLOR: Record<string, string> = {
  Alta: "text-green-400 bg-green-400/10 border-green-400/20",
  Out: "text-red-400 bg-red-400/10 border-red-400/20",
  "Dar de baja": "text-red-400 bg-red-400/10 border-red-400/20",
  Descartada: "text-zinc-500 bg-zinc-500/10 border-zinc-500/20",
  Potencial: "text-blue-400 bg-blue-400/10 border-blue-400/20",
};

function statusColor(s: string) {
  return STATUS_COLOR[s] ?? "text-muted bg-muted/10 border-border";
}

function fmt(n: number | null) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}
</script>

<template>
  <div class="space-y-5 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Comunidad</p>
        <h1 class="text-3xl font-semibold tracking-tight text-cream">Content Makers</h1>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-muted"><span class="text-cream font-semibold">{{ store.list.length }}</span> registradas</span>
        <NuxtLink
          to="/dashboard/content-makers/nuevo"
          class="flex items-center gap-2 h-9 px-4 rounded-xl bg-gold text-ink text-xs font-semibold
                 hover:bg-gold/90 active:scale-[0.98] transition-all duration-150"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Dar de alta CM
        </NuxtLink>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[200px] max-w-xs">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Buscar por nombre o email…"
          class="input-field pl-9 text-xs"
        />
      </div>

      <select v-model="filterStatus" class="input-field text-xs max-w-[160px]">
        <option value="">Todos los estados</option>
        <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
      </select>

      <select v-model="filterTipo" class="input-field text-xs max-w-[160px]">
        <option value="">Todos los tipos</option>
        <option v-for="t in TIPO_OPTIONS" :key="t" :value="t">{{ t }}</option>
      </select>

      <select v-model="filterCuenta" class="input-field text-xs max-w-[160px]">
        <option value="">Todas</option>
        <option value="true">Con cuenta</option>
        <option value="false">Sin cuenta</option>
      </select>

      <button
        v-if="filterStatus || filterTipo || filterCuenta || search"
        class="px-3 h-10 rounded-xl text-xs text-muted hover:text-cream border border-border hover:border-subtle transition-colors"
        @click="search = ''; filterStatus = ''; filterTipo = ''; filterCuenta = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border overflow-hidden" style="background:#0f0f11">
      <!-- Loading -->
      <div v-if="store.isLoading" class="flex justify-center items-center h-40">
        <svg class="animate-spin w-5 h-5 text-gold" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-border">
            <th class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-widest">Nombre</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-widest hidden md:table-cell">Instagram</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-widest hidden lg:table-cell">TikTok</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-widest hidden lg:table-cell">Contenido</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-widest">Estado</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-muted uppercase tracking-widest">Cuenta</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="store.list.length === 0">
            <td colspan="6" class="text-center py-14 text-sm text-muted">Sin resultados con estos filtros.</td>
          </tr>
          <tr
            v-for="cm in store.list"
            :key="cm.id"
            class="border-b border-border/40 hover:bg-white/[0.02] cursor-pointer transition-colors group"
            @click="navigateTo(`/dashboard/content-makers/${cm.id}`)"
          >
            <td class="px-5 py-3.5">
              <div>
                <p class="text-sm text-cream font-medium group-hover:text-gold transition-colors">
                  {{ cm.nombre_completo }}
                </p>
                <p class="text-xs text-muted mt-0.5">{{ cm.stimada_id }}</p>
              </div>
            </td>
            <td class="px-4 py-3.5 hidden md:table-cell">
              <div v-if="cm.instagram_handle">
                <p class="text-xs text-cream">@{{ cm.instagram_handle }}</p>
                <p class="text-xs text-muted">{{ fmt(cm.seguidores_instagram) }}</p>
              </div>
              <span v-else class="text-xs text-muted">—</span>
            </td>
            <td class="px-4 py-3.5 hidden lg:table-cell">
              <div v-if="cm.tiktok_handle">
                <p class="text-xs text-cream">{{ cm.tiktok_handle }}</p>
                <p class="text-xs text-muted">{{ fmt(cm.seguidores_tiktok) }}</p>
              </div>
              <span v-else class="text-xs text-muted">—</span>
            </td>
            <td class="px-4 py-3.5 hidden lg:table-cell">
              <p class="text-xs text-muted truncate max-w-[150px]">{{ cm.categorias_contenido || "—" }}</p>
            </td>
            <td class="px-4 py-3.5">
              <span
                class="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border"
                :class="statusColor(cm.status)"
              >
                {{ cm.status || "—" }}
              </span>
            </td>
            <td class="px-4 py-3.5">
              <span
                v-if="cm.tiene_cuenta"
                class="inline-flex items-center gap-1 text-xs text-green-400"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                </svg>
                Activa
              </span>
              <span v-else class="text-xs text-muted">Sin cuenta</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
