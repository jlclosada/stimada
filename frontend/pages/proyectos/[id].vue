<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useProjectsStore } from "~/stores/projects";

definePageMeta({
  layout: "app",
  middleware: ["auth"],
});

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const projectsStore = useProjectsStore();
const config = useRuntimeConfig();

const project = ref<any>(null);
const isLoading = ref(true);
const actionLoading = ref(false);

const isContentMaker = computed(() => auth.user?.role === "content_maker");
const isClient = computed(() => auth.user?.role === "client");
const isAdminOrEmployee = computed(() =>
  auth.user?.role === "admin" || auth.user?.role === "stimada_employee"
);

// Edit mode
const isEditing = ref(false);
const editForm = ref<any>({});
const saving = ref(false);
const showDeleteConfirm = ref(false);

function startEdit() {
  editForm.value = {
    nombre: project.value.nombre,
    descripcion: project.value.descripcion || "",
    base_imponible: project.value.base_imponible,
    impuestos: project.value.impuestos,
    fecha_venta: project.value.fecha_venta || "",
    fecha_servicio: project.value.fecha_servicio || "",
    fecha_fin: project.value.fecha_fin || "",
    status: project.value.status,
    service_type: project.value.service_type,
  };
  isEditing.value = true;
}

function cancelEdit() {
  isEditing.value = false;
}

async function saveEdit() {
  saving.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: {
        nombre: editForm.value.nombre,
        descripcion: editForm.value.descripcion,
        base_imponible: editForm.value.base_imponible,
        impuestos: editForm.value.impuestos,
        fecha_venta: editForm.value.fecha_venta || null,
        fecha_servicio: editForm.value.fecha_servicio || null,
        fecha_fin: editForm.value.fecha_fin || null,
        status: editForm.value.status || null,
        service_type: editForm.value.service_type || null,
      },
    });
    isEditing.value = false;
    await loadProject();
  } catch {
    // silent
  } finally {
    saving.value = false;
  }
}

async function unlinkCM() {
  actionLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { content_maker: null },
    });
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

async function deleteProject() {
  actionLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    router.push("/proyectos");
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

// Check if the CM has a pending decision on this project
const cmParticipation = computed(() => {
  if (!isContentMaker.value || !project.value) return null;
  return project.value.content_makers?.find(
    (cm: any) => cm.user_id === auth.user?.id
  );
});

const cmNeedToRespond = computed(() => {
  if (!cmParticipation.value) return false;
  return cmParticipation.value.status === "pending";
});

// Client needs to select a CM?
const clientNeedsToSelectCM = computed(() => {
  if (!isClient.value || !project.value) return false;
  if (project.value.content_maker_name) return false; // already has definitive CM
  const mode = project.value.cm_selection_mode;
  if (mode !== "client_chooses" && mode !== "recommended") return false;
  // Check if there's any pending CM already selected by client (waiting for response)
  const hasPending = project.value.content_makers?.some(
    (cm: any) => cm.status === "pending"
  );
  return !hasPending;
});

const clientWaitingForCM = computed(() => {
  if (!isClient.value || !project.value) return false;
  if (project.value.content_maker_name) return false;
  return project.value.content_makers?.some(
    (cm: any) => cm.status === "pending"
  );
});

// CM search for client selection
const cmSearchQuery = ref("");
const cmSearchResults = ref<any[]>([]);
const cmSearching = ref(false);

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

function onCMSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(async () => {
    if (!cmSearchQuery.value.trim()) {
      cmSearchResults.value = [];
      return;
    }
    cmSearching.value = true;
    try {
      cmSearchResults.value = await $fetch<any[]>(
        `${config.public.apiBase}/projects/search_cms/`,
        {
          params: { q: cmSearchQuery.value },
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        }
      );
    } catch {
      cmSearchResults.value = [];
    } finally {
      cmSearching.value = false;
    }
  }, 300);
}

async function selectCM(cmId: number) {
  actionLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/select_cm/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { content_maker_id: cmId },
    });
    cmSearchQuery.value = "";
    cmSearchResults.value = [];
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

async function loadProject() {
  isLoading.value = true;
  try {
    project.value = await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
  } catch {
    project.value = null;
  } finally {
    isLoading.value = false;
  }
}

