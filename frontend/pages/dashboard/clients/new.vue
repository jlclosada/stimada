<script setup lang="ts">
import { useClientsStore } from '~/stores/clients';

definePageMeta({ middleware: ['auth', 'role'] });

const store = useClientsStore();
const router = useRouter();

onMounted(() => store.fetchTypes());

const form = reactive({
  name: '',
  client_type: '' as string | number,
  web_instagram: '',
  contact_person: '',
  contact_email: '',
  phone: '',
  is_agency: false,
  billing_name: '',
  cif: '',
  billing_email: '',
  billing_address: '',
  postal_code: '',
  city: '',
  country: 'España',
  contract_signed: false,
});

const contratoFile = ref<File | null>(null);
const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Required + email/url validation grouped by section.
const SECTION_VALIDATORS: Record<string, () => Record<string, string>> = {
  identificacion: () => {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = 'El nombre comercial es obligatorio.';
    if (
      form.web_instagram &&
      !/^https?:\/\/.+/i.test(form.web_instagram.trim())
    ) {
      e.web_instagram = 'La URL debe empezar por http:// o https://';
    }
    return e;
  },
  contacto: () => {
    const e: Record<string, string> = {};
    if (!form.contact_person.trim())
      e.contact_person = 'La persona de contacto es obligatoria.';
    if (!form.contact_email.trim()) {
      e.contact_email = 'El email de contacto es obligatorio.';
    } else if (!EMAIL_RE.test(form.contact_email.trim())) {
      e.contact_email = 'Introduce un email válido (ej: nombre@dominio.com).';
    }
    return e;
  },
  facturacion: () => {
    const e: Record<string, string> = {};
    if (!form.billing_name.trim())
      e.billing_name = 'El nombre de facturación es obligatorio.';
    if (!form.cif.trim()) e.cif = 'El CIF es obligatorio.';
    if (!form.billing_email.trim()) {
      e.billing_email = 'El email de facturación es obligatorio.';
    } else if (!EMAIL_RE.test(form.billing_email.trim())) {
      e.billing_email = 'Introduce un email válido (ej: facturas@dominio.com).';
    }
    if (!form.billing_address.trim())
      e.billing_address = 'La dirección es obligatoria.';
    if (!form.postal_code.trim())
      e.postal_code = 'El código postal es obligatorio.';
    if (!form.city.trim()) e.city = 'La ciudad es obligatoria.';
    return e;
  },
  marcas: () => ({}),
  contrato: () => ({}),
};

function validateSection(sectionId: string): boolean {
  const sectionErrors = SECTION_VALIDATORS[sectionId]?.() || {};
  // Clear previous errors for this section's fields and apply new ones.
  const newErrors = { ...errors.value };
  Object.keys(SECTION_VALIDATORS[sectionId]?.() || {}).forEach(
    (k) => delete newErrors[k],
  );
  Object.assign(newErrors, sectionErrors);
  errors.value = newErrors;
  return Object.keys(sectionErrors).length === 0;
}

function goToSection(target: string) {
  // Allow free backward navigation; validate when moving forward.
  const order = [
    'identificacion',
    'contacto',
    'facturacion',
    'marcas',
    'contrato',
  ];
  const currentIdx = order.indexOf(activeSection.value);
  const targetIdx = order.indexOf(target);
  if (targetIdx > currentIdx) {
    if (!validateSection(activeSection.value)) return;
  }
  activeSection.value = target;
}

function handleFile(e: Event) {
  const input = e.target as HTMLInputElement;
  contratoFile.value = input.files?.[0] ?? null;
}

