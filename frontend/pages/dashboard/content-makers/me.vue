<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import type { ContentMakerDetail } from "~/stores/contentMakers";
import { formatContentMakerId } from "~/utils/formatId";

definePageMeta({ middleware: ["auth", "role"] });

const auth = useAuthStore();
const config = useRuntimeConfig();

const cm = ref<ContentMakerDetail | null>(null);
const isLoading = ref(true);
const error = ref("");

// Edit state
const isEditing = ref(false);
const isSaving = ref(false);
const editData = ref<Partial<ContentMakerDetail>>({});
const saveError = ref("");

// Fields the CM cannot edit
const READONLY_FIELDS = ["nombre", "apellidos", "fee_instagram", "fee_tiktok", "status", "tipo_cm", "categorias_contenido", "stimada_id"];

// IBAN copy
const ibanCopied = ref(false);
async function copyIban() {
  if (!cm.value?.iban) return;
  await navigator.clipboard.writeText(cm.value.iban);
  ibanCopied.value = true;
  setTimeout(() => (ibanCopied.value = false), 2000);
}

// Photo upload
const photoInput = ref<HTMLInputElement | null>(null);
const isUploadingPhoto = ref(false);

function triggerPhotoUpload() {
  photoInput.value?.click();
}

async function handlePhotoChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  isUploadingPhoto.value = true;
  try {
    const formData = new FormData();
    formData.append("foto", file);

    cm.value = await $fetch<ContentMakerDetail>(
      `${config.public.apiBase}/content-makers/me/`,
      {
        method: "PATCH",
        body: formData,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      }
    );
  } catch {
    // Silently fail — user can retry
  } finally {
    isUploadingPhoto.value = false;
    if (photoInput.value) photoInput.value.value = "";
  }
}

