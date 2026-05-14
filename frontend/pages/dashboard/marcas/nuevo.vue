<script setup lang="ts">
import { useBrandsStore } from "~/stores/brands";
import { useClientsStore } from "~/stores/clients";

definePageMeta({ middleware: ["auth", "role"] });

const brandsStore = useBrandsStore();
const clientsStore = useClientsStore();
const router = useRouter();

onMounted(() => clientsStore.fetchTypes());

// Client search
const clientSearch = ref("");
const clientResults = ref<any[]>([]);
const selectedClient = ref<any>(null);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

function onClientSearch() {
  if (searchTimeout) clearTimeout(searchTimeout);
  if (!clientSearch.value.trim()) {
    clientResults.value = [];
    return;
  }
  searchTimeout = setTimeout(async () => {
    clientResults.value = await brandsStore.searchClients(clientSearch.value);
  }, 300);
}

function selectClient(client: any) {
  selectedClient.value = client;
  clientSearch.value = "";
  clientResults.value = [];
  // Auto-inherit fields if client is not an agency
  if (!client.es_agencia) {
    form.nombre = client.nombre_cliente;
    form.tipo_marca = client.tipo_cliente;
    form.web_instagram = client.web_instagram || "";
  }
}

function clearClient() {
  selectedClient.value = null;
  form.nombre = "";
  form.tipo_marca = null;
  form.web_instagram = "";
}

// Form
const form = reactive({
  nombre: "",
  tipo_marca: null as number | null,
  web_instagram: "",
  notas: "",
});

const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

async function handleSubmit() {
  errors.value = {};
  if (!selectedClient.value) {
    errors.value.client = "Debes seleccionar un cliente.";
    return;
  }
  if (!form.nombre.trim()) {
    errors.value.nombre = "El nombre de la marca es obligatorio.";
    return;
  }

  isLoading.value = true;
  try {
    await brandsStore.create({
      client: selectedClient.value.id,
      nombre: form.nombre,
      tipo_marca: form.tipo_marca || null,
      web_instagram: form.web_instagram,
      notas: form.notas,
    });
    router.push("/dashboard/marcas");
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        errors.value[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
      });
    } else {
      errors.value.general = "Error al crear la marca.";
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="max-w-2xl animate-fade-up">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-7">
      <NuxtLink to="/dashboard/marcas" class="flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Marcas
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nueva marca</span>
    </div>

    <div class="mb-6">
      <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Alta</p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">Nueva marca</h1>
    </div>

    <form class="space-y-5" @submit.prevent="handleSubmit">
      <!-- 1. Seleccionar cliente -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Cliente asociado</h3>
        </div>

        <!-- Selected client -->
        <div v-if="selectedClient" class="flex items-center justify-between p-3.5 rounded-xl border border-blue-400/30 bg-blue-400/[0.04]">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-400/20 flex items-center justify-center">
              <span class="text-sm font-bold text-blue-400">{{ selectedClient.nombre_cliente.charAt(0) }}</span>
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ selectedClient.nombre_cliente }}</p>
              <p class="text-[10px] text-muted/70">
                {{ selectedClient.es_agencia ? 'Agencia' : 'Marca directa' }}
                <span v-if="selectedClient.tipo_nombre"> · {{ selectedClient.tipo_nombre }}</span>
              </p>
            </div>
          </div>
          <button type="button" class="text-xs text-red-400 hover:text-red-300 transition-colors" @click="clearClient">
            Cambiar
          </button>
        </div>

        <!-- Search -->
        <div v-else>
          <input
            v-model="clientSearch"
            type="text"
            class="input-field"
            placeholder="Buscar cliente por nombre…"
            @input="onClientSearch"
          />
          <div v-if="clientResults.length" class="mt-2 rounded-xl border border-border/60 max-h-48 overflow-auto bg-white">
            <button
              v-for="c in clientResults"
              :key="c.id"
              type="button"
              class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
              @click="selectClient(c)"
            >
              <span class="font-medium text-ink">{{ c.nombre_cliente }}</span>
              <span class="text-muted ml-2 text-xs">{{ c.es_agencia ? '(Agencia)' : '(Marca directa)' }}</span>
            </button>
          </div>
          <p v-if="errors.client" class="text-xs text-red-400 mt-1.5">{{ errors.client }}</p>
        </div>

        <!-- Inheritance notice -->
        <div v-if="selectedClient && !selectedClient.es_agencia" class="rounded-lg bg-blue-50 border border-blue-200/50 px-4 py-2.5">
          <p class="text-xs text-blue-600">
            <strong>Herencia automática:</strong> Como el cliente es una marca directa, los datos se han heredado automáticamente. Puedes ajustarlos si es necesario.
          </p>
        </div>
      </div>

      <!-- 2. Datos de la marca -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
            <svg class="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
            </svg>
          </div>
          <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Datos de la marca</h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Nombre de la marca *</label>
            <input v-model="form.nombre" type="text" required class="input-field" placeholder="Nombre comercial" />
            <p v-if="errors.nombre" class="text-xs text-red-400 mt-1">{{ errors.nombre }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Tipo de marca *</label>
            <select v-model="form.tipo_marca" class="select-field">
              <option :value="null">Seleccionar tipo…</option>
              <option v-for="t in clientsStore.types" :key="t.id" :value="t.id">{{ t.nombre }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Web / Instagram</label>
            <input v-model="form.web_instagram" type="url" class="input-field" placeholder="https://..." />
          </div>
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Notas</label>
            <textarea v-model="form.notas" rows="3" class="input-field resize-none" placeholder="Notas internas sobre la marca…" />
          </div>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="errors.general" class="rounded-xl border border-red-500/20 bg-red-500/[0.04] p-3 text-xs text-red-400">
        {{ errors.general }}
      </div>

      <!-- Submit -->
      <div class="flex justify-end">
        <button
          type="submit"
          :disabled="isLoading"
          class="h-9 px-6 rounded-xl bg-gold text-ink text-xs font-semibold flex items-center gap-2 hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all"
        >
          <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ isLoading ? 'Creando…' : 'Crear marca' }}
        </button>
      </div>
    </form>
  </div>
</template>
