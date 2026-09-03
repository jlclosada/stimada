<script setup lang="ts">
import { useBrandsStore } from '~/stores/brands';
import { useClientsStore } from '~/stores/clients';

definePageMeta({ middleware: ['auth', 'role'] });

const brandsStore = useBrandsStore();
const clientsStore = useClientsStore();
const router = useRouter();

onMounted(() => clientsStore.fetchTypes());

// Client search
const clientSearch = ref('');
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
  clientSearch.value = '';
  clientResults.value = [];
  // Auto-inherit fields if client is not an agency
  if (!client.is_agency) {
    form.name = client.name;
    form.brand_type = client.client_type;
    form.web_instagram = client.web_instagram || '';
  }
}

function clearClient() {
  selectedClient.value = null;
  form.name = '';
  form.brand_type = null;
  form.web_instagram = '';
  form.contact_person = '';
  form.contact_email = '';
  form.phone = '';
}

// Form
const form = reactive({
  name: '',
  brand_type: null as number | null,
  web_instagram: '',
  contact_person: '',
  contact_email: '',
  phone: '',
  notes: '',
});

const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_RE = /^https?:\/\/.+/i;

function validateForm(): Record<string, string> {
  const e: Record<string, string> = {};
  if (!selectedClient.value) {
    e.client = 'Debes seleccionar un cliente.';
  }
  if (!form.name.trim()) {
    e.name = 'El nombre de la marca es obligatorio.';
  }
  if (!form.brand_type) {
    e.brand_type = 'Selecciona un tipo de marca.';
  }
  if (form.web_instagram && !URL_RE.test(form.web_instagram.trim())) {
    e.web_instagram = 'La URL debe empezar por http:// o https://';
  }
  if (form.contact_email && !EMAIL_RE.test(form.contact_email.trim())) {
    e.contact_email = 'Introduce un email válido (ej: nombre@dominio.com).';
  }
  return e;
}

const errorList = computed(() => Object.values(errors.value).filter(Boolean));

