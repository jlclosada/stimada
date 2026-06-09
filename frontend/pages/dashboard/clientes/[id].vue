<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import type { ClientProfileDetail } from "~/stores/clients";
import { useClientsStore } from "~/stores/clients";
import { formatBrandId, formatClientId } from "~/utils/formatId";

definePageMeta({ middleware: ["auth", "role"] });

const route = useRoute();
const router = useRouter();
const store = useClientsStore();
const auth = useAuthStore();

const client = ref<ClientProfileDetail | null>(null);
const isLoading = ref(true);
const error = ref("");

// Edit state
const isEditing = ref(false);
const isSaving = ref(false);
const editData = ref<Record<string, unknown>>({});
const saveError = ref("");

// Delete state
const showDeleteModal = ref(false);
const isDeleting = ref(false);

// Brand editing state
const newBrandName = ref("");
const isBrandSaving = ref(false);

async function addBrandToClient() {
  const name = newBrandName.value.trim();
  if (!name || !client.value) return;
  isBrandSaving.value = true;
  try {
    await store.createBrand({ client: client.value.id, nombre: name });
    newBrandName.value = "";
    client.value = await store.fetchDetail(route.params.id as string);
  } catch {
    // silent
  } finally {
    isBrandSaving.value = false;
  }
}

async function removeBrandFromClient(brandId: number) {
  isBrandSaving.value = true;
  try {
    await store.deleteBrand(brandId);
    client.value = await store.fetchDetail(route.params.id as string);
  } catch {
    // silent
  } finally {
    isBrandSaving.value = false;
  }
}

// Account creation state
const showAccountModal = ref(false);
const accountForm = ref({ email: "", full_name: "", password: "" });
const isCreatingAccount = ref(false);
const accountError = ref("");
const accountSuccess = ref<{ email: string; password: string } | null>(null);

const canEdit = computed(() => {
  return auth.user?.role === "admin" || auth.user?.role === "stimada_employee";
});

async function load() {
  isLoading.value = true;
  try {
    client.value = await store.fetchDetail(route.params.id as string);
  } catch {
    error.value = "No se pudo cargar el cliente.";
  } finally {
    isLoading.value = false;
  }
}

function startEditing() {
  if (!client.value) return;
  editData.value = { ...client.value };
  isEditing.value = true;
  saveError.value = "";
}

function cancelEditing() {
  isEditing.value = false;
  editData.value = {};
  saveError.value = "";
}

async function saveChanges() {
  if (!client.value) return;
  isSaving.value = true;
  saveError.value = "";
  try {
    const payload: Record<string, unknown> = {};
    const skipKeys = ["id", "tipo_nombre", "created_by_name", "created_by", "created_at", "updated_at", "contrato_url", "user", "user_email", "user_name", "has_account"];
    for (const key of Object.keys(editData.value)) {
      if (skipKeys.includes(key)) continue;
      if (key === "contrato") continue;
      if (editData.value[key] !== (client.value as Record<string, unknown>)[key]) {
        payload[key] = editData.value[key];
      }
    }
    if (Object.keys(payload).length === 0) {
      isEditing.value = false;
      return;
    }
    const updated = await store.updateClient(route.params.id as string, payload);
    client.value = updated;
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
    await store.deleteClient(route.params.id as string);
    router.push("/dashboard/clientes");
  } catch {
    showDeleteModal.value = false;
  } finally {
    isDeleting.value = false;
  }
}

function openAccountModal() {
  accountForm.value = {
    email: client.value?.email_facturacion || "",
    full_name: client.value?.nombre_cliente || "",
    password: "",
  };
  accountError.value = "";
  accountSuccess.value = null;
  showAccountModal.value = true;
}

