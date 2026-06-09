<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth", "role"] });

const auth = useAuthStore();
const config = useRuntimeConfig();

const isClient = computed(() => auth.user?.role === "client");

// Tabs
const activeTab = ref<"personal" | "security">("personal");

// Personal info form
const form = reactive({
  full_name: auth.user?.full_name ?? "",
});
const isLoading = ref(false);
const success = ref(false);
const error = ref("");

// Avatar upload
const avatarFile = ref<File | null>(null);
const avatarPreview = ref<string | null>(null);
const avatarUploading = ref(false);

const avatarUrl = computed(() => {
  if (avatarPreview.value) return avatarPreview.value;
  if (auth.user?.avatar) {
    if (auth.user.avatar.startsWith("http")) return auth.user.avatar;
    return `${config.public.apiBase.replace("/api/v1", "")}${auth.user.avatar}`;
  }
  return null;
});

const initials = computed(() => {
  const name = auth.user?.full_name ?? "";
  return name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
});

function onAvatarSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  avatarFile.value = file;
  avatarPreview.value = URL.createObjectURL(file);
}

async function uploadAvatar() {
  if (!avatarFile.value) return;
  avatarUploading.value = true;
  try {
    const formData = new FormData();
    formData.append("avatar", avatarFile.value);
    await $fetch(`${config.public.apiBase}/auth/me/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: formData,
    });
    await auth.fetchMe();
    avatarFile.value = null;
    avatarPreview.value = null;
  } catch {
    // silent
  } finally {
    avatarUploading.value = false;
  }
}

async function handleSave() {
  isLoading.value = true;
  error.value = "";
  success.value = false;
  try {
    await $fetch(`${config.public.apiBase}/auth/me/`, {
      method: "PATCH",
      body: { full_name: form.full_name },
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    await auth.fetchMe();
    success.value = true;
    setTimeout(() => (success.value = false), 3000);
  } catch {
    error.value = "No se pudo guardar. Inténtalo de nuevo.";
  } finally {
    isLoading.value = false;
  }
}

// Password change
const pwForm = reactive({
  current_password: "",
  new_password: "",
  confirm_password: "",
});
const pwLoading = ref(false);
const pwSuccess = ref(false);
const pwError = ref("");

async function handleChangePassword() {
  pwLoading.value = true;
  pwError.value = "";
  pwSuccess.value = false;

  if (pwForm.new_password !== pwForm.confirm_password) {
    pwError.value = "Las contraseñas no coinciden.";
    pwLoading.value = false;
    return;
  }

  try {
    await $fetch(`${config.public.apiBase}/auth/me/change-password/`, {
      method: "POST",
      body: pwForm,
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    pwSuccess.value = true;
    pwForm.current_password = "";
    pwForm.new_password = "";
    pwForm.confirm_password = "";
    setTimeout(() => (pwSuccess.value = false), 4000);
  } catch (err: unknown) {
    const fetchErr = err as { data?: Record<string, string[]> };
    if (fetchErr?.data) {
      const firstKey = Object.keys(fetchErr.data)[0];
      pwError.value = fetchErr.data[firstKey]?.[0] ?? "Error al cambiar la contraseña.";
    } else {
      pwError.value = "Error al cambiar la contraseña.";
    }
  } finally {
    pwLoading.value = false;
  }
}

// Favorite CMs (client only)
const favoriteCMs = ref<any[]>([]);
const loadingFavorites = ref(false);

// Client brands
const clientBrands = ref<{ id: number; brand_id: string; nombre: string; estado: string }[]>([]);
const loadingBrands = ref(false);

async function fetchClientBrands() {
  if (!isClient.value) return;
  loadingBrands.value = true;
  try {
    const data = await $fetch<any>(
      `${config.public.apiBase}/clients/me/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    clientBrands.value = data.brands ?? [];
  } catch {
    clientBrands.value = [];
  } finally {
    loadingBrands.value = false;
  }
}

async function fetchFavoriteCMs() {
  if (!isClient.value) return;
  loadingFavorites.value = true;
  try {
    favoriteCMs.value = await $fetch<any[]>(
      `${config.public.apiBase}/clients/me/favorite-cms/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
  } catch {
    favoriteCMs.value = [];
  } finally {
    loadingFavorites.value = false;
  }
}

async function removeFavorite(cmId: number) {
  try {
    await $fetch(`${config.public.apiBase}/clients/me/favorite-cms/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { content_maker_id: cmId },
    });
    favoriteCMs.value = favoriteCMs.value.filter((cm) => cm.id !== cmId);
  } catch {
    // ignore
  }
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  stimada_employee: "Empleado Stimada",
  client: "Cliente",
  content_maker: "Content Maker",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "text-gold bg-gold/10 border-gold/25",
  stimada_employee: "text-blue-500 bg-blue-50 border-blue-200",
  client: "text-emerald-600 bg-emerald-50 border-emerald-200",
  content_maker: "text-orange-500 bg-orange-50 border-orange-200",
};

