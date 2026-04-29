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

watch(params, () => store.fetchList(params.value), { immediate: true });
onMounted(() => store.fetchTypes());
</script>

<template>
  <div class="space-y-5 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Directorio</p>
        <h1 class="text-3xl font-semibold tracking-tight text-cream">Clientes</h1>
      </div>
      <NuxtLink
        to="/dashboard/clientes/nuevo"
        class="flex items-center gap-2 h-9 px-4 rounded-xl bg-gold text-ink text-xs font-semibold
               hover:bg-gold/90 active:scale-[0.98] transition-all duration-150"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Dar de alta cliente
      </NuxtLink>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[200px] max-w-xs">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input v-model="search" type="text" placeholder="Buscar cliente o ID…" class="input-field pl-9 text-xs" />
      </div>
      <select v-model="filterTipo" class="input-field text-xs max-w-[200px]">
        <option value="">Todos los tipos</option>
        <option v-for="t in store.types" :key="t.slug" :value="t.slug">{{ t.nombre }}</option>
      </select>
      <button
        v-if="search || filterTipo"
        class="px-3 h-10 rounded-xl text-xs text-muted hover:text-cream border border-border hover:border-subtle transition-colors"
        @click="search = ''; filterTipo = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border overflow-hidden" style="background:#0f0f11">
      <div v-if="store.isLoading" class="flex justify-center items-center h-40">
        <svg class="animate-spin w-5 h-5 text-gold" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-border">
            <th v-for="col in ['Cliente', 'ID', 'Tipo', 'Ciudad', 'Contrato', 'Alta por', 'Fecha']"
                :key="col"
                class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-widest">
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!store.list.length">
            <td colspan="7" class="text-center py-14 text-sm text-muted">
              {{ store.isLoading ? '' : 'No hay clientes registrados aún.' }}
            </td>
          </tr>
          <tr
            v-for="client in store.list"
            :key="client.id"
            class="border-b border-border/40 hover:bg-white/[0.02] cursor-pointer transition-colors group"
            @click="navigateTo(`/dashboard/clientes/${client.id}`)"
          >
            <td class="px-5 py-3.5">
              <p class="text-sm text-cream font-medium group-hover:text-gold transition-colors">{{ client.nombre_cliente }}</p>
            </td>
            <td class="px-5 py-3.5 text-xs text-muted font-mono">{{ client.cliente_id }}</td>
            <td class="px-5 py-3.5">
              <span v-if="client.tipo_nombre" class="text-xs px-2 py-0.5 rounded-full border border-blue-400/20 text-blue-400 bg-blue-400/8">
                {{ client.tipo_nombre }}
              </span>
              <span v-else class="text-xs text-muted">—</span>
            </td>
            <td class="px-5 py-3.5 text-xs text-muted">{{ client.ciudad || '—' }}</td>
            <td class="px-5 py-3.5">
              <span v-if="client.contrato_firmado" class="flex items-center gap-1 text-xs text-green-400">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                </svg>
                Firmado
              </span>
              <span v-else class="text-xs text-muted">Pendiente</span>
            </td>
            <td class="px-5 py-3.5 text-xs text-muted">{{ client.created_by_name || '—' }}</td>
            <td class="px-5 py-3.5 text-xs text-muted">
              {{ new Date(client.created_at).toLocaleDateString('es-ES', { day:'2-digit', month:'short', year:'numeric' }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
