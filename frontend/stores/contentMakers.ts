import { defineStore } from 'pinia';
import { useAuthStore } from '~/stores/auth';

export interface TipoChoice {
  value: string;
  label: string;
}

export interface ContentMaker {
  id: number;
  stimada_id: string;
  nombre_completo: string;
  nombre: string;
  apellidos: string;
  tipo: string;
  tipo_display: string;
  tipo_cm: string;
  status: string;
  categorias_contenido: string;
  instagram_handle: string;
  seguidores_instagram: number | null;
  tiktok_handle: string;
  seguidores_tiktok: number | null;
  tiene_cuenta: boolean;
  user_email: string | null;
  email: string;
  foto_url?: string | null;
}

export interface ContentMakerProject {
  id: number;
  project_id: string;
  nombre: string;
  brand_name: string | null;
  status_name: string | null;
  fecha_servicio: string | null;
}

export interface DesempenoOption {
  id: number;
  nombre: string;
}

export interface ContentMakerDetail extends ContentMaker {
  sexo: string;
  desempeno: string;
  calidad_contenido: number | null;
  desempeno_opciones: number[];
  desempeno_opciones_display: DesempenoOption[];
  apariencia: string;
  es_mama: boolean;
  sigue_stimada: boolean;
  stimada_en_bio: boolean;
  contrato_firmado: boolean;
  fee_instagram: string | null;
  categoria_seguidores_ig: string;
  link_instagram: string;
  fee_tiktok: string | null;
  categoria_seguidores_tt: string;
  link_tiktok: string;
  talla_arriba: string;
  talla_abajo: string;
  talla_pie: string;
  altura_medidas: string;
  comentarios: string;
  telefono: string;
  direccion_facturacion: string;
  codigo_postal: string;
  provincia: string;
  pais: string;
  dni_cif: string;
  iban: string;
  user_id: number | null;
  foto: string | null;
  foto_url: string | null;
  proyectos_asociados: ContentMakerProject[];
}

export const useContentMakersStore = defineStore('contentMakers', {
  state: () => ({
    list: [] as ContentMaker[],
    isLoading: false,
    total: 0,
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
    filterOptions: {
      statuses: [] as string[],
      tipos: [] as string[],
      tipo_choices: [] as TipoChoice[],
      sexos: [] as string[],
      calidad_contenido: [] as string[],
      apariencia: [] as string[],
      categoria_seguidores_ig: [] as string[],
      categoria_seguidores_tt: [] as string[],
    },
    desempenoOptions: [] as DesempenoOption[],
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

    async fetchDesempenoOptions() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (this.desempenoOptions.length) return;
      const data = await $fetch<DesempenoOption[]>(
        `${config.public.apiBase}/content-makers/desempeno_options/`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } },
      );
      this.desempenoOptions = data;
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