async function handleCreateAccount() {
  isCreatingAccount.value = true;
  accountError.value = "";
  try {
    const result = await store.createClientAccount(route.params.id as string, {
      email: accountForm.value.email,
      full_name: accountForm.value.full_name || undefined,
      password: accountForm.value.password || undefined,
    });
    accountSuccess.value = { email: result.user.email, password: result.password };
    client.value = await store.fetchDetail(route.params.id as string);
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    accountError.value = e?.data?.detail || "Error al crear la cuenta.";
  } finally {
    isCreatingAccount.value = false;
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString("es-ES", { day: "2-digit", month: "long", year: "numeric" });
}

onMounted(() => {
  store.fetchTypes();
});

load();
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <div class="w-10 h-10 rounded-full border-2 border-gold/20 border-t-gold animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-20">
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/5 border border-red-500/20">
        <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <p class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>

    <div v-else-if="client" class="max-w-5xl space-y-6 animate-fade-up">
      <!-- Back -->
      <NuxtLink
        to="/dashboard/clientes"
        class="group inline-flex items-center gap-2 text-xs text-muted hover:text-ink transition-all duration-300"
      >
        <svg class="w-4 h-4 transition-transform duration-300 group-hover:-translate-x-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        <span class="relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px after:bg-ink after:transition-all after:duration-300 group-hover:after:w-full">
          Volver a Clientes
        </span>
      </NuxtLink>

      <!-- Header Card -->
      <div class="relative overflow-hidden rounded-2xl border border-border/60 bg-white shadow-card p-7 transition-all duration-300" >
        <div class="absolute -top-20 -right-20 w-60 h-60 rounded-full opacity-[0.04] pointer-events-none" style="background: radial-gradient(circle, #60a5fa, transparent 70%)" />

        <div class="relative flex items-start justify-between gap-6">
          <div class="flex items-center gap-5">
            <div class="relative group/avatar">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-400/20 flex items-center justify-center text-blue-400 text-xl font-semibold transition-all duration-300 group-hover/avatar:scale-105 group-hover/avatar:shadow-lg group-hover/avatar:shadow-blue-500/10">
                {{ client.nombre_cliente.charAt(0) }}
              </div>
              <div
                v-if="client.has_account"
                class="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center"
              >
                <svg class="w-3 h-3 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
            <div>
              <h1 class="text-2xl font-semibold tracking-tight text-ink">{{ client.nombre_cliente }}</h1>
              <div class="flex items-center gap-2.5 mt-2 flex-wrap">
                <span class="text-[11px] text-muted/80 font-mono bg-white/[0.03] px-2 py-0.5 rounded-md border border-white/[0.04]">{{ formatClientId(client.cliente_id) }}</span>
                <span v-if="client.tipo_nombre" class="text-[11px] px-2.5 py-0.5 rounded-full border border-blue-400/15 text-blue-400 bg-blue-400/[0.06] font-medium">
                  {{ client.tipo_nombre }}
                </span>
                <span
                  v-if="client.contrato_firmado"
                  class="text-[11px] font-medium px-2.5 py-0.5 rounded-full border text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15"
                >
                  Contrato firmado
                </span>
                <span v-else class="text-[11px] font-medium px-2.5 py-0.5 rounded-full border text-amber-400 bg-amber-400/[0.06] border-amber-400/15">
                  Contrato pendiente
                </span>
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex-shrink-0 flex items-center gap-2">
            <template v-if="canEdit && !isEditing">
              <button
                v-if="!client.has_account"
                class="group/btn px-4 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400 hover:bg-emerald-500/15 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5 active:scale-[0.97] transition-all duration-200"
                @click="openAccountModal"
              >
                <span class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 transition-transform duration-200 group-hover/btn:scale-110" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                  Crear cuenta
                </span>
              </button>
              <button
                class="group/btn px-4 h-9 rounded-xl border border-border/80 text-xs font-medium text-muted hover:text-ink hover:border-ink/20 hover:bg-panel active:scale-[0.97] transition-all duration-200"
                @click="startEditing"
              >
                <span class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 transition-transform duration-200 group-hover/btn:rotate-[-4deg]" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                  Editar
                </span>
              </button>
              <button
                class="group/btn px-4 h-9 rounded-xl border border-red-500/15 text-xs font-medium text-red-400/80 hover:text-red-400 hover:bg-red-500/[0.06] hover:border-red-500/30 active:scale-[0.97] transition-all duration-200"
                @click="showDeleteModal = true"
              >
                <span class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 transition-transform duration-200 group-hover/btn:scale-110" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                  Eliminar
                </span>
              </button>
            </template>
            <template v-if="isEditing">
              <button
                class="px-4 h-9 rounded-xl border border-border text-xs font-medium text-muted hover:text-ink hover:border-ink/20 active:scale-[0.97] transition-all duration-200"
                :disabled="isSaving"
                @click="cancelEditing"
              >
                Cancelar
              </button>
              <button
                class="px-5 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 hover:shadow-lg hover:shadow-gold/10 active:scale-[0.97] disabled:opacity-60 transition-all duration-200 flex items-center gap-2"
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
      </div>

      <!-- Save error -->
      <Transition name="modal">
        <div v-if="saveError" class="rounded-2xl border border-red-500/20 px-5 py-3 text-xs text-red-400 flex items-center gap-2" style="background:rgba(239,68,68,0.03)">
          <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
          </svg>
          {{ saveError }}
        </div>
      </Transition>

      <!-- ============ VIEW MODE ============ -->
      <template v-if="!isEditing">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Datos generales -->
          <div class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Datos del cliente</h3>
            </div>
            <div class="space-y-3">
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Nombre</p>
                <p class="text-sm text-ink font-medium">{{ client.nombre_cliente }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">ID</p>
                <p class="text-sm text-ink font-mono tracking-wide">{{ formatClientId(client.cliente_id) }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Tipo</p>
                <p class="text-sm text-ink">{{ client.tipo_nombre || "\u2014" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Ciudad</p>
                <p class="text-sm text-ink">{{ client.ciudad || "\u2014" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">País</p>
                <p class="text-sm text-ink">{{ client.pais || "—" }}</p>
              </div>
            </div>
          </div>

          <!-- Facturación -->
          <div class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-purple-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Facturación</h3>
            </div>
            <div class="space-y-3">
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Razón social</p>
                <p class="text-sm text-ink">{{ client.nombre_facturacion || "—" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">CIF</p>
                <p class="text-sm text-ink font-mono tracking-wide">{{ client.cif || "—" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Email</p>
                <p class="text-sm text-ink">{{ client.email_facturacion || "—" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Dirección</p>
                <p class="text-sm text-ink">{{ client.direccion_facturacion || "—" }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">C.P.</p>
                <p class="text-sm text-ink">{{ client.codigo_postal || "—" }}</p>
              </div>
            </div>
          </div>

          <!-- Cuenta de acceso -->
          <div class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Cuenta de acceso</h3>
            </div>
            <div v-if="client.has_account" class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <p class="text-sm text-emerald-400 font-medium">Cuenta activa</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Email</p>
                <p class="text-sm text-ink">{{ client.user_email }}</p>
              </div>
              <div class="flex items-start gap-3">
                <p class="text-[11px] text-muted/70 w-20 flex-shrink-0 pt-0.5 uppercase tracking-wider">Nombre</p>
                <p class="text-sm text-ink">{{ client.user_name }}</p>
              </div>
            </div>
            <div v-else class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-zinc-500" />
                <p class="text-sm text-muted">Sin cuenta asignada</p>
              </div>
              <p class="text-xs text-muted/60 leading-relaxed">
                Este cliente a\u00fan no tiene cuenta de acceso a la plataforma.
              </p>
              <button
                v-if="canEdit"
                class="mt-1 inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors duration-200"
                @click="openAccountModal"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Crear cuenta de acceso
              </button>
            </div>
          </div>

          <!-- Contrato -->
          <div class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Contrato</h3>
            </div>
            <div class="space-y-3">
              <div class="flex items-center gap-2.5">
                <div
                  class="w-8 h-8 rounded-lg flex items-center justify-center"
                  :class="client.contrato_firmado ? 'bg-emerald-500/10' : 'bg-amber-500/10'"
                >
                  <svg v-if="client.contrato_firmado" class="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                  </svg>
                  <svg v-else class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p class="text-sm font-medium" :class="client.contrato_firmado ? 'text-emerald-400' : 'text-amber-400'">
                  {{ client.contrato_firmado ? "Contrato firmado" : "Pendiente de firma" }}
                </p>
              </div>
              <a
                v-if="client.contrato_url"
                :href="client.contrato_url"
                target="_blank"
                class="group/dl inline-flex items-center gap-2 text-xs text-gold hover:text-gold/80 transition-all duration-200"
              >
                <svg class="w-3.5 h-3.5 transition-transform duration-200 group-hover/dl:translate-y-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
                Descargar contrato
              </a>
              <p v-else class="text-xs text-muted/50">Sin documento subido</p>
            </div>
          </div>
        </div>

        <!-- Metadatos -->
        <div class="rounded-2xl border border-border/60 bg-white shadow-card px-6 py-4 flex items-center justify-between" >
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              <span class="text-[11px] text-muted/60">Creado por</span>
              <span class="text-xs text-ink/80 font-medium">{{ client.created_by_name || "Sistema" }}</span>
            </div>
            <div class="w-px h-3 bg-border/50" />
            <div class="flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
              <span class="text-[11px] text-muted/60">Alta</span>
              <span class="text-xs text-ink/80 font-medium">{{ formatDate(client.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Proyectos asociados -->
        <div class="group rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4 transition-all duration-300 hover:border-border hover:shadow-soft">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <svg class="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
              </svg>
            </div>
            <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Marcas asociadas</h3>
            <span v-if="client.marcas && client.marcas.length" class="ml-auto text-[10px] text-muted/60 bg-panel px-2 py-0.5 rounded-full border border-border/40">{{ client.marcas.length }}</span>
          </div>
          <div v-if="client.marcas && client.marcas.length > 0" class="space-y-2">
            <NuxtLink
              v-for="brand in client.marcas"
              :key="brand.id"
              :to="`/dashboard/marcas/${brand.id}`"
              class="flex items-center justify-between p-3.5 rounded-xl border border-border/50 hover:border-indigo-400/30 hover:bg-indigo-400/[0.02] transition-all duration-200 group/item"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-400/20 flex items-center justify-center flex-shrink-0">
                  <span class="text-[11px] font-bold text-indigo-400">{{ brand.nombre.charAt(0) }}</span>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium text-ink truncate group-hover/item:text-indigo-400 transition-colors duration-200">{{ brand.nombre }}</p>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-[11px] text-muted/70 font-mono">{{ formatBrandId(brand.brand_id) }}</span>
                    <span v-if="brand.tipo_marca_nombre" class="text-[11px] text-muted/70">· {{ brand.tipo_marca_nombre }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                <a v-if="brand.web_instagram" :href="brand.web_instagram" target="_blank" class="text-[11px] text-gold hover:text-gold/80 transition-colors" @click.stop>
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                </a>
                <span
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border"
                  :class="brand.estado === 'activa' ? 'text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15' : 'text-muted/60 bg-panel border-border/40'"
                >
                  {{ brand.estado === 'activa' ? 'Activa' : 'Inactiva' }}
                </span>
                <svg class="w-4 h-4 text-muted/40 group-hover/item:text-indigo-400 transition-colors duration-200" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </div>
            </NuxtLink>
          </div>
          <div v-else class="py-4 text-center">
            <p class="text-xs text-muted/60">Este cliente no tiene marcas asociadas.</p>
          </div>
        </div>

      </template>

      <!-- ============ EDIT MODE ============ -->
      <template v-if="isEditing">
        <div class="space-y-5">
          <!-- Datos generales -->
          <div class="rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-5" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-gold" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold">Datos del cliente</h3>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Nombre del cliente</label>
                <input v-model="editData.nombre_cliente" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">ID Cliente</label>
                <input :value="formatClientId(editData.cliente_id)" type="text" disabled class="input-field opacity-60 cursor-not-allowed" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Tipo de cliente</label>
                <select v-model="editData.tipo_cliente" class="select-field">
                  <option :value="null">Sin tipo</option>
                  <option v-for="t in store.types" :key="t.id" :value="t.id">{{ t.nombre }}</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Ciudad</label>
                <input v-model="editData.ciudad" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">País</label>
                <input v-model="editData.pais" type="text" class="input-field" />
              </div>
            </div>
          </div>

          <!-- Facturaci\u00f3n -->
          <div class="rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-5" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-gold" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold">Facturación</h3>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Nombre / Razón social</label>
                <input v-model="editData.nombre_facturacion" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">CIF</label>
                <input v-model="editData.cif" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Email de facturación</label>
                <input v-model="editData.email_facturacion" type="email" class="input-field" />
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Código Postal</label>
                <input v-model="editData.codigo_postal" type="text" class="input-field" />
              </div>
              <div class="md:col-span-2">
                <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Dirección de facturación</label>
                <input v-model="editData.direccion_facturacion" type="text" class="input-field" />
              </div>
            </div>
          </div>

          <!-- Contrato -->
          <div class="rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-gold" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold">Contrato</h3>
            </div>
            <label class="flex items-center gap-3 cursor-pointer group/check">
              <input v-model="editData.contrato_firmado" type="checkbox" class="w-4 h-4 rounded border-border bg-raised accent-gold" />
              <span class="text-sm text-ink">Contrato firmado</span>
            </label>
          </div>

          <!-- Marcas -->
          <div class="rounded-3xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
                </svg>
              </div>
              <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold">Marcas asociadas</h3>
            </div>
            <!-- Current brands -->
            <div v-if="client!.marcas && client!.marcas.length" class="space-y-2">
              <div
                v-for="brand in client!.marcas"
                :key="brand.id"
                class="flex items-center justify-between p-3 rounded-xl border border-border/50 bg-panel/30"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                    <span class="text-[11px] font-bold text-indigo-400">{{ brand.nombre.charAt(0) }}</span>
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-ink truncate">{{ brand.nombre }}</p>
                    <span class="text-[10px] text-muted/60 font-mono">{{ formatBrandId(brand.brand_id) }}</span>
                  </div>
                </div>
                <button
                  type="button"
                  :disabled="isBrandSaving"
                  class="text-xs text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                  @click="removeBrandFromClient(brand.id)"
                >
                  Quitar
                </button>
              </div>
            </div>
            <p v-else class="text-xs text-muted/50 italic">Sin marcas asociadas.</p>
            <!-- Add new brand -->
            <div class="flex gap-2 pt-2">
              <input
                v-model="newBrandName"
                type="text"
                class="input-field flex-1"
                placeholder="Nombre de la nueva marca"
                @keydown.enter.prevent="addBrandToClient"
              />
              <button
                type="button"
                :disabled="isBrandSaving || !newBrandName.trim()"
                class="h-9 px-4 rounded-xl bg-gold/10 text-gold text-xs font-medium border border-gold/20 hover:bg-gold/20 transition-colors disabled:opacity-50"
                @click="addBrandToClient"
              >
                + Añadir
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ============ CREATE ACCOUNT MODAL ============ -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showAccountModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.75); backdrop-filter: blur(8px)"
          @click.self="!isCreatingAccount && (showAccountModal = false)"
        >
          <Transition name="modal-content" appear>
            <div class="w-full max-w-md rounded-3xl border border-border/60 p-8 shadow-2xl shadow-black/40" style="background: linear-gradient(180deg, #161619 0%, #111113 100%)">
              <!-- Success state -->
              <div v-if="accountSuccess" class="space-y-5">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                    <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 class="text-lg font-semibold text-ink">Cuenta creada</h2>
                    <p class="text-xs text-muted mt-0.5">Credenciales de acceso</p>
                  </div>
                </div>

                <div class="rounded-2xl border border-emerald-500/15 p-5 space-y-3" style="background: rgba(16,185,129,0.03)">
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] text-muted uppercase tracking-wider">Email</span>
                    <span class="text-sm text-ink font-mono">{{ accountSuccess.email }}</span>
                  </div>
                  <div class="h-px bg-border/30" />
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] text-muted uppercase tracking-wider">Contraseña</span>
                    <span class="text-sm text-ink font-mono bg-white/[0.04] px-2 py-0.5 rounded">{{ accountSuccess.password }}</span>
                  </div>
                </div>

                <p class="text-xs text-muted/60 leading-relaxed">
                  Comunica estas credenciales al cliente de forma segura. Se recomienda cambiar la contraseña tras el primer acceso.
                </p>

                <button
                  class="w-full h-11 rounded-xl bg-gold text-ink text-sm font-semibold hover:bg-gold/90 active:scale-[0.98] transition-all duration-200"
                  @click="showAccountModal = false"
                >
                  Entendido
                </button>
              </div>

              <!-- Form state -->
              <div v-else class="space-y-6">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                    <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
                    </svg>
                  </div>
                  <div>
                    <h2 class="text-lg font-semibold text-ink">Crear cuenta de acceso</h2>
                    <p class="text-xs text-muted mt-0.5">El cliente podrá iniciar sesión con estas credenciales</p>
                  </div>
                </div>

                <form class="space-y-4" @submit.prevent="handleCreateAccount">
                  <div>
                    <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Email de acceso *</label>
                    <input
                      v-model="accountForm.email"
                      type="email"
                      required
                      placeholder="email@cliente.com"
                      class="input-field"
                    />
                  </div>
                  <div>
                    <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Nombre completo</label>
                    <input
                      v-model="accountForm.full_name"
                      type="text"
                      :placeholder="client?.nombre_cliente"
                      class="input-field"
                    />
                    <p class="text-[10px] text-muted/40 mt-1.5">Si se deja vacío se usará el nombre del cliente</p>
                  </div>
                  <div>
                    <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Contraseña</label>
                    <input
                      v-model="accountForm.password"
                      type="text"
                      placeholder="Se generará automáticamente"
                      class="input-field"
                    />
                    <p class="text-[10px] text-muted/40 mt-1.5">Si se deja vacío se generará una contraseña segura</p>
                  </div>

                  <Transition name="modal">
                    <div v-if="accountError" class="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/[0.04] px-4 py-3">
                      <svg class="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
                      </svg>
                      <p class="text-xs text-red-400">{{ accountError }}</p>
                    </div>
                  </Transition>

                  <div class="flex gap-3 pt-2">
                    <button
                      type="button"
                      class="flex-1 h-11 rounded-xl border border-border text-sm text-muted hover:text-ink hover:border-ink/20 transition-all duration-200"
                      :disabled="isCreatingAccount"
                      @click="showAccountModal = false"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      class="flex-1 h-11 rounded-xl bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-400 active:scale-[0.98] disabled:opacity-60 transition-all duration-200 flex items-center justify-center gap-2"
                      :disabled="isCreatingAccount"
                    >
                      <svg v-if="isCreatingAccount" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      {{ isCreatingAccount ? "Creando\u2026" : "Crear cuenta" }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- ============ DELETE MODAL ============ -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showDeleteModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.75); backdrop-filter: blur(8px)"
          @click.self="showDeleteModal = false"
        >
          <Transition name="modal-content" appear>
            <div class="w-full max-w-sm rounded-3xl border border-red-500/20 p-8 shadow-2xl shadow-black/40" style="background: linear-gradient(180deg, #161619 0%, #111113 100%)">
              <div class="flex items-center gap-3 mb-5">
                <div class="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                  <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-lg font-semibold text-ink">Eliminar cliente</h2>
                  <p class="text-xs text-muted mt-0.5">Esta acción no se puede deshacer</p>
                </div>
              </div>
              <p class="text-sm text-muted mb-6 leading-relaxed">
                ¿Estás seguro de que quieres eliminar a <span class="text-ink font-medium">{{ client?.nombre_cliente }}</span>?
                Se eliminará toda la información asociada.
              </p>
              <div class="flex gap-3">
                <button
                  type="button"
                  class="flex-1 h-11 rounded-xl border border-border text-sm text-muted hover:text-ink hover:border-ink/20 transition-all duration-200"
                  :disabled="isDeleting"
                  @click="showDeleteModal = false"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  class="flex-1 h-11 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-400 active:scale-[0.98] disabled:opacity-60 transition-all duration-200 flex items-center justify-center gap-2"
                  :disabled="isDeleting"
                  @click="handleDelete"
                >
                  <svg v-if="isDeleting" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ isDeleting ? "Eliminando\u2026" : "Eliminar" }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
