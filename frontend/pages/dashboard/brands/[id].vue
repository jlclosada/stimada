<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import { useBrandsStore, type BrandDetail } from '~/stores/brands';
import { useClientsStore } from '~/stores/clients';
import { formatBrandId } from '~/utils/formatId';

definePageMeta({ middleware: ['auth', 'role'] });

const route = useRoute();
const router = useRouter();
const store = useBrandsStore();
const clientsStore = useClientsStore();
const auth = useAuthStore();

const brand = ref<BrandDetail | null>(null);
const isLoading = ref(true);
const error = ref('');

// Edit state
const isEditing = ref(false);
const isSaving = ref(false);
const editData = ref<Record<string, unknown>>({});
const saveError = ref('');

// Delete
const showDeleteModal = ref(false);
const isDeleting = ref(false);

const canEdit = computed(() => {
  return auth.user?.role === 'admin' || auth.user?.role === 'stimada_employee';
});

async function load() {
  isLoading.value = true;
  try {
    brand.value = await store.fetchDetail(route.params.id as string);
  } catch {
    error.value = 'No se pudo cargar la marca.';
  } finally {
    isLoading.value = false;
  }
}

function startEditing() {
  if (!brand.value) return;
  editData.value = { ...brand.value };
  isEditing.value = true;
  saveError.value = '';
}

function cancelEditing() {
  isEditing.value = false;
  editData.value = {};
}

async function saveChanges() {
  if (!brand.value) return;
  isSaving.value = true;
  saveError.value = '';
  try {
    const payload: Record<string, unknown> = {};
    const editableKeys = [
      'name',
      'brand_type',
      'web_instagram',
      'contact_person',
      'contact_email',
      'phone',
      'notes',
      'status',
    ];
    for (const key of editableKeys) {
      if (
        editData.value[key] !== (brand.value as Record<string, unknown>)[key]
      ) {
        payload[key] = editData.value[key];
      }
    }
    if (Object.keys(payload).length === 0) {
      isEditing.value = false;
      return;
    }
    brand.value = await store.update(route.params.id as string, payload);
    isEditing.value = false;
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      const firstField = Object.keys(e.data)[0];
      saveError.value = Array.isArray(e.data[firstField])
        ? e.data[firstField][0]
        : 'Error al guardar.';
    } else {
      saveError.value = 'Error al guardar los cambios.';
    }
  } finally {
    isSaving.value = false;
  }
}

async function handleDelete() {
  isDeleting.value = true;
  try {
    await store.deleteBrand(route.params.id as string);
    router.push('/dashboard/brands');
  } catch {
    showDeleteModal.value = false;
  } finally {
    isDeleting.value = false;
  }
}

onMounted(() => clientsStore.fetchTypes());
load();
</script>

