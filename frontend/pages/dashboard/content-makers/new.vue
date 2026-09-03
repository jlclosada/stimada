<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type { PerformanceOption } from '~/stores/contentMakers';
import { useContentMakersStore } from '~/stores/contentMakers';

definePageMeta({ middleware: ['auth', 'role'] });

const store = useContentMakersStore();
const auth = useAuthStore();
const config = useRuntimeConfig();
const router = useRouter();

// --- Next ID ---
const nextId = ref('');

// Sizing options from backend
const sizingOptions = ref<Record<string, { label: string; options: string[] }>>(
  {},
);

// Performance options from backend
const performanceOptions = ref<PerformanceOption[]>([]);

onMounted(async () => {
  store.fetchFilters();
  try {
    const data = await $fetch<{ next_id: string }>(
      `${config.public.apiBase}/content-makers/next_id/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    );
    nextId.value = data.next_id;
    form.stimada_id = data.next_id;
  } catch {}
  try {
    sizingOptions.value = await $fetch(
      `${config.public.apiBase}/content-makers/sizing_options/`,
      {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
  } catch {}
  try {
    performanceOptions.value = await $fetch(
      `${config.public.apiBase}/content-makers/performance_options/`,
      {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
  } catch {}
});

// --- Steps ---
const STEPS = [
  { id: 'basic', label: 'Datos básicos' },
  { id: 'social', label: 'Redes sociales' },
  { id: 'rating', label: 'Valoración' },
  { id: 'sizing', label: 'Tallaje' },
  { id: 'contact', label: 'Contacto y facturación' },
];
const currentStep = ref(0);
function prev() {
  currentStep.value = Math.max(0, currentStep.value - 1);
}
function next() {
  currentStep.value = Math.min(STEPS.length - 1, currentStep.value + 1);
}

// --- Form data ---
const form = reactive({
  stimada_id: '',
  first_name: '',
  last_name: '',
  type: 'content_maker',
  cm_type: '',
  gender: '',
  status: '',
  email: '',
  // Redes
  instagram_handle: '',
  instagram_link: '',
  instagram_followers: '' as string | number,
  instagram_followers_category: '',
  fee_instagram: '' as string | number,
  tiktok_handle: '',
  tiktok_link: '',
  tiktok_followers: '' as string | number,
  tiktok_followers_category: '',
  fee_tiktok: '' as string | number,
  // Valoración
  content_quality: null as number | null,
  performance_options: [] as number[],
  appearance: '',
  performance: '',
  is_mother: false,
  content_categories: '',
  follows_stimada: false,
  stimada_in_bio: false,
  contract_signed: false,
  comments: '',
  // Tallaje
  top_size: '',
  bottom_size: '',
  shoe_size: '',
  height_measurements: '',
  // Contacto
  phone: '',
  billing_address: '',
  postal_code: '',
  province: '',
  country: 'España',
  dni_cif: '',
  iban: '',
});

const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

function boolField(key: keyof typeof form) {
  return {
    modelValue: form[key] as boolean,
    'onUpdate:modelValue': (v: boolean) => {
      (form as Record<string, unknown>)[key] = v;
    },
  };
}

function togglePerformance(id: number) {
  if (form.performance_options.includes(id)) {
    form.performance_options = form.performance_options.filter((x) => x !== id);
  } else {
    form.performance_options = [...form.performance_options, id];
  }
}

async function handleSubmit() {
  errors.value = {};
  isLoading.value = true;
  try {
    // Build payload, omitting empty strings
    const payload: Record<string, unknown> = {};
    Object.entries(form).forEach(([k, v]) => {
      if (v !== '' && v !== null && v !== undefined) payload[k] = v;
    });

    await $fetch(`${config.public.apiBase}/content-makers/`, {
      method: 'POST',
      body: payload,
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    await router.push('/dashboard/content-makers');
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        errors.value[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
      });
      // Jump to the step that has the first error
      const errorFields = Object.keys(errors.value);
      const stepFields: Record<string, string[]> = {
        basic: [
          'stimada_id',
          'first_name',
          'last_name',
          'type',
          'cm_type',
          'gender',
          'status',
          'email',
        ],
        social: [
          'instagram_handle',
          'instagram_link',
          'instagram_followers',
          'fee_instagram',
          'tiktok_handle',
          'tiktok_link',
          'tiktok_followers',
          'fee_tiktok',
        ],
        rating: ['content_quality', 'performance_options', 'comments'],
        sizing: ['top_size', 'bottom_size', 'shoe_size', 'height_measurements'],
        contact: [
          'phone',
          'billing_address',
          'postal_code',
          'province',
          'country',
          'dni_cif',
          'iban',
        ],
      };
      for (const [step, fields] of Object.entries(stepFields)) {
        if (errorFields.some((f) => fields.includes(f))) {
          currentStep.value = STEPS.findIndex((s) => s.id === step);
          break;
        }
      }
    } else {
      errors.value.general =
        'Error al registrar la content maker. Inténtalo de nuevo.';
    }
  } finally {
    isLoading.value = false;
  }
}

function fieldError(field: string) {
  return errors.value[field];
}
</script>

<template>
  <div class="max-w-2xl animate-fade-up">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-7">
      <NuxtLink
        to="/dashboard/content-makers"
        class="flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors"
      >
        <svg
          class="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
          />
        </svg>
        Content Makers
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nueva content maker</span>
    </div>

    <div class="mb-6">
      <p
        class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5"
      >
        Alta
      </p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">
        Nueva content maker
      </h1>
      <p class="text-xs text-muted mt-1">
        ID asignado:
        <span class="font-mono text-gold">{{ nextId || '…' }}</span>
        · No se creará cuenta de acceso hasta que se active manualmente.
      </p>
    </div>

    <!-- Step indicators -->
    <div class="flex items-center gap-1 mb-6">
      <template v-for="(step, i) in STEPS" :key="step.id">
        <button
          type="button"
          class="flex items-center gap-1.5 text-xs transition-colors"
          :class="
            i === currentStep
              ? 'text-ink font-medium'
              : i < currentStep
                ? 'text-gold'
                : 'text-muted'
          "
          @click="currentStep = i"
        >
          <span
            class="w-5 h-5 rounded-full border flex items-center justify-center text-[10px] flex-shrink-0 transition-colors"
            :class="
              i === currentStep
                ? 'border-gold bg-gold/15 text-gold'
                : i < currentStep
                  ? 'border-green-500 bg-green-500/15 text-green-400'
                  : 'border-border'
            "
          >
            <svg
              v-if="i < currentStep"
              class="w-2.5 h-2.5"
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
          </span>
          <span class="hidden sm:inline">{{ step.label }}</span>
        </button>
        <div
          v-if="i < STEPS.length - 1"
          class="flex-1 h-px bg-border max-w-[24px]"
        />
      </template>
    </div>

    <form @submit.prevent="handleSubmit">
      <!-- STEP 1: Datos básicos -->
      <div
        v-show="currentStep === 0"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >ID Stimada</label
            >
            <input
              :value="'CM-' + (form.stimada_id || '…')"
              type="text"
              disabled
              class="input-field font-mono opacity-60 cursor-not-allowed"
            />
            <p class="text-xs text-muted/60 mt-1">Se asigna automáticamente</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Tipo *</label
            >
            <BaseSelect
              v-model="form.type"
              :options="
                store.filterOptions.type_choices.map((t) => ({
                  value: t.value,
                  label: t.label,
                }))
              "
            />
            <p class="text-xs text-muted/60 mt-1">
              Content Maker o Colaborador
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Subtipo / Tipo de CM *</label
            >
            <BaseSelect
              v-model="form.cm_type"
              placeholder="Selecciona tipo"
              :options="
                store.filterOptions.types.map((t) => ({ value: t, label: t }))
              "
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Nombre *</label
            >
            <input
              v-model="form.first_name"
              type="text"
              required
              class="input-field"
              placeholder="Nombre"
            />
            <p
              v-if="fieldError('first_name')"
              class="text-xs text-red-400 mt-1"
            >
              {{ fieldError('first_name') }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Apellidos</label
            >
            <input
              v-model="form.last_name"
              type="text"
              class="input-field"
              placeholder="Apellidos"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Sexo</label
            >
            <BaseSelect
              v-model="form.gender"
              :options="[
                { value: '', label: 'Sin especificar' },
                ...store.filterOptions.genders.map((s) => ({
                  value: s,
                  label: s,
                })),
              ]"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Status</label
            >
            <BaseSelect
              v-model="form.status"
              placeholder="Selecciona estado"
              :options="
                store.filterOptions.statuses.map((s) => ({
                  value: s,
                  label: s,
                }))
              "
            />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Email *</label
            >
            <input
              v-model="form.email"
              type="email"
              required
              class="input-field"
              placeholder="contacto@ejemplo.com"
            />
            <p v-if="fieldError('email')" class="text-xs text-red-400 mt-1">
              {{ fieldError('email') }}
            </p>
          </div>
        </div>
      </div>

      <!-- STEP 2: Redes sociales -->
      <div
        v-show="currentStep === 1"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5"
      >
        <!-- Instagram -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <div
              class="w-6 h-6 rounded-lg bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center"
            >
              <svg
                class="w-3.5 h-3.5 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"
                />
              </svg>
            </div>
            <span class="text-sm font-medium text-ink">Instagram</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1">Handle</label>
              <input
                v-model="form.instagram_handle"
                type="text"
                class="input-field"
                placeholder="usuario"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Seguidores</label>
              <input
                v-model="form.instagram_followers"
                type="number"
                class="input-field"
                placeholder="0"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1"
                >Categoría seguidores</label
              >
              <BaseSelect
                v-model="form.instagram_followers_category"
                :options="[
                  { value: '', label: '—' },
                  ...store.filterOptions.instagram_followers_category.map(
                    (c) => ({
                      value: c,
                      label: c,
                    }),
                  ),
                ]"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Fee (€)</label>
              <input
                v-model="form.fee_instagram"
                type="number"
                class="input-field"
                placeholder="0"
              />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-muted mb-1">Link perfil</label>
              <input
                v-model="form.instagram_link"
                type="url"
                class="input-field"
                placeholder="https://instagram.com/…"
              />
            </div>
          </div>
        </div>

        <div class="border-t border-border" />

        <!-- TikTok -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <div
              class="w-6 h-6 rounded-lg bg-black border border-border flex items-center justify-center"
            >
              <svg
                class="w-3.5 h-3.5 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"
                />
              </svg>
            </div>
            <span class="text-sm font-medium text-ink">TikTok</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1">Handle</label>
              <input
                v-model="form.tiktok_handle"
                type="text"
                class="input-field"
                placeholder="@usuario"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Seguidores</label>
              <input
                v-model="form.tiktok_followers"
                type="number"
                class="input-field"
                placeholder="0"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1"
                >Categoría seguidores</label
              >
              <BaseSelect
                v-model="form.tiktok_followers_category"
                :options="[
                  { value: '', label: '—' },
                  ...store.filterOptions.tiktok_followers_category.map((c) => ({
                    value: c,
                    label: c,
                  })),
                ]"
              />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Fee (€)</label>
              <input
                v-model="form.fee_tiktok"
                type="number"
                class="input-field"
                placeholder="0"
              />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-muted mb-1">Link perfil</label>
              <input
                v-model="form.tiktok_link"
                type="url"
                class="input-field"
                placeholder="https://tiktok.com/@…"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 3: Valoración -->
      <div
        v-show="currentStep === 2"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Calidad del contenido (0–5)</label
            >
            <BaseSelect
              v-model="form.content_quality"
              :options="[
                { value: null, label: '—' },
                ...[0, 1, 2, 3, 4, 5].map((n) => ({
                  value: n,
                  label: String(n),
                })),
              ]"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Desempeño</label
            >
            <div
              class="flex flex-wrap gap-2 p-2 rounded-xl border border-border bg-raised min-h-[38px]"
            >
              <button
                v-for="opt in performanceOptions"
                :key="opt.id"
                type="button"
                class="text-xs px-2.5 py-1 rounded-full border transition-colors"
                :class="
                  form.performance_options.includes(opt.id)
                    ? 'border-gold bg-gold/15 text-gold font-medium'
                    : 'border-border text-muted hover:border-gold/40 hover:text-ink'
                "
                @click="togglePerformance(opt.id)"
              >
                {{ opt.name }}
              </button>
            </div>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Comentarios internos</label
            >
            <textarea
              v-model="form.comments"
              rows="3"
              class="input-field resize-none"
              placeholder="Observaciones internas sobre la content maker…"
            />
          </div>
        </div>

        <!-- Boolean checks -->
        <div class="grid grid-cols-2 gap-3 pt-1">
          <label
            v-for="item in [
              { key: 'is_mother', label: 'Es mamá' },
              { key: 'follows_stimada', label: 'Sigue @stimada' },
              { key: 'stimada_in_bio', label: 'Stimada en bio' },
              { key: 'contract_signed', label: 'Contrato firmado' },
            ]"
            :key="item.key"
            class="flex items-center gap-2.5 cursor-pointer group"
          >
            <div
              class="w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-colors"
              :class="
                (form as Record<string, unknown>)[item.key]
                  ? 'bg-gold border-gold'
                  : 'border-border group-hover:border-subtle'
              "
              @click="
                (form as Record<string, unknown>)[item.key] = !(
                  form as Record<string, unknown>
                )[item.key]
              "
            >
              <svg
                v-if="(form as Record<string, unknown>)[item.key]"
                class="w-3 h-3 text-ink"
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
            </div>
            <span class="text-sm text-ink">{{ item.label }}</span>
          </label>
        </div>
      </div>

      <!-- STEP 4: Tallaje -->
      <div
        v-show="currentStep === 3"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="grid grid-cols-3 gap-4">
          <div v-for="(cat, field) in sizingOptions" :key="field">
            <label class="block text-xs font-medium text-muted mb-1.5">{{
              cat.label
            }}</label>
            <BaseSelect
              v-model="(form as Record<string, unknown>)[field]"
              :options="[
                { value: '', label: '—' },
                ...cat.options.map((opt) => ({ value: opt, label: opt })),
              ]"
            />
          </div>
          <div class="col-span-3">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Altura (cm)</label
            >
            <input
              v-model="form.height_measurements"
              type="number"
              min="0"
              step="1"
              class="input-field"
              placeholder="Ej: 169"
            />
          </div>
        </div>
      </div>

      <!-- STEP 5: Contacto y facturación -->
      <div
        v-show="currentStep === 4"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Teléfono</label
            >
            <input
              v-model="form.phone"
              type="tel"
              class="input-field"
              placeholder="6XXXXXXXX"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >DNI / NIF <span class="text-red-400">*</span></label
            >
            <input
              v-model="form.dni_cif"
              type="text"
              class="input-field"
              placeholder="12345678A"
            />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Dirección de facturación
              <span class="text-red-400">*</span></label
            >
            <input
              v-model="form.billing_address"
              type="text"
              class="input-field"
              placeholder="Calle, número…"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Código postal <span class="text-red-400">*</span></label
            >
            <input v-model="form.postal_code" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Provincia <span class="text-red-400">*</span></label
            >
            <input
              v-model="form.province"
              type="text"
              class="input-field"
              placeholder="Madrid"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >País <span class="text-red-400">*</span></label
            >
            <input v-model="form.country" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >IBAN <span class="text-red-400">*</span></label
            >
            <input
              v-model="form.iban"
              type="text"
              class="input-field"
              placeholder="ES00 0000 0000 0000 0000 0000"
            />
          </div>
        </div>

        <!-- Error general -->
        <div
          v-if="errors.general"
          class="rounded-xl border border-red-500/20 bg-red-500/8 p-3 text-xs text-red-400"
        >
          {{ errors.general }}
        </div>
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-4">
        <button
          v-if="currentStep > 0"
          type="button"
          class="h-9 px-5 rounded-xl border border-border text-xs text-muted hover:text-ink transition-colors"
          @click="prev"
        >
          ← Anterior
        </button>
        <div v-else />

        <button
          v-if="currentStep < STEPS.length - 1"
          type="button"
          class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors"
          @click="next"
        >
          Siguiente →
        </button>

        <button
          v-else
          type="submit"
          :disabled="isLoading"
          class="h-9 px-6 rounded-xl bg-gold text-ink text-xs font-semibold flex items-center gap-2 hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all"
        >
          <svg
            v-if="isLoading"
            class="animate-spin w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          {{ isLoading ? 'Guardando…' : 'Registrar content maker' }}
        </button>
      </div>
    </form>
  </div>
</template>
