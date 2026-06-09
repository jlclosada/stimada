import { defineStore } from 'pinia';
import { useAuthStore } from '~/stores/auth';

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
  es_agencia: boolean;
  estado: string;
  semaforo_cliente: number | null;
  has_account: boolean;
  created_by_name: string | null;
  created_at: string;
}

export interface ClientBrand {
  id: number;
  brand_id: string;
  nombre: string;
  tipo_marca_nombre: string | null;
  web_instagram: string;
  estado: string;
}

export interface ClientProfileDetail extends ClientProfile {
  tipo_cliente: number | null;
  web_instagram: string;
  persona_contacto: string;
  email_contacto: string;
  telefono: string;
  nombre_facturacion: string;
  email_facturacion: string;
  direccion_facturacion: string;
  codigo_postal: string;
  contrato_url: string | null;
  notas_internas: string;
  user_email: string | null;
  user_name: string | null;
  has_account: boolean;
  marcas: ClientBrand[];
}

export const useClientsStore = defineStore('clients', {
  state: () => ({
    list: [] as ClientProfile[],
    types: [] as ClientType[],
    isLoading: false,
    total: 0,
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
  }),

  actions: {
    async fetchTypes() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (this.types.length) return;
      const data = await $fetch<ClientType[]>(
        `${config.public.apiBase}/client-types/`,
        {
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
      this.types = data;
    },

    async fetchList(params?: Record<string, string>, page?: number) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;
      try {
        const p = page ?? this.currentPage;
        const query = new URLSearchParams({
          page_size: String(this.pageSize),
          page: String(p),
          ...(params ?? {}),
        }).toString();
        const data = await $fetch<{ count: number; results: ClientProfile[] }>(
          `${config.public.apiBase}/clients/?${query}`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } },
        );
        this.list = data.results;
        this.total = data.count;
        this.currentPage = p;
        this.totalPages = Math.ceil(data.count / this.pageSize);
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDetail(id: number | string): Promise<ClientProfileDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientProfileDetail>(
        `${config.public.apiBase}/clients/${id}/`,
        {
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
    },

    async create(formData: FormData): Promise<ClientProfileDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientProfileDetail>(`${config.public.apiBase}/clients/`, {
        method: 'POST',
        body: formData,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async updateClient(
      id: number | string,
      data: Record<string, unknown>,
    ): Promise<ClientProfileDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientProfileDetail>(
        `${config.public.apiBase}/clients/${id}/`,
        {
          method: 'PATCH',
          body: data,
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
    },

    async deleteClient(id: number | string): Promise<void> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      await $fetch(`${config.public.apiBase}/clients/${id}/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async createClientAccount(
      id: number | string,
      data: { email: string; full_name?: string; password?: string },
    ): Promise<{
      detail: string;
      user: { id: number; email: string; full_name: string };
      password: string;
    }> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch(`${config.public.apiBase}/clients/${id}/create-account/`, {
        method: 'POST',
        body: data,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async createBrand(data: {
      client: number;
      nombre: string;
      tipo_marca?: number | null;
      web_instagram?: string;
    }): Promise<ClientBrand> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientBrand>(`${config.public.apiBase}/brands/`, {
        method: 'POST',
        body: data,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async updateBrand(
      id: number,
      data: Record<string, unknown>,
    ): Promise<ClientBrand> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ClientBrand>(`${config.public.apiBase}/brands/${id}/`, {
        method: 'PATCH',
        body: data,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async deleteBrand(id: number): Promise<void> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      await $fetch(`${config.public.apiBase}/brands/${id}/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },
  },
});
