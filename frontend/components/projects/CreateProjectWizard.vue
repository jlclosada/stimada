<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import { useProjectsStore } from '~/stores/projects';
import { formatBrandId } from '~/utils/formatId';

const emit = defineEmits<{ close: []; created: [] }>();

const auth = useAuthStore();
const projectsStore = useProjectsStore();
const config = useRuntimeConfig();

// Steps
const currentStep = ref(1);
const totalSteps = 5;
const isSubmitting = ref(false);
const error = ref('');

// Step 1: Brand selection (project → brand → client auto-inherited)
const brandSearch = ref('');
const brandResults = ref<
  {
    id: number;
    brand_id: string;
    name: string;
    client: number;
    client_name: string;
  }[]
>([]);
const selectedBrand = ref<number | null>(null);
const selectedBrandName = ref('');
const inheritedClientName = ref('');

let brandSearchTimeout: ReturnType<typeof setTimeout>;
watch(brandSearch, (val) => {
  clearTimeout(brandSearchTimeout);
  if (val.trim().length >= 1 && !selectedBrand.value) {
    brandSearchTimeout = setTimeout(searchBrands, 300);
  } else if (!val.trim()) {
    brandResults.value = [];
  }
});

async function searchBrands() {
  try {
    const data = await $fetch<{ results: typeof brandResults.value }>(
      `${config.public.apiBase}/brands/?q=${encodeURIComponent(brandSearch.value)}&page_size=10`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    );
    brandResults.value = data.results;
  } catch {
    brandResults.value = [];
  }
}

function selectBrand(brand: (typeof brandResults.value)[0]) {
  selectedBrand.value = brand.id;
  selectedBrandName.value = brand.name;
  inheritedClientName.value = brand.client_name;
  brandSearch.value = brand.name;
  brandResults.value = [];
}

function clearBrand() {
  selectedBrand.value = null;
  selectedBrandName.value = '';
  inheritedClientName.value = '';
  brandSearch.value = '';
  brandResults.value = [];
}

// Step 2: Project details
const form = reactive({
  project_id: '',
  name: '',
  description: '',
  service_type: null as number | null,
  economic_model: null as number | null,
  product_logistics: null as number | null,
  product_pickup: null as number | null,
  who_records: null as number | null,
  who_reviews: null as number | null,
  who_publishes: null as number | null,
  product_return: false,
  status: null as number | null,
  win_status: null as number | null,
  traffic_light: null as number | null,
  // Propuesta económica (paso 3)
  fee: '',
  num_contents: '',
  num_profiles: '',
  gifting: false,
  discount_active: false,
  discount_percentage: '',
  sale_date: '',
  service_date: '',
  product_arrival_date: '',
  delivery_deadline: '',
  end_date: '',
  comments: '',
});

// Servicio: red social y formato (aplican a servicios "en perfiles")
const selectedSocialNetworks = ref<number[]>([]);
const selectedFormats = ref<number[]>([]);

const statuses = ref<{ id: number; name: string }[]>([]);
const creationStatuses = ref<{ id: number; name: string }[]>([]);
const serviceTypes = ref<
  { id: number; name: string; requires_profiles?: boolean }[]
>([]);
const socialNetworksOpts = ref<{ id: number; name: string }[]>([]);
const formatsOpts = ref<{ id: number; name: string }[]>([]);
const economicModelsOpts = ref<{ id: number; name: string }[]>([]);
const productLogisticsOpts = ref<{ id: number; name: string }[]>([]);
const productPickupOpts = ref<{ id: number; name: string }[]>([]);
const whoRecordsOpts = ref<{ id: number; name: string }[]>([]);
const whoReviewsOpts = ref<{ id: number; name: string }[]>([]);
const whoPublishesOpts = ref<{ id: number; name: string }[]>([]);
const winStatuses = ref<{ id: number; name: string }[]>([]);

// Whether the selected service type requires red social + formato sections.
const requiresProfiles = computed(() => {
  const st = serviceTypes.value.find((s) => s.id === form.service_type);
  return !!st?.requires_profiles;
});

function toggleSocialNetwork(id: number) {
  const i = selectedSocialNetworks.value.indexOf(id);
  if (i === -1) selectedSocialNetworks.value.push(id);
  else selectedSocialNetworks.value.splice(i, 1);
}

function toggleFormat(id: number) {
  const i = selectedFormats.value.indexOf(id);
  if (i === -1) selectedFormats.value.push(id);
  else selectedFormats.value.splice(i, 1);
}

// Clear red social / formato selection when the service type no longer requires it.
watch(requiresProfiles, (val) => {
  if (!val) {
    selectedSocialNetworks.value = [];
    selectedFormats.value = [];
  }
});

// ── Cálculo de la propuesta económica ────────────────────────────────────
const grossPrice = computed(() => {
  const fee = parseFloat(form.fee) || 0;
  const contents = parseInt(form.num_contents) || 0;
  const profiles = parseInt(form.num_profiles) || 0;
  return fee * contents * profiles;
});

