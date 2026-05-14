<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import type { ContentMakerDetail } from "~/stores/contentMakers";
import { useContentMakersStore } from "~/stores/contentMakers";
import { formatContentMakerId } from "~/utils/formatId";

definePageMeta({ middleware: ["auth", "role"] });

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const store = useContentMakersStore();
const auth = useAuthStore();

const cm = ref<ContentMakerDetail | null>(null);
const isLoading = ref(true);
const error = ref("");

// Edit state
const isEditing = ref(false);
const isSaving = ref(false);
const editData = ref<Partial<ContentMakerDetail>>({});
const saveError = ref("");

// Delete state
const showDeleteModal = ref(false);
const isDeleting = ref(false);

// Account creation state
const showCreateModal = ref(false);
const createEmail = ref("");
const isCreating = ref(false);
const createError = ref("");
const createdCredentials = ref<{ email: string; password: string } | null>(null);

// Send credentials state
const isSending = ref(false);
const sendSuccess = ref(false);
const copied = ref(false);

// IBAN copy state
const ibanCopied = ref(false);
async function copyIban() {
  if (!cm.value?.iban) return;
  await navigator.clipboard.writeText(cm.value.iban);
  ibanCopied.value = true;
  setTimeout(() => (ibanCopied.value = false), 2000);
}

const canEdit = computed(() => {
  return auth.user?.role === "admin" || auth.user?.role === "stimada_employee";
});

const canEditTallaje = computed(() => auth.user?.role === "admin");

const canEditFiscal = computed(() => auth.user?.role === "admin");

const canEditDni = computed(() => auth.user?.role === "admin");

const isClient = computed(() => auth.user?.role === "client");

// Tallaje options from backend
const tallajeOptions = ref<Record<string, { label: string; options: string[] }>>({});

// Desempeño options from backend
const desempenoOptions = ref<DesempenoOption[]>([]);

async function loadTallajeOptions() {
  try {
    tallajeOptions.value = await $fetch(`${config.public.apiBase}/content-makers/tallaje_options/`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
  } catch {
    // fallback empty
  }
}

async function loadDesempenoOptions() {
  try {
    desempenoOptions.value = await $fetch(`${config.public.apiBase}/content-makers/desempeno_options/`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
  } catch {
    // fallback empty
  }
}

// Favorites
const isFavorite = ref(false);
const favoriteLoading = ref(false);

// Project selection flow (when coming from a project's CM browser)
const fromProject = computed(() => route.query.fromProject as string | undefined);
const selectLoading = ref(false);
const selectDone = ref(false);

async function selectForProject() {
  if (!fromProject.value) return;
  selectLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${fromProject.value}/select_cm/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { content_maker_id: Number(route.params.id) },
    });
    selectDone.value = true;
  } catch {
    // silent
  } finally {
    selectLoading.value = false;
  }
}