async function handleSubmit() {
  errors.value = validateForm();
  if (Object.keys(errors.value).length > 0) {
    return;
  }

  isLoading.value = true;
  try {
    await brandsStore.create({
      client: selectedClient.value.id,
      name: form.name,
      brand_type: form.brand_type || null,
      web_instagram: form.web_instagram,
      contact_person: form.contact_person,
      contact_email: form.contact_email,
      phone: form.phone,
      notes: form.notes,
    });
    router.push('/dashboard/brands');
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[] | string> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        let msg = Array.isArray(msgs) ? msgs[0] : String(msgs);
        // Mensaje más claro para el unique_together (cliente + nombre).
        if (
          field === 'non_field_errors' &&
          /conjunto único|unique set|deben formar un conjunto/i.test(msg)
        ) {
          msg = `Ya existe una marca llamada "${form.name}" para este cliente. Elige otro nombre o edita la marca existente.`;
          // También marcamos el campo "name" para destacarlo inline.
          errors.value.name = msg;
        }
        errors.value[field] = msg;
      });
    } else {
      errors.value.general = 'Error al crear la marca.';
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
      <NuxtLink
        to="/dashboard/brands"
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
        Marcas
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nueva marca</span>
    </div>

    <div class="mb-6">
      <p
        class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5"
      >
        Alta
      </p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">
        Nueva marca
      </h1>
    </div>

    <form novalidate class="space-y-5" @submit.prevent="handleSubmit">
      <!-- Banner de errores -->
      <div
        v-if="errorList.length"
        class="rounded-xl border border-red-300/60 bg-red-50 p-3 text-xs text-red-600"
      >
        <p class="font-medium mb-1">
          Revisa los siguientes campos antes de continuar:
        </p>
        <ul class="list-disc pl-5 space-y-0.5">
          <li v-for="(msg, i) in errorList" :key="i">{{ msg }}</li>
        </ul>
      </div>
      <!-- 1. Seleccionar cliente -->
      <div
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="flex items-center gap-2">
          <div
            class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center"
          >
            <svg
              class="w-3.5 h-3.5 text-blue-400"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
              />
            </svg>
          </div>
          <h3
            class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
          >
            Cliente asociado
          </h3>
        </div>

        <!-- Selected client -->
        <div
          v-if="selectedClient"
          class="flex items-center justify-between p-3.5 rounded-xl border border-blue-400/30 bg-blue-400/[0.04]"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-400/20 flex items-center justify-center"
            >
              <span class="text-sm font-bold text-blue-400">{{
                selectedClient.name.charAt(0)
              }}</span>
            </div>
            <div>
              <p class="text-sm font-medium text-ink">
                {{ selectedClient.name }}
              </p>
              <p class="text-[10px] text-muted/70">
                {{ selectedClient.is_agency ? 'Agencia' : 'Marca directa' }}
                <span v-if="selectedClient.type_name">
                  · {{ selectedClient.type_name }}</span
                >
              </p>
            </div>
          </div>
          <button
            type="button"
            class="text-xs text-red-400 hover:text-red-300 transition-colors"
            @click="clearClient"
          >
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
          <div
            v-if="clientResults.length"
            class="mt-2 rounded-xl border border-border/60 max-h-48 overflow-auto bg-white"
          >
            <button
              v-for="c in clientResults"
              :key="c.id"
              type="button"
              class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
              @click="selectClient(c)"
            >
              <span class="font-medium text-ink">{{ c.name }}</span>
              <span class="text-muted ml-2 text-xs">{{
                c.is_agency ? '(Agencia)' : '(Marca directa)'
              }}</span>
            </button>
          </div>
          <p v-if="errors.client" class="text-xs text-red-400 mt-1.5">
            {{ errors.client }}
          </p>
        </div>

        <!-- Inheritance notice -->
        <div
          v-if="selectedClient && !selectedClient.is_agency"
          class="rounded-lg bg-blue-50 border border-blue-200/50 px-4 py-2.5"
        >
          <p class="text-xs text-blue-600">
            <strong>Herencia automática:</strong> Como el cliente es una marca
            directa, los datos se han heredado automáticamente. Puedes
            ajustarlos si es necesario.
          </p>
        </div>
      </div>

      <!-- 2. Datos de la marca -->
      <div
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="flex items-center gap-2">
          <div
            class="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center"
          >
            <svg
              class="w-3.5 h-3.5 text-indigo-400"
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
          <h3
            class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
          >
            Datos de la marca
          </h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Nombre de la marca *</label
            >
            <input
              v-model="form.name"
              type="text"
              required
              class="input-field"
              placeholder="Nombre comercial"
            />
            <p v-if="errors.name" class="text-xs text-red-400 mt-1">
              {{ errors.name }}
            </p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Tipo de marca *</label
            >
            <BaseSelect
              v-model="form.brand_type"
              placeholder="Seleccionar tipo…"
              :options="[
                { value: null, label: 'Seleccionar tipo…' },
                ...clientsStore.types.map((t) => ({
                  value: t.id,
                  label: t.name,
                })),
              ]"
            />
            <p v-if="errors.brand_type" class="text-xs text-red-400 mt-1">
              {{ errors.brand_type }}
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
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Notas</label
            >
            <textarea
              v-model="form.notes"
              rows="3"
              class="input-field resize-none"
              placeholder="Notas internas sobre la marca…"
            />
          </div>
        </div>
      </div>

      <!-- 3. Contacto de la marca -->
      <div
        class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
      >
        <div class="flex items-center gap-2">
          <div
            class="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center"
          >
            <svg
              class="w-3.5 h-3.5 text-emerald-400"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
              />
            </svg>
          </div>
          <h3
            class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
          >
            Contacto de la marca
          </h3>
        </div>
        <p class="text-xs text-muted/60">
          Opcional. Si se dejan vacíos, se heredarán automáticamente del cliente
          asociado.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Persona de contacto</label
            >
            <input
              v-model="form.contact_person"
              type="text"
              class="input-field"
              placeholder="Nombre del contacto de la marca"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Email de contacto</label
            >
            <input
              v-model="form.contact_email"
              type="text"
              class="input-field"
              placeholder="email@marca.com"
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
              type="tel"
              class="input-field"
              placeholder="+34 …"
            />
          </div>
        </div>
      </div>

      <!-- Errors -->
      <div
        v-if="errors.general"
        class="rounded-xl border border-red-500/20 bg-red-500/[0.04] p-3 text-xs text-red-400"
      >
        {{ errors.general }}
      </div>

      <!-- Submit -->
      <div class="flex justify-end">
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
          {{ isLoading ? 'Creando…' : 'Crear marca' }}
        </button>
      </div>
    </form>
  </div>
</template>