const finalPrice = computed(() => {
  if (form.gifting) return 0;
  let total = grossPrice.value;
  if (form.discount_active) {
    const pct = parseFloat(form.discount_percentage) || 0;
    total = total * (1 - pct / 100);
  }
  return total;
});

// True when the final price differs from the gross price (gifting or discount).
const priceModified = computed(
  () =>
    form.gifting ||
    (form.discount_active && (parseFloat(form.discount_percentage) || 0) > 0),
);

function formatEuro(value: number): string {
  return (
    value.toLocaleString('es-ES', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }) + ' €'
  );
}

// Animated display of the final price (smoothly counts up/down on change).
const displayedPrice = ref(0);
let priceRaf: ReturnType<typeof requestAnimationFrame> | null = null;
watch(finalPrice, (target) => {
  const start = displayedPrice.value;
  const delta = target - start;
  const duration = 450;
  const startTime = performance.now();
  if (priceRaf) cancelAnimationFrame(priceRaf);
  const tick = (now: number) => {
    const t = Math.min((now - startTime) / duration, 1);
    // easeOutCubic
    const eased = 1 - Math.pow(1 - t, 3);
    displayedPrice.value = start + delta * eased;
    if (t < 1) {
      priceRaf = requestAnimationFrame(tick);
    } else {
      displayedPrice.value = target;
    }
  };
  priceRaf = requestAnimationFrame(tick);
});

// Step 3: Content Maker
const cmSelectionMode = ref<'defined' | 'recommended' | 'client_chooses'>(
  'client_chooses',
);
const cmSearch = ref('');
const cmResults = ref<
  {
    id: number;
    first_name: string;
    last_name: string;
    instagram_handle: string;
    instagram_followers: number | null;
  }[]
>([]);
const selectedCMs = ref<
  {
    id: number;
    first_name: string;
    last_name: string;
    instagram_handle: string;
  }[]
>([]);
const recommendedCMs = ref<
  {
    id: number;
    first_name: string;
    last_name: string;
    instagram_handle: string;
  }[]
>([]);
const substituteCMs = ref<
  {
    id: number;
    first_name: string;
    last_name: string;
    instagram_handle: string;
  }[]
>([]);

async function searchCMs() {
  if (!cmSearch.value.trim()) {
    cmResults.value = [];
    return;
  }
  try {
    const data = await $fetch<{ results: typeof cmResults.value }>(
      `${config.public.apiBase}/content-makers/?q=${encodeURIComponent(cmSearch.value)}&page_size=10`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    );
    cmResults.value = data.results;
  } catch {
    cmResults.value = [];
  }
}

function addDefinedCM(cm: (typeof cmResults.value)[0]) {
  if (!selectedCMs.value.find((r) => r.id === cm.id)) {
    selectedCMs.value.push({
      id: cm.id,
      first_name: cm.first_name,
      last_name: cm.last_name,
      instagram_handle: cm.instagram_handle,
    });
  }
  cmSearch.value = '';
  cmResults.value = [];
}

function removeDefinedCM(id: number) {
  selectedCMs.value = selectedCMs.value.filter((r) => r.id !== id);
}

function addRecommendedCM(cm: (typeof cmResults.value)[0]) {
  if (!recommendedCMs.value.find((r) => r.id === cm.id)) {
    recommendedCMs.value.push({
      id: cm.id,
      first_name: cm.first_name,
      last_name: cm.last_name,
      instagram_handle: cm.instagram_handle,
    });
  }
  cmSearch.value = '';
  cmResults.value = [];
}

function removeRecommendedCM(id: number) {
  recommendedCMs.value = recommendedCMs.value.filter((r) => r.id !== id);
}

function addSubstituteCM(cm: (typeof cmResults.value)[0]) {
  if (!substituteCMs.value.find((r) => r.id === cm.id)) {
    substituteCMs.value.push({
      id: cm.id,
      first_name: cm.first_name,
      last_name: cm.last_name,
      instagram_handle: cm.instagram_handle,
    });
  }
  cmSearch.value = '';
  cmResults.value = [];
}

function removeSubstituteCM(id: number) {
  substituteCMs.value = substituteCMs.value.filter((r) => r.id !== id);
}

// Auto-calculate end_date
watch(
  () => form.service_date,
  (val) => {
    if (val && !form.end_date) {
      const d = new Date(val);
      d.setDate(d.getDate() + 14);
      form.end_date = d.toISOString().split('T')[0];
    }
  },
);

