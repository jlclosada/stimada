import { defineStore } from 'pinia';
import { useAuthStore } from '~/stores/auth';

export interface TypeChoice {
  value: string;
  label: string;
}

export interface ContentMaker {
  id: number;
  stimada_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  type: string;
  type_display: string;
  cm_type: string;
  status: string;
  content_categories: string;
  instagram_handle: string;
  instagram_followers: number | null;
  tiktok_handle: string;
  tiktok_followers: number | null;
  has_account: boolean;
  user_email: string | null;
  email: string;
  photo_url?: string | null;
}

export interface ContentMakerProject {
  id: number;
  project_id: string;
  name: string;
  brand_name: string | null;
  status_name: string | null;
  service_date: string | null;
}

export interface PerformanceOption {
  id: number;
  name: string;
}

export interface ContentMakerDetail extends ContentMaker {
  gender: string;
  performance: string;
  content_quality: number | null;
  performance_options: number[];
  performance_options_display: PerformanceOption[];
  appearance: string;
  is_mother: boolean;
  follows_stimada: boolean;
  stimada_in_bio: boolean;
  contract_signed: boolean;
  fee_instagram: string | null;
  instagram_followers_category: string;
  instagram_link: string;
  fee_tiktok: string | null;
  tiktok_followers_category: string;
  tiktok_link: string;
  top_size: string;
  bottom_size: string;
  shoe_size: string;
  height_measurements: string;
  comments: string;
  phone: string;
  billing_address: string;
  postal_code: string;
  province: string;
  country: string;
  dni_cif: string;
  iban: string;
  user_id: number | null;
  photo: string | null;
  photo_url: string | null;
  associated_projects: ContentMakerProject[];
}

export const useContentMakersStore = defineStore('contentMakers', {
  state: () => ({
    list: [] as ContentMaker[],
    isLoading: false,
    total: 0,
    currentPage: 1,
    pageSize: 24,
    totalPages: 1,
    filterOptions: {
      statuses: [] as string[],
      types: [] as string[],
      type_choices: [] as TypeChoice[],
      genders: [] as string[],
      content_quality: [] as string[],
      appearance: [] as string[],
      instagram_followers_category: [] as string[],
      tiktok_followers_category: [] as string[],
    },
    performanceOptions: [] as PerformanceOption[],
  }),

  actions: {
    async fetchFilters() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (this.filterOptions.statuses.length) return;
      const data = await $fetch<typeof this.filterOptions>(
        `${config.public.apiBase}/content-makers/filters/`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      );
      this.filterOptions = data;
    },

    async fetchPerformanceOptions() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (this.performanceOptions.length) return;
      const data = await $fetch<PerformanceOption[]>(
        `${config.public.apiBase}/content-makers/performance_options/`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      );
      this.performanceOptions = data;
    },

    async fetchList(params?: Record<string, string>, page?: number) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;
      try {
        const p = page ?? this.currentPage;
        const baseParams = new URLSearchParams({
          page_size: String(this.pageSize),
          page: String(p),
          ...(params ?? {}),
        });
        const data = await $fetch<{ count: number; results: ContentMaker[] }>(
          `${config.public.apiBase}/content-makers/?${baseParams.toString()}`,
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

    async fetchDetail(id: number | string): Promise<ContentMakerDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ContentMakerDetail>(
        `${config.public.apiBase}/content-makers/${id}/`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      );
    },

    async createAccount(id: number | string, email?: string) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<{
        user_id: number;
        email: string;
        password: string;
        detail: string;
      }>(`${config.public.apiBase}/content-makers/${id}/create_account/`, {
        method: 'POST',
        body: email ? { email } : {},
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },

    async sendCredentials(
      id: number | string,
      email: string,
      password: string,
    ) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch(
        `${config.public.apiBase}/content-makers/${id}/send_credentials/`,
        {
          method: 'POST',
          body: { email, password },
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
    },

    async updateContentMaker(
      id: number | string,
      data: Partial<ContentMakerDetail>,
    ) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ContentMakerDetail>(
        `${config.public.apiBase}/content-makers/${id}/`,
        {
          method: 'PATCH',
          body: data,
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
    },

    async deleteContentMaker(id: number | string) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      await $fetch(`${config.public.apiBase}/content-makers/${id}/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
    },
  },
});
