<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useContentMakersStore } from "~/stores/contentMakers";

definePageMeta({ middleware: ["auth", "role"] });

const store = useContentMakersStore();
const auth = useAuthStore();
const config = useRuntimeConfig();
const router = useRouter();

// --- Next ID ---
const nextId = ref("");
onMounted(async () => {
  store.fetchFilters();
  try {
    const data = await $fetch<{ next_id: string }>(
      `${config.public.apiBase}/content-makers/next_id/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    nextId.value = data.next_id;
    form.stimada_id = data.next_id;
  } catch {}
});

// --- Steps ---
const STEPS = [
  { id: "basico", label: "Datos básicos" },
  { id: "redes", label: "Redes sociales" },
  { id: "valoracion", label: "Valoración" },
  { id: "tallaje", label: "Tallaje" },
  { id: "contacto", label: "Contacto" },
];
const currentStep = ref(0);
function prev() { currentStep.value = Math.max(0, currentStep.value - 1); }
function next() { currentStep.value = Math.min(STEPS.length - 1, currentStep.value + 1); }

// --- Form data ---
const form = reactive({
  stimada_id: "",
  nombre: "",
  apellidos: "",
  tipo_cm: "",
  sexo: "",
  status: "",
  email: "",
  // Redes
  instagram_handle: "",
  link_instagram: "",
  seguidores_instagram: "" as string | number,
  categoria_seguidores_ig: "",
  fee_instagram: "" as string | number,
  tiktok_handle: "",
  link_tiktok: "",
  seguidores_tiktok: "" as string | number,
  categoria_seguidores_tt: "",
  fee_tiktok: "" as string | number,
  // Valoración
  calidad_contenido: "",
  apariencia: "",
  desempeno: "",
  es_mama: false,
  categorias_contenido: "",
  sigue_stimada: false,
  stimada_en_bio: false,
  contrato_firmado: false,
  // Tallaje
  talla_arriba: "",
  talla_abajo: "",
  talla_pie: "",
  altura_medidas: "",
  // Contacto
  telefono: "",
  direccion_facturacion: "",
  codigo_postal: "",
  provincia: "",
  pais: "España",
  dni_cif: "",
  iban: "",
  comentarios: "",
});

const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

function boolField(key: keyof typeof form) {
  return {
    modelValue: form[key] as boolean,
    "onUpdate:modelValue": (v: boolean) => { (form as Record<string, unknown>)[key] = v; },
  };
}

async function handleSubmit() {
  errors.value = {};
  isLoading.value = true;
  try {
    // Build payload, omitting empty strings
    const payload: Record<string, unknown> = {};
    Object.entries(form).forEach(([k, v]) => {
      if (v !== "" && v !== null && v !== undefined) payload[k] = v;
    });

    await $fetch(`${config.public.apiBase}/content-makers/`, {
      method: "POST",
      body: payload,
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    await router.push("/dashboard/content-makers");
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        errors.value[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
      });
      // Jump to the step that has the first error
      const errorFields = Object.keys(errors.value);
      const stepFields: Record<string, string[]> = {
        basico: ["stimada_id", "nombre", "apellidos", "tipo_cm", "sexo", "status", "email"],
        redes: ["instagram_handle", "link_instagram", "seguidores_instagram", "fee_instagram", "tiktok_handle", "link_tiktok", "seguidores_tiktok", "fee_tiktok"],
        valoracion: ["calidad_contenido", "apariencia", "desempeno", "categorias_contenido"],
        tallaje: ["talla_arriba", "talla_abajo", "talla_pie", "altura_medidas"],
        contacto: ["telefono", "direccion_facturacion", "codigo_postal", "provincia", "pais", "dni_cif", "iban", "comentarios"],
      };
      for (const [step, fields] of Object.entries(stepFields)) {
        if (errorFields.some(f => fields.includes(f))) {
          currentStep.value = STEPS.findIndex(s => s.id === step);
          break;
        }
      }
    } else {
      errors.value.general = "Error al registrar la content maker. Inténtalo de nuevo.";
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
      <NuxtLink to="/dashboard/content-makers" class="flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Content Makers
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nueva content maker</span>
    </div>

    <div class="mb-6">
      <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Alta</p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">Nueva content maker</h1>
      <p class="text-xs text-muted mt-1">
        ID asignado: <span class="font-mono text-gold">{{ nextId || '…' }}</span>
        · No se creará cuenta de acceso hasta que se active manualmente.
      </p>
    </div>

    <!-- Step indicators -->
    <div class="flex items-center gap-1 mb-6">
      <template v-for="(step, i) in STEPS" :key="step.id">
        <button
          type="button"
          class="flex items-center gap-1.5 text-xs transition-colors"
          :class="i === currentStep ? 'text-ink font-medium' : i < currentStep ? 'text-gold' : 'text-muted'"
          @click="currentStep = i"
        >
          <span
            class="w-5 h-5 rounded-full border flex items-center justify-center text-[10px] flex-shrink-0 transition-colors"
            :class="i === currentStep ? 'border-gold bg-gold/15 text-gold' : i < currentStep ? 'border-green-500 bg-green-500/15 text-green-400' : 'border-border'"
          >
            <svg v-if="i < currentStep" class="w-2.5 h-2.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span class="hidden sm:inline">{{ step.label }}</span>
        </button>
        <div v-if="i < STEPS.length - 1" class="flex-1 h-px bg-border max-w-[24px]" />
      </template>
    </div>

    <form @submit.prevent="handleSubmit">

      <!-- STEP 1: Datos básicos -->
      <div v-show="currentStep === 0" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">ID Stimada</label>
            <input :value="'CM-' + (form.stimada_id || '…')" type="text" disabled class="input-field font-mono opacity-60 cursor-not-allowed" />
            <p class="text-xs text-muted/60 mt-1">Se asigna automáticamente</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Tipo de CM *</label>
            <select v-model="form.tipo_cm" required class="select-field">
              <option value="" disabled>Selecciona tipo</option>
              <option v-for="t in store.filterOptions.tipos" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Nombre *</label>
            <input v-model="form.nombre" type="text" required class="input-field" placeholder="Nombre" />
            <p v-if="fieldError('nombre')" class="text-xs text-red-400 mt-1">{{ fieldError('nombre') }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Apellidos</label>
            <input v-model="form.apellidos" type="text" class="input-field" placeholder="Apellidos" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Sexo</label>
            <select v-model="form.sexo" class="select-field">
              <option value="">Sin especificar</option>
              <option v-for="s in store.filterOptions.sexos" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Status</label>
            <select v-model="form.status" class="select-field">
              <option value="" disabled>Selecciona estado</option>
              <option v-for="s in store.filterOptions.statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Email *</label>
            <input v-model="form.email" type="email" required class="input-field" placeholder="contacto@ejemplo.com" />
            <p v-if="fieldError('email')" class="text-xs text-red-400 mt-1">{{ fieldError('email') }}</p>
          </div>
        </div>
      </div>

      <!-- STEP 2: Redes sociales -->
      <div v-show="currentStep === 1" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5" >
        <!-- Instagram -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 rounded-lg bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
              <svg class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            </div>
            <span class="text-sm font-medium text-ink">Instagram</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1">Handle</label>
              <input v-model="form.instagram_handle" type="text" class="input-field" placeholder="usuario" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Seguidores</label>
              <input v-model="form.seguidores_instagram" type="number" class="input-field" placeholder="0" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Categoría seguidores</label>
              <select v-model="form.categoria_seguidores_ig" class="select-field">
                <option value="">—</option>
                <option v-for="c in store.filterOptions.categoria_seguidores_ig" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Fee (€)</label>
              <input v-model="form.fee_instagram" type="number" class="input-field" placeholder="0" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-muted mb-1">Link perfil</label>
              <input v-model="form.link_instagram" type="url" class="input-field" placeholder="https://instagram.com/…" />
            </div>
          </div>
        </div>

        <div class="border-t border-border" />

        <!-- TikTok -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 rounded-lg bg-black border border-border flex items-center justify-center">
              <svg class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"/></svg>
            </div>
            <span class="text-sm font-medium text-ink">TikTok</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1">Handle</label>
              <input v-model="form.tiktok_handle" type="text" class="input-field" placeholder="@usuario" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Seguidores</label>
              <input v-model="form.seguidores_tiktok" type="number" class="input-field" placeholder="0" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Categoría seguidores</label>
              <select v-model="form.categoria_seguidores_tt" class="select-field">
                <option value="">—</option>
                <option v-for="c in store.filterOptions.categoria_seguidores_tt" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">Fee (€)</label>
              <input v-model="form.fee_tiktok" type="number" class="input-field" placeholder="0" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-muted mb-1">Link perfil</label>
              <input v-model="form.link_tiktok" type="url" class="input-field" placeholder="https://tiktok.com/@…" />
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 3: Valoración -->
      <div v-show="currentStep === 2" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Calidad del contenido</label>
            <select v-model="form.calidad_contenido" class="select-field">
              <option value="">—</option>
              <option v-for="c in store.filterOptions.calidad_contenido" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Apariencia</label>
            <select v-model="form.apariencia" class="select-field">
              <option value="">—</option>
              <option v-for="a in store.filterOptions.apariencia" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Desempeño</label>
            <input v-model="form.desempeno" type="text" class="input-field" placeholder="Ej: Fiable, Engage" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Categorías de contenido</label>
            <input v-model="form.categorias_contenido" type="text" class="input-field" placeholder="Ej: Moda & Beauty, Lifestyle" />
          </div>
        </div>

        <!-- Boolean checks -->
        <div class="grid grid-cols-2 gap-3 pt-1">
          <label v-for="item in [
            { key: 'es_mama', label: 'Es mamá' },
            { key: 'sigue_stimada', label: 'Sigue @stimada' },
            { key: 'stimada_en_bio', label: 'Stimada en bio' },
            { key: 'contrato_firmado', label: 'Contrato firmado' },
          ]" :key="item.key" class="flex items-center gap-2.5 cursor-pointer group">
            <div
              class="w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-colors"
              :class="(form as Record<string, unknown>)[item.key] ? 'bg-gold border-gold' : 'border-border group-hover:border-subtle'"
              @click="(form as Record<string, unknown>)[item.key] = !(form as Record<string, unknown>)[item.key]"
            >
              <svg v-if="(form as Record<string, unknown>)[item.key]" class="w-3 h-3 text-ink" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <span class="text-sm text-ink">{{ item.label }}</span>
          </label>
        </div>
      </div>

      <!-- STEP 4: Tallaje -->
      <div v-show="currentStep === 3" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Parte arriba</label>
            <input v-model="form.talla_arriba" type="text" class="input-field" placeholder="Ej: M / L" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Parte abajo</label>
            <input v-model="form.talla_abajo" type="text" class="input-field" placeholder="Ej: 38" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Pie</label>
            <input v-model="form.talla_pie" type="text" class="input-field" placeholder="Ej: 38" />
          </div>
          <div class="col-span-3">
            <label class="block text-xs font-medium text-muted mb-1.5">Altura y medidas</label>
            <textarea v-model="form.altura_medidas" rows="3" class="input-field resize-none" placeholder="Ej: Altura: 1,69m / Pecho: 90cm / Cintura: 68cm" />
          </div>
        </div>
      </div>

      <!-- STEP 5: Contacto -->
      <div v-show="currentStep === 4" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Teléfono</label>
            <input v-model="form.telefono" type="tel" class="input-field" placeholder="6XXXXXXXX" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">DNI / CIF</label>
            <input v-model="form.dni_cif" type="text" class="input-field" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Dirección de facturación</label>
            <input v-model="form.direccion_facturacion" type="text" class="input-field" placeholder="Calle, número…" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Código postal</label>
            <input v-model="form.codigo_postal" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Provincia</label>
            <input v-model="form.provincia" type="text" class="input-field" placeholder="Madrid" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">País</label>
            <input v-model="form.pais" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">IBAN</label>
            <input v-model="form.iban" type="text" class="input-field" placeholder="ES00 0000 0000 0000 0000 0000" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Comentarios internos</label>
            <textarea v-model="form.comentarios" rows="3" class="input-field resize-none" placeholder="Notas visibles solo para el equipo de Stimada…" />
          </div>
        </div>

        <!-- Error general -->
        <div v-if="errors.general" class="rounded-xl border border-red-500/20 bg-red-500/8 p-3 text-xs text-red-400">
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
          <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ isLoading ? 'Guardando…' : 'Registrar content maker' }}
        </button>
      </div>
    </form>
  </div>
</template>