async function handleSubmit() {
  // Validate all sections; jump to first invalid section if any.
  const order = [
    'identificacion',
    'contacto',
    'facturacion',
    'marcas',
    'contrato',
  ];
  errors.value = {};
  for (const sec of order) {
    const secErrors = SECTION_VALIDATORS[sec]?.() || {};
    if (Object.keys(secErrors).length > 0) {
      Object.assign(errors.value, secErrors);
      activeSection.value = sec;
      return;
    }
  }

  isLoading.value = true;

  try {
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (v !== '' && v !== null && v !== undefined) {
        fd.append(k, String(v));
      }
    });
    if (contratoFile.value) fd.append('contract', contratoFile.value);

    await store.create(fd);
    await router.push('/dashboard/clients');
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        errors.value[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
      });
      // Jump to the first section that contains a field with an error.
      const sectionByField: Record<string, string> = {
        name: 'identificacion',
        client_type: 'identificacion',
        web_instagram: 'identificacion',
        contact_person: 'contacto',
        contact_email: 'contacto',
        phone: 'contacto',
        billing_name: 'facturacion',
        cif: 'facturacion',
        billing_email: 'facturacion',
        billing_address: 'facturacion',
        postal_code: 'facturacion',
        city: 'facturacion',
        country: 'facturacion',
      };
      const firstField = Object.keys(e.data)[0];
      if (firstField && sectionByField[firstField]) {
        activeSection.value = sectionByField[firstField];
      }
    } else {
      errors.value.general = 'Error al crear el cliente. Inténtalo de nuevo.';
    }
  } finally {
    isLoading.value = false;
  }
}

const SECTIONS = [
  { id: 'identificacion', label: 'Identificación' },
  { id: 'contacto', label: 'Contacto' },
  { id: 'facturacion', label: 'Facturación' },
  { id: 'marcas', label: 'Marcas' },
  { id: 'contrato', label: 'Contrato' },
];

const activeSection = ref('identificacion');

// Fields that belong to each section (used to filter the error banner).
const SECTION_FIELDS: Record<string, string[]> = {
  identificacion: ['name', 'client_type', 'web_instagram'],
  contacto: ['contact_person', 'contact_email', 'phone'],
  facturacion: [
    'billing_name',
    'cif',
    'billing_email',
    'billing_address',
    'postal_code',
    'city',
    'country',
  ],
  marcas: [],
  contrato: [],
};

// Errors currently shown in the active section (for the inline banner).
const currentSectionErrors = computed(() => {
  const fields = SECTION_FIELDS[activeSection.value] || [];
  return fields
    .map((f) => errors.value[f])
    .filter((msg): msg is string => Boolean(msg));
});
</script>

