<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useProjectsStore } from "~/stores/projects";

const emit = defineEmits<{ close: []; created: [] }>();

const auth = useAuthStore();
const projectsStore = useProjectsStore();
const config = useRuntimeConfig();

// Steps
const currentStep = ref(1);
const totalSteps = 4;
const isSubmitting = ref(false);
const error = ref("");

// Step 1: Client & Brand
const clients = ref<{ id: number; nombre_cliente: string; cliente_id: string; es_agencia: boolean }[]>([]);
const brands = ref<{ id: number; nombre: string }[]>([]);
const clientSearch = ref("");
const selectedClient = ref<number | null>(null);
const selectedBrand = ref<number | null>(null);
const clientSearchResults = computed(() => {
  if (!clientSearch.value.trim()) return clients.value.slice(0, 10);
  const q = clientSearch.value.toLowerCase();
  return clients.value.filter(
    (c) => c.nombre_cliente.toLowerCase().includes(q) || c.cliente_id.toLowerCase().includes(q)
  );
});

watch(selectedClient, async (id) => {
  if (!id) { brands.value = []; return; }
  try {
    const data = await $fetch<{ id: number; nombre: string }[]>(
      `${config.public.apiBase}/clients/${id}/brands/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    brands.value = data;
  } catch {
    brands.value = [];
  }
});

// Step 2: Project details
const form = reactive({
  project_id: "",
  nombre: "",
  descripcion: "",
  service_type: null as number | null,
  status: null as number | null,
  base_imponible: "",
  impuestos: "",
  fecha_venta: "",
  fecha_servicio: "",
  fecha_fin: "",
});

const statuses = ref<{ id: number; nombre: string }[]>([]);
const serviceTypes = ref<{ id: number; nombre: string }[]>([]);

// Step 3: Content Maker
const cmSelectionMode = ref<"defined" | "recommended" | "client_chooses">("client_chooses");
const cmSearch = ref("");
const cmResults = ref<{ id: number; nombre: string; apellidos: string; instagram_handle: string; seguidores_instagram: number | null }[]>([]);
const selectedCM = ref<number | null>(null);
const recommendedCMs = ref<{ id: number; nombre: string; apellidos: string; instagram_handle: string }[]>([]);

async function searchCMs() {
  if (!cmSearch.value.trim()) { cmResults.value = []; return; }
  try {
    const data = await $fetch<{ results: typeof cmResults.value }>(
      `${config.public.apiBase}/content-makers/?q=${encodeURIComponent(cmSearch.value)}&page_size=10`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    cmResults.value = data.results;
  } catch {
    cmResults.value = [];
  }
}

function selectDefinedCM(cm: typeof cmResults.value[0]) {
  selectedCM.value = cm.id;
  cmSearch.value = `${cm.nombre} ${cm.apellidos}`;
  cmResults.value = [];
}

function addRecommendedCM(cm: typeof cmResults.value[0]) {
  if (!recommendedCMs.value.find((r) => r.id === cm.id)) {
    recommendedCMs.value.push({ id: cm.id, nombre: cm.nombre, apellidos: cm.apellidos, instagram_handle: cm.instagram_handle });
  }
  cmSearch.value = "";
  cmResults.value = [];
}

function removeRecommendedCM(id: number) {
  recommendedCMs.value = recommendedCMs.value.filter((r) => r.id !== id);
}

// Auto-calculate fecha_fin
watch(() => form.fecha_venta, (val) => {
  if (val && !form.fecha_fin) {
    const d = new Date(val);
    d.setDate(d.getDate() + 14);
    form.fecha_fin = d.toISOString().split("T")[0];
  }
});

// Watch CM search with debounce
let cmSearchTimeout: ReturnType<typeof setTimeout>;
watch(cmSearch, (val) => {
  clearTimeout(cmSearchTimeout);
  if (val.trim().length >= 2) {
    cmSearchTimeout = setTimeout(searchCMs, 300);
  } else {
    cmResults.value = [];
  }
});

// Load data
onMounted(async () => {
  try {
    const [clientsData, statusData, typesData] = await Promise.all([
      $fetch<{ results: typeof clients.value }>(`${config.public.apiBase}/clients/?page_size=500`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      }),
      $fetch<typeof statuses.value>(`${config.public.apiBase}/projects/filters/`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      }),
      Promise.resolve(null),
    ]);
    clients.value = clientsData.results;
  } catch {
    // silent
  }
  // Load statuses and service types for dropdowns
  try {
    const data = await $fetch<{ statuses: { id: number; nombre: string }[]; service_types: { id: number; nombre: string }[] }>(
      `${config.public.apiBase}/projects/filters/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    statuses.value = data.statuses;
    serviceTypes.value = data.service_types;
  } catch {
    // silent
  }
});

// Navigation
function nextStep() {
  error.value = "";
  if (currentStep.value === 1 && !selectedClient.value) {
    error.value = "Debes seleccionar un cliente.";
    return;
  }
  if (currentStep.value === 2 && (!form.nombre || !form.project_id)) {
    error.value = "Nombre e ID del proyecto son obligatorios.";
    return;
  }
  if (currentStep.value < totalSteps) currentStep.value++;
}

function prevStep() {
  error.value = "";
  if (currentStep.value > 1) currentStep.value--;
}

// Submit
async function submit() {
  error.value = "";
  isSubmitting.value = true;

  try {
    const payload: Record<string, unknown> = {
      project_id: form.project_id,
      nombre: form.nombre,
      descripcion: form.descripcion,
      client: selectedClient.value,
      brand: selectedBrand.value || null,
      status: form.status,
      service_type: form.service_type,
      base_imponible: form.base_imponible || "0",
      impuestos: form.impuestos || "0",
      fecha_venta: form.fecha_venta || null,
      fecha_servicio: form.fecha_servicio || null,
      fecha_fin: form.fecha_fin || null,
      cm_selection_mode: cmSelectionMode.value,
      content_maker: cmSelectionMode.value === "defined" ? selectedCM.value : null,
      recommended_cms: cmSelectionMode.value === "recommended" ? recommendedCMs.value.map((c) => c.id) : [],
    };

    await projectsStore.createProject(payload);
    emit("created");
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      const msgs = Object.values(e.data).flat();
      error.value = msgs.join(" ");
    } else {
      error.value = "Error al crear el proyecto.";
    }
  } finally {
    isSubmitting.value = false;
  }
}