async function checkFavorite() {
  if (!isClient.value) return;
  try {
    const favorites = await $fetch<{ id: number }[]>(
      `${config.public.apiBase}/clients/me/favorite-cms/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    isFavorite.value = favorites.some((f) => f.id === Number(route.params.id));
  } catch {
    // ignore
  }
}

async function toggleFavorite() {
  favoriteLoading.value = true;
  try {
    if (isFavorite.value) {
      await $fetch(`${config.public.apiBase}/clients/me/favorite-cms/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { content_maker_id: Number(route.params.id) },
      });
      isFavorite.value = false;
    } else {
      await $fetch(`${config.public.apiBase}/clients/me/favorite-cms/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { content_maker_id: Number(route.params.id) },
      });
      isFavorite.value = true;
    }
  } catch {
    // ignore
  } finally {
    favoriteLoading.value = false;
  }
}

async function load() {
  isLoading.value = true;
  try {
    cm.value = await store.fetchDetail(route.params.id as string);
    createEmail.value = cm.value?.email ?? "";
    checkFavorite();
    loadTallajeOptions();
  } catch {
    error.value = "No se pudo cargar el perfil.";
  } finally {
    isLoading.value = false;
  }
}

function startEditing() {
  if (!cm.value) return;
  editData.value = { ...cm.value };
  isEditing.value = true;
  saveError.value = "";
  loadTallajeOptions();
  loadDesempenoOptions();
}

function cancelEditing() {
  isEditing.value = false;
  editData.value = {};
  saveError.value = "";
}

function toggleDesempeno(id: number) {
  const current = editData.value.desempeno_opciones as number[] || [];
  if (current.includes(id)) {
    editData.value.desempeno_opciones = current.filter((x: number) => x !== id);
  } else {
    editData.value.desempeno_opciones = [...current, id];
  }
}

async function saveChanges() {
  if (!cm.value) return;
  isSaving.value = true;
  saveError.value = "";
  try {
    // Only send changed fields
    const payload: Record<string, unknown> = {};
    const keys = Object.keys(editData.value) as (keyof ContentMakerDetail)[];
    for (const key of keys) {
      if (["id", "nombre_completo", "tiene_cuenta", "user_id", "user_email", "created_at", "updated_at"].includes(key)) continue;
      if (editData.value[key] !== (cm.value as Record<string, unknown>)[key]) {
        payload[key] = editData.value[key];
      }
    }
    if (Object.keys(payload).length === 0) {
      isEditing.value = false;
      return;
    }
    cm.value = await store.updateContentMaker(route.params.id as string, payload);
    isEditing.value = false;
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      const firstField = Object.keys(e.data)[0];
      saveError.value = Array.isArray(e.data[firstField]) ? e.data[firstField][0] : "Error al guardar.";
    } else {
      saveError.value = "Error al guardar los cambios.";
    }
  } finally {
    isSaving.value = false;
  }
}

async function handleDelete() {
  isDeleting.value = true;
  try {
    await store.deleteContentMaker(route.params.id as string);
    router.push("/dashboard/content-makers");
  } catch {
    showDeleteModal.value = false;
  } finally {
    isDeleting.value = false;
  }
}

async function handleCreateAccount() {
  createError.value = "";
  isCreating.value = true;
  try {
    const result = await store.createAccount(route.params.id as string, createEmail.value || undefined);
    createdCredentials.value = { email: result.email, password: result.password };
    showCreateModal.value = false;
    await load();
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    createError.value = e?.data?.detail ?? "Error al crear la cuenta.";
  } finally {
    isCreating.value = false;
  }
}

async function handleSendCredentials() {
  if (!createdCredentials.value) return;
  isSending.value = true;
  sendSuccess.value = false;
  try {
    await store.sendCredentials(
      route.params.id as string,
      createdCredentials.value.email,
      createdCredentials.value.password
    );
    sendSuccess.value = true;
  } catch {
    // ignore, credentials are still shown
  } finally {
    isSending.value = false;
  }
}

async function copyPassword() {
  if (!createdCredentials.value) return;
  await navigator.clipboard.writeText(createdCredentials.value.password);
  copied.value = true;
  setTimeout(() => (copied.value = false), 2000);
}

function fmt(n: number | null) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

function bool(v: boolean) { return v ? "Sí" : "No"; }

load();
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <svg class="animate-spin w-6 h-6 text-gold" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <div v-else-if="cm" class="animate-fade-up">
      <!-- Back -->
      <div class="max-w-5xl">
        <NuxtLink v-if="fromProject" :to="`/proyectos/${fromProject}`" class="inline-flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors mb-4">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Volver al proyecto
        </NuxtLink>
        <NuxtLink v-else-if="canEdit" to="/dashboard/content-makers" class="inline-flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors mb-4">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Volver a Content Makers
        </NuxtLink>
      </div>

      <!-- Two-column layout: content + photo -->
      <div class="flex gap-6 items-start">
        <!-- Main content column -->
        <div class="max-w-4xl flex-1 space-y-5">

      <!-- Header -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 flex items-start justify-between gap-4" >
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0">
              <img
                v-if="cm.foto_url"
                :src="cm.foto_url"
                :alt="cm.nombre_completo"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full bg-orange-400/10 border border-orange-400/20 flex items-center justify-center text-orange-400 text-lg font-semibold">
                {{ cm.nombre.charAt(0) }}{{ cm.apellidos.charAt(0) }}
              </div>
            </div>
            <div>
              <div class="flex items-center gap-3 flex-wrap">
                <h1 class="text-2xl font-semibold tracking-tight text-ink">{{ cm.nombre_completo }}</h1>
                <!-- Fee badge -->
                <div v-if="canEdit && (cm.fee_instagram || cm.fee_tiktok)" class="flex items-center gap-1.5">
                  <span v-if="cm.fee_instagram" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gold/10 border border-gold/20">
                    <svg class="w-3.5 h-3.5 text-gold" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5" /><circle cx="12" cy="12" r="5" /><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none" /></svg>
                    <span class="text-xs font-semibold text-gold">{{ cm.fee_instagram }}€</span>
                  </span>
                  <span v-if="cm.fee_tiktok" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-ink/5 border border-ink/10">
                    <svg class="w-3 h-3 text-ink/70" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"/></svg>
                    <span class="text-xs font-semibold text-ink/70">{{ cm.fee_tiktok }}€</span>
                  </span>
                </div>
              </div>
              <div class="flex items-center gap-2 mt-1 flex-wrap">
                <span v-if="canEdit" class="text-xs text-muted">{{ formatContentMakerId(cm.stimada_id) }}</span>
                <span v-if="canEdit" class="text-border">·</span>
                <span class="text-xs text-muted">{{ cm.tipo_cm }}</span>
                <span
                  v-if="cm.status"
                  class="text-xs font-medium px-2 py-0.5 rounded-full border"
                  :class="cm.status === 'Alta' ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : 'text-muted border-border'"
                >
                  {{ cm.status }}
                </span>
              </div>
            </div>
          </div>

        <!-- Action buttons -->
        <div class="flex-shrink-0 flex items-center gap-2">
          <!-- Select for project button (when coming from project CM browser) -->
          <button
            v-if="isClient && fromProject && !selectDone"
            :disabled="selectLoading"
            class="px-5 h-9 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50 flex items-center gap-1.5"
            @click="selectForProject"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Seleccionar para proyecto
          </button>
          <span
            v-if="isClient && fromProject && selectDone"
            class="px-4 h-9 rounded-xl text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Invitación enviada
          </span>
          <!-- Favorite button for clients -->
          <button
            v-if="isClient"
            :disabled="favoriteLoading"
            class="px-4 h-9 rounded-xl border text-xs font-medium transition-all flex items-center gap-1.5 disabled:opacity-50"
            :class="isFavorite
              ? 'border-pink-200 text-pink-600 bg-pink-50 hover:bg-pink-100'
              : 'border-border text-muted hover:text-pink-600 hover:border-pink-200 hover:bg-pink-50'"
            @click="toggleFavorite"
          >
            <svg class="w-3.5 h-3.5" :fill="isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
            </svg>
            {{ isFavorite ? 'Favorita' : 'Guardar como favorita' }}
          </button>
          <!-- Edit/Delete buttons for admin/employee -->
          <template v-if="canEdit && !isEditing">
            <button
              class="px-4 h-9 rounded-xl border border-border text-xs font-medium text-muted hover:text-ink hover:border-ink/20 transition-all"
              @click="startEditing"
            >
              <span class="flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                </svg>
                Editar
              </span>
            </button>
            <button
              class="px-4 h-9 rounded-xl border border-red-200 text-xs font-medium text-red-500 hover:bg-red-50 hover:border-red-300 transition-all"
              @click="showDeleteModal = true"
            >
              <span class="flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
                Eliminar
              </span>
            </button>
          </template>
          <!-- Save/Cancel when editing -->
          <template v-if="isEditing">
            <button
              class="px-4 h-9 rounded-xl border border-border text-xs font-medium text-muted hover:text-ink transition-all"
              :disabled="isSaving"
              @click="cancelEditing"
            >
              Cancelar
            </button>
            <button
              class="px-4 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all flex items-center gap-1.5"
              :disabled="isSaving"
              @click="saveChanges"
            >
              <svg v-if="isSaving" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ isSaving ? "Guardando…" : "Guardar cambios" }}
            </button>
          </template>
        </div>
      </div>

      <!-- Save error -->
      <div v-if="saveError" class="rounded-xl border border-red-200 p-3 text-xs text-red-500" style="background:rgba(239,68,68,0.04)">
        {{ saveError }}
      </div>

      <!-- Account status -->
      <div v-if="canEdit" class="rounded-2xl border border-border/60 bg-white shadow-card p-5 flex items-center justify-between" >
        <div v-if="cm.tiene_cuenta" class="flex items-center gap-2">
          <svg class="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
          </svg>
          <span class="text-xs text-emerald-600 font-medium">Cuenta activa</span>
          <span class="text-xs text-muted ml-2">{{ cm.user_email }}</span>
        </div>
        <button
          v-else
          class="px-4 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 active:scale-[0.98] transition-all"
          @click="showCreateModal = true"
        >
          Crear cuenta de acceso
        </button>
      </div>

      <!-- Credentials revealed after creation -->
      <Transition name="modal-content" appear>
        <div
          v-if="createdCredentials"
          class="rounded-2xl border border-emerald-200 p-5 space-y-3"
          style="background: rgba(74,222,128,0.04)"
        >
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <p class="text-sm font-semibold text-emerald-600">Cuenta creada correctamente</p>
          </div>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div>
              <p class="text-muted mb-1">Email de acceso</p>
              <p class="text-ink font-medium">{{ createdCredentials.email }}</p>
            </div>
            <div>
              <p class="text-muted mb-1">Contraseña generada</p>
              <div class="flex items-center gap-2">
                <code class="font-mono text-ink bg-raised px-2 py-1 rounded-lg border border-border">{{ createdCredentials.password }}</code>
                <button
                  class="text-muted hover:text-ink transition-colors flex-shrink-0"
                  :title="copied ? 'Copiado' : 'Copiar'"
                  @click="copyPassword"
                >
                  <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  <svg v-else class="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 pt-1">
            <button
              class="h-8 px-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-600 font-medium hover:bg-emerald-100 transition-colors flex items-center gap-1.5 disabled:opacity-50"
              :disabled="isSending || sendSuccess"
              @click="handleSendCredentials"
            >
              <svg v-if="isSending" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ sendSuccess ? "✓ Email enviado" : isSending ? "Enviando…" : "Enviar por email" }}
            </button>
            <p class="text-xs text-muted">Guarda la contraseña — no se volverá a mostrar.</p>
          </div>
        </div>
      </Transition>

      <!-- ============ VIEW MODE ============ -->
      <template v-if="!isEditing">
        <!-- Info grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Redes sociales -->
          <div class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Redes sociales</h3>
            <div class="space-y-3">
              <!-- Instagram -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                  </svg>
                </div>
                <div>
                  <a
                    v-if="cm.link_instagram"
                    :href="cm.link_instagram"
                    target="_blank"
                    class="text-sm text-ink hover:text-gold transition-colors font-medium"
                  >
                    @{{ cm.instagram_handle }}
                  </a>
                  <p v-else class="text-sm text-ink">@{{ cm.instagram_handle || "—" }}</p>
                  <p class="text-xs text-muted">{{ fmt(cm.seguidores_instagram) }} seguidores · {{ cm.categoria_seguidores_ig || "—" }}</p>
                </div>
              </div>
              <!-- TikTok -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-xl bg-black border border-border flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"/>
                  </svg>
                </div>
                <div>
                  <a
                    v-if="cm.link_tiktok"
                    :href="cm.link_tiktok"
                    target="_blank"
                    class="text-sm text-ink hover:text-gold transition-colors font-medium"
                  >
                    {{ cm.tiktok_handle || "—" }}
                  </a>
                  <p v-else class="text-sm text-ink">{{ cm.tiktok_handle || "—" }}</p>
                  <p class="text-xs text-muted">{{ fmt(cm.seguidores_tiktok) }} seguidores · {{ cm.categoria_seguidores_tt || "—" }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Valoración interna -->
          <div v-if="canEdit" class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-3" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Valoración</h3>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-xs text-muted">Calidad del contenido</p>
                <p class="text-xs text-ink mt-0.5">{{ cm.calidad_contenido != null ? `${cm.calidad_contenido} / 5` : "—" }}</p>
              </div>
              <div>
                <p class="text-xs text-muted">Desempeño</p>
                <div class="flex flex-wrap gap-1 mt-0.5">
                  <span
                    v-for="opt in cm.desempeno_opciones_display"
                    :key="opt.id"
                    class="text-xs px-2 py-0.5 rounded-full border border-amber-200 text-amber-700 bg-amber-50"
                  >{{ opt.nombre }}</span>
                  <span v-if="!cm.desempeno_opciones_display?.length" class="text-xs text-ink">—</span>
                </div>
              </div>
              <div class="col-span-2">
                <p class="text-xs text-muted">Comentarios internos</p>
                <p class="text-sm text-ink/80 mt-0.5 leading-relaxed">{{ cm.comentarios || "—" }}</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2 pt-1">
              <span v-if="cm.es_mama" class="text-xs px-2 py-0.5 rounded-full border border-pink-200 text-pink-600 bg-pink-50">Mamá</span>
              <span v-if="cm.sigue_stimada" class="text-xs px-2 py-0.5 rounded-full border border-blue-200 text-blue-600 bg-blue-50">Sigue @stimada</span>
              <span v-if="cm.stimada_en_bio" class="text-xs px-2 py-0.5 rounded-full border border-purple-200 text-purple-600 bg-purple-50">Stimada en bio</span>
              <span v-if="cm.contrato_firmado" class="text-xs px-2 py-0.5 rounded-full border border-emerald-200 text-emerald-600 bg-green-400/8">Contrato firmado</span>
            </div>
          </div>

          <!-- Tallaje -->
          <div class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Tallaje</h3>
            <div class="grid grid-cols-3 gap-3">
              <div
                v-for="(cat, campo) in tallajeOptions"
                :key="campo"
                class="flex flex-col items-center p-3 rounded-xl border border-border bg-panel"
              >
                <svg class="w-5 h-5 text-muted mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                </svg>
                <p class="text-[10px] uppercase tracking-wider text-muted mb-1">{{ cat.label }}</p>
                <p class="text-lg font-semibold text-ink">{{ (cm as Record<string, unknown>)[campo] || "—" }}</p>
              </div>
            </div>
            <div v-if="cm.altura_medidas" class="flex items-center gap-3 pt-3 border-t border-border/50">
              <div class="w-8 h-8 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 4.5h14.25M3 9h9.75M3 13.5h5.25m5.25-.75L17.25 9m0 0L21 12.75M17.25 9v12" />
                </svg>
              </div>
              <div>
                <p class="text-[10px] uppercase tracking-wider text-muted font-medium">Altura</p>
                <p class="text-lg font-bold text-ink">{{ cm.altura_medidas }} <span class="text-sm font-normal text-muted">cm</span></p>
              </div>
            </div>
          </div>

          <!-- Contacto -->
          <div v-if="canEdit" class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-3" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Contacto</h3>
            <div class="space-y-2.5">
              <!-- Email -->
              <div v-if="cm.email" class="flex items-center gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0">Email</p>
                <a :href="`mailto:${cm.email}`" class="text-xs text-ink hover:text-gold transition-colors font-medium">{{ cm.email }}</a>
              </div>
              <!-- Teléfono -->
              <div v-if="cm.telefono" class="flex items-center gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0">Teléfono</p>
                <a :href="`tel:${cm.telefono}`" class="text-xs text-ink hover:text-gold transition-colors">{{ cm.telefono }}</a>
              </div>
            </div>
          </div>

          <!-- Datos fiscales y bancarios -->
          <div v-if="canEdit" class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-3" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Datos fiscales y bancarios</h3>
            <div class="space-y-2.5">
              <!-- DNI / NIF -->
              <div v-if="cm.dni_cif" class="flex items-center gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0">DNI / NIF</p>
                <p class="text-xs text-ink">{{ cm.dni_cif }}</p>
              </div>
              <!-- IBAN with copy -->
              <div v-if="cm.iban" class="flex items-center gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0">IBAN</p>
                <p class="text-xs text-ink font-mono">{{ cm.iban }}</p>
                <button
                  class="ml-1 p-1 rounded-md hover:bg-panel/60 transition-colors group"
                  :title="ibanCopied ? 'Copiado' : 'Copiar IBAN'"
                  @click="copyIban"
                >
                  <svg v-if="!ibanCopied" class="w-3.5 h-3.5 text-muted group-hover:text-ink transition-colors" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  <svg v-else class="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </button>
              </div>
              <!-- Dirección with Google Maps link -->
              <div v-if="cm.direccion_facturacion" class="flex items-start gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0 pt-0.5">Dirección</p>
                <a
                  :href="`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent([cm.direccion_facturacion, cm.codigo_postal, cm.provincia, cm.pais].filter(Boolean).join(', '))}`"
                  target="_blank"
                  class="text-xs text-ink hover:text-gold transition-colors group flex items-start gap-1.5"
                >
                  <span>{{ cm.direccion_facturacion }}<span v-if="cm.codigo_postal">, {{ cm.codigo_postal }}</span><span v-if="cm.provincia"> — {{ cm.provincia }}</span></span>
                  <svg class="w-3 h-3 text-muted group-hover:text-gold transition-colors flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                  </svg>
                </a>
              </div>
              <!-- Provincia standalone if no address -->
              <div v-else-if="cm.provincia" class="flex items-center gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0">Provincia</p>
                <p class="text-xs text-ink">{{ cm.provincia }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Proyectos asociados -->
        <div v-if="canEdit" class="rounded-2xl border border-border/60 bg-white shadow-card p-5 space-y-4">
          <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Proyectos asociados</h3>
          <div v-if="cm.proyectos_asociados && cm.proyectos_asociados.length > 0" class="space-y-2">
            <NuxtLink
              v-for="project in cm.proyectos_asociados"
              :key="project.id"
              :to="`/proyectos/${project.id}`"
              class="flex items-center justify-between p-3 rounded-xl border border-border/50 hover:border-gold/30 hover:bg-gold/3 transition-all group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-8 h-8 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium text-ink truncate group-hover:text-gold transition-colors">{{ project.nombre }}</p>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-[11px] text-muted">{{ project.project_id }}</span>
                    <span v-if="project.brand_name" class="text-[11px] text-muted">· {{ project.brand_name }}</span>
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
                <span v-if="project.fecha_servicio" class="text-[11px] text-muted hidden sm:inline">
                  {{ new Date(project.fecha_servicio).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" }) }}
                </span>
                <svg class="w-4 h-4 text-muted group-hover:text-gold transition-colors" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </div>
            </NuxtLink>
          </div>
          <div v-else class="py-4 text-center">
            <p class="text-xs text-muted">Esta content maker no tiene proyectos asociados.</p>
          </div>
        </div>
      </template>

      <!-- ============ EDIT MODE ============ -->
      <template v-if="isEditing">
        <div class="space-y-4">
          <!-- Datos personales -->
          <div class="rounded-2xl border border-gold/20 p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gold">Datos personales</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Nombre</label>
                <input v-model="editData.nombre" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Apellidos</label>
                <input v-model="editData.apellidos" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Tipo de CM</label>
                <input v-model="editData.tipo_cm" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Sexo</label>
                <input v-model="editData.sexo" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Status</label>
                <input v-model="editData.status" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">ID Stimada</label>
                <input :value="formatContentMakerId(editData.stimada_id)" type="text" disabled class="input-field opacity-60 cursor-not-allowed" />
              </div>
            </div>
          </div>

          <!-- Redes sociales -->
          <div class="rounded-2xl border border-gold/20 p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gold">Redes sociales</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Instagram Handle</label>
                <input v-model="editData.instagram_handle" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Seguidores Instagram</label>
                <input v-model.number="editData.seguidores_instagram" type="number" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Link Instagram</label>
                <input v-model="editData.link_instagram" type="url" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Fee Instagram (€)</label>
                <input v-model="editData.fee_instagram" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Categoría seguidores IG</label>
                <input v-model="editData.categoria_seguidores_ig" type="text" class="input-field" />
              </div>
              <div class="hidden md:block" />
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">TikTok Handle</label>
                <input v-model="editData.tiktok_handle" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Seguidores TikTok</label>
                <input v-model.number="editData.seguidores_tiktok" type="number" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Link TikTok</label>
                <input v-model="editData.link_tiktok" type="url" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Fee TikTok (€)</label>
                <input v-model="editData.fee_tiktok" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Categoría seguidores TT</label>
                <input v-model="editData.categoria_seguidores_tt" type="text" class="input-field" />
              </div>
            </div>
          </div>

          <!-- Valoración -->
          <div class="rounded-2xl border border-gold/20 p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gold">Valoración interna</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Calidad del contenido (0–5)</label>
                <select v-model="editData.calidad_contenido" class="input-field">
                  <option :value="null">—</option>
                  <option v-for="n in [0, 1, 2, 3, 4, 5]" :key="n" :value="n">{{ n }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Desempeño</label>
                <div class="flex flex-wrap gap-2 p-2 rounded-xl border border-border bg-raised min-h-[38px]">
                  <button
                    v-for="opt in desempenoOptions"
                    :key="opt.id"
                    type="button"
                    class="text-xs px-2.5 py-1 rounded-full border transition-colors"
                    :class="(editData.desempeno_opciones || []).includes(opt.id)
                      ? 'border-gold bg-gold/15 text-gold font-medium'
                      : 'border-border text-muted hover:border-gold/40 hover:text-ink'"
                    @click="toggleDesempeno(opt.id)"
                  >{{ opt.nombre }}</button>
                </div>
              </div>
              <div class="col-span-2">
                <label class="block text-xs font-medium text-muted mb-1.5">Comentarios internos</label>
                <textarea
                  v-model="editData.comentarios"
                  rows="4"
                  class="input-field resize-none"
                />
              </div>
              <div class="flex items-center gap-6 col-span-2">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editData.es_mama" type="checkbox" class="w-4 h-4 rounded border-border bg-raised accent-gold" />
                  <span class="text-xs text-ink">Es mamá</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editData.sigue_stimada" type="checkbox" class="w-4 h-4 rounded border-border bg-raised accent-gold" />
                  <span class="text-xs text-ink">Sigue @stimada</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editData.stimada_en_bio" type="checkbox" class="w-4 h-4 rounded border-border bg-raised accent-gold" />
                  <span class="text-xs text-ink">Stimada en bio</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editData.contrato_firmado" type="checkbox" class="w-4 h-4 rounded border-border bg-raised accent-gold" />
                  <span class="text-xs text-ink">Contrato firmado</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Tallaje -->
          <div class="rounded-2xl border border-gold/20 p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gold">Tallaje</h3>
            <p v-if="!canEditTallaje" class="text-xs text-muted italic">Solo administradores y la propia content maker pueden modificar el tallaje.</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div v-for="(cat, campo) in tallajeOptions" :key="campo">
                <label class="block text-xs font-medium text-muted mb-1.5">{{ cat.label }}</label>
                <select v-model="(editData as Record<string, unknown>)[campo]" class="input-field" :disabled="!canEditTallaje" :class="{ 'opacity-50 cursor-not-allowed': !canEditTallaje }">
                  <option value="">—</option>
                  <option v-for="opt in cat.options" :key="opt" :value="opt">{{ opt }}</option>
                </select>
              </div>
              <div class="md:col-span-3">
                <label class="block text-xs font-medium text-muted mb-1.5">Altura (cm)</label>
                <input v-model="editData.altura_medidas" type="number" min="0" step="1" class="input-field" placeholder="Ej: 169" :disabled="!canEditTallaje" :class="{ 'opacity-50 cursor-not-allowed': !canEditTallaje }" />
              </div>
            </div>
          </div>

          <!-- Contacto y facturación -->
          <div class="rounded-2xl border border-gold/20 p-5 space-y-4" >
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gold">Contacto y facturación</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Email</label>
                <input v-model="editData.email" type="email" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Teléfono</label>
                <input v-model="editData.telefono" type="text" class="input-field" />
              </div>
            </div>

            <!-- Datos fiscales y bancarios -->
            <h4 class="text-[11px] font-semibold uppercase tracking-widest text-gold/80 pt-2">Datos fiscales y bancarios</h4>
            <p v-if="!canEditFiscal" class="text-xs text-muted italic">Solo administradores pueden modificar los datos fiscales.</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">DNI / NIF</label>
                <input v-model="editData.dni_cif" type="text" class="input-field" :disabled="!canEditDni" :class="{ 'opacity-50 cursor-not-allowed': !canEditDni }" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">IBAN</label>
                <input v-model="editData.iban" type="text" class="input-field" :disabled="!canEditFiscal" :class="{ 'opacity-50 cursor-not-allowed': !canEditFiscal }" />
              </div>
              <div class="md:col-span-2">
                <label class="block text-xs font-medium text-muted mb-1.5">Dirección de facturación</label>
                <input v-model="editData.direccion_facturacion" type="text" class="input-field" :disabled="!canEditFiscal" :class="{ 'opacity-50 cursor-not-allowed': !canEditFiscal }" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Código Postal</label>
                <input v-model="editData.codigo_postal" type="text" class="input-field" :disabled="!canEditFiscal" :class="{ 'opacity-50 cursor-not-allowed': !canEditFiscal }" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">Provincia</label>
                <input v-model="editData.provincia" type="text" class="input-field" :disabled="!canEditFiscal" :class="{ 'opacity-50 cursor-not-allowed': !canEditFiscal }" />
              </div>
              <div>
                <label class="block text-xs font-medium text-muted mb-1.5">País</label>
                <input v-model="editData.pais" type="text" class="input-field" :disabled="!canEditFiscal" :class="{ 'opacity-50 cursor-not-allowed': !canEditFiscal }" />
              </div>
            </div>
          </div>

        </div>
      </template>

        </div><!-- end main content column -->

        <!-- Photo column (sticky on the right) -->
        <div class="hidden lg:block sticky top-8 flex-shrink-0">
          <div class="w-[280px] h-[380px] rounded-2xl overflow-hidden shadow-card border border-border/60">
            <img
              v-if="cm.foto_url"
              :src="cm.foto_url"
              alt="Content Maker"
              class="w-full h-full object-cover"
            />
            <div
              v-else
              class="w-full h-full flex items-center justify-center bg-orange-400/5"
            >
              <span class="text-6xl font-semibold text-orange-400/40">{{ cm.nombre.charAt(0) }}{{ cm.apellidos.charAt(0) }}</span>
            </div>
          </div>
        </div>
      </div><!-- end flex layout -->
    </div>

    <!-- Create account modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.4); backdrop-filter: blur(4px)"
          @click.self="showCreateModal = false"
        >
          <Transition name="modal-content" appear>
            <div class="w-full max-w-sm rounded-2xl border border-border/60 bg-white p-7 shadow-elevated" >
              <h2 class="text-base font-semibold text-ink mb-1">Crear cuenta de acceso</h2>
              <p class="text-sm text-muted mb-5">
                Se creará una cuenta para <span class="text-ink">{{ cm?.nombre_completo }}</span> con rol Content Maker.
              </p>

              <form class="space-y-4" @submit.prevent="handleCreateAccount">
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Email de acceso</label>
                  <input
                    v-model="createEmail"
                    type="email"
                    required
                    :disabled="isCreating"
                    class="input-field disabled:opacity-50"
                    placeholder="email@ejemplo.com"
                  />
                  <p class="text-xs text-muted mt-1.5">La contraseña se generará automáticamente.</p>
                </div>

                <Transition name="modal">
                  <p v-if="createError" class="text-xs text-red-500">{{ createError }}</p>
                </Transition>

                <div class="flex gap-2 pt-1">
                  <button
                    type="button"
                    class="flex-1 h-10 rounded-xl border border-border text-sm text-muted hover:text-ink transition-colors"
                    @click="showCreateModal = false"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    :disabled="isCreating"
                    class="flex-1 h-10 rounded-xl bg-gold text-ink text-sm font-semibold hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all flex items-center justify-center gap-1.5"
                  >
                    <svg v-if="isCreating" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {{ isCreating ? "Creando…" : "Crear cuenta" }}
                  </button>
                </div>
              </form>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showDeleteModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.4); backdrop-filter: blur(4px)"
          @click.self="showDeleteModal = false"
        >
          <Transition name="modal-content" appear>
            <div class="w-full max-w-sm rounded-2xl border border-red-200 p-7 shadow-card" >
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-base font-semibold text-ink">Eliminar Content Maker</h2>
                  <p class="text-xs text-muted mt-0.5">Esta acción no se puede deshacer</p>
                </div>
              </div>
              <p class="text-sm text-muted mb-5">
                ¿Estás seguro de que quieres eliminar el perfil de <span class="text-ink font-medium">{{ cm?.nombre_completo }}</span>?
                Se eliminará toda la información asociada.
              </p>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="flex-1 h-10 rounded-xl border border-border text-sm text-muted hover:text-ink transition-colors"
                  :disabled="isDeleting"
                  @click="showDeleteModal = false"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  class="flex-1 h-10 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-600 active:scale-[0.98] disabled:opacity-60 transition-all flex items-center justify-center gap-1.5"
                  :disabled="isDeleting"
                  @click="handleDelete"
                >
                  <svg v-if="isDeleting" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ isDeleting ? "Eliminando…" : "Eliminar" }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