async function acceptProject() {
  actionLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/accept/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

async function rejectProject() {
  actionLoading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/reject/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

function formatDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-600 border-red-200",
  selected: "bg-blue-50 text-blue-700 border-blue-200",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  accepted: "Aceptada",
  rejected: "Rechazada",
  selected: "Seleccionada",
};

onMounted(() => {
  loadProject();
  if (isAdminOrEmployee.value) {
    projectsStore.fetchFilters();
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-8 py-10 animate-fade-up">
    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center items-center h-64">
      <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
    </div>

    <!-- Not found -->
    <div v-else-if="!project" class="text-center py-20">
      <p class="text-muted">Proyecto no encontrado</p>
      <NuxtLink to="/proyectos" class="text-sm text-gold mt-4 inline-block">← Volver a proyectos</NuxtLink>
    </div>

    <!-- Project Detail -->
    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between mb-8">
        <div>
          <NuxtLink to="/proyectos" class="text-xs text-muted hover:text-gold transition-colors mb-2 inline-flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
            Proyectos
          </NuxtLink>
          <h1 class="text-2xl font-semibold text-ink mt-1">{{ project.nombre }}</h1>
          <p class="text-sm text-muted mt-1">{{ project.project_id }} · {{ project.client_name }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span
            v-if="project.status_name"
            class="px-3 py-1 rounded-lg text-xs font-medium"
            :class="{
              'bg-emerald-50 text-emerald-700': project.status_name === 'Activo',
              'bg-amber-50 text-amber-700': project.status_name === 'Pendiente',
              'bg-gray-100 text-gray-600': project.status_name === 'Finalizado',
            }"
          >{{ project.status_name }}</span>
          <button
            v-if="isAdminOrEmployee && !isEditing"
            class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
            @click="startEdit"
          >
            Editar
          </button>
          <button
            v-if="isAdminOrEmployee && !isEditing"
            class="px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 text-red-500 hover:bg-red-50 transition-all"
            @click="showDeleteConfirm = true"
          >
            Eliminar
          </button>
        </div>
      </div>

      <!-- Delete Confirmation -->
      <div v-if="showDeleteConfirm" class="rounded-2xl border border-red-200 bg-red-50/50 p-6 mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-red-700">¿Eliminar este proyecto?</h3>
            <p class="text-xs text-red-600 mt-1">Esta acción no se puede deshacer.</p>
          </div>
          <div class="flex items-center gap-3">
            <button
              class="px-4 py-2 rounded-xl text-sm font-medium border border-border/60 text-muted hover:text-ink transition-all"
              @click="showDeleteConfirm = false"
            >
              Cancelar
            </button>
            <button
              :disabled="actionLoading"
              class="px-4 py-2 rounded-xl text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-all disabled:opacity-50"
              @click="deleteProject"
            >
              Confirmar eliminación
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Form -->
      <div v-if="isEditing" class="rounded-2xl border border-gold/30 bg-gold/5 p-6 mb-8 space-y-5">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-ink">Editar proyecto</h3>
          <div class="flex items-center gap-2">
            <button class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all" @click="cancelEdit">
              Cancelar
            </button>
            <button
              :disabled="saving"
              class="px-4 py-1.5 rounded-lg text-xs font-medium bg-gold text-white hover:bg-gold/90 transition-all disabled:opacity-50"
              @click="saveEdit"
            >
              Guardar
            </button>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="text-[11px] text-muted font-medium mb-1 block">Nombre</label>
            <input v-model="editForm.nombre" type="text" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div class="md:col-span-2">
            <label class="text-[11px] text-muted font-medium mb-1 block">Descripción</label>
            <textarea v-model="editForm.descripcion" rows="3" class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Base imponible (€)</label>
            <input v-model="editForm.base_imponible" type="number" step="0.01" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Impuestos (€)</label>
            <input v-model="editForm.impuestos" type="number" step="0.01" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Fecha de venta</label>
            <input v-model="editForm.fecha_venta" type="date" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Fecha de servicio</label>
            <input v-model="editForm.fecha_servicio" type="date" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Fecha fin</label>
            <input v-model="editForm.fecha_fin" type="date" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40" />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block">Estado</label>
            <select v-model="editForm.status" class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40">
              <option :value="null">Sin estado</option>
              <option v-for="s in projectsStore.filters.statuses" :key="s.id" :value="s.id">{{ s.nombre }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- CM Action Banner (for Content Makers with pending response) -->
      <div
        v-if="cmNeedToRespond"
        class="rounded-2xl border border-gold/30 bg-gold/5 p-6 mb-8"
      >
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-ink">¿Aceptas este proyecto?</h3>
            <p class="text-xs text-muted mt-1">Tienes una solicitud pendiente para participar en esta campaña.</p>
          </div>
          <div class="flex items-center gap-3">
            <button
              :disabled="actionLoading"
              class="px-4 py-2 rounded-xl text-sm font-medium border border-red-200 text-red-600 hover:bg-red-50 transition-all duration-200 disabled:opacity-50"
              @click="rejectProject"
            >
              Rechazar
            </button>
            <button
              :disabled="actionLoading"
              class="px-5 py-2 rounded-xl text-sm font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all duration-200 disabled:opacity-50"
              @click="acceptProject"
            >
              Aceptar
            </button>
          </div>
        </div>
      </div>

      <!-- Info Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- Details Card -->
        <div class="rounded-2xl border border-border/60 bg-white p-6 space-y-4">
          <h2 class="text-sm font-semibold text-ink">Detalles del proyecto</h2>
          <div class="space-y-3 text-xs">
            <div class="flex justify-between"><span class="text-muted">Tipo de servicio</span><span class="text-ink font-medium">{{ project.service_type_name || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-muted">Base imponible</span><span class="text-ink font-medium">{{ project.base_imponible }} €</span></div>
            <div class="flex justify-between"><span class="text-muted">Impuestos</span><span class="text-ink font-medium">{{ project.impuestos }} €</span></div>
            <div class="flex justify-between border-t border-border/40 pt-3"><span class="text-muted font-medium">Total</span><span class="text-ink font-bold">{{ project.precio_total }} €</span></div>
          </div>
        </div>

        <!-- Dates Card -->
        <div class="rounded-2xl border border-border/60 bg-white p-6 space-y-4">
          <h2 class="text-sm font-semibold text-ink">Fechas</h2>
          <div class="space-y-3 text-xs">
            <div class="flex justify-between"><span class="text-muted">Fecha de venta</span><span class="text-ink font-medium">{{ formatDate(project.fecha_venta) }}</span></div>
            <div class="flex justify-between"><span class="text-muted">Fecha de servicio</span><span class="text-ink font-medium">{{ formatDate(project.fecha_servicio) }}</span></div>
            <div class="flex justify-between"><span class="text-muted">Fecha fin</span><span class="text-ink font-medium">{{ formatDate(project.fecha_fin) }}</span></div>
            <div class="flex justify-between"><span class="text-muted">Creado</span><span class="text-ink font-medium">{{ formatDate(project.created_at) }}</span></div>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="project.descripcion" class="rounded-2xl border border-border/60 bg-white p-6 mb-8">
        <h2 class="text-sm font-semibold text-ink mb-3">Descripción</h2>
        <p class="text-sm text-muted leading-relaxed">{{ project.descripcion }}</p>
      </div>

      <!-- Content Maker Section -->
      <div class="rounded-2xl border border-border/60 bg-white p-6 mb-8">
        <h2 class="text-sm font-semibold text-ink mb-4">Content Maker</h2>

        <!-- Assigned CM -->
        <div v-if="project.content_maker_name" class="flex items-center justify-between p-3 rounded-xl bg-emerald-50/50 border border-emerald-200/50">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ project.content_maker_name }}</p>
              <p class="text-[11px] text-emerald-600">Asignada al proyecto</p>
            </div>
          </div>
          <button
            v-if="isAdminOrEmployee"
            :disabled="actionLoading"
            class="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-red-200 text-red-500 hover:bg-red-50 transition-all disabled:opacity-50"
            @click="unlinkCM"
          >
            Desvincular
          </button>
        </div>

        <!-- Client waiting for CM response -->
        <div v-else-if="clientWaitingForCM" class="rounded-xl bg-amber-50/50 border border-amber-200/50 p-4">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center">
              <svg class="w-4 h-4 text-amber-600 animate-pulse" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-ink">Esperando respuesta de la Content Maker</p>
              <p class="text-[11px] text-amber-600">La Content Maker seleccionada debe confirmar su participación.</p>
            </div>
          </div>
        </div>

        <!-- Client CM Selector (client_chooses mode, no CM assigned, no pending) -->
        <div v-else-if="clientNeedsToSelectCM" class="space-y-4">
          <div class="rounded-xl bg-blue-50/50 border border-blue-200/50 p-4 mb-4">
            <p class="text-sm font-medium text-ink">Elige una Content Maker para este proyecto</p>
            <p class="text-[11px] text-blue-600 mt-1">Busca por nombre o usuario de Instagram y selecciona a la Content Maker que quieres para esta campaña.</p>
          </div>

          <!-- Search input -->
          <div class="relative">
            <div class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg class="w-4 h-4 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
            </div>
            <input
              v-model="cmSearchQuery"
              type="text"
              placeholder="Buscar content maker por nombre o Instagram..."
              class="w-full h-10 pl-10 pr-4 rounded-xl border border-border/60 bg-panel/30 text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 transition-all"
              @input="onCMSearchInput"
            />
          </div>

          <!-- Search results -->
          <div v-if="cmSearching" class="flex justify-center py-4">
            <div class="w-5 h-5 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
          </div>
          <div v-else-if="cmSearchResults.length > 0" class="space-y-2 max-h-64 overflow-auto">
            <div
              v-for="cm in cmSearchResults"
              :key="cm.id"
              class="flex items-center justify-between p-3 rounded-xl border border-border/40 bg-panel/30 hover:border-gold/40 transition-all cursor-pointer"
            >
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-panel flex items-center justify-center text-[10px] font-bold text-muted">
                  {{ cm.nombre?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) }}
                </div>
                <div>
                  <p class="text-xs font-medium text-ink">{{ cm.nombre }}</p>
                  <p v-if="cm.instagram_handle" class="text-[10px] text-muted">@{{ cm.instagram_handle }} · {{ cm.seguidores_instagram?.toLocaleString() }} seg.</p>
                </div>
              </div>
              <button
                :disabled="actionLoading"
                class="px-3 py-1.5 rounded-lg text-[11px] font-medium bg-gold text-white hover:bg-gold/90 transition-all disabled:opacity-50"
                @click="selectCM(cm.id)"
              >
                Seleccionar
              </button>
            </div>
          </div>
          <div v-else-if="cmSearchQuery.trim() && !cmSearching" class="text-center py-4">
            <p class="text-xs text-muted">No se encontraron resultados</p>
          </div>
        </div>

        <!-- CM candidates (visible to admins/employees) -->
        <div v-if="isAdminOrEmployee && project.content_makers?.length" class="mt-4 space-y-2">
          <p class="text-xs text-muted font-medium mb-2">Candidatas / Recomendadas:</p>
          <div
            v-for="cm in project.content_makers"
            :key="cm.id"
            class="flex items-center justify-between p-3 rounded-xl border border-border/40 bg-panel/30"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-panel flex items-center justify-center text-[10px] font-bold text-muted">
                {{ cm.nombre?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) }}
              </div>
              <div>
                <p class="text-xs font-medium text-ink">{{ cm.nombre }}</p>
                <p v-if="cm.instagram_handle" class="text-[10px] text-muted">@{{ cm.instagram_handle }}</p>
              </div>
            </div>
            <span
              class="px-2 py-0.5 rounded-md text-[10px] font-medium border"
              :class="STATUS_COLORS[cm.status] || 'bg-gray-50 text-gray-600 border-gray-200'"
            >{{ STATUS_LABELS[cm.status] || cm.status }}</span>
          </div>
        </div>

        <!-- No CM yet (only for admin when no candidates) -->
        <div v-if="!project.content_maker_name && !project.content_makers?.length && !clientNeedsToSelectCM && !clientWaitingForCM" class="text-center py-6">
          <p class="text-xs text-muted">Aún no se ha asignado una Content Maker</p>
        </div>
      </div>

      <!-- Client info (visible to admin/employee) -->
      <div v-if="isAdminOrEmployee" class="rounded-2xl border border-border/60 bg-white p-6">
        <h2 class="text-sm font-semibold text-ink mb-3">Cliente</h2>
        <div class="space-y-2 text-xs">
          <div class="flex justify-between"><span class="text-muted">Nombre</span><span class="text-ink font-medium">{{ project.client_name }}</span></div>
          <div v-if="project.brand_name" class="flex justify-between"><span class="text-muted">Marca</span><span class="text-ink font-medium">{{ project.brand_name }}</span></div>
          <div v-if="project.created_by_name" class="flex justify-between"><span class="text-muted">Creado por</span><span class="text-ink font-medium">{{ project.created_by_name }}</span></div>
        </div>
      </div>
    </template>
  </div>
</template>