<template>
  <div class="max-w-2xl animate-fade-up">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-7">
      <NuxtLink
        to="/dashboard/clients"
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
        Clientes
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nuevo cliente</span>
    </div>

    <div class="mb-6">
      <p
        class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5"
      >
        Alta
      </p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">
        Nuevo cliente
      </h1>
    </div>

    <!-- Section tabs -->
    <div
      class="flex gap-1 mb-6 p-1 rounded-xl border border-border/60 bg-white"
    >
      <button
        v-for="s in SECTIONS"
        :key="s.id"
        class="flex-1 py-2 rounded-lg text-xs font-medium transition-colors"
        :class="
          activeSection === s.id
            ? 'bg-white/8 text-ink'
            : 'text-muted hover:text-ink'
        "
        @click="goToSection(s.id)"
      >
        {{ s.label }}
      </button>
    </div>

    <form novalidate @submit.prevent="handleSubmit">
      <!-- Banner de errores de la sección actual -->
      <div
        v-if="currentSectionErrors.length"
        class="mb-4 rounded-xl border border-red-300/60 bg-red-50 p-3 text-xs text-red-600"
      >
        <p class="font-medium mb-1">
          Revisa los siguientes campos antes de continuar:
        </p>
        <ul class="list-disc pl-5 space-y-0.5">
          <li v-for="(msg, i) in currentSectionErrors" :key="i">{{ msg }}</li>
        </ul>
      </div>
      <!-- IDENTIFICACIÓN -->
      <div
        v-show="activeSection === 'identificacion'"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5"
      >
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Nombre comercial del cliente *</label
            >
            <input
              v-model="form.name"
              type="text"
              required
              class="input-field"
              placeholder="Ej: Brand Company S.L."
            />
            <p v-if="errors.name" class="text-xs text-red-400 mt-1">
              {{ errors.name }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Tipo de cliente</label
            >
            <BaseSelect
              v-model="form.client_type"
              placeholder="Seleccionar tipo…"
              :options="[
                { value: '', label: 'Seleccionar tipo…' },
                ...store.types.map((t) => ({ value: t.id, label: t.name })),
              ]"
            />
            <p v-if="errors.client_type" class="text-xs text-red-400 mt-1">
              {{ errors.client_type }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Web / Instagram</label
            >
            <input
              v-model="form.web_instagram"
              type="text"
              class="input-field"
              placeholder="https://..."
            />
            <p v-if="errors.web_instagram" class="text-xs text-red-400 mt-1">
              {{ errors.web_instagram }}
            </p>
          </div>
          <div class="col-span-2">
            <label class="flex items-center gap-3 cursor-pointer group">
              <div
                class="w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-colors"
                :class="
                  form.is_agency
                    ? 'bg-gold border-gold'
                    : 'border-border group-hover:border-subtle'
                "
                @click="form.is_agency = !form.is_agency"
              >
                <svg
                  v-if="form.is_agency"
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
              <span class="text-sm text-ink"
                >Es una agencia (representa a varias marcas)</span
              >
            </label>
          </div>
          <div class="col-span-2">
            <p class="block text-xs font-medium text-muted mb-1.5">
              ID del cliente
            </p>
            <p class="text-xs text-muted/60 italic mt-2">
              Se asignará automáticamente
            </p>
          </div>
        </div>
        <div class="flex justify-end pt-2">
          <button
            type="button"
            class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors"
            @click="goToSection('contacto')"
          >
            Siguiente →
          </button>
        </div>
      </div>

      <!-- CONTACTO -->
      <div
        v-show="activeSection === 'contacto'"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5"
      >
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Persona de contacto *</label
            >
            <input
              v-model="form.contact_person"
              type="text"
              class="input-field"
              placeholder="Nombre y apellidos"
            />
            <p v-if="errors.contact_person" class="text-xs text-red-400 mt-1">
              {{ errors.contact_person }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Email de contacto *</label
            >
            <input
              v-model="form.contact_email"
              type="text"
              class="input-field"
              placeholder="contacto@empresa.com"
            />
            <p v-if="errors.contact_email" class="text-xs text-red-400 mt-1">
              {{ errors.contact_email }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Teléfono</label
            >
            <input
              v-model="form.phone"
              type="text"
              class="input-field"
              placeholder="+34 600 000 000"
            />
          </div>
        </div>
        <div class="flex justify-between pt-2">
          <button
            type="button"
            class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors"
            @click="goToSection('identificacion')"
          >
            ← Anterior
          </button>
          <button
            type="button"
            class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors"
            @click="goToSection('facturacion')"
          >
            Siguiente →
          </button>
        </div>
      </div>

      <!-- FACTURACIÓN -->
      <div
        v-show="activeSection === 'facturacion'"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Nombre de facturación *</label
            >
            <input
              v-model="form.billing_name"
              type="text"
              required
              class="input-field"
              placeholder="Razón social"
            />
            <p v-if="errors.billing_name" class="text-xs text-red-400 mt-1">
              {{ errors.billing_name }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >CIF *</label
            >
            <input
              v-model="form.cif"
              type="text"
              required
              class="input-field"
              placeholder="B12345678"
            />
            <p v-if="errors.cif" class="text-xs text-red-400 mt-1">
              {{ errors.cif }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Email de facturación *</label
            >
            <input
              v-model="form.billing_email"
              type="text"
              required
              class="input-field"
              placeholder="facturas@empresa.com"
            />
            <p v-if="errors.billing_email" class="text-xs text-red-400 mt-1">
              {{ errors.billing_email }}
            </p>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Dirección de facturación *</label
            >
            <input
              v-model="form.billing_address"
              type="text"
              required
              class="input-field"
              placeholder="Calle, número, piso…"
            />
            <p v-if="errors.billing_address" class="text-xs text-red-400 mt-1">
              {{ errors.billing_address }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Código postal *</label
            >
            <input
              v-model="form.postal_code"
              type="text"
              required
              class="input-field"
              placeholder="28001"
            />
            <p v-if="errors.postal_code" class="text-xs text-red-400 mt-1">
              {{ errors.postal_code }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Ciudad *</label
            >
            <input
              v-model="form.city"
              type="text"
              required
              class="input-field"
              placeholder="Madrid"
            />
            <p v-if="errors.city" class="text-xs text-red-400 mt-1">
              {{ errors.city }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >País</label
            >
            <input v-model="form.country" type="text" class="input-field" />
          </div>
        </div>
        <div class="flex justify-between pt-2">
          <button
            type="button"
            class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors"
            @click="goToSection('contacto')"
          >
            ← Anterior
          </button>
          <button
            type="button"
            class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors"
            @click="goToSection('marcas')"
          >
            Siguiente →
          </button>
        </div>
      </div>

      <!-- MARCAS -->
      <div
        v-show="activeSection === 'marcas'"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5"
      >
        <div class="py-6 text-center space-y-3">
          <div
            class="w-12 h-12 mx-auto rounded-xl bg-gold/10 flex items-center justify-center"
          >
            <svg
              class="w-6 h-6 text-gold"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6 6h.008v.008H6V6z"
              />
            </svg>
          </div>
          <p class="text-sm text-ink font-medium">
            Las marcas se gestionan de forma independiente
          </p>
          <p class="text-xs text-muted max-w-sm mx-auto">
            Una vez creado el cliente, podrás asociarle marcas desde la sección
            de Marcas.
          </p>
          <NuxtLink
            to="/dashboard/brands"
            class="inline-flex items-center gap-1.5 text-xs text-gold hover:text-gold/80 transition-colors mt-2"
          >
            Ir a Marcas
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
              />
            </svg>
          </NuxtLink>
        </div>
        <div class="flex justify-between pt-2">
          <button
            type="button"
            class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors"
            @click="goToSection('facturacion')"
          >
            ← Anterior
          </button>
          <button
            type="button"
            class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors"
            @click="goToSection('contrato')"
          >
            Siguiente →
          </button>
        </div>
      </div>

      <!-- CONTRATO -->
      <div
        v-show="activeSection === 'contrato'"
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5"
      >
        <!-- Contrato firmado -->
        <label class="flex items-center gap-3 cursor-pointer group">
          <div
            class="w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-colors"
            :class="
              form.contract_signed
                ? 'bg-gold border-gold'
                : 'border-border group-hover:border-subtle'
            "
            @click="form.contract_signed = !form.contract_signed"
          >
            <svg
              v-if="form.contract_signed"
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
          <span class="text-sm text-ink">Contrato firmado</span>
        </label>

        <!-- File upload -->
        <div>
          <label class="block text-xs font-medium text-muted mb-2"
            >Archivo de contrato
            <span class="text-subtle">(PDF, DOC…)</span></label
          >
          <label
            class="flex flex-col items-center justify-center gap-2 h-28 rounded-xl border border-dashed border-border hover:border-gold/40 hover:bg-gold/4 cursor-pointer transition-colors"
          >
            <svg
              class="w-6 h-6 text-muted"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
            <span class="text-xs text-muted">
              {{
                contratoFile
                  ? contratoFile.name
                  : 'Haz clic o arrastra un archivo aquí'
              }}
            </span>
            <input
              type="file"
              class="hidden"
              accept=".pdf,.doc,.docx,.png,.jpg"
              @change="handleFile"
            />
          </label>
        </div>

        <!-- Errors generales -->
        <div
          v-if="errors.general || errors.non_field_errors"
          class="rounded-xl border border-red-500/20 bg-red-500/8 p-3 text-xs text-red-400"
        >
          {{ errors.general || errors.non_field_errors }}
        </div>

        <div class="flex justify-between pt-2">
          <button
            type="button"
            class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors"
            @click="goToSection('marcas')"
          >
            ← Anterior
          </button>
          <button
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
            {{ isLoading ? 'Guardando…' : 'Dar de alta cliente' }}
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
