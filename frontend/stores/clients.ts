import { defineStore } from "pinia";
import { useAuthStore } from "~/stores/auth";

export interface ClientType {
  id: number;
  nombre: string;
  slug: string;
}

export interface ClientProfile {
  id: number;
  cliente_id: string;
  nombre_cliente: string;
  tipo_nombre: string | null;
  cif: string;
  ciudad: string;
  pais: string;
  contrato_firmado: boolean;
  created_by_name: string | null;
  created_at: string;
}

export interface ClientProfileDetail extends ClientProfile {
  tipo_cliente: number | null;
  nombre_facturacion: string;
  email_facturacion: string;
  direccion_facturacion: string;
  codigo_postal: string;
  contrato_url: string | null;
}

export const useClientsStore = defineStore("clients", {
  state: () => ({
    list: [] as ClientProfile[],
    types: [] as ClientType[],
    isLoading: false,
    total: 0,
  }),

  actions: {
    async fetchTypes() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (this.types.length) return;
      const data = await $fetch<ClientType[]>(`${config.public.apiBase}/client-types/`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
      this.types = data;
    },

    async fetchList(params?: Record<string, string>) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;
      try {
        const query = new URLSearchParams({ page_size: "300", ...(params ?? {}) }).toString();
        const data = await $fetch<{ count: number; results: ClientProfile[] }>(
          `${config.public.apiBase}/clients/?${query}`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.list = data.results;
        this.total = data.count;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDetail(id: number | string): Promise<ClientProfileDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientProfileDetail>(`${config.public.apiBase}/clients/${id}/`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async create(formData: FormData): Promise<ClientProfileDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientProfileDetail>(`${config.public.apiBase}/clients/`, {
        method: "POST",
        body: formData,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },
  },
});
