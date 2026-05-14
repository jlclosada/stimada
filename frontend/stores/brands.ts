import { defineStore } from "pinia";
import { useAuthStore } from "~/stores/auth";

export interface BrandListItem {
  id: number;
  brand_id: string;
  nombre: string;
  client: number;
  client_name: string;
  tipo_marca: number | null;
  tipo_marca_nombre: string | null;
  web_instagram: string;
  estado: string;
  created_at: string;
}

export interface BrandProject {
  id: number;
  project_id: string;
  nombre: string;
  status_name: string | null;
  fecha_servicio: string | null;
  content_maker_name: string | null;
}

export interface BrandDetail extends BrandListItem {
  notas: string;
  proyectos: BrandProject[];
}

export const useBrandsStore = defineStore("brands", {
  state: () => ({
    list: [] as BrandListItem[],
    isLoading: false,
    total: 0,
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
  }),

  actions: {
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
        const data = await $fetch<{ count: number; results: BrandListItem[] }>(
          `${config.public.apiBase}/brands/?${query}`,
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

    async fetchDetail(id: number | string): Promise<BrandDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<BrandDetail>(`${config.public.apiBase}/brands/${id}/`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async create(data: Record<string, unknown>): Promise<BrandDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<BrandDetail>(`${config.public.apiBase}/brands/`, {
        method: "POST",
        body: data,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async update(id: number | string, data: Record<string, unknown>): Promise<BrandDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<BrandDetail>(`${config.public.apiBase}/brands/${id}/`, {
        method: "PATCH",
        body: data,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async deleteBrand(id: number | string): Promise<void> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      await $fetch(`${config.public.apiBase}/brands/${id}/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async searchClients(q: string): Promise<{ id: number; cliente_id: string; nombre_cliente: string; es_agencia: boolean; tipo_cliente: number | null; tipo_nombre: string | null; web_instagram: string }[]> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      const data = await $fetch<{ results: any[] }>(
        `${config.public.apiBase}/clients/?q=${encodeURIComponent(q)}&page_size=10`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      );
      return data.results;
    },
  },
});