async function load() {
  isLoading.value = true;
  try {
    cm.value = await $fetch<ContentMakerDetail>(
      `${config.public.apiBase}/content-makers/me/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
  } catch {
    error.value = "No se pudo cargar tu perfil.";
  } finally {
    isLoading.value = false;
  }
}

function startEditing() {
  if (!cm.value) return;
  editData.value = { ...cm.value };
  isEditing.value = true;
  saveError.value = "";
}

function cancelEditing() {
  isEditing.value = false;
  editData.value = {};
  saveError.value = "";
}

async function saveChanges() {
  if (!cm.value) return;
  isSaving.value = true;
  saveError.value = "";
  try {
    const payload: Record<string, unknown> = {};
    const keys = Object.keys(editData.value) as (keyof ContentMakerDetail)[];
    for (const key of keys) {
      // Skip readonly and metadata fields
      if (READONLY_FIELDS.includes(key)) continue;
      if (["id", "nombre_completo", "tiene_cuenta", "user_id", "user_email", "created_at", "updated_at"].includes(key)) continue;
      if (editData.value[key] !== (cm.value as Record<string, unknown>)[key]) {
        payload[key] = editData.value[key];
      }
    }
    if (Object.keys(payload).length === 0) {
      isEditing.value = false;
      return;
    }
    cm.value = await $fetch<ContentMakerDetail>(
      `${config.public.apiBase}/content-makers/me/`,
      {
        method: "PATCH",
        body: payload,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      }
    );
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

function fmt(n: number | null) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

load();
</script>

<template>
  <div class="min-h-screen">
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <svg class="animate-spin w-6 h-6 text-gold" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex flex-col items-center justify-center h-60 gap-3">
      <p class="text-sm text-red-500">{{ error }}</p>
      <button class="text-xs text-gold hover:underline" @click="load">Reintentar</button>
    </div>

    <div v-else-if="cm" class="animate-fade-up max-w-5xl mx-auto px-4 pb-12">
      <!-- Hidden file input for photo upload -->
      <input
        ref="photoInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handlePhotoChange"
      />

      <!-- Hero header — centered photo + identity -->
      <div class="text-center pt-8 pb-10">
        <!-- Photo -->
        <div class="relative inline-block group mb-5">
          <div class="w-40 h-40 rounded-full overflow-hidden border-4 border-white shadow-elevated ring-1 ring-border/30 mx-auto">
            <img
              v-if="cm.foto_url"
              :src="cm.foto_url"
              alt="Mi foto"
              class="w-full h-full object-cover"
            />
            <div
              v-else
              class="w-full h-full flex items-center justify-center text-5xl font-semibold text-gold/70 bg-gradient-to-br from-gold/5 to-gold/15"
            >
              {{ cm.nombre.charAt(0) }}{{ cm.apellidos.charAt(0) }}
            </div>
          </div>
          <!-- Upload overlay -->
          <button
            class="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition-all duration-200 flex flex-col items-center justify-center cursor-pointer gap-1"
            :disabled="isUploadingPhoto"
            @click="triggerPhotoUpload"
          >
            <svg v-if="!isUploadingPhoto" class="w-7 h-7 text-white" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
            </svg>
            <svg v-else class="animate-spin w-6 h-6 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span v-if="!isUploadingPhoto" class="text-[10px] text-white/90 font-medium">Cambiar foto</span>
          </button>
        </div>

        <!-- Name + meta -->
        <h1 class="text-3xl font-bold tracking-tight text-ink">{{ cm.nombre_completo }}</h1>
        <div class="flex items-center justify-center gap-3 mt-2 flex-wrap">
          <span class="text-sm text-muted">{{ formatContentMakerId(cm.stimada_id) }}</span>
          <span class="w-1 h-1 rounded-full bg-border" />
          <span class="text-sm text-muted">{{ cm.tipo_cm }}</span>
          <span
            v-if="cm.status"
            class="text-xs font-medium px-2.5 py-0.5 rounded-full border"
            :class="cm.status === 'Alta' ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : 'text-muted border-border bg-panel'"
          >
            {{ cm.status }}
          </span>
        </div>

        <!-- Fee badges -->
        <div class="flex items-center justify-center gap-3 mt-4">
          <span v-if="cm.fee_instagram" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/20 text-sm font-semibold text-gold">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            {{ cm.fee_instagram }}€
          </span>
          <span v-if="cm.fee_tiktok" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-ink/5 border border-ink/10 text-sm font-semibold text-ink/70">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"/></svg>
            {{ cm.fee_tiktok }}€
          </span>
        </div>

        <!-- Action button -->
        <div class="mt-6">
          <template v-if="!isEditing">
            <button
              class="px-5 h-10 rounded-full bg-gold text-ink text-sm font-semibold hover:bg-gold/90 active:scale-[0.97] transition-all inline-flex items-center gap-2 shadow-sm"
              @click="startEditing"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Editar mi perfil
            </button>
          </template>
          <template v-else>
            <div class="inline-flex items-center gap-3">
              <button
                class="px-5 h-10 rounded-full border border-border text-sm font-medium text-muted hover:text-ink hover:border-ink/30 transition-all"
                :disabled="isSaving"
                @click="cancelEditing"
              >
                Cancelar
              </button>
              <button
                class="px-5 h-10 rounded-full bg-gold text-ink text-sm font-semibold hover:bg-gold/90 active:scale-[0.97] disabled:opacity-60 transition-all inline-flex items-center gap-2 shadow-sm"
                :disabled="isSaving"
                @click="saveChanges"
              >
                <svg v-if="isSaving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ isSaving ? "Guardando…" : "Guardar cambios" }}
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- Save error -->
      <div v-if="saveError" class="max-w-2xl mx-auto rounded-xl border border-red-200 p-3 text-sm text-red-500 mb-6 text-center" style="background:rgba(239,68,68,0.04)">
        {{ saveError }}
      </div>

      <!-- Divider -->
      <div class="border-t border-border/40 mb-10" />

      <!-- ============ VIEW MODE ============ -->
      <template v-if="!isEditing">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Redes sociales -->
          <div class="lg:col-span-1 space-y-5">
            <h3 class="text-[11px] font-semibold uppercase tracking-widest text-muted/80 pl-1">Redes sociales</h3>
            <div class="space-y-4">
              <!-- Instagram -->
              <div class="rounded-2xl border border-border/50 bg-white p-5 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-9 h-9 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <svg class="w-4.5 h-4.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                    </svg>
                  </div>
                  <div>
                    <a v-if="cm.link_instagram" :href="cm.link_instagram" target="_blank" class="text-sm text-ink hover:text-gold transition-colors font-semibold">
                      @{{ cm.instagram_handle }}
                    </a>
                    <p v-else class="text-sm text-ink font-semibold">@{{ cm.instagram_handle || "—" }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-4 pl-12">
                  <div>
                    <p class="text-lg font-bold text-ink leading-none">{{ fmt(cm.seguidores_instagram) }}</p>
                    <p class="text-[10px] uppercase tracking-wide text-muted mt-0.5">Seguidores</p>
                  </div>
                  <div v-if="cm.categoria_seguidores_ig" class="border-l border-border/50 pl-4">
                    <p class="text-sm font-medium text-ink leading-none">{{ cm.categoria_seguidores_ig }}</p>
                    <p class="text-[10px] uppercase tracking-wide text-muted mt-0.5">Categoría</p>
                  </div>
                </div>
              </div>

              <!-- TikTok -->
              <div class="rounded-2xl border border-border/50 bg-white p-5 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-9 h-9 rounded-full bg-black flex items-center justify-center flex-shrink-0">
                    <svg class="w-4.5 h-4.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.84 1.56V6.8a4.85 4.85 0 01-1.07-.11z"/>
                    </svg>
                  </div>
                  <div>
                    <a v-if="cm.link_tiktok" :href="cm.link_tiktok" target="_blank" class="text-sm text-ink hover:text-gold transition-colors font-semibold">
                      {{ cm.tiktok_handle || "—" }}
                    </a>
                    <p v-else class="text-sm text-ink font-semibold">{{ cm.tiktok_handle || "—" }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-4 pl-12">
                  <div>
                    <p class="text-lg font-bold text-ink leading-none">{{ fmt(cm.seguidores_tiktok) }}</p>
                    <p class="text-[10px] uppercase tracking-wide text-muted mt-0.5">Seguidores</p>
                  </div>
                  <div v-if="cm.categoria_seguidores_tt" class="border-l border-border/50 pl-4">
                    <p class="text-sm font-medium text-ink leading-none">{{ cm.categoria_seguidores_tt }}</p>
                    <p class="text-[10px] uppercase tracking-wide text-muted mt-0.5">Categoría</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tallaje + Contacto stacked -->
          <div class="lg:col-span-2 space-y-8">
            <!-- Tallaje -->
            <div>
              <h3 class="text-[11px] font-semibold uppercase tracking-widest text-muted/80 pl-1 mb-5">Tallaje</h3>
              <div class="rounded-2xl border border-border/50 bg-white p-6">
                <div class="grid grid-cols-3 gap-4">
                  <div class="text-center p-4 rounded-xl bg-gradient-to-b from-panel to-white border border-border/40">
                    <p class="text-[10px] uppercase tracking-wider text-muted mb-2 font-medium">Arriba</p>
                    <p class="text-2xl font-bold text-ink">{{ cm.talla_arriba || "—" }}</p>
                  </div>
                  <div class="text-center p-4 rounded-xl bg-gradient-to-b from-panel to-white border border-border/40">
                    <p class="text-[10px] uppercase tracking-wider text-muted mb-2 font-medium">Abajo</p>
                    <p class="text-2xl font-bold text-ink">{{ cm.talla_abajo || "—" }}</p>
                  </div>
                  <div class="text-center p-4 rounded-xl bg-gradient-to-b from-panel to-white border border-border/40">
                    <p class="text-[10px] uppercase tracking-wider text-muted mb-2 font-medium">Pie</p>
                    <p class="text-2xl font-bold text-ink">{{ cm.talla_pie || "—" }}</p>
                  </div>
                </div>
                <div v-if="cm.altura_medidas" class="mt-5 pt-4 border-t border-border/40 flex items-center gap-3">
                  <svg class="w-4 h-4 text-muted flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                  <p class="text-sm text-ink font-medium">{{ cm.altura_medidas }}</p>
                </div>
              </div>
            </div>

            <!-- Contacto y facturación -->
            <div>
              <h3 class="text-[11px] font-semibold uppercase tracking-widest text-muted/80 pl-1 mb-5">Contacto y facturación</h3>
              <div class="rounded-2xl border border-border/50 bg-white p-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                  <div v-if="cm.email">
                    <p class="text-[10px] uppercase tracking-wider text-muted font-medium mb-1">Email</p>
                    <p class="text-sm text-ink font-medium">{{ cm.email }}</p>
                  </div>
                  <div v-if="cm.telefono">
                    <p class="text-[10px] uppercase tracking-wider text-muted font-medium mb-1">Teléfono</p>
                    <p class="text-sm text-ink">{{ cm.telefono }}</p>
                  </div>
                  <div v-if="cm.dni_cif">
                    <p class="text-[10px] uppercase tracking-wider text-muted font-medium mb-1">DNI / CIF</p>
                    <p class="text-sm text-ink">{{ cm.dni_cif }}</p>
                  </div>
                  <div v-if="cm.iban">
                    <p class="text-[10px] uppercase tracking-wider text-muted font-medium mb-1">IBAN</p>
                    <div class="flex items-center gap-2">
                      <p class="text-sm text-ink font-mono">{{ cm.iban }}</p>
                      <button class="p-1 rounded-md hover:bg-panel transition-colors" @click="copyIban">
                        <svg v-if="!ibanCopied" class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                        </svg>
                        <svg v-else class="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div v-if="cm.direccion_facturacion" class="sm:col-span-2">
                    <p class="text-[10px] uppercase tracking-wider text-muted font-medium mb-1">Dirección</p>
                    <p class="text-sm text-ink">
                      {{ cm.direccion_facturacion }}<span v-if="cm.codigo_postal">, {{ cm.codigo_postal }}</span><span v-if="cm.provincia"> — {{ cm.provincia }}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ============ EDIT MODE ============ -->
      <template v-if="isEditing">
        <div class="max-w-3xl mx-auto space-y-8">
          <!-- Datos personales (readonly fields shown disabled) -->
          <div>
            <h3 class="text-[11px] font-semibold uppercase tracking-widest text-muted/80 pl-1 mb-4">Datos personales <span class="normal-case text-muted/50">(no editable)</span></h3>
            <div class="rounded-2xl border border-border/50 bg-white p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Nombre</label>
                  <input :value="cm.nombre" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Apellidos</label>
                  <input :value="cm.apellidos" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Tipo CM</label>
                  <input :value="cm.tipo_cm" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Estado</label>
                  <input :value="cm.status" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Categorías contenido</label>
                  <input :value="cm.categorias_contenido" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Fee Instagram</label>
                  <input :value="cm.fee_instagram ? `${cm.fee_instagram}€` : '—'" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Fee TikTok</label>
                  <input :value="cm.fee_tiktok ? `${cm.fee_tiktok}€` : '—'" type="text" disabled class="input-field opacity-50 cursor-not-allowed" />
                </div>
              </div>
            </div>
          </div>

          <!-- Redes sociales (editable) -->
          <div>
            <h3 class="text-[11px] font-semibold uppercase tracking-widest text-gold pl-1 mb-4">Redes sociales</h3>
            <div class="rounded-2xl border border-gold/20 bg-white p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
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
                  <label class="block text-xs font-medium text-muted mb-1.5">Categoría seguidores IG</label>
                  <input v-model="editData.categoria_seguidores_ig" type="text" class="input-field" />
                </div>
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
                  <label class="block text-xs font-medium text-muted mb-1.5">Categoría seguidores TT</label>
                  <input v-model="editData.categoria_seguidores_tt" type="text" class="input-field" />
                </div>
              </div>
            </div>
          </div>

          <!-- Tallaje (editable) -->
          <div>
            <h3 class="text-[11px] font-semibold uppercase tracking-widest text-gold pl-1 mb-4">Tallaje</h3>
            <div class="rounded-2xl border border-gold/20 bg-white p-6">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Parte de arriba</label>
                  <input v-model="editData.talla_arriba" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Parte de abajo</label>
                  <input v-model="editData.talla_abajo" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Pie</label>
                  <input v-model="editData.talla_pie" type="text" class="input-field" />
                </div>
                <div class="md:col-span-3">
                  <label class="block text-xs font-medium text-muted mb-1.5">Altura / Medidas</label>
                  <input v-model="editData.altura_medidas" type="text" class="input-field" />
                </div>
              </div>
            </div>
          </div>

          <!-- Contacto y facturación (editable) -->
          <div>
            <h3 class="text-[11px] font-semibold uppercase tracking-widest text-gold pl-1 mb-4">Contacto y facturación</h3>
            <div class="rounded-2xl border border-gold/20 bg-white p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Email</label>
                  <input v-model="editData.email" type="email" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Teléfono</label>
                  <input v-model="editData.telefono" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">DNI / CIF</label>
                  <input v-model="editData.dni_cif" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">IBAN</label>
                  <input v-model="editData.iban" type="text" class="input-field" />
                </div>
                <div class="md:col-span-2">
                  <label class="block text-xs font-medium text-muted mb-1.5">Dirección de facturación</label>
                  <input v-model="editData.direccion_facturacion" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Código Postal</label>
                  <input v-model="editData.codigo_postal" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Provincia</label>
                  <input v-model="editData.provincia" type="text" class="input-field" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">País</label>
                  <input v-model="editData.pais" type="text" class="input-field" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
