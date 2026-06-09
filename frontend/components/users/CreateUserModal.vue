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
  role: "stimada_employee",
});
const isLoading = ref(false);
const error = ref("");
const createdPassword = ref("");
const copied = ref(false);

function generatePassword(length = 14): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#&*";
  let pwd = "";
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  for (let i = 0; i < length; i++) {
    pwd += chars[array[i] % chars.length];
  }
  return pwd;
}

onMounted(() => {
  form.password = generatePassword();
});

function regenerate() {
  form.password = generatePassword();
}

async function copyPassword() {
  const pwd = createdPassword.value || form.password;
  await navigator.clipboard.writeText(pwd);
  copied.value = true;
  setTimeout(() => { copied.value = false; }, 2000);
}

async function handleSubmit() {
  error.value = "";
  isLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/users/`, {
      method: "POST",
      body: form,
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    createdPassword.value = form.password;
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

function handleClose() {
  if (createdPassword.value) emit("created");
  else emit("close");
}

function closeOnBackdrop(e: MouseEvent) {
  if (e.target === e.currentTarget) handleClose();
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0,0,0,0.4); backdrop-filter: blur(4px)"
      @click="closeOnBackdrop"
    >
      <div class="w-full max-w-md rounded-2xl border border-border/60 bg-white shadow-elevated animate-scale-in">
        <!-- Header -->
        <div class="flex items-center justify-between px-7 pt-7 pb-1">
          <div>
            <h2 class="text-lg font-semibold text-ink">Nuevo empleado</h2>
            <p class="text-sm text-muted mt-0.5">Crea una cuenta de acceso para un empleado</p>
          </div>
          <button
            class="w-8 h-8 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-panel transition-all duration-150"
            aria-label="Cerrar"
            @click="handleClose"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Success state -->
        <div v-if="createdPassword" class="px-7 py-6 space-y-4">
          <div class="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <svg class="w-5 h-5 text-emerald-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm text-emerald-700 font-medium">Usuario creado correctamente</p>
          </div>

          <div>
            <label class="block text-xs font-medium text-ink/70 mb-1.5">Contraseña generada</label>
            <div class="flex items-center gap-2">
              <code class="flex-1 h-[42px] leading-[42px] px-4 rounded-xl border border-border bg-panel text-sm font-mono text-ink select-all truncate">{{ createdPassword }}</code>
              <button
                type="button"
                class="h-[42px] px-4 rounded-xl border border-border text-sm font-medium transition-all duration-150"
                :class="copied ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'text-muted hover:text-ink hover:border-ink/20 hover:bg-panel'"
                @click="copyPassword"
              >
                {{ copied ? "¡Copiada!" : "Copiar" }}
              </button>
            </div>
            <p class="text-xs text-muted mt-2">Envía esta contraseña al empleado. Podrá cambiarla desde su perfil.</p>
          </div>

          <button
            type="button"
            class="w-full h-11 rounded-xl bg-ink text-white text-sm font-medium hover:bg-ink/85 hover:shadow-soft active:scale-[0.98] transition-all duration-200"
            @click="handleClose"
          >
            Cerrar
          </button>
        </div>

        <!-- Form -->
        <form v-else class="px-7 py-6 space-y-4" @submit.prevent="handleSubmit">
          <!-- Nombre -->
          <div>
            <label for="m-name" class="block text-xs font-medium text-ink/70 mb-1.5">Nombre completo</label>
            <input
              id="m-name"
              v-model="form.full_name"
              type="text"
              placeholder="María García López"
              required
              :disabled="isLoading"
              class="input-field"
            />
          </div>

          <!-- Email -->
          <div>
            <label for="m-email" class="block text-xs font-medium text-ink/70 mb-1.5">Email</label>
            <input
              id="m-email"
              v-model="form.email"
              type="email"
              placeholder="maria@stimada.com"
              required
              :disabled="isLoading"
              class="input-field"
            />
          </div>

          <!-- Password (auto-generated) -->
          <div>
            <label class="block text-xs font-medium text-ink/70 mb-1.5">Contraseña generada</label>
            <div class="flex items-center gap-2">
              <code class="flex-1 h-[42px] leading-[42px] px-4 rounded-xl border border-border bg-panel text-sm font-mono text-ink truncate">{{ form.password }}</code>
              <button
                type="button"
                class="h-[42px] px-3 rounded-xl border border-border text-muted hover:text-ink hover:border-ink/20 hover:bg-panel transition-all duration-150"
                title="Regenerar"
                @click="regenerate"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>
              <button
                type="button"
                class="h-[42px] px-3 rounded-xl border border-border transition-all duration-150"
                :class="copied ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'text-muted hover:text-ink hover:border-ink/20 hover:bg-panel'"
                title="Copiar"
                @click="copyPassword"
              >
                <svg v-if="!copied" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                </svg>
                <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Error -->
          <Transition name="fade">
            <div
              v-if="error"
              class="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3"
            >
              <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
              </svg>
              <p class="text-xs text-red-600 leading-relaxed">{{ error }}</p>
            </div>
          </Transition>

          <!-- Actions -->
          <div class="flex gap-3 pt-3">
            <button
              type="button"
              class="flex-1 h-11 rounded-xl border border-border text-sm font-medium text-muted hover:text-ink hover:border-ink/20 hover:bg-panel active:scale-[0.98] transition-all duration-200"
              @click="emit('close')"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="isLoading"
              class="flex-1 h-11 rounded-xl bg-ink text-white text-sm font-medium hover:bg-ink/85 hover:shadow-soft active:scale-[0.98] disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2"
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
              {{ isLoading ? "Creando…" : "Crear empleado" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
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