<template>
  <div class="max-w-5xl animate-fade-up">
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <div
        class="w-10 h-10 rounded-full border-2 border-gold/20 border-t-gold animate-spin"
      />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-sm text-red-400">{{ error }}</p>
    </div>

    <div v-else-if="brand" class="space-y-6">
      <!-- Back -->
      <NuxtLink
        to="/dashboard/brands"
        class="group inline-flex items-center gap-2 text-xs text-muted hover:text-ink transition-colors"
      >
        <svg
          class="w-4 h-4 transition-transform group-hover:-translate-x-0.5"
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
        Volver a Marcas
      </NuxtLink>

      <!-- Header -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-7">
        <div class="flex items-start justify-between gap-6">
          <div class="flex items-center gap-5">
            <div
              class="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-400/20 flex items-center justify-center text-indigo-400 text-xl font-semibold"
            >
              {{ brand.name.charAt(0) }}
            </div>
            <div>
              <h1 class="text-2xl font-semibold tracking-tight text-ink">
                {{ brand.name }}
              </h1>
              <div class="flex items-center gap-2.5 mt-1.5">
                <span class="text-[11px] text-muted/70 font-mono">{{
                  formatBrandId(brand.brand_id)
                }}</span>
                <span
                  v-if="brand.brand_type_name"
                  class="text-[11px] px-2 py-0.5 rounded-full border border-indigo-400/15 text-indigo-400 bg-indigo-400/[0.06] font-medium"
                >
                  {{ brand.brand_type_name }}
                </span>
                <span
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border"
                  :class="
                    brand.status === 'activa'
                      ? 'text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15'
                      : 'text-muted/60 bg-panel border-border/40'
                  "
                >
                  {{ brand.status === 'activa' ? 'Activa' : 'Inactiva' }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="canEdit && !isEditing" class="flex items-center gap-2">
            <button
              class="px-4 h-9 rounded-xl border border-border/80 text-xs font-medium text-muted hover:text-ink hover:border-ink/20 transition-all"
              @click="startEditing"
            >
              Editar
            </button>
            <button
              class="px-4 h-9 rounded-xl border border-red-500/15 text-xs font-medium text-red-400/80 hover:text-red-400 hover:bg-red-500/[0.06] transition-all"
              @click="showDeleteModal = true"
            >
              Eliminar
            </button>
          </div>
          <div v-if="isEditing" class="flex items-center gap-2">
            <button
              class="px-4 h-9 rounded-xl border border-border text-xs font-medium text-muted hover:text-ink transition-all"
              :disabled="isSaving"
              @click="cancelEditing"
            >
              Cancelar
            </button>
            <button
              class="px-5 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 disabled:opacity-60 transition-all"
              :disabled="isSaving"
              @click="saveChanges"
            >
              {{ isSaving ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Save error -->
      <div
        v-if="saveError"
        class="rounded-2xl border border-red-500/20 px-5 py-3 text-xs text-red-400"
      >
        {{ saveError }}
      </div>

      <!-- VIEW MODE -->
      <template v-if="!isEditing">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Datos de la marca -->
          <div
            class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center"
              >
                <svg
                  class="w-3.5 h-3.5 text-indigo-400"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
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
            <div class="space-y-3">
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Nombre
                </p>
                <p class="text-sm text-ink font-medium">{{ brand.name }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  ID
                </p>
                <p class="text-sm text-ink font-mono tracking-wide">
                  {{ formatBrandId(brand.brand_id) }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Tipo
                </p>
                <p class="text-sm text-ink">
                  {{ brand.brand_type_name || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Web / IG
                </p>
                <a
                  v-if="brand.web_instagram"
                  :href="brand.web_instagram"
                  target="_blank"
                  class="text-sm text-gold hover:text-gold/80 truncate transition-colors"
                  >{{ brand.web_instagram }}</a
                >
                <p v-else class="text-sm text-muted/50">—</p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Estado
                </p>
                <span
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border"
                  :class="
                    brand.status === 'activa'
                      ? 'text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15'
                      : 'text-muted/60 bg-panel border-border/40'
                  "
                >
                  {{ brand.status === 'activa' ? 'Activa' : 'Inactiva' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Cliente asociado -->
          <div
            class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft"
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
                    d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z"
                  />
                </svg>
              </div>
              <h3
                class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
              >
                Cliente asociado
              </h3>
              <span
                v-if="brand.client_data?.is_agency"
                class="ml-auto text-[10px] text-amber-400 bg-amber-400/[0.06] px-2 py-0.5 rounded-full border border-amber-400/15 font-medium"
                >Agencia</span
              >
              <span
                v-else
                class="ml-auto text-[10px] text-blue-400 bg-blue-400/[0.06] px-2 py-0.5 rounded-full border border-blue-400/15 font-medium"
                >Marca directa</span
              >
            </div>
            <div class="space-y-3">
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Cliente
                </p>
                <NuxtLink
                  :to="`/dashboard/clients/${brand.client}`"
                  class="text-sm text-ink font-medium hover:text-gold transition-colors"
                >
                  {{ brand.client_name }}
                </NuxtLink>
              </div>
              <div v-if="brand.client_data" class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  ID Cliente
                </p>
                <p class="text-sm text-ink font-mono tracking-wide">
                  {{ brand.client_data.client_id }}
                </p>
              </div>
              <div
                v-if="brand.client_data?.type_name"
                class="flex items-start gap-3"
              >
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Tipo
                </p>
                <p class="text-sm text-ink">
                  {{ brand.client_data.type_name }}
                </p>
              </div>
              <div
                v-if="brand.client_data?.web_instagram"
                class="flex items-start gap-3"
              >
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Web / IG
                </p>
                <a
                  :href="brand.client_data.web_instagram"
                  target="_blank"
                  class="text-sm text-gold hover:text-gold/80 truncate transition-colors"
                  >{{ brand.client_data.web_instagram }}</a
                >
              </div>
            </div>
          </div>

          <!-- Contacto -->
          <div
            class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft"
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
                Contacto
              </h3>
              <span
                v-if="brand.effective_contact?.is_own"
                class="ml-auto text-[10px] text-emerald-400 bg-emerald-400/[0.06] px-2 py-0.5 rounded-full border border-emerald-400/15 font-medium"
                >Propio</span
              >
              <span v-else class="ml-auto text-[10px] text-muted/50 italic"
                >heredado del cliente</span
              >
            </div>
            <div v-if="brand.effective_contact" class="space-y-3">
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Persona
                </p>
                <p class="text-sm text-ink">
                  {{ brand.effective_contact.contact_person || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Email
                </p>
                <a
                  v-if="brand.effective_contact.contact_email"
                  :href="`mailto:${brand.effective_contact.contact_email}`"
                  class="text-sm text-gold hover:text-gold/80 transition-colors"
                  >{{ brand.effective_contact.contact_email }}</a
                >
                <p v-else class="text-sm text-muted/50">—</p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Teléfono
                </p>
                <p class="text-sm text-ink">
                  {{ brand.effective_contact.phone || '—' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Facturación (heredado del cliente) -->
          <div
            class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center"
              >
                <svg
                  class="w-3.5 h-3.5 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                  />
                </svg>
              </div>
              <h3
                class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
              >
                Facturación
              </h3>
              <span class="ml-auto text-[10px] text-muted/50 italic"
                >vía cliente</span
              >
            </div>
            <div v-if="brand.client_data" class="space-y-3">
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Razón social
                </p>
                <p class="text-sm text-ink">
                  {{ brand.client_data.billing_name || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  CIF
                </p>
                <p class="text-sm text-ink font-mono tracking-wide">
                  {{ brand.client_data.cif || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Email
                </p>
                <p class="text-sm text-ink">
                  {{ brand.client_data.billing_email || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  Dirección
                </p>
                <p class="text-sm text-ink">
                  {{ brand.client_data.billing_address || '—' }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  C.P. / Ciudad
                </p>
                <p class="text-sm text-ink">
                  {{
                    [brand.client_data.postal_code, brand.client_data.city]
                      .filter(Boolean)
                      .join(', ') || '—'
                  }}
                </p>
              </div>
              <div class="flex items-start gap-3">
                <p
                  class="text-[11px] text-muted/70 w-24 flex-shrink-0 pt-0.5 uppercase tracking-wider"
                >
                  País
                </p>
                <p class="text-sm text-ink">
                  {{ brand.client_data.country || '—' }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Notas -->
        <div
          v-if="brand.notes"
          class="rounded-3xl border border-border/60 bg-white shadow-card p-6 transition-all duration-300 hover:border-border hover:shadow-soft"
        >
          <div class="flex items-center gap-2 mb-3">
            <div
              class="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center"
            >
              <svg
                class="w-3.5 h-3.5 text-amber-400"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"
                />
              </svg>
            </div>
            <h3
              class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
            >
              Notas
            </h3>
          </div>
          <p class="text-sm text-muted leading-relaxed whitespace-pre-wrap">
            {{ brand.notes }}
          </p>
        </div>

        <!-- Proyectos asociados -->
        <div
          class="rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft"
        >
          <div class="flex items-center gap-2">
            <div
              class="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center"
            >
              <svg
                class="w-3.5 h-3.5 text-gold"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
                />
              </svg>
            </div>
            <h3
              class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted"
            >
              Proyectos asociados
            </h3>
            <span
              v-if="brand.projects && brand.projects.length"
              class="ml-auto text-[10px] text-muted/60 bg-panel px-2 py-0.5 rounded-full border border-border/40"
              >{{ brand.projects.length }}</span
            >
          </div>
          <div
            v-if="brand.projects && brand.projects.length > 0"
            class="space-y-2"
          >
            <NuxtLink
              v-for="project in brand.projects"
              :key="project.id"
              :to="`/projects/${project.id}`"
              class="flex items-center justify-between p-3.5 rounded-xl border border-border/50 hover:border-gold/30 hover:bg-gold/[0.02] transition-all duration-200 group/item"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-9 h-9 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0"
                >
                  <svg
                    class="w-4 h-4 text-gold"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
                    />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p
                    class="text-sm font-medium text-ink truncate group-hover/item:text-gold transition-colors duration-200"
                  >
                    {{ project.name }}
                  </p>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-[11px] text-muted/70 font-mono">{{
                      project.project_id
                    }}</span>
                    <span
                      v-if="project.content_maker_name"
                      class="text-[11px] text-muted/70"
                      >· {{ project.content_maker_name }}</span
                    >
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-3 flex-shrink-0 ml-3">
                <span
                  v-if="project.status_name"
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border border-border bg-panel text-muted"
                >
                  {{ project.status_name }}
                </span>
                <span
                  v-if="project.service_date"
                  class="text-[11px] text-muted/60 hidden sm:inline"
                >
                  {{
                    new Date(project.service_date).toLocaleDateString('es-ES', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })
                  }}
                </span>
                <svg
                  class="w-4 h-4 text-muted/40 group-hover/item:text-gold transition-colors duration-200"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M8.25 4.5l7.5 7.5-7.5 7.5"
                  />
                </svg>
              </div>
            </NuxtLink>
          </div>
          <div v-else class="py-4 text-center">
            <p class="text-xs text-muted/60">
              Esta marca no tiene proyectos asociados.
            </p>
          </div>
        </div>
      </template>

      <!-- EDIT MODE -->
      <template v-if="isEditing">
        <div
          class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4"
        >
          <h3
            class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold"
          >
            Editar marca
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Nombre de la marca</label
              >
              <input v-model="editData.name" type="text" class="input-field" />
            </div>
            <div>
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Tipo de marca</label
              >
              <BaseSelect
                v-model="editData.brand_type"
                :options="[
                  { value: null, label: 'Sin tipo' },
                  ...clientsStore.types.map((t) => ({
                    value: t.id,
                    label: t.name,
                  })),
                ]"
              />
            </div>
            <div>
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Web / Instagram</label
              >
              <input
                v-model="editData.web_instagram"
                type="url"
                class="input-field"
              />
            </div>
            <div>
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Estado</label
              >
              <BaseSelect
                v-model="editData.status"
                :options="[
                  { value: 'activa', label: 'Activa' },
                  { value: 'inactiva', label: 'Inactiva' },
                ]"
              />
            </div>
            <div class="md:col-span-2">
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Notas</label
              >
              <textarea
                v-model="editData.notes"
                rows="3"
                class="input-field resize-none"
              />
            </div>
          </div>
        </div>

        <!-- Contacto propio de la marca -->
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
              class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold"
            >
              Contacto de la marca
            </h3>
          </div>
          <p class="text-xs text-muted/60">
            Si se dejan vacíos, se heredarán automáticamente del cliente.
          </p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Persona de contacto</label
              >
              <input
                v-model="editData.contact_person"
                type="text"
                class="input-field"
                :placeholder="
                  brand?.client_data?.contact_person || 'Heredado del cliente'
                "
              />
            </div>
            <div>
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Email de contacto</label
              >
              <input
                v-model="editData.contact_email"
                type="email"
                class="input-field"
                :placeholder="
                  brand?.client_data?.contact_email || 'Heredado del cliente'
                "
              />
            </div>
            <div>
              <label
                class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider"
                >Teléfono</label
              >
              <input
                v-model="editData.phone"
                type="tel"
                class="input-field"
                :placeholder="
                  brand?.client_data?.phone || 'Heredado del cliente'
                "
              />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- DELETE MODAL -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showDeleteModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px)"
          @click.self="showDeleteModal = false"
        >
          <div
            class="w-full max-w-sm rounded-3xl border border-red-500/20 p-8 shadow-2xl"
            style="
              background: linear-gradient(180deg, #161619 0%, #111113 100%);
            "
          >
            <h2 class="text-lg font-semibold text-ink mb-2">Eliminar marca</h2>
            <p class="text-sm text-muted mb-6">
              ¿Estás seguro de que quieres eliminar
              <strong class="text-ink">{{ brand?.name }}</strong
              >?
            </p>
            <div class="flex gap-3">
              <button
                class="flex-1 h-11 rounded-xl border border-border text-sm text-muted hover:text-ink transition-all"
                :disabled="isDeleting"
                @click="showDeleteModal = false"
              >
                Cancelar
              </button>
              <button
                class="flex-1 h-11 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-400 disabled:opacity-60 transition-all"
                :disabled="isDeleting"
                @click="handleDelete"
              >
                {{ isDeleting ? 'Eliminando…' : 'Eliminar' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