onMounted(() => {
  fetchFavoriteCMs();
  fetchClientBrands();
});
</script>

<template>
  <div class="max-w-2xl mx-auto animate-fade-up">
    <!-- Header with avatar -->
    <div class="mb-8">
      <div class="flex items-center gap-5">
        <div class="w-20 h-20 rounded-2xl overflow-hidden border-2 border-border/60 shadow-card flex-shrink-0">
          <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-gradient-to-br from-gold/15 to-amber-100 flex items-center justify-center text-gold text-2xl font-semibold">
            {{ initials }}
          </div>
        </div>
        <div>
          <h1 class="text-2xl font-semibold tracking-tight text-ink">{{ auth.user?.full_name }}</h1>
          <p class="text-sm text-muted mt-0.5">{{ auth.user?.email }}</p>
          <span
            class="inline-block mt-2 text-[11px] font-medium px-2.5 py-0.5 rounded-full border"
            :class="ROLE_COLORS[auth.user?.role ?? ''] ?? 'text-ink border-border'"
          >
            {{ ROLE_LABELS[auth.user?.role ?? ""] ?? auth.user?.role }}
          </span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-border/60 mb-6">
      <nav class="flex gap-6">
        <button
          class="pb-3 text-sm font-medium transition-all border-b-2 -mb-px"
          :class="activeTab === 'personal' ? 'border-gold text-ink' : 'border-transparent text-muted hover:text-ink'"
          @click="activeTab = 'personal'"
        >
          Información personal
        </button>
        <button
          class="pb-3 text-sm font-medium transition-all border-b-2 -mb-px"
          :class="activeTab === 'security' ? 'border-gold text-ink' : 'border-transparent text-muted hover:text-ink'"
          @click="activeTab = 'security'"
        >
          Seguridad
        </button>
      </nav>
    </div>

    <!-- Tab: Personal Info -->
    <div v-if="activeTab === 'personal'" class="space-y-6">
      <!-- Avatar upload -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-4">Foto de perfil</h2>
        <div class="flex items-center gap-5">
          <div class="w-16 h-16 rounded-xl overflow-hidden border border-border/60 flex-shrink-0">
            <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-gradient-to-br from-gold/10 to-amber-50 flex items-center justify-center text-gold text-lg font-semibold">
              {{ initials }}
            </div>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <label class="px-4 h-9 rounded-xl border border-border/60 text-xs font-medium text-muted hover:text-ink hover:border-ink/20 cursor-pointer transition-all flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                Seleccionar archivo
                <input type="file" accept="image/*" class="hidden" @change="onAvatarSelect" />
              </label>
              <button
                v-if="avatarFile"
                :disabled="avatarUploading"
                class="px-4 h-9 rounded-xl bg-gold text-white text-xs font-medium hover:bg-gold/90 transition-all disabled:opacity-50 flex items-center gap-1.5"
                @click="uploadAvatar"
              >
                <svg v-if="avatarUploading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Guardar foto
              </button>
            </div>
            <p class="text-[11px] text-muted mt-2">JPG, PNG o WebP. Máx. 5MB.</p>
          </div>
        </div>
      </div>

      <!-- Name & Email -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-5">Datos personales</h2>
        <form class="space-y-4" @submit.prevent="handleSave">
          <div>
            <label class="block text-[11px] font-medium text-muted mb-1.5">Nombre completo</label>
            <input v-model="form.full_name" type="text" class="input-field" :disabled="isLoading" />
          </div>
          <div>
            <label class="block text-[11px] font-medium text-muted mb-1.5">Email</label>
            <input :value="auth.user?.email" type="email" disabled class="input-field opacity-50 cursor-not-allowed" />
            <p class="text-[10px] text-muted mt-1.5">El email no se puede cambiar desde aquí.</p>
          </div>

          <Transition name="modal">
            <div v-if="success" class="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3">
              <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <p class="text-xs text-emerald-700">Cambios guardados correctamente.</p>
            </div>
          </Transition>

          <Transition name="modal">
            <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
          </Transition>

          <button
            type="submit"
            :disabled="isLoading"
            class="h-10 px-5 rounded-xl bg-gold text-white text-sm font-medium flex items-center gap-2 hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all duration-150"
          >
            <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? "Guardando…" : "Guardar cambios" }}
          </button>
        </form>
      </div>

      <!-- Client Brands -->
      <div v-if="isClient" class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-5 flex items-center gap-2">
          <svg class="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
          </svg>
          Mis marcas
        </h2>

        <div v-if="loadingBrands" class="flex justify-center py-6">
          <div class="w-5 h-5 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
        </div>

        <div v-else-if="clientBrands.length" class="space-y-2">
          <div
            v-for="brand in clientBrands"
            :key="brand.id"
            class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-panel/40 transition-colors"
          >
            <div class="w-9 h-9 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
              <span class="text-[11px] font-bold text-indigo-400">{{ brand.nombre.charAt(0) }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-xs font-medium text-ink truncate">{{ brand.nombre }}</p>
              <p class="text-[10px] text-muted/60 font-mono">{{ brand.brand_id }}</p>
            </div>
            <span
              class="text-[10px] font-medium px-2 py-0.5 rounded-full border"
              :class="brand.estado === 'activa' ? 'text-emerald-500 bg-emerald-50 border-emerald-200' : 'text-muted bg-panel border-border/40'"
            >
              {{ brand.estado === 'activa' ? 'Activa' : 'Inactiva' }}
            </span>
          </div>
        </div>

        <div v-else class="text-center py-6">
          <svg class="w-8 h-8 text-muted/20 mx-auto mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
          </svg>
          <p class="text-[11px] text-muted">No hay marcas asociadas a tu cuenta.</p>
        </div>
      </div>

      <!-- Favorite CMs (client only) -->
      <div v-if="isClient" class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-5 flex items-center gap-2">
          <svg class="w-4 h-4 text-pink-500" fill="currentColor" stroke="currentColor" stroke-width="0.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
          </svg>
          Tus CM favoritas
        </h2>

        <div v-if="loadingFavorites" class="flex justify-center py-6">
          <div class="w-5 h-5 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
        </div>

        <div v-else-if="favoriteCMs.length" class="space-y-2">
          <div
            v-for="cm in favoriteCMs"
            :key="cm.id"
            class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-panel/40 transition-colors group"
          >
            <NuxtLink :to="`/dashboard/content-makers/${cm.id}`" class="flex items-center gap-3 flex-1 min-w-0">
              <div class="w-9 h-9 rounded-lg overflow-hidden flex-shrink-0">
                <img v-if="cm.foto_url" :src="cm.foto_url" :alt="cm.nombre" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-gradient-to-br from-pink-100 to-pink-50 flex items-center justify-center text-[10px] font-bold text-pink-400">
                  {{ cm.nombre?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) }}
                </div>
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium text-ink truncate group-hover:text-gold transition-colors">{{ cm.nombre }}</p>
                <p class="text-[10px] text-muted truncate">
                  <span v-if="cm.instagram_handle">@{{ cm.instagram_handle }}</span>
                  <span v-if="cm.tiktok_handle"> · {{ cm.tiktok_handle }}</span>
                </p>
              </div>
            </NuxtLink>
            <button
              class="p-1.5 rounded-lg text-muted/40 hover:text-red-500 hover:bg-red-50 transition-all flex-shrink-0"
              title="Eliminar de favoritas"
              @click="removeFavorite(cm.id)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div v-else class="text-center py-6">
          <svg class="w-8 h-8 text-muted/20 mx-auto mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
          </svg>
          <p class="text-[11px] text-muted">Aún no tienes Content Makers favoritas.</p>
          <NuxtLink to="/dashboard/content-makers" class="inline-block mt-2 text-[11px] text-gold hover:text-gold/80 font-medium transition-colors">
            Explorar Content Makers →
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Tab: Security -->
    <div v-if="activeTab === 'security'" class="space-y-6">
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-1">Cambiar contraseña</h2>
        <p class="text-[11px] text-muted mb-5">Tu contraseña debe tener al menos 8 caracteres.</p>
        <form class="space-y-4" @submit.prevent="handleChangePassword">
          <div>
            <label class="block text-[11px] font-medium text-muted mb-1.5">Contraseña actual</label>
            <input v-model="pwForm.current_password" type="password" required :disabled="pwLoading" class="input-field" placeholder="Tu contraseña actual" />
          </div>
          <div>
            <label class="block text-[11px] font-medium text-muted mb-1.5">Nueva contraseña</label>
            <input v-model="pwForm.new_password" type="password" required minlength="8" :disabled="pwLoading" class="input-field" placeholder="Mínimo 8 caracteres" />
          </div>
          <div>
            <label class="block text-[11px] font-medium text-muted mb-1.5">Confirmar nueva contraseña</label>
            <input v-model="pwForm.confirm_password" type="password" required minlength="8" :disabled="pwLoading" class="input-field" placeholder="Repite la nueva contraseña" />
          </div>

          <Transition name="modal">
            <div v-if="pwSuccess" class="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3">
              <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <p class="text-xs text-emerald-700">Contraseña actualizada correctamente.</p>
            </div>
          </Transition>

          <Transition name="modal">
            <div v-if="pwError" class="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3">
              <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
              </svg>
              <p class="text-xs text-red-600 leading-relaxed">{{ pwError }}</p>
            </div>
          </Transition>

          <button
            type="submit"
            :disabled="pwLoading"
            class="h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium flex items-center gap-2 hover:bg-ink/85 active:scale-[0.98] disabled:opacity-60 transition-all duration-150"
          >
            <svg v-if="pwLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ pwLoading ? "Guardando…" : "Cambiar contraseña" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
