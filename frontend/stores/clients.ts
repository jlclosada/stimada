import { defineStore } from 'pinia';
import { useAuthStore } from '~/stores/auth';

export interface ClientType {
  id: number;
  name: string;
  slug: string;
}

export interface ClientProfile {
  id: number;
  client_id: string;
  name: string;
  type_name: string | null;
  cif: string;
  city: string;
  country: string;
  contract_signed: boolean;
  is_agency: boolean;
  status: string;
  traffic_light: number | null;
  has_account: boolean;
  created_by_name: string | null;
  created_at: string;
}

export interface ClientBrand {
  id: number;
  brand_id: string;
  name: string;
  brand_type_name: string | null;
  web_instagram: string;
  status: string;
}

export interface ClientProfileDetail extends ClientProfile {
  client_type: number | null;
  web_instagram: string;
  contact_person: string;
  contact_email: string;
  phone: string;
  billing_name: string;
  billing_email: string;
  billing_address: string;
  postal_code: string;
  contract_url: string | null;
  internal_notes: string;
  user_email: string | null;
  user_name: string | null;
  has_account: boolean;
  brands: ClientBrand[];
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
      name: string;
      brand_type?: number | null;
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
