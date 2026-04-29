<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth"] });

const auth = useAuthStore();
const config = useRuntimeConfig();

const form = reactive({
  full_name: auth.user?.full_name ?? "",
});

const isLoading = ref(false);
const success = ref(false);
const error = ref("");

// Password change
const pwForm = reactive({
  current_password: "",
  new_password: "",
  confirm_password: "",
});
const pwLoading = ref(false);
const pwSuccess = ref(false);
const pwError = ref("");

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  stimada_employee: "Empleado Stimada",
  client: "Cliente",
  content_maker: "Content Maker",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "text-gold bg-gold/10 border-gold/25",
  stimada_employee: "text-blue-400 bg-blue-400/10 border-blue-400/25",
  client: "text-green-400 bg-green-400/10 border-green-400/25",
  content_maker: "text-orange-400 bg-orange-400/10 border-orange-400/25",
};

const initials = computed(() => {
  const name = auth.user?.full_name ?? "";
  return name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
});

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
</script>

<template>
  <div class="max-w-xl animate-fade-up">
    <div class="mb-8">
      <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-1">Cuenta</p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">Mi perfil</h1>
    </div>

    <div class="space-y-4">
      <!-- Avatar + rol -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 flex items-center gap-5" >
        <div
          class="w-16 h-16 rounded-2xl bg-gold/15 border border-gold/20 flex items-center justify-center
                 text-gold text-xl font-semibold flex-shrink-0"
        >
          {{ initials }}
        </div>
        <div>
          <p class="text-lg font-semibold text-ink">{{ auth.user?.full_name }}</p>
          <p class="text-sm text-muted mt-0.5">{{ auth.user?.email }}</p>
          <span
            class="inline-block mt-2 text-xs font-medium px-2.5 py-0.5 rounded-full border"
            :class="ROLE_COLORS[auth.user?.role ?? ''] ?? 'text-ink border-border'"
          >
            {{ ROLE_LABELS[auth.user?.role ?? ""] ?? auth.user?.role }}
          </span>
        </div>
      </div>

      <!-- Edit form -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6" >
        <h2 class="text-sm font-semibold text-ink mb-5">Información personal</h2>
        <form class="space-y-4" @submit.prevent="handleSave">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Nombre completo</label>
            <input
              v-model="form.full_name"
              type="text"
              class="input-field"
              :disabled="isLoading"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Email</label>
            <input
              :value="auth.user?.email"
              type="email"
              disabled
              class="input-field opacity-40 cursor-not-allowed"
            />
            <p class="text-xs text-muted mt-1.5">El email no se puede cambiar desde aquí.</p>
          </div>

          <Transition name="modal">
            <div
              v-if="success"
              class="flex items-center gap-2 rounded-xl border border-green-500/20 bg-green-500/8 p-3"
            >
              <svg class="w-4 h-4 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <p class="text-xs text-green-400">Cambios guardados correctamente.</p>
            </div>
          </Transition>

          <Transition name="modal">
            <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
          </Transition>

          <button
            type="submit"
            :disabled="isLoading"
            class="h-10 px-5 rounded-xl bg-gold text-ink text-sm font-semibold
                   flex items-center gap-2
                   hover:bg-gold/90 active:scale-[0.98]
                   disabled:opacity-60 transition-all duration-150"
          >
            <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? "Guardando…" : "Guardar cambios" }}
          </button>
        </form>
      </div>

      <!-- Password change -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
        <h2 class="text-sm font-semibold text-ink mb-5">Cambiar contraseña</h2>
        <form class="space-y-4" @submit.prevent="handleChangePassword">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Contraseña actual</label>
            <input
              v-model="pwForm.current_password"
              type="password"
              required
              :disabled="pwLoading"
              class="input-field"
              placeholder="Tu contraseña actual"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Nueva contraseña</label>
            <input
              v-model="pwForm.new_password"
              type="password"
              required
              minlength="8"
              :disabled="pwLoading"
              class="input-field"
              placeholder="Mínimo 8 caracteres"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Confirmar nueva contraseña</label>
            <input
              v-model="pwForm.confirm_password"
              type="password"
              required
              minlength="8"
              :disabled="pwLoading"
              class="input-field"
              placeholder="Repite la nueva contraseña"
            />
          </div>

          <Transition name="modal">
            <div
              v-if="pwSuccess"
              class="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3"
            >
              <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <p class="text-xs text-emerald-700">Contraseña actualizada correctamente.</p>
            </div>
          </Transition>

          <Transition name="modal">
            <div
              v-if="pwError"
              class="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3"
            >
              <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
              </svg>
              <p class="text-xs text-red-600 leading-relaxed">{{ pwError }}</p>
            </div>
          </Transition>

          <button
            type="submit"
            :disabled="pwLoading"
            class="h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium
                   flex items-center gap-2
                   hover:bg-ink/85 active:scale-[0.98]
                   disabled:opacity-60 transition-all duration-150"
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
