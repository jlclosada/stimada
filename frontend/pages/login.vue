<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ layout: false, middleware: "auth" });

const auth = useAuthStore();
const email = ref("");
const password = ref("");
const showPassword = ref(false);
const showForgot = ref(false);

const ROLE_REDIRECTS: Record<string, string> = {
  admin: "/home",
  stimada_employee: "/home",
  client: "/home",
  content_maker: "/home",
};

async function handleSubmit() {
  auth.clearError();
  try {
    await auth.login(email.value, password.value);
    const role = auth.user?.role ?? "";
    await navigateTo(ROLE_REDIRECTS[role] ?? "/home");
  } catch {
    // error already in auth.error
  }
}
</script>

<template>
  <div class="relative min-h-screen flex items-center justify-center overflow-hidden bg-panel">

    <!-- Subtle background gradient -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div
        class="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full opacity-[0.04]"
        style="background: radial-gradient(circle, #c9a84c, transparent 70%)"
      />
      <div
        class="absolute -bottom-32 -right-32 w-[500px] h-[500px] rounded-full opacity-[0.03]"
        style="background: radial-gradient(circle, #0071e3, transparent 70%)"
      />
    </div>

    <!-- Card -->
    <div
      class="relative z-10 w-full max-w-[420px] mx-4 animate-scale-in"
      style="animation-delay: 80ms"
    >
      <!-- Logo -->
      <div class="text-center mb-10 animate-slide-down" style="animation-delay: 0ms">
        <img src="~/assets/images/stimada_logo.png" alt="Stimada" class="h-10 w-auto mx-auto" />
      </div>

      <div class="rounded-2xl border border-border/60 bg-white p-9 shadow-elevated">
        <!-- Heading -->
        <div class="mb-8 animate-fade-up delay-100">
          <h1 class="text-[26px] font-semibold tracking-tight text-ink leading-tight">
            Bienvenido de nuevo
          </h1>
          <p class="text-sm text-muted mt-1.5">Accede a tu cuenta para continuar</p>
        </div>

        <!-- Form -->
        <form class="space-y-4" @submit.prevent="handleSubmit">

          <!-- Email -->
          <div class="animate-fade-up delay-150">
            <label class="block text-xs font-medium text-ink/70 mb-2" for="email">
              Email
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="tu@email.com"
              autocomplete="email"
              required
              :disabled="auth.isLoading"
              class="input-field disabled:opacity-50"
            />
          </div>

          <!-- Password -->
          <div class="animate-fade-up delay-200">
            <label class="block text-xs font-medium text-ink/70 mb-2" for="password">
              Contraseña
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
                required
                :disabled="auth.isLoading"
                class="input-field pr-11 disabled:opacity-50"
              />
              <button
                type="button"
                tabindex="-1"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink transition-colors"
                @click="showPassword = !showPassword"
              >
                <svg v-if="!showPassword" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.964-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Forgot password -->
          <div class="text-right animate-fade-up delay-250">
            <button
              type="button"
              class="text-xs text-gold hover:text-gold-dim transition-colors font-medium"
              @click="showForgot = true"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          <!-- Error -->
          <Transition name="modal">
            <div
              v-if="auth.error"
              class="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3"
            >
              <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
              </svg>
              <p class="text-xs text-red-600 leading-relaxed">{{ auth.error }}</p>
            </div>
          </Transition>

          <!-- Submit -->
          <div class="animate-fade-up delay-300 pt-2">
            <button
              type="submit"
              :disabled="auth.isLoading"
              class="w-full h-12 rounded-xl bg-ink text-white text-sm font-semibold
                     flex items-center justify-center gap-2
                     hover:bg-ink/85 hover:shadow-soft active:scale-[0.98]
                     disabled:opacity-60 disabled:cursor-not-allowed
                     transition-all duration-200"
            >
              <svg v-if="auth.isLoading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ auth.isLoading ? "Entrando…" : "Entrar" }}
            </button>
          </div>
        </form>
      </div>

      <!-- Footer -->
      <div class="mt-10 animate-fade-in delay-700 text-center space-y-3">
        <img src="~/assets/images/stimada_logo.png" alt="Stimada" class="h-5 w-auto mx-auto opacity-40" />
        <p class="text-xs text-muted/50">
          Acceso restringido · Solo usuarios invitados
        </p>
      </div>
    </div>

    <!-- Forgot password modal -->
    <ForgotPasswordModal v-if="showForgot" @close="showForgot = false" />
  </div>
</template>
