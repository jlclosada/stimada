import { defineStore } from 'pinia';
import { useAuthStore } from '~/stores/auth';

export interface ProjectListItem {
  id: number;
  project_id: string;
  name: string;
  client_name: string;
  brand_name: string | null;
  status_name: string | null;
  service_type_name: string | null;
  economic_model_name: string | null;
  win_status_name: string | null;
  traffic_light: number | null;
  tax_base: string;
  taxes: string;
  total_price: string;
  sale_date: string | null;
  service_date: string | null;
  end_date: string | null;
  cm_selection_mode: string;
  content_maker_name: string | null;
  is_draft: boolean;
  is_active: boolean;
  created_at: string;
}

export interface FilterOption {
  id: number;
  name: string;
}

export interface ProjectFilters {
  statuses: FilterOption[];
  service_types: FilterOption[];
  economic_models: FilterOption[];
  product_logistics: FilterOption[];
  product_pickup: FilterOption[];
  who_records: FilterOption[];
  who_reviews: FilterOption[];
  who_publishes: FilterOption[];
  win_statuses: FilterOption[];
}

interface ProjectsState {
  list: ProjectListItem[];
  count: number;
  isLoading: boolean;
  filters: ProjectFilters;
}

export const useProjectsStore = defineStore('projects', {
  state: (): ProjectsState => ({
    list: [],
    count: 0,
    isLoading: false,
    filters: {
      statuses: [],
      service_types: [],
      economic_models: [],
      product_logistics: [],
      product_pickup: [],
      who_records: [],
      who_reviews: [],
      who_publishes: [],
      win_statuses: [],
    },
  }),

  actions: {
    async fetchList(params: Record<string, string> = {}, page = 1) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;

      try {
        const query = new URLSearchParams({
          page: String(page),
          page_size: '20',
          ...params,
        });
        const data = await $fetch<{
          count: number;
          results: ProjectListItem[];
        }>(`${config.public.apiBase}/projects/?${query}`, {
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        });
        this.list = data.results;
        this.count = data.count;
      } catch (err) {
        console.error('Error fetching projects:', err);
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
          { headers: { Authorization: `Bearer ${auth.accessToken}` } },
        );
        this.filters = data;
      } catch (err) {
        console.error('Error fetching project filters:', err);
      }
    },

    async createProject(payload: Record<string, unknown>) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      const data = await $fetch<ProjectListItem>(
        `${config.public.apiBase}/projects/`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: payload,
        },
      );
      return data;
    },
  },
});
