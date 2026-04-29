import { defineStore } from "pinia";
import { useAuthStore } from "~/stores/auth";

export interface ContentMaker {
  id: number;
  stimada_id: string;
  nombre_completo: string;
  nombre: string;
  apellidos: string;
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
}

export interface ContentMakerDetail extends ContentMaker {
  sexo: string;
  desempeno: string;
  calidad_contenido: string;
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
}

export const useContentMakersStore = defineStore("contentMakers", {
  state: () => ({
    list: [] as ContentMaker[],
    isLoading: false,
    total: 0,
  }),

  actions: {
    async fetchList(params?: Record<string, string>) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      this.isLoading = true;
      try {
        // Fetch all pages
        const baseParams = new URLSearchParams({ page_size: "300", ...(params ?? {}) });
        const data = await $fetch<{ count: number; results: ContentMaker[] }>(
          `${config.public.apiBase}/content-makers/?${baseParams.toString()}`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.list = data.results;
        this.total = data.count;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDetail(id: number | string): Promise<ContentMakerDetail> {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<ContentMakerDetail>(
        `${config.public.apiBase}/content-makers/${id}/`,
        { headers: { Authorization: `Bearer ${auth.accessToken}` } }
      );
    },

    async createAccount(id: number | string, email?: string) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch<{ user_id: number; email: string; password: string; detail: string }>(
        `${config.public.apiBase}/content-makers/${id}/create_account/`,
        {
          method: "POST",
          body: email ? { email } : {},
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        }
      );
    },

    async sendCredentials(id: number | string, email: string, password: string) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      return $fetch(
        `${config.public.apiBase}/content-makers/${id}/send_credentials/`,
        {
          method: "POST",
          body: { email, password },
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        }
      );
    },
  },
});
