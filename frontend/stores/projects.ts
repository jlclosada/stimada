import { defineStore } from "pinia";
import { useAuthStore } from "~/stores/auth";

export interface ProjectListItem {
  id: number;
  project_id: string;
  nombre: string;
  client_name: string;
  brand_name: string | null;
  status_name: string | null;
  service_type_name: string | null;
  base_imponible: string;
  impuestos: string;
  precio_total: string;
  fecha_venta: string | null;
  fecha_servicio: string | null;
  fecha_fin: string | null;
  cm_selection_mode: string;
  content_maker_name: string | null;
  created_at: string;
}

export interface FilterOption {
  id: number;
  nombre: string;
}

export interface ProjectFilters {
  statuses: FilterOption[];
  service_types: FilterOption[];
}

interface ProjectsState {
  list: ProjectListItem[];
  count: number;
  isLoading: boolean;
  filters: ProjectFilters;
}

export const useProjectsStore = defineStore("projects", {
  state: (): ProjectsState => ({
    list: [],
    count: 0,
    isLoading: false,
    filters: { statuses: [], service_types: [] },
  }),

  actions: {
    async fetchList(params: Record<string, string> = {}, page = 1) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;

      try {
        const query = new URLSearchParams({ page: String(page), page_size: "20", ...params });
        const data = await $fetch<{ count: number; results: ProjectListItem[] }>(
          `${config.public.apiBase}/projects/?${query}`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.list = data.results;
        this.count = data.count;
      } catch (err) {
        console.error("Error fetching projects:", err);
      } finally {
        this.isLoading = false;
      }
    },

    async fetchFilters() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      try {
        const data = await $fetch<ProjectFilters>(
          `${config.public.apiBase}/projects/filters/`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.filters = data;
      } catch (err) {
        console.error("Error fetching project filters:", err);
      }
    },

    async createProject(payload: Record<string, unknown>) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      const data = await $fetch<ProjectListItem>(
        `${config.public.apiBase}/projects/`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: payload,
        }
      );
      return data;
    },
  },
});
