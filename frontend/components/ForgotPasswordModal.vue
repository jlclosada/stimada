<script setup lang="ts">
const emit = defineEmits<{ close: [] }>();
const config = useRuntimeConfig();

const email = ref("");
const isLoading = ref(false);
const error = ref("");
const success = ref(false);

async function handleSubmit() {
  error.value = "";
  isLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/auth/password-reset/`, {
      method: "POST",
      body: { email: email.value },
    });
    success.value = true;
  } catch (err: unknown) {
    const e = err as { data?: { email?: string[]; non_field_errors?: string[]; detail?: string } };
    error.value =
      e?.data?.email?.[0] ??
      e?.data?.non_field_errors?.[0] ??
      e?.data?.detail ??
      "Ha ocurrido un error. Inténtalo de nuevo.";
  } finally {
    isLoading.value = false;
  }
}

function onBackdrop(e: MouseEvent) {
  if (e.target === e.currentTarget) emit("close");
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background: rgba(0,0,0,0.72); backdrop-filter: blur(6px)"
        @click="onBackdrop"
      >
        <Transition name="modal-content" appear>
          <div
            class="w-full max-w-sm rounded-2xl border border-border p-7 shadow-card"
            style="background: #141417"
          >
            <!-- Close -->
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-base font-semibold text-cream">Recuperar acceso</h2>
              <button
                class="text-muted hover:text-cream transition-colors rounded-lg p-1"
                @click="emit('close')"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Success -->
            <div v-if="success" class="text-center py-4 space-y-3">
              <div class="w-12 h-12 rounded-full bg-green-500/12 border border-green-500/20 flex items-center justify-center mx-auto">
                <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <p class="text-sm font-medium text-cream">Solicitud enviada</p>
              <p class="text-xs text-muted leading-relaxed">
                Hemos notificado a los administradores de Stimada.<br/>
                Recibirás tus nuevas credenciales pronto.
              </p>
              <button
                class="mt-2 text-xs text-gold hover:text-gold/80 transition-colors"
                @click="emit('close')"
              >
                Cerrar
              </button>
            </div>

            <!-- Form -->
            <template v-else>
              <p class="text-sm text-muted mb-5 leading-relaxed">
                Introduce tu email y notificaremos a los administradores para que te proporcionen acceso.
              </p>

              <form class="space-y-4" @submit.prevent="handleSubmit">
                <div>
                  <label class="block text-xs font-medium text-muted mb-1.5">Email</label>
                  <input
                    v-model="email"
                    type="email"
                    placeholder="tu@email.com"
                    required
                    :disabled="isLoading"
                    class="input-field disabled:opacity-50"
                  />
                </div>

                <Transition name="modal">
                  <div
                    v-if="error"
                    class="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/8 p-3"
                  >
                    <svg class="w-3.5 h-3.5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
                    </svg>
                    <p class="text-xs text-red-400">{{ error }}</p>
                  </div>
                </Transition>

                <div class="flex gap-2 pt-1">
                  <button
                    type="button"
                    class="flex-1 h-10 rounded-xl border border-border text-sm text-muted hover:text-cream hover:border-subtle transition-colors"
                    @click="emit('close')"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    :disabled="isLoading"
                    class="flex-1 h-10 rounded-xl bg-gold text-ink text-sm font-semibold
                           flex items-center justify-center gap-1.5
                           hover:bg-gold/90 active:scale-[0.98]
                           disabled:opacity-60 transition-all duration-150"
                  >
                    <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {{ isLoading ? "Enviando…" : "Solicitar acceso" }}
                  </button>
                </div>
              </form>
            </template>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