// Auto-calculate delivery_deadline from product_arrival_date + 14 days (for UGC)
watch(
  () => form.product_arrival_date,
  (val) => {
    if (val && !form.delivery_deadline) {
      const d = new Date(val);
      d.setDate(d.getDate() + 14);
      form.delivery_deadline = d.toISOString().split('T')[0];
    }
  },
);

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
    const data = await $fetch<Record<string, { id: number; name: string }[]>>(
      `${config.public.apiBase}/projects/filters/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    );
    statuses.value = data.statuses || [];
    creationStatuses.value = data.creation_statuses || [];
    serviceTypes.value = data.service_types || [];
    socialNetworksOpts.value = data.social_networks || [];
    formatsOpts.value = data.formats || [];
    economicModelsOpts.value = data.economic_models || [];
    productLogisticsOpts.value = data.product_logistics || [];
    productPickupOpts.value = data.product_pickup || [];
    whoRecordsOpts.value = data.who_records || [];
    whoReviewsOpts.value = data.who_reviews || [];
    whoPublishesOpts.value = data.who_publishes || [];
    winStatuses.value = data.win_statuses || [];
  } catch {
    // silent
  }
});

// Navigation
function nextStep() {
  error.value = '';
  if (currentStep.value === 1 && !selectedBrand.value) {
    error.value = 'Debes seleccionar una marca.';
    return;
  }
  if (currentStep.value === 2 && !form.name) {
    error.value = 'El nombre del proyecto es obligatorio.';
    return;
  }
  if (currentStep.value === 4) {
    if (cmSelectionMode.value === 'defined' && selectedCMs.value.length === 0) {
      error.value = 'Debes seleccionar al menos una Content Maker.';
      return;
    }
    if (
      cmSelectionMode.value === 'recommended' &&
      recommendedCMs.value.length === 0
    ) {
      error.value = 'Debes recomendar al menos una Content Maker.';
      return;
    }
  }
  if (currentStep.value < totalSteps) currentStep.value++;
}

function prevStep() {
  error.value = '';
  if (currentStep.value > 1) currentStep.value--;
}

// Submit
async function submit() {
  error.value = '';
  isSubmitting.value = true;

  try {
    const payload: Record<string, unknown> = {
      name: form.name,
      description: form.description,
      brand: selectedBrand.value,
      status: form.status,
      service_type: form.service_type,
      economic_model: form.economic_model,
      product_logistics: form.product_logistics,
      product_pickup: form.product_pickup,
      who_records: form.who_records,
      who_reviews: form.who_reviews,
      who_publishes: form.who_publishes,
      product_return: form.product_return,
      win_status: form.win_status,
      traffic_light: form.traffic_light,
      // Servicio: red social y formato
      social_networks: requiresProfiles.value
        ? selectedSocialNetworks.value
        : [],
      formats: requiresProfiles.value ? selectedFormats.value : [],
      // Propuesta económica
      fee: form.fee || '0',
      num_contents: parseInt(form.num_contents) || 0,
      num_profiles: parseInt(form.num_profiles) || 0,
      gifting: form.gifting,
      discount_active: form.discount_active,
      discount_percentage: form.discount_active
        ? form.discount_percentage || '0'
        : '0',
      taxes: '0',
      sale_date: form.sale_date || null,
      service_date: form.service_date || null,
      product_arrival_date: form.product_arrival_date || null,
      delivery_deadline: form.delivery_deadline || null,
      end_date: form.end_date || null,
      comments: form.comments,
      cm_selection_mode: cmSelectionMode.value,
      content_maker: null,
      defined_cms:
        cmSelectionMode.value === 'defined'
          ? selectedCMs.value.map((c) => c.id)
          : [],
      recommended_cms:
        cmSelectionMode.value === 'recommended'
          ? recommendedCMs.value.map((c) => c.id)
          : [],
      substitute_cms: substituteCMs.value.map((c) => c.id),
    };

    await projectsStore.createProject(payload);
    emit('created');
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      const msgs = Object.values(e.data).flat();
      error.value = msgs.join(' ');
    } else {
      error.value = 'Error al crear el proyecto.';
    }
  } finally {
    isSubmitting.value = false;
  }
}

const stepLabels = [
  'Marca',
  'Detalles',
  'Propuesta económica',
  'Content Maker',
  'Resumen',
];

// Exit warning
const showExitWarning = ref(false);

const hasFormData = computed(() => {
  return !!(
    selectedBrand.value ||
    form.name ||
    form.description ||
    selectedCMs.value.length ||
    recommendedCMs.value.length
  );
});

function attemptClose() {
  if (hasFormData.value) {
    showExitWarning.value = true;
  } else {
    emit('close');
  }
}

const savingDraft = ref(false);

async function saveDraftAndClose() {
  savingDraft.value = true;
  try {
    const payload: Record<string, unknown> = {
      name: form.name || '',
      description: form.description,
      brand: selectedBrand.value || null,
      status: form.status,
      service_type: form.service_type,
      economic_model: form.economic_model,
      product_logistics: form.product_logistics,
      product_pickup: form.product_pickup,
      who_records: form.who_records,
      who_reviews: form.who_reviews,
      who_publishes: form.who_publishes,
      product_return: form.product_return,
      win_status: form.win_status,
      traffic_light: form.traffic_light,
      // Servicio: red social y formato
      social_networks: requiresProfiles.value
        ? selectedSocialNetworks.value
        : [],
      formats: requiresProfiles.value ? selectedFormats.value : [],
      // Propuesta económica
      fee: form.fee || '0',
      num_contents: parseInt(form.num_contents) || 0,
      num_profiles: parseInt(form.num_profiles) || 0,
      gifting: form.gifting,
      discount_active: form.discount_active,
      discount_percentage: form.discount_active
        ? form.discount_percentage || '0'
        : '0',
      taxes: '0',
      sale_date: form.sale_date || null,
      service_date: form.service_date || null,
      product_arrival_date: form.product_arrival_date || null,
      delivery_deadline: form.delivery_deadline || null,
      end_date: form.end_date || null,
      comments: form.comments,
      cm_selection_mode: cmSelectionMode.value,
      content_maker: null,
      defined_cms:
        cmSelectionMode.value === 'defined'
          ? selectedCMs.value.map((c) => c.id)
          : [],
      recommended_cms:
        cmSelectionMode.value === 'recommended'
          ? recommendedCMs.value.map((c) => c.id)
          : [],
      substitute_cms: substituteCMs.value.map((c) => c.id),
      is_draft: true,
    };

    await projectsStore.createProject(payload);
    showExitWarning.value = false;
    emit('created');
  } catch {
    // If draft save fails, just close without saving
    showExitWarning.value = false;
    emit('close');
  } finally {
    savingDraft.value = false;
  }
}

function discardAndClose() {
  showExitWarning.value = false;
  emit('close');
}
</script>

<template>
  <!-- Overlay -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/40 backdrop-blur-sm"
        @click="attemptClose"
      />

      <!-- Modal -->
      <div
        class="relative w-full max-w-2xl bg-white rounded-2xl shadow-elevated overflow-hidden animate-scale-in"
      >
        <!-- Header -->
        <div class="px-8 pt-8 pb-4">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-ink">Nuevo proyecto</h2>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-panel/80 transition-colors"
              @click="attemptClose"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <!-- Step indicator -->
          <div class="flex items-center gap-2 mb-2">
            <template v-for="(label, i) in stepLabels" :key="i">
              <div class="flex items-center gap-2">
                <div
                  class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition-all duration-300"
                  :class="
                    currentStep > i + 1
                      ? 'bg-gold text-white'
                      : currentStep === i + 1
                        ? 'bg-gold/15 text-gold border border-gold/30'
                        : 'bg-panel text-muted border border-border/60'
                  "
                >
                  <svg
                    v-if="currentStep > i + 1"
                    class="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M4.5 12.75l6 6 9-13.5"
                    />
                  </svg>
                  <span v-else>{{ i + 1 }}</span>
                </div>
                <span
                  class="text-xs font-medium hidden sm:inline"
                  :class="currentStep === i + 1 ? 'text-ink' : 'text-muted'"
                  >{{ label }}</span
                >
              </div>
              <div
                v-if="i < stepLabels.length - 1"
                class="flex-1 h-px"
                :class="currentStep > i + 1 ? 'bg-gold/40' : 'bg-border/60'"
              />
            </template>
          </div>
        </div>

        <!-- Body -->
        <div class="px-8 pb-4 max-h-[60vh] overflow-auto">
          <!-- Error -->
          <p
            v-if="error"
            class="text-xs text-red-500 bg-red-50 rounded-xl px-4 py-2.5 mb-4"
          >
            {{ error }}
          </p>

          <!-- Step 1: Brand -->
          <div v-if="currentStep === 1" class="space-y-5 animate-fade-up">
            <div>
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Buscar marca *</label
              >
              <input
                v-model="brandSearch"
                type="text"
                placeholder="Nombre de la marca…"
                class="input-field"
                :disabled="!!selectedBrand"
              />
              <div
                v-if="brandResults.length && !selectedBrand"
                class="mt-2 rounded-xl border border-border/60 max-h-48 overflow-auto"
              >
                <button
                  v-for="b in brandResults"
                  :key="b.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="selectBrand(b)"
                >
                  <span class="font-medium text-ink">{{ b.name }}</span>
                  <span class="text-muted ml-2 text-xs">{{
                    formatBrandId(b.brand_id)
                  }}</span>
                  <span class="text-muted/60 ml-2 text-xs"
                    >— {{ b.client_name }}</span
                  >
                </button>
              </div>
              <div v-if="selectedBrand" class="mt-2 flex items-center gap-2">
                <span class="text-xs text-gold font-medium"
                  >✓ Marca seleccionada</span
                >
                <button
                  class="text-xs text-muted hover:text-red-500 transition-colors"
                  @click="clearBrand"
                >
                  Cambiar
                </button>
              </div>
            </div>

            <div
              v-if="selectedBrand"
              class="rounded-xl border border-border/60 bg-panel/30 p-4 space-y-2"
            >
              <p class="text-xs text-muted font-medium">
                Cliente asociado (automático)
              </p>
              <p class="text-sm text-ink font-medium">
                {{ inheritedClientName }}
              </p>
            </div>
          </div>

          <!-- Step 2: Project details -->
          <div v-if="currentStep === 2" class="space-y-4 animate-fade-up">
            <div>
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Nombre del proyecto *</label
              >
              <input
                v-model="form.name"
                type="text"
                placeholder="Campaña verano 2026…"
                class="input-field"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Tipo de servicio</label
                >
                <BaseSelect
                  v-model="form.service_type"
                  placeholder="Seleccionar…"
                  :options="[
                    { value: null, label: 'Seleccionar…' },
                    ...serviceTypes.map((st) => ({
                      value: st.id,
                      label: st.name,
                    })),
                  ]"
                />
              </div>
            </div>

            <!-- Red Social + Formato (solo servicios en perfiles) -->
            <Transition name="fade-expand">
              <div v-if="requiresProfiles" class="space-y-4">
                <div>
                  <label class="block text-xs font-medium text-muted mb-2"
                    >Red social</label
                  >
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="red in socialNetworksOpts"
                      :key="red.id"
                      type="button"
                      class="px-3.5 py-2 rounded-xl text-xs font-medium border transition-all duration-200 active:scale-[0.97]"
                      :class="
                        selectedSocialNetworks.includes(red.id)
                          ? 'border-gold/50 bg-gold/10 text-gold'
                          : 'border-border/60 text-muted hover:border-border hover:text-ink'
                      "
                      @click="toggleSocialNetwork(red.id)"
                    >
                      <span class="inline-flex items-center gap-1.5">
                        <svg
                          v-if="selectedSocialNetworks.includes(red.id)"
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4.5 12.75l6 6 9-13.5"
                          />
                        </svg>
                        {{ red.name }}
                      </span>
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-medium text-muted mb-2"
                    >Formato</label
                  >
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="fmt in formatsOpts"
                      :key="fmt.id"
                      type="button"
                      class="px-3.5 py-2 rounded-xl text-xs font-medium border transition-all duration-200 active:scale-[0.97]"
                      :class="
                        selectedFormats.includes(fmt.id)
                          ? 'border-gold/50 bg-gold/10 text-gold'
                          : 'border-border/60 text-muted hover:border-border hover:text-ink'
                      "
                      @click="toggleFormat(fmt.id)"
                    >
                      <span class="inline-flex items-center gap-1.5">
                        <svg
                          v-if="selectedFormats.includes(fmt.id)"
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4.5 12.75l6 6 9-13.5"
                          />
                        </svg>
                        {{ fmt.name }}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </Transition>

            <div>
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Descripción</label
              >
              <textarea
                v-model="form.description"
                rows="3"
                placeholder="Detalles del proyecto…"
                class="input-field"
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Estado</label
              >
              <BaseSelect
                v-model="form.status"
                placeholder="Seleccionar…"
                :options="[
                  { value: null, label: 'Seleccionar…' },
                  ...creationStatuses.map((s) => ({
                    value: s.id,
                    label: s.name,
                  })),
                ]"
              />
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Fecha de venta</label
                >
                <input
                  v-model="form.sale_date"
                  type="date"
                  class="input-field"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Fecha de servicio</label
                >
                <input
                  v-model="form.service_date"
                  type="date"
                  class="input-field"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Fecha fin</label
                >
                <input
                  v-model="form.end_date"
                  type="date"
                  class="input-field"
                />
              </div>
            </div>
          </div>

          <!-- Step 3: Propuesta económica -->
          <div v-if="currentStep === 3" class="space-y-5 animate-fade-up">
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Fee (€/contenido)</label
                >
                <input
                  v-model="form.fee"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  class="input-field"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Nº de contenidos</label
                >
                <input
                  v-model="form.num_contents"
                  type="number"
                  min="0"
                  step="1"
                  placeholder="0"
                  class="input-field"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5"
                  >Nº de perfiles</label
                >
                <input
                  v-model="form.num_profiles"
                  type="number"
                  min="0"
                  step="1"
                  placeholder="0"
                  class="input-field"
                />
              </div>
            </div>

            <!-- Gifting & Descuento -->
            <div class="space-y-2">
              <label
                class="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200"
                :class="
                  form.gifting
                    ? 'border-gold/40 bg-gold/5'
                    : 'border-border/60 hover:border-border'
                "
              >
                <input
                  v-model="form.gifting"
                  type="checkbox"
                  class="mt-0.5 accent-[#c9a84c]"
                />
                <div>
                  <p class="text-sm font-medium text-ink">Gifting</p>
                  <p class="text-xs text-muted mt-0.5">
                    Stimada invita al contenido. El importe final será 0 €.
                  </p>
                </div>
              </label>

              <label
                class="flex items-start gap-3 p-3 rounded-xl border transition-all duration-200"
                :class="[
                  form.discount_active
                    ? 'border-gold/40 bg-gold/5'
                    : 'border-border/60 hover:border-border',
                  form.gifting
                    ? 'opacity-50 cursor-not-allowed'
                    : 'cursor-pointer',
                ]"
              >
                <input
                  v-model="form.discount_active"
                  type="checkbox"
                  :disabled="form.gifting"
                  class="mt-0.5 accent-[#c9a84c]"
                />
                <div class="flex-1">
                  <p class="text-sm font-medium text-ink">Descuento</p>
                  <p class="text-xs text-muted mt-0.5">
                    Aplica un porcentaje de descuento sobre el precio total.
                  </p>
                  <Transition name="fade-expand">
                    <div
                      v-if="form.discount_active && !form.gifting"
                      class="mt-3 flex items-center gap-2"
                    >
                      <input
                        v-model="form.discount_percentage"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        placeholder="0"
                        class="input-field w-24"
                        @click.stop
                      />
                      <span class="text-sm text-muted">% de descuento</span>
                    </div>
                  </Transition>
                </div>
              </label>
            </div>

            <!-- Desglose del precio -->
            <div
              class="rounded-xl border border-border/60 bg-panel/30 p-4 space-y-2"
            >
              <div class="flex items-center justify-between">
                <span class="text-xs text-muted"
                  >Fee × contenidos × perfiles</span
                >
                <span class="text-xs text-muted">
                  {{ formatEuro(parseFloat(form.fee) || 0) }} ×
                  {{ parseInt(form.num_contents) || 0 }} ×
                  {{ parseInt(form.num_profiles) || 0 }}
                </span>
              </div>
              <div
                class="flex items-center justify-between pt-2 border-t border-border/40"
              >
                <span class="text-sm font-medium text-ink">Precio total</span>
                <span class="flex items-center gap-2">
                  <span
                    v-if="priceModified"
                    class="text-sm text-muted line-through decoration-red-400/70"
                  >
                    {{ formatEuro(grossPrice) }}
                  </span>
                  <Transition name="price-pop" mode="out-in">
                    <span
                      :key="priceModified ? 'mod' : 'base'"
                      class="text-base font-bold"
                      :class="
                        form.gifting
                          ? 'text-gold'
                          : priceModified
                            ? 'text-gold'
                            : 'text-ink'
                      "
                    >
                      {{ formatEuro(finalPrice) }}
                    </span>
                  </Transition>
                </span>
              </div>
              <p
                v-if="form.gifting"
                class="flex items-center justify-end gap-1.5 text-[11px] text-gold/80 text-right font-medium"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M21 11.25v8.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 109.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1114.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
                  />
                </svg>
                Contenido invitado por Stimada
              </p>
            </div>
          </div>

          <!-- Step 4: Content Maker -->
          <div v-if="currentStep === 4" class="space-y-5 animate-fade-up">
            <div>
              <label class="block text-xs font-medium text-muted mb-3"
                >¿Cómo se asignará la Content Maker?</label
              >
              <div class="grid grid-cols-1 gap-2">
                <label
                  v-for="opt in [
                    {
                      value: 'defined',
                      label: 'Ya está definida',
                      desc: 'Seleccionas directamente la content maker',
                    },
                    {
                      value: 'recommended',
                      label: 'Recomendar opciones',
                      desc: 'Sugieres varias opciones al cliente',
                    },
                    {
                      value: 'client_chooses',
                      label: 'El cliente elige',
                      desc: 'El cliente explora y selecciona por sí mismo',
                    },
                  ]"
                  :key="opt.value"
                  class="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200"
                  :class="
                    cmSelectionMode === opt.value
                      ? 'border-gold/40 bg-gold/5'
                      : 'border-border/60 hover:border-border'
                  "
                >
                  <input
                    v-model="cmSelectionMode"
                    type="radio"
                    :value="opt.value"
                    class="mt-0.5 accent-[#c9a84c]"
                  />
                  <div>
                    <p class="text-sm font-medium text-ink">{{ opt.label }}</p>
                    <p class="text-xs text-muted mt-0.5">{{ opt.desc }}</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Defined: search and select multiple -->
            <div v-if="cmSelectionMode === 'defined'" class="space-y-3">
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Buscar y añadir Content Makers</label
              >
              <input
                v-model="cmSearch"
                type="text"
                placeholder="Nombre o @instagram…"
                class="input-field"
              />
              <div
                v-if="cmResults.length"
                class="rounded-xl border border-border/60 max-h-48 overflow-auto"
              >
                <button
                  v-for="cm in cmResults"
                  :key="cm.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="addDefinedCM(cm)"
                >
                  <span class="font-medium text-ink"
                    >{{ cm.first_name }} {{ cm.last_name }}</span
                  >
                  <span
                    v-if="cm.instagram_handle"
                    class="text-muted ml-2 text-xs"
                    >@{{ cm.instagram_handle }}</span
                  >
                </button>
              </div>

              <!-- Selected defined CMs -->
              <div v-if="selectedCMs.length" class="space-y-1.5">
                <p class="text-xs text-muted font-medium">
                  Seleccionadas ({{ selectedCMs.length }}):
                </p>
                <div
                  v-for="cm in selectedCMs"
                  :key="cm.id"
                  class="flex items-center justify-between px-3 py-2 rounded-lg bg-panel/60 border border-border/40"
                >
                  <span class="text-xs text-ink font-medium"
                    >{{ cm.first_name }} {{ cm.last_name }}
                    <span class="text-muted"
                      >@{{ cm.instagram_handle }}</span
                    ></span
                  >
                  <button
                    class="text-xs text-red-400 hover:text-red-600 transition-colors"
                    @click="removeDefinedCM(cm.id)"
                  >
                    Quitar
                  </button>
                </div>
              </div>
            </div>

            <!-- Recommended: search and add multiple -->
            <div v-if="cmSelectionMode === 'recommended'" class="space-y-3">
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Buscar y añadir recomendaciones</label
              >
              <input
                v-model="cmSearch"
                type="text"
                placeholder="Nombre o @instagram…"
                class="input-field"
              />
              <div
                v-if="cmResults.length"
                class="rounded-xl border border-border/60 max-h-48 overflow-auto"
              >
                <button
                  v-for="cm in cmResults"
                  :key="cm.id"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                  @click="addRecommendedCM(cm)"
                >
                  <span class="font-medium text-ink"
                    >{{ cm.first_name }} {{ cm.last_name }}</span
                  >
                  <span
                    v-if="cm.instagram_handle"
                    class="text-muted ml-2 text-xs"
                    >@{{ cm.instagram_handle }}</span
                  >
                </button>
              </div>

              <!-- Selected recommendations -->
              <div v-if="recommendedCMs.length" class="space-y-1.5">
                <p class="text-xs text-muted font-medium">
                  Recomendadas ({{ recommendedCMs.length }}):
                </p>
                <div
                  v-for="cm in recommendedCMs"
                  :key="cm.id"
                  class="flex items-center justify-between px-3 py-2 rounded-lg bg-panel/60 border border-border/40"
                >
                  <span class="text-xs text-ink font-medium"
                    >{{ cm.first_name }} {{ cm.last_name }}
                    <span class="text-muted"
                      >@{{ cm.instagram_handle }}</span
                    ></span
                  >
                  <button
                    class="text-xs text-red-400 hover:text-red-600 transition-colors"
                    @click="removeRecommendedCM(cm.id)"
                  >
                    Quitar
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 5: Summary -->
          <div v-if="currentStep === 5" class="space-y-4 animate-fade-up">
            <div
              class="rounded-xl border border-border/60 divide-y divide-border/40"
            >
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Marca</span>
                <span class="text-xs text-ink font-medium">{{
                  selectedBrandName
                }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Cliente (heredado)</span>
                <span class="text-xs text-ink font-medium">{{
                  inheritedClientName
                }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">ID Proyecto</span>
                <span class="text-xs text-ink font-medium text-muted/60 italic"
                  >Se asignará automáticamente</span
                >
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Nombre</span>
                <span class="text-xs text-ink font-medium">{{
                  form.name
                }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Tipo de servicio</span>
                <span class="text-xs text-ink font-medium">{{
                  serviceTypes.find((s) => s.id === form.service_type)?.name ||
                  '—'
                }}</span>
              </div>
              <div
                v-if="requiresProfiles && selectedSocialNetworks.length"
                class="px-4 py-3 flex justify-between gap-4"
              >
                <span class="text-xs text-muted">Red social</span>
                <span class="text-xs text-ink font-medium text-right">{{
                  socialNetworksOpts
                    .filter((r) => selectedSocialNetworks.includes(r.id))
                    .map((r) => r.name)
                    .join(', ')
                }}</span>
              </div>
              <div
                v-if="requiresProfiles && selectedFormats.length"
                class="px-4 py-3 flex justify-between gap-4"
              >
                <span class="text-xs text-muted">Formato</span>
                <span class="text-xs text-ink font-medium text-right">{{
                  formatsOpts
                    .filter((f) => selectedFormats.includes(f.id))
                    .map((f) => f.name)
                    .join(', ')
                }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Estado inicial</span>
                <span class="text-xs text-ink font-medium">{{
                  creationStatuses.find((s) => s.id === form.status)?.name ||
                  '—'
                }}</span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Propuesta económica</span>
                <span class="text-xs text-ink font-medium">
                  {{ formatEuro(parseFloat(form.fee) || 0) }} ×
                  {{ parseInt(form.num_contents) || 0 }} cont. ×
                  {{ parseInt(form.num_profiles) || 0 }} perf.
                </span>
              </div>
              <div class="px-4 py-3 flex justify-between items-center">
                <span class="text-xs text-muted">Precio total</span>
                <span class="flex items-center gap-2">
                  <span
                    v-if="priceModified"
                    class="text-xs text-muted line-through decoration-red-400/70"
                    >{{ formatEuro(grossPrice) }}</span
                  >
                  <span
                    class="text-sm font-bold"
                    :class="priceModified ? 'text-gold' : 'text-ink'"
                    >{{ formatEuro(finalPrice) }}</span
                  >
                  <span
                    v-if="form.gifting"
                    class="inline-flex items-center gap-1 text-[10px] text-gold/80 font-medium"
                  >
                    <svg
                      class="w-3 h-3"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21 11.25v8.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 109.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1114.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
                      />
                    </svg>
                    Gifting
                  </span>
                  <span
                    v-else-if="form.discount_active"
                    class="text-[10px] text-gold/80 font-medium"
                    >−{{ parseFloat(form.discount_percentage) || 0 }}%</span
                  >
                </span>
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Fechas</span>
                <span class="text-xs text-ink font-medium"
                  >{{ form.sale_date || '—' }} →
                  {{ form.end_date || '—' }}</span
                >
              </div>
              <div class="px-4 py-3 flex justify-between">
                <span class="text-xs text-muted">Content Makers</span>
                <span class="text-xs text-ink font-medium">
                  <template v-if="cmSelectionMode === 'defined'"
                    >{{ selectedCMs.length }} definida{{
                      selectedCMs.length !== 1 ? 's' : ''
                    }}</template
                  >
                  <template v-else-if="cmSelectionMode === 'recommended'"
                    >{{ recommendedCMs.length }} recomendadas</template
                  >
                  <template v-else>El cliente elige</template>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Precio total (animado) -->
        <Transition name="fade-expand">
          <div
            v-if="currentStep >= 3 && (grossPrice > 0 || form.gifting)"
            class="px-8 py-3 border-t border-border/40 bg-panel/40 flex items-center justify-between"
          >
            <span class="text-xs font-medium text-muted">Precio total</span>
            <span class="flex items-baseline gap-2">
              <span
                v-if="priceModified"
                class="text-xs text-muted line-through decoration-red-400/70"
                >{{ formatEuro(grossPrice) }}</span
              >
              <span
                class="text-lg font-bold tabular-nums transition-colors duration-300"
                :class="priceModified ? 'text-gold' : 'text-ink'"
                >{{ formatEuro(displayedPrice) }}</span
              >
            </span>
          </div>
        </Transition>

        <!-- Footer -->
        <div
          class="px-8 py-5 border-t border-border/40 flex items-center justify-between"
        >
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
              @click="attemptClose"
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
              {{ isSubmitting ? 'Creando…' : 'Crear proyecto' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Exit Warning Modal -->
    <div
      v-if="showExitWarning"
      class="fixed inset-0 z-[110] flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50"
        @click="showExitWarning = false"
      />
      <div
        class="relative w-full max-w-sm bg-white rounded-2xl shadow-elevated p-6 animate-scale-in"
      >
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0"
          >
            <svg
              class="w-5 h-5 text-amber-600"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-ink">
            ¿Salir de la creación del proyecto?
          </h3>
        </div>
        <p class="text-xs text-muted leading-relaxed mb-6">
          Tienes datos sin guardar. Puedes guardar el proyecto como borrador
          para continuar más tarde, o descartarlo.
        </p>
        <div class="flex items-center justify-end gap-2">
          <button
            class="px-3 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
            @click="showExitWarning = false"
          >
            Seguir editando
          </button>
          <button
            :disabled="savingDraft"
            class="px-3 py-2 rounded-xl text-xs font-medium border border-gold/40 text-gold hover:bg-gold/5 transition-all disabled:opacity-50"
            @click="saveDraftAndClose"
          >
            {{ savingDraft ? 'Guardando…' : 'Guardar borrador' }}
          </button>
          <button
            class="px-3 py-2 rounded-xl text-xs font-medium bg-red-500 text-white hover:bg-red-600 transition-all"
            @click="discardAndClose"
          >
            Descartar
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Expand/collapse transition for conditional sections (red social, formato, descuento, price bar) */
.fade-expand-enter-active,
.fade-expand-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease,
    max-height 0.3s ease;
  overflow: hidden;
  max-height: 320px;
}
.fade-expand-enter-from,
.fade-expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
  max-height: 0;
}

/* Pop animation for the price value when it switches (gifting/discount) */
.price-pop-enter-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.price-pop-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.price-pop-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
.price-pop-leave-to {
  opacity: 0;
  transform: scale(1.1);
}
</style>
