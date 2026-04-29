import { defineStore } from "pinia";

interface UserInfo {
  id: number;
  email: string;
  full_name: string;
  role: string;
  avatar: string | null;
}

interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  stimada_employee: "Empleado Stimada",
  client: "Cliente",
  content_maker: "Content Maker",
};

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    isAdmin: (state) => state.user?.role === "admin",
    isEmployee: (state) => state.user?.role === "stimada_employee",
    isClient: (state) => state.user?.role === "client",
    isContentMaker: (state) => state.user?.role === "content_maker",
    canCreateUsers: (state) =>
      state.user?.role === "admin" || state.user?.role === "stimada_employee",
    userRole: (state) =>
      state.user ? (ROLE_LABELS[state.user.role] ?? state.user.role) : "",
  },

  actions: {
    async login(email: string, password: string) {
      this.isLoading = true;
      this.error = null;
      const config = useRuntimeConfig();

      try {
        const data = await $fetch<{
          access: string;
          refresh: string;
          user: UserInfo;
        }>(`${config.public.apiBase}/auth/login/`, {
          method: "POST",
          body: { email, password },
        });

        this.accessToken = data.access;
        this.refreshToken = data.refresh;
        this.user = data.user;

        localStorage.setItem("stimada_access", data.access);
        localStorage.setItem("stimada_refresh", data.refresh);
      } catch (err: unknown) {
        const fetchError = err as { data?: { non_field_errors?: string[]; detail?: string } };
        this.error =
          fetchError?.data?.non_field_errors?.[0] ??
          fetchError?.data?.detail ??
          "Error al iniciar sesión.";
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    async logout() {
      const config = useRuntimeConfig();
      if (this.refreshToken) {
        try {
          await $fetch(`${config.public.apiBase}/auth/logout/`, {
            method: "POST",
            body: { refresh: this.refreshToken },
            headers: { Authorization: `Bearer ${this.accessToken}` },
          });
        } catch {
          // Continuar aunque el server falle
        }
      }
      this.$reset();
      localStorage.removeItem("stimada_access");
      localStorage.removeItem("stimada_refresh");
      await navigateTo("/login");
    },

    async refreshTokens() {
      const config = useRuntimeConfig();
      const refresh = this.refreshToken ?? localStorage.getItem("stimada_refresh");
      if (!refresh) return false;

      try {
        const data = await $fetch<{ access: string; refresh: string }>(
          `${config.public.apiBase}/auth/refresh/`,
          { method: "POST", body: { refresh } }
        );
        this.accessToken = data.access;
        this.refreshToken = data.refresh;
        localStorage.setItem("stimada_access", data.access);
        localStorage.setItem("stimada_refresh", data.refresh);
        return true;
      } catch {
        this.$reset();
        localStorage.removeItem("stimada_access");
        localStorage.removeItem("stimada_refresh");
        return false;
      }
    },

    async fetchMe() {
      const config = useRuntimeConfig();
      const token = this.accessToken ?? localStorage.getItem("stimada_access");
      if (!token) return;

      try {
        const user = await $fetch<UserInfo>(`${config.public.apiBase}/auth/me/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        this.user = user;
        this.accessToken = token;
        this.refreshToken =
          this.refreshToken ?? localStorage.getItem("stimada_refresh");
      } catch {
        // Token expirado — intentar refresh
        const ok = await this.refreshTokens();
        if (ok) await this.fetchMe();
      }
    },

    clearError() {
      this.error = null;
    },

    initFromStorage() {
      if (import.meta.client) {
        this.accessToken = localStorage.getItem("stimada_access");
        this.refreshToken = localStorage.getItem("stimada_refresh");
      }
    },
  },
});
