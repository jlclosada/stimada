<script setup lang="ts">
import { useContentMakersStore } from "~/stores/contentMakers";
import type { ContentMakerDetail } from "~/stores/contentMakers";
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth", "role"] });

const route = useRoute();
const store = useContentMakersStore();
const auth = useAuthStore();

const cm = ref<ContentMakerDetail | null>(null);
const isLoading = ref(true);
const error = ref("");

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

async function load() {
  isLoading.value = true;
  try {
    cm.value = await store.fetchDetail(route.params.id as string);
    createEmail.value = cm.value?.email ?? "";
  } catch {
    error.value = "No se pudo cargar el perfil.";
  } finally {
    isLoading.value = false;
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

    <div v-else-if="cm" class="max-w-4xl animate-fade-up space-y-5">
      <!-- Back -->
      <NuxtLink to="/dashboard/content-makers" class="inline-flex items-center gap-1.5 text-xs text-muted hover:text-cream transition-colors mb-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Volver a Content Makers
      </NuxtLink>

      <!-- Header -->
      <div class="rounded-2xl border border-border p-6 flex items-start justify-between gap-4" style="background:#141417">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-orange-400/10 border border-orange-400/20 flex items-center justify-center text-orange-400 text-lg font-semibold flex-shrink-0">
            {{ cm.nombre.charAt(0) }}{{ cm.apellidos.charAt(0) }}
          </div>
          <div>
            <h1 class="text-2xl font-semibold tracking-tight text-cream">{{ cm.nombre_completo }}</h1>
            <div class="flex items-center gap-2 mt-1 flex-wrap">
              <span class="text-xs text-muted">{{ cm.stimada_id }}</span>
              <span class="text-border">·</span>
              <span class="text-xs text-muted">{{ cm.tipo_cm }}</span>
              <span
                v-if="cm.status"
                class="text-xs font-medium px-2 py-0.5 rounded-full border"
                :class="cm.status === 'Alta' ? 'text-green-400 bg-green-400/10 border-green-400/20' : 'text-muted border-border'"
              >
                {{ cm.status }}
              </span>
            </div>
          </div>
        </div>

        <!-- Account status + create button -->
        <div class="flex-shrink-0 text-right">
          <div v-if="cm.tiene_cuenta" class="space-y-1">
            <div class="flex items-center justify-end gap-1.5 text-xs text-green-400">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
              </svg>
              Cuenta activa
            </div>
            <p class="text-xs text-muted">{{ cm.user_email }}</p>
          </div>
          <button
            v-else
            class="px-4 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 active:scale-[0.98] transition-all"
            @click="showCreateModal = true"
          >
            Crear cuenta de acceso
          </button>
        </div>
      </div>

      <!-- Credentials revealed after creation -->
      <Transition name="modal-content" appear>
        <div
          v-if="createdCredentials"
          class="rounded-2xl border border-green-500/25 p-5 space-y-3"
          style="background: rgba(74,222,128,0.04)"
        >
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <p class="text-sm font-semibold text-green-400">Cuenta creada correctamente</p>
          </div>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div>
              <p class="text-muted mb-1">Email de acceso</p>
              <p class="text-cream font-medium">{{ createdCredentials.email }}</p>
            </div>
            <div>
              <p class="text-muted mb-1">Contraseña generada</p>
              <div class="flex items-center gap-2">
                <code class="font-mono text-cream bg-raised px-2 py-1 rounded-lg border border-border">{{ createdCredentials.password }}</code>
                <button
                  class="text-muted hover:text-cream transition-colors flex-shrink-0"
                  :title="copied ? 'Copiado' : 'Copiar'"
                  @click="copyPassword"
                >
                  <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  <svg v-else class="w-3.5 h-3.5 text-green-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 pt-1">
            <button
              class="h-8 px-4 rounded-xl bg-green-500/15 border border-green-500/25 text-xs text-green-400 font-medium hover:bg-green-500/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
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

      <!-- Info grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Redes sociales -->
        <div class="rounded-2xl border border-border p-5 space-y-4" style="background:#141417">
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
                  class="text-sm text-cream hover:text-gold transition-colors font-medium"
                >
                  @{{ cm.instagram_handle }}
                </a>
                <p v-else class="text-sm text-cream">@{{ cm.instagram_handle || "—" }}</p>
                <p class="text-xs text-muted">{{ fmt(cm.seguidores_instagram) }} seguidores · {{ cm.categoria_seguidores_ig || "—" }}</p>
                <p v-if="cm.fee_instagram" class="text-xs text-gold mt-0.5">Fee: {{ cm.fee_instagram }}€</p>
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
                  class="text-sm text-cream hover:text-gold transition-colors font-medium"
                >
                  {{ cm.tiktok_handle || "—" }}
                </a>
                <p v-else class="text-sm text-cream">{{ cm.tiktok_handle || "—" }}</p>
                <p class="text-xs text-muted">{{ fmt(cm.seguidores_tiktok) }} seguidores · {{ cm.categoria_seguidores_tt || "—" }}</p>
                <p v-if="cm.fee_tiktok" class="text-xs text-gold mt-0.5">Fee: {{ cm.fee_tiktok }}€</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Valoración interna -->
        <div class="rounded-2xl border border-border p-5 space-y-3" style="background:#141417">
          <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Valoración</h3>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="item in [
              { label: 'Calidad', value: cm.calidad_contenido },
              { label: 'Apariencia', value: cm.apariencia },
              { label: 'Desempeño', value: cm.desempeno },
              { label: 'Contenido', value: cm.categorias_contenido },
            ]" :key="item.label">
              <p class="text-xs text-muted">{{ item.label }}</p>
              <p class="text-xs text-cream mt-0.5">{{ item.value || "—" }}</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2 pt-1">
            <span v-if="cm.es_mama" class="text-xs px-2 py-0.5 rounded-full border border-pink-400/20 text-pink-400 bg-pink-400/8">Mamá</span>
            <span v-if="cm.sigue_stimada" class="text-xs px-2 py-0.5 rounded-full border border-blue-400/20 text-blue-400 bg-blue-400/8">Sigue @stimada</span>
            <span v-if="cm.stimada_en_bio" class="text-xs px-2 py-0.5 rounded-full border border-purple-400/20 text-purple-400 bg-purple-400/8">Stimada en bio</span>
            <span v-if="cm.contrato_firmado" class="text-xs px-2 py-0.5 rounded-full border border-green-400/20 text-green-400 bg-green-400/8">Contrato firmado</span>
          </div>
        </div>

        <!-- Tallaje -->
        <div class="rounded-2xl border border-border p-5 space-y-3" style="background:#141417">
          <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Tallaje</h3>
          <div class="grid grid-cols-3 gap-3">
            <div v-for="item in [
              { label: 'Parte arriba', value: cm.talla_arriba },
              { label: 'Parte abajo', value: cm.talla_abajo },
              { label: 'Pie', value: cm.talla_pie },
            ]" :key="item.label">
              <p class="text-xs text-muted">{{ item.label }}</p>
              <p class="text-sm text-cream font-medium mt-0.5">{{ item.value || "—" }}</p>
            </div>
          </div>
          <div v-if="cm.altura_medidas">
            <p class="text-xs text-muted">Medidas</p>
            <p class="text-xs text-cream mt-0.5 leading-relaxed">{{ cm.altura_medidas }}</p>
          </div>
        </div>

        <!-- Contacto -->
        <div class="rounded-2xl border border-border p-5 space-y-3" style="background:#141417">
          <h3 class="text-xs font-semibold uppercase tracking-widest text-muted">Contacto y facturación</h3>
          <div class="space-y-2">
            <div v-for="item in [
              { label: 'Email', value: cm.email },
              { label: 'Teléfono', value: cm.telefono },
              { label: 'DNI / CIF', value: cm.dni_cif },
              { label: 'IBAN', value: cm.iban },
              { label: 'Dirección', value: cm.direccion_facturacion },
              { label: 'C.P.', value: cm.codigo_postal },
              { label: 'Provincia', value: cm.provincia },
            ]" :key="item.label">
              <div v-if="item.value" class="flex items-start gap-2">
                <p class="text-xs text-muted w-16 flex-shrink-0 pt-0.5">{{ item.label }}</p>
                <p class="text-xs text-cream">{{ item.value }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Comentarios -->
      <div v-if="cm.comentarios" class="rounded-2xl border border-border p-5" style="background:#141417">
        <h3 class="text-xs font-semibold uppercase tracking-widest text-muted mb-2">Comentarios internos</h3>
        <p class="text-sm text-cream/80 leading-relaxed">{{ cm.comentarios }}</p>
      </div>
    </div>

    <!-- Create account modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.72); backdrop-filter: blur(6px)"
          @click.self="showCreateModal = false"
        >
          <Transition name="modal-content" appear>
            <div class="w-full max-w-sm rounded-2xl border border-border p-7 shadow-card" style="background:#141417">
              <h2 class="text-base font-semibold text-cream mb-1">Crear cuenta de acceso</h2>
              <p class="text-sm text-muted mb-5">
                Se creará una cuenta para <span class="text-cream">{{ cm?.nombre_completo }}</span> con rol Content Maker.
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
                  <p v-if="createError" class="text-xs text-red-400">{{ createError }}</p>
                </Transition>

                <div class="flex gap-2 pt-1">
                  <button
                    type="button"
                    class="flex-1 h-10 rounded-xl border border-border text-sm text-muted hover:text-cream transition-colors"
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
  </div>
</template>