const stepLabels = ["Cliente", "Detalles", "Content Maker", "Resumen"];
</script>

<template>
  <!-- Overlay -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')" />

      <!-- Modal -->
      <div class="relative w-full max-w-2xl bg-white rounded-2xl shadow-elevated overflow-hidden animate-scale-in">
        <!-- Header -->
        <div class="px-8 pt-8 pb-4">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-ink">Nuevo proyecto</h2>
            <button class="w-8 h-8 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-panel/80 transition-colors" @click="emit('close')">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Step indicator -->
          <div class="flex items-center gap-2 mb-2">
            <template v-for="(label, i) in stepLabels" :key="i">
              <div class="flex items-center gap-2">
                <div
                  class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition-all duration-300"
                  :class="currentStep > i + 1
                    ? 'bg-gold text-white'
                    : currentStep === i + 1
                      ? 'bg-gold/15 text-gold border border-gold/30'
                      : 'bg-panel text-muted border border-border/60'"
                >
                  <svg v-if="currentStep > i + 1" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  <span v-else>{{ i + 1 }}</span>
                </div>
                <span class="text-xs font-medium hidden sm:inline" :class="currentStep === i + 1 ? 'text-ink' : 'text-muted'">{{ label }}</span>
              </div>
              <div v-if="i < stepLabels.length - 1" class="flex-1 h-px" :class="currentStep > i + 1 ? 'bg-gold/40' : 'bg-border/60'" />
            </template>
          </div>
        </div>

        <!-- Body -->
        <div class="px-8 pb-4 max-h-[60vh] overflow-auto">
          <!-- Error -->
          <p v-if="error" class="text-xs text-red-500 bg-red-50 rounded-xl px-4 py-2.5 mb-4">{{ error }}</p>

          <!-- Step 1: Client & Brand -->
          <div v-if="currentStep === 1" class="space-y-5 animate-fade-up">
            <div>
              <label class="block text-xs font-medium text-muted mb-1.5">Buscar cliente *</label>
              <input
                v-model="clientSearch"
                type="text"
                placeholder="Nombre o ID del cliente…"
                class="input-field"
              />
              <div v-if="clientSearchResults.length && !selectedClient" class="mt-2 rounded-xl border border-border/60 max-h-48 overflow-auto">
                <button
                  v-for="c in clientSearchResults"
                  :key="c.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="selectedClient = c.id; clientSearch = c.nombre_cliente"
                >
                  <span class="font-medium text-ink">{{ c.nombre_cliente }}</span>
                  <span class="text-muted ml-2 text-xs">{{ c.cliente_id }}</span>
                  <span v-if="c.es_agencia" class="ml-2 text-[10px] px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-600 font-medium">Agencia</span>
                </button>
              </div>
              <div v-if="selectedClient" class="mt-2 flex items-center gap-2">
                <span class="text-xs text-gold font-medium">✓ Cliente seleccionado</span>
                <button class="text-xs text-muted hover:text-red-500 transition-colors" @click="selectedClient = null; selectedBrand = null; clientSearch = ''">Cambiar</button>
              </div>
            </div>

            <div v-if="selectedClient && brands.length > 0">
              <label class="block text-xs font-medium text-muted mb-1.5">Marca (opcional)</label>
              <select v-model="selectedBrand" class="select-field">
                <option :value="null">Sin marca específica</option>
                <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.nombre }}</option>
              </select>
            </div>
          </div>

          <!-- Step 2: Project details -->
          <div v-if="currentStep === 2" class="space-y-4 animate-fade-up">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">ID del proyecto *</label>
                <input v-model="form.project_id" type="text" placeholder="STM-001" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Tipo de servicio</label>
                <select v-model="form.service_type" class="select-field">
                  <option :value="null">Seleccionar…</option>
                  <option v-for="st in serviceTypes" :key="st.id" :value="st.id">{{ st.nombre }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-muted mb-1.5">Nombre del proyecto *</label>
              <input v-model="form.nombre" type="text" placeholder="Campaña verano 2026…" class="input-field" />
            </div>

            <div>
              <label class="block text-xs font-medium text-muted mb-1.5">Descripción</label>
              <textarea v-model="form.descripcion" rows="3" placeholder="Detalles del proyecto…" class="input-field" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Base imponible (€)</label>
                <input v-model="form.base_imponible" type="number" step="0.01" placeholder="0.00" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Impuestos (€)</label>
                <input v-model="form.impuestos" type="number" step="0.01" placeholder="0.00" class="input-field" />
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-muted mb-1.5">Estado</label>
              <select v-model="form.status" class="select-field">
                <option :value="null">Seleccionar…</option>
                <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.nombre }}</option>
              </select>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Fecha de venta</label>
                <input v-model="form.fecha_venta" type="date" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Fecha de servicio</label>
                <input v-model="form.fecha_servicio" type="date" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Fecha fin</label>
                <input v-model="form.fecha_fin" type="date" class="input-field" />
              </div>
            </div>
          </div>

          <!-- Step 3: Content Maker -->
          <div v-if="currentStep === 3" class="space-y-5 animate-fade-up">
            <div>
              <label class="block text-xs font-medium text-muted mb-3">¿Cómo se asignará la Content Maker?</label>
              <div class="grid grid-cols-1 gap-2">
                <label
                  v-for="opt in [
                    { value: 'defined', label: 'Ya está definida', desc: 'Seleccionas directamente la content maker' },
                    { value: 'recommended', label: 'Recomendar opciones', desc: 'Sugieres varias opciones al cliente' },
                    { value: 'client_chooses', label: 'El cliente elige', desc: 'El cliente explora y selecciona por sí mismo' },
                  ]"
                  :key="opt.value"
                  class="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200"
                  :class="cmSelectionMode === opt.value ? 'border-gold/40 bg-gold/5' : 'border-border/60 hover:border-border'"
                >
                  <input v-model="cmSelectionMode" type="radio" :value="opt.value" class="mt-0.5 accent-[#c9a84c]" />
                  <div>
                    <p class="text-sm font-medium text-ink">{{ opt.label }}</p>
                    <p class="text-xs text-muted mt-0.5">{{ opt.desc }}</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Defined: search and select one -->
            <div v-if="cmSelectionMode === 'defined'" class="space-y-3">
              <label class="block text-xs font-medium text-muted mb-1.5">Buscar Content Maker</label>
              <input
                v-model="cmSearch"
                type="text"
                placeholder="Nombre o @instagram…"
                class="input-field"
              />
              <div v-if="cmResults.length" class="rounded-xl border border-border/60 max-h-48 overflow-auto">
                <button
                  v-for="cm in cmResults"
                  :key="cm.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="selectDefinedCM(cm)"
                >
                  <span class="font-medium text-ink">{{ cm.nombre }} {{ cm.apellidos }}</span>
                  <span v-if="cm.instagram_handle" class="text-muted ml-2 text-xs">@{{ cm.instagram_handle }}</span>
                </button>
              </div>
              <p v-if="selectedCM" class="text-xs text-gold font-medium">✓ Content Maker seleccionada</p>
            </div>

            <!-- Recommended: search and add multiple -->
            <div v-if="cmSelectionMode === 'recommended'" class="space-y-3">
              <label class="block text-xs font-medium text-muted mb-1.5">Buscar y añadir recomendaciones</label>
              <input
                v-model="cmSearch"
                type="text"
                placeholder="Nombre o @instagram…"
                class="input-field"
              />
              <div v-if="cmResults.length" class="rounded-xl border border-border/60 max-h-48 overflow-auto">
                <button
                  v-for="cm in cmResults"
                  :key="cm.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="addRecommendedCM(cm)"
                >
                  <span class="font-medium text-ink">{{ cm.nombre }} {{ cm.apellidos }}</span>
                  <span v-if="cm.instagram_handle" class="text-muted ml-2 text-xs">@{{ cm.instagram_handle }}</span>
                </button>
              </div>

              <!-- Selected recommendations -->
              <div v-if="recommendedCMs.length" class="space-y-1.5">
                <p class="text-xs text-muted font-medium">Recomendadas ({{ recommendedCMs.length }}):</p>
                <div v-for="cm in recommendedCMs" :key="cm.id" class="flex items-center justify-between px-3 py-2 rounded-lg bg-panel/60 border border-border/40">
                  <span class="text-xs text-ink font-medium">{{ cm.nombre }} {{ cm.apellidos }} <span class="text-muted">@{{ cm.instagram_handle }}</span></span>
                  <button class="text-xs text-red-400 hover:text-red-600 transition-colors" @click="removeRecommendedCM(cm.id)">Quitar</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 4: Summary -->
          <div v-if="currentStep === 4" class="space-y-4 animate-fade-up">
            <div class="rounded-xl border border-border/60 divide-y divide-border/40">
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Cliente</span>
                <span class="text-xs text-ink font-medium">{{ clientSearch }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">ID Proyecto</span>
                <span class="text-xs text-ink font-medium">{{ form.project_id }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Nombre</span>
                <span class="text-xs text-ink font-medium">{{ form.nombre }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Tipo de servicio</span>
                <span class="text-xs text-ink font-medium">{{ serviceTypes.find(s => s.id === form.service_type)?.nombre || '—' }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Precio total</span>
                <span class="text-xs text-ink font-medium">{{ (parseFloat(form.base_imponible || '0') + parseFloat(form.impuestos || '0')).toFixed(2) }} €</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Fechas</span>
                <span class="text-xs text-ink font-medium">{{ form.fecha_venta || '—' }} → {{ form.fecha_fin || '—' }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Content Maker</span>
                <span class="text-xs text-ink font-medium">
                  <template v-if="cmSelectionMode === 'defined'">Definida</template>
                  <template v-else-if="cmSelectionMode === 'recommended'">{{ recommendedCMs.length }} recomendadas</template>
                  <template v-else>El cliente elige</template>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-8 py-5 border-t border-border/40 flex items-center justify-between">
          <button
            v-if="currentStep > 1"
            class="px-4 py-2 rounded-xl text-sm text-muted hover:text-ink border border-border/60 hover:border-border transition-all duration-200"
            @click="prevStep"
          >
            Atrás
          </button>
          <div v-else />

          <div class="flex items-center gap-3">
            <button
              class="px-4 py-2 rounded-xl text-sm text-muted hover:text-ink transition-colors"
              @click="emit('close')"
            >
              Cancelar
            </button>
            <button
              v-if="currentStep < totalSteps"
              class="px-5 py-2.5 rounded-xl text-sm font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm active:scale-[0.97] transition-all duration-200"
              @click="nextStep"
            >
              Siguiente
            </button>
            <button
              v-else
              :disabled="isSubmitting"
              class="px-5 py-2.5 rounded-xl text-sm font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm active:scale-[0.97] transition-all duration-200 disabled:opacity-50"
              @click="submit"
            >
              {{ isSubmitting ? "Creando…" : "Crear proyecto" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
