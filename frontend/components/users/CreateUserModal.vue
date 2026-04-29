<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

const emit = defineEmits<{
  close: [];
  created: [];
}>();

const auth = useAuthStore();
const config = useRuntimeConfig();

const form = reactive({
  full_name: "",
  email: "",
  password: "",
  role: "",
});
const isLoading = ref(false);
const error = ref("");

const ALL_ROLES = [
  { value: "admin", label: "Administrador" },
  { value: "stimada_employee", label: "Empleado Stimada" },
  { value: "client", label: "Cliente" },
  { value: "content_maker", label: "Content Maker" },
];

const availableRoles = computed(() =>
  auth.isAdmin
    ? ALL_ROLES
    : ALL_ROLES.filter((r) => r.value === "client" || r.value === "content_maker")
);

async function handleSubmit() {
  error.value = "";
  isLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/users/`, {
      method: "POST",
      body: form,
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    emit("created");
  } catch (err: unknown) {
    const fetchError = err as { data?: Record<string, string[]> };
    if (fetchError?.data) {
      const firstKey = Object.keys(fetchError.data)[0];
      error.value = fetchError.data[firstKey]?.[0] ?? "Error al crear el usuario.";
    } else {
      error.value = "Error al crear el usuario.";
    }
  } finally {
    isLoading.value = false;
  }
}

function closeOnBackdrop(e: MouseEvent) {
  if (e.target === e.currentTarget) emit("close");
}
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-ink/80 backdrop-blur-sm"
    @click="closeOnBackdrop"
  >
    <div
      class="w-full max-w-md border border-border fade-enter"
      style="background-color: #141414"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-7 py-5 border-b border-border">
        <h2 class="font-display text-2xl font-light text-cream">Nuevo usuario</h2>
        <button
          class="text-gray-muted hover:text-cream transition-colors"
          aria-label="Cerrar"
          @click="emit('close')"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form class="px-7 py-6 space-y-7" @submit.prevent="handleSubmit">
        <!-- Nombre -->
        <div class="relative">
          <input
            id="m-name"
            v-model="form.full_name"
            type="text"
            placeholder="name"
            required
            :disabled="isLoading"
            class="input-editorial peer"
          />
          <label for="m-name" class="label-floating peer-focus:top-0 peer-focus:text-xs peer-focus:text-gold peer-[:not(:placeholder-shown)]:top-0 peer-[:not(:placeholder-shown)]:text-xs peer-[:not(:placeholder-shown)]:text-gold">
            Nombre completo
          </label>
        </div>

        <!-- Email -->
        <div class="relative">
          <input
            id="m-email"
            v-model="form.email"
            type="email"
            placeholder="email"
            required
            :disabled="isLoading"
            class="input-editorial peer"
          />
          <label for="m-email" class="label-floating peer-focus:top-0 peer-focus:text-xs peer-focus:text-gold peer-[:not(:placeholder-shown)]:top-0 peer-[:not(:placeholder-shown)]:text-xs peer-[:not(:placeholder-shown)]:text-gold">
            Email
          </label>
        </div>

        <!-- Password -->
        <div class="relative">
          <input
            id="m-password"
            v-model="form.password"
            type="password"
            placeholder="password"
            required
            minlength="8"
            :disabled="isLoading"
            class="input-editorial peer"
          />
          <label for="m-password" class="label-floating peer-focus:top-0 peer-focus:text-xs peer-focus:text-gold peer-[:not(:placeholder-shown)]:top-0 peer-[:not(:placeholder-shown)]:text-xs peer-[:not(:placeholder-shown)]:text-gold">
            Contraseña
          </label>
        </div>

        <!-- Rol -->
        <div class="relative">
          <select
            id="m-role"
            v-model="form.role"
            required
            :disabled="isLoading"
            class="input-editorial appearance-none cursor-pointer"
            :class="form.role ? '' : 'text-gray-muted'"
          >
            <option value="" disabled>Selecciona un rol</option>
            <option
              v-for="r in availableRoles"
              :key="r.value"
              :value="r.value"
              class="bg-panel text-cream"
            >
              {{ r.label }}
            </option>
          </select>
          <label for="m-role" class="absolute left-0 top-0 text-xs text-gold pointer-events-none">
            Rol
          </label>
          <svg
            class="absolute right-0 bottom-2.5 w-3.5 h-3.5 text-gray-muted pointer-events-none"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </div>

        <!-- Error -->
        <Transition name="fade">
          <p
            v-if="error"
            class="text-sm text-red-400 font-sans py-2 px-3 border border-red-400/20 bg-red-400/5"
          >
            {{ error }}
          </p>
        </Transition>

        <!-- Actions -->
        <div class="flex gap-3 pt-2">
          <button
            type="button"
            class="flex-1 h-11 border border-border text-gray-muted font-sans text-sm hover:text-cream hover:border-gold/30 transition-colors duration-200"
            @click="emit('close')"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex-1 h-11 bg-gold text-ink font-sans text-sm font-medium hover:opacity-85 disabled:opacity-50 transition-opacity duration-200 flex items-center justify-center gap-2"
          >
            <svg
              v-if="isLoading"
              class="animate-spin w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? "Creando..." : "Crear usuario" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
