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
  modalidad_economica_name: string | null;
  win_status_name: string | null;
  semaforo_proyecto: number | null;
  base_imponible: string;
  impuestos: string;
  precio_total: string;
  fecha_venta: string | null;
  fecha_servicio: string | null;
  fecha_fin: string | null;
  cm_selection_mode: string;
  content_maker_name: string | null;
  is_draft: boolean;
  is_active: boolean;
  created_at: string;
}

export interface FilterOption {
  id: number;
  nombre: string;
}

export interface ProjectFilters {
  statuses: FilterOption[];
  service_types: FilterOption[];
  modalidades_economicas: FilterOption[];
  logistica_producto: FilterOption[];
  recogida_producto: FilterOption[];
  quien_graba: FilterOption[];
  quien_revisa: FilterOption[];
  quien_publica: FilterOption[];
  win_statuses: FilterOption[];
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
    filters: {
      statuses: [],
      service_types: [],
      modalidades_economicas: [],
      logistica_producto: [],
      recogida_producto: [],
      quien_graba: [],
      quien_revisa: [],
      quien_publica: [],
      win_statuses: [],
    },
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
