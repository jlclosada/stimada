<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import { useProjectsStore } from '~/stores/projects';
import { formatProjectId } from '~/utils/formatId';

definePageMeta({
  layout: 'app',
  middleware: ['auth'],
});

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const projectsStore = useProjectsStore();
const config = useRuntimeConfig();

const project = ref<any>(null);
const isLoading = ref(true);
const actionLoading = ref(false);

const isContentMaker = computed(() => auth.user?.role === 'content_maker');
const isClient = computed(() => auth.user?.role === 'client');
const isAdminOrEmployee = computed(
  () => auth.user?.role === 'admin' || auth.user?.role === 'stimada_employee',
);

// Edit mode
const isEditing = ref(false);
const editForm = ref<any>({});
const saving = ref(false);
const showDeleteConfirm = ref(false);

// Edit mode - CM selection
const editSelectedCMs = ref<
  { id: number; nombre: string; instagram_handle: string }[]
>([]);
const editRecommendedCMs = ref<
  { id: number; nombre: string; instagram_handle: string }[]
>([]);
const editCMSearch = ref('');
const editCMResults = ref<any[]>([]);
const editCMSearching = ref(false);

let editCMSearchTimeout: ReturnType<typeof setTimeout> | null = null;

function onEditCMSearch() {
  if (editCMSearchTimeout) clearTimeout(editCMSearchTimeout);
  editCMSearchTimeout = setTimeout(async () => {
    if (!editCMSearch.value.trim()) {
      editCMResults.value = [];
      return;
    }
    editCMSearching.value = true;
    try {
      const data = await $fetch<{ results: any[] }>(
        `${config.public.apiBase}/content-makers/`,
        {
          params: { q: editCMSearch.value, page_size: 10 },
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        },
      );
      editCMResults.value = data.results;
    } catch {
      editCMResults.value = [];
    } finally {
      editCMSearching.value = false;
    }
  }, 300);
}

function addEditDefinedCM(cm: any) {
  if (!editSelectedCMs.value.find((r) => r.id === cm.id)) {
    editSelectedCMs.value.push({
      id: cm.id,
      nombre: `${cm.nombre} ${cm.apellidos}`.trim(),
      instagram_handle: cm.instagram_handle || '',
    });
  }
  editCMSearch.value = '';
  editCMResults.value = [];
}

function removeEditDefinedCM(id: number) {
  editSelectedCMs.value = editSelectedCMs.value.filter((r) => r.id !== id);
}

function addEditRecommendedCM(cm: any) {
  if (!editRecommendedCMs.value.find((r) => r.id === cm.id)) {
    editRecommendedCMs.value.push({
      id: cm.id,
      nombre: `${cm.nombre} ${cm.apellidos}`.trim(),
      instagram_handle: cm.instagram_handle || '',
    });
  }
  editCMSearch.value = '';
  editCMResults.value = [];
}

function removeEditRecommendedCM(id: number) {
  editRecommendedCMs.value = editRecommendedCMs.value.filter(
    (r) => r.id !== id,
  );
}

// Confirmation modal
const confirmAction = ref<{
  show: boolean;
  title: string;
  message: string;
  action: (() => Promise<void>) | null;
}>({ show: false, title: '', message: '', action: null });

async function executeConfirmAction() {
  if (confirmAction.value.action) {
    await confirmAction.value.action();
  }
  confirmAction.value = { show: false, title: '', message: '', action: null };
}

function cancelConfirmAction() {
  confirmAction.value = { show: false, title: '', message: '', action: null };
}

function startEdit() {
  editForm.value = {
    nombre: project.value.nombre,
    descripcion: project.value.descripcion || '',
    base_imponible: project.value.base_imponible,
    impuestos: project.value.impuestos,
    fecha_venta: project.value.fecha_venta || '',
    fecha_servicio: project.value.fecha_servicio || '',
    fecha_fin: project.value.fecha_fin || '',
    status: project.value.status,
    service_type: project.value.service_type,
    cm_selection_mode: project.value.cm_selection_mode || 'client_chooses',
  };
  // Populate selected CMs from current project content_makers
  editSelectedCMs.value = [];
  editRecommendedCMs.value = [];
  if (project.value.content_makers) {
    for (const cm of project.value.content_makers) {
      const entry = {
        id: cm.content_maker_id,
        nombre: cm.nombre,
        instagram_handle: cm.instagram_handle || '',
      };
      if (cm.is_recommended || cm.status === 'recommended') {
        editRecommendedCMs.value.push(entry);
      } else if (cm.status === 'pending' || cm.status === 'accepted') {
        editSelectedCMs.value.push(entry);
      }
    }
  }
  isEditing.value = true;
}

function cancelEdit() {
  isEditing.value = false;
}

async function saveEdit() {
  saving.value = true;
  try {
    const body: Record<string, unknown> = {
      nombre: editForm.value.nombre,
      descripcion: editForm.value.descripcion,
      base_imponible: editForm.value.base_imponible,
      impuestos: editForm.value.impuestos,
      fecha_venta: editForm.value.fecha_venta || null,
      fecha_servicio: editForm.value.fecha_servicio || null,
      fecha_fin: editForm.value.fecha_fin || null,
      status: editForm.value.status || null,
      service_type: editForm.value.service_type || null,
      cm_selection_mode: editForm.value.cm_selection_mode,
      is_draft: false,
    };

    // Include CM data based on selection mode
    if (editForm.value.cm_selection_mode === 'defined') {
      body.defined_cms = editSelectedCMs.value.map((c) => c.id);
    } else if (editForm.value.cm_selection_mode === 'recommended') {
      body.recommended_cms = editRecommendedCMs.value.map((c) => c.id);
    }

    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body,
    });
    isEditing.value = false;
    await loadProject();
  } catch {
    // silent
  } finally {
    saving.value = false;
  }
}

async function unlinkCM(cmId: number) {
  actionLoading.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/unlink_cm/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { content_maker_id: cmId },
      },
    );
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
      method: 'DELETE',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    router.push('/proyectos');
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
    (cm: any) => cm.user_id === auth.user?.id,
  );
});

const cmNeedToRespond = computed(() => {
  if (!cmParticipation.value) return false;
  return cmParticipation.value.status === 'pending';
});

// Client needs to select a CM?
const clientNeedsToSelectCM = computed(() => {
  if (!isClient.value || !project.value) return false;
  const mode = project.value.cm_selection_mode;
  if (mode !== 'client_chooses' && mode !== 'recommended') return false;
  return true;
});

const clientWaitingForCM = computed(() => {
  if (!isClient.value || !project.value) return false;
  return (
    project.value.content_makers?.some((cm: any) => cm.status === 'pending') ||
    false
  );
});

// Track CMs selected during current browser session
const selectedCMIds = ref<number[]>([]);

// CM browser for client selection
const showCMBrowser = ref(false);
const cmBrowserResults = ref<any[]>([]);
const cmBrowserLoading = ref(false);
const cmBrowserSearch = ref('');
const selectedCMProfile = ref<any>(null);

let cmBrowserTimeout: ReturnType<typeof setTimeout> | null = null;

async function openCMBrowser() {
  showCMBrowser.value = true;
  selectedCMProfile.value = null;
  cmBrowserSearch.value = '';
  await loadCMBrowserResults();
}

async function loadCMBrowserResults() {
  cmBrowserLoading.value = true;
  try {
    cmBrowserResults.value = await $fetch<any[]>(
      `${config.public.apiBase}/projects/search_cms/`,
      {
        params: { q: cmBrowserSearch.value },
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
  } catch {
    cmBrowserResults.value = [];
  } finally {
    cmBrowserLoading.value = false;
  }
}

function onCMBrowserSearchInput() {
  if (cmBrowserTimeout) clearTimeout(cmBrowserTimeout);
  cmBrowserTimeout = setTimeout(() => {
    loadCMBrowserResults();
  }, 300);
}

function viewCMProfile(cm: any) {
  selectedCMProfile.value = cm;
}

function backToGrid() {
  selectedCMProfile.value = null;
}

async function selectCM(cmId: number) {
  showCMBrowser.value = false;
  selectedCMProfile.value = null;
  confirmAction.value = {
    show: true,
    title: 'Confirmar selección',
    message: `¿Estás seguro de elegir a esta Content Maker para tu campaña? Se le enviará una invitación y deberá aceptar para confirmar su participación.`,
    action: async () => {
      actionLoading.value = true;
      try {
        await $fetch(
          `${config.public.apiBase}/projects/${route.params.id}/select_cm/`,
          {
            method: 'POST',
            headers: { Authorization: `Bearer ${auth.accessToken}` },
            body: { content_maker_id: cmId },
          },
        );
        selectedCMIds.value.push(cmId);
        await loadProject();
      } catch {
        // silent
      } finally {
        actionLoading.value = false;
      }
    },
  };
}

async function loadProject() {
  isLoading.value = true;
  try {
    project.value = await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/`,
      {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
  } catch {
    project.value = null;
  } finally {
    isLoading.value = false;
  }
}

async function acceptProject() {
  confirmAction.value = {
    show: true,
    title: 'Confirmar aceptación',
    message: `¿Estás seguro de que quieres aceptar esta campaña? Al confirmar, te comprometes a participar en el proyecto.`,
    action: async () => {
      actionLoading.value = true;
      try {
        await $fetch(
          `${config.public.apiBase}/projects/${route.params.id}/accept/`,
          {
            method: 'POST',
            headers: { Authorization: `Bearer ${auth.accessToken}` },
          },
        );
        await loadProject();
      } catch {
        // silent
      } finally {
        actionLoading.value = false;
      }
    },
  };
}

async function rejectProject() {
  actionLoading.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/reject/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

function formatDate(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

const STATUS_COLORS: Record<string, string> = {
  recommended: 'bg-gold/10 text-gold border-gold/30',
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  accepted: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-50 text-red-600 border-red-200',
  selected: 'bg-blue-50 text-blue-700 border-blue-200',
};

const STATUS_LABELS: Record<string, string> = {
  recommended: 'Recomendada',
  pending: 'Pendiente',
  accepted: 'Aceptada',
  rejected: 'Rechazada',
  selected: 'Seleccionada',
};

// Briefing
const acceptedCMs = computed(() => {
  if (!project.value) return [];
  return (
    project.value.content_makers?.filter(
      (cm: any) => cm.status === 'accepted',
    ) || []
  );
});

const needsBriefing = computed(() => {
  if (!project.value) return false;
  // Show briefing section whenever there are accepted CMs without a briefing yet
  const hasAccepted = acceptedCMs.value.length > 0;
  const hasPendingBriefings = acceptedCMs.value.some(
    (cm: any) => !hasBriefing(cm.content_maker_id),
  );
  return hasAccepted && hasPendingBriefings;
});

// For each accepted CM, check if a briefing already exists
function hasBriefing(cmId: number) {
  return project.value?.briefings?.some((b: any) => b.content_maker === cmId);
}

function getBriefing(cmId: number) {
  return project.value?.briefings?.find((b: any) => b.content_maker === cmId);
}

// Briefing form per CM
const briefingForms = ref<
  Record<
    number,
    { links: { url: string; titulo: string }[]; comentarios: string }
  >
>({});
const briefingSaving = ref<Record<number, boolean>>({});

function initBriefingForm(cmId: number) {
  if (!briefingForms.value[cmId]) {
    briefingForms.value[cmId] = {
      links: [{ url: '', titulo: '' }],
      comentarios: '',
    };
  }
}

function addLink(cmId: number) {
  initBriefingForm(cmId);
  briefingForms.value[cmId].links.push({ url: '', titulo: '' });
}

function removeLink(cmId: number, index: number) {
  briefingForms.value[cmId].links.splice(index, 1);
}

async function submitBriefing(cmId: number) {
  briefingSaving.value[cmId] = true;
  try {
    const form = briefingForms.value[cmId];
    const validLinks = (form?.links || []).filter((l) => l.url.trim());

    await $fetch(`${config.public.apiBase}/briefings/`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: {
        project: project.value.id,
        content_maker: cmId,
        comentarios: form?.comentarios || '',
        links: validLinks,
      },
    });
    await loadProject();
  } catch {
    // silent
  } finally {
    briefingSaving.value[cmId] = false;
  }
}

// Briefing edit mode (admin/employee only)
const editingBriefingCmId = ref<number | null>(null);
const editBriefingForm = ref<{
  links: { url: string; titulo: string }[];
  comentarios: string;
  existingPhotos: { id: number; imagen_url: string; descripcion: string }[];
  removePhotoIds: number[];
}>({
  links: [],
  comentarios: '',
  existingPhotos: [],
  removePhotoIds: [],
});

function startEditBriefing(cmId: number) {
  const briefing = getBriefing(cmId);
  if (!briefing) return;
  editBriefingForm.value = {
    links: briefing.links?.length
      ? briefing.links.map((l: any) => ({ url: l.url, titulo: l.titulo || '' }))
      : [{ url: '', titulo: '' }],
    comentarios: briefing.comentarios || '',
    existingPhotos:
      briefing.photos?.map((p: any) => ({
        id: p.id,
        imagen_url: p.imagen_url,
        descripcion: p.descripcion,
      })) || [],
    removePhotoIds: [],
  };
  editingBriefingCmId.value = cmId;
}

function cancelEditBriefing() {
  editingBriefingCmId.value = null;
}

function addEditBriefingLink() {
  editBriefingForm.value.links.push({ url: '', titulo: '' });
}

function removeEditBriefingLink(index: number) {
  editBriefingForm.value.links.splice(index, 1);
}

function markExistingPhotoForRemoval(photoId: number) {
  editBriefingForm.value.removePhotoIds.push(photoId);
  editBriefingForm.value.existingPhotos =
    editBriefingForm.value.existingPhotos.filter((p) => p.id !== photoId);
}

async function saveEditBriefing(cmId: number) {
  const briefing = getBriefing(cmId);
  if (!briefing) return;
  briefingSaving.value[cmId] = true;
  try {
    const form = editBriefingForm.value;
    const validLinks = form.links.filter((l) => l.url.trim());

    const body: Record<string, any> = {
      comentarios: form.comentarios,
      links: validLinks,
    };
    if (form.removePhotoIds.length) {
      body.remove_photos = form.removePhotoIds;
    }

    await $fetch(`${config.public.apiBase}/briefings/${briefing.id}/`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body,
    });
    editingBriefingCmId.value = null;
    await loadProject();
  } catch {
    // silent
  } finally {
    briefingSaving.value[cmId] = false;
  }
}

// ─── Pipeline Progress ─────────────────────────────────────────────────────────
const pipelineSteps = computed(() => {
  if (!project.value) return [];
  const logistica = (project.value.logistica_producto_name || '').toLowerCase();
  const hasShipping =
    logistica.includes('envío') || logistica.includes('envio');
  const hasDevolucion = project.value.devolucion_producto;

  const steps: string[] = ['Perfiles Propuestos', 'Perfiles Aprobados'];
  if (hasShipping) steps.push('Producto Enviado');
  steps.push('Briefing');
  if (hasShipping) steps.push('Producto Recibido');
  steps.push('En producción', 'Revisión', 'Publicado');
  if (hasDevolucion) steps.push('Producto a Recoger');
  steps.push('Proyecto Finalizado');
  return steps;
});

const currentStepIndex = computed(() => {
  if (!project.value?.status_name) return -1;
  return pipelineSteps.value.indexOf(project.value.status_name);
});

// ─── Entregables (Deliverables) ────────────────────────────────────────────────
const entregables = ref<any[]>([]);
const entregablesLoading = ref(false);
const uploadFile = ref<File | null>(null);
const uploadDescripcion = ref('');
const uploading = ref(false);
const reviewNotes = ref('');
const reviewingId = ref<number | null>(null);
const reviewAction = ref<'approve' | 'reject' | null>(null);

const showEntregables = computed(() => {
  if (!project.value) return false;
  const statusOrder = [
    'En producción',
    'Revisión',
    'Publicado',
    'Producto a Recoger',
    'Proyecto Finalizado',
    'Cerrado',
  ];
  return (
    statusOrder.includes(project.value.status_name) ||
    entregables.value.length > 0
  );
});

const canUploadEntregable = computed(() => {
  if (!isContentMaker.value || !project.value) return false;
  // CM must be accepted on this project
  const participation = project.value.content_makers?.find(
    (cm: any) => cm.user_id === auth.user?.id && cm.status === 'accepted',
  );
  return !!participation;
});

async function loadEntregables() {
  if (!project.value) return;
  entregablesLoading.value = true;
  try {
    entregables.value = await $fetch<any[]>(
      `${config.public.apiBase}/projects/${route.params.id}/entregables/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } },
    );
  } catch {
    entregables.value = [];
  } finally {
    entregablesLoading.value = false;
  }
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  uploadFile.value = target.files?.[0] || null;
}

async function uploadEntregable() {
  if (!uploadFile.value) return;
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('archivo', uploadFile.value);
    formData.append('descripcion', uploadDescripcion.value);
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/upload_entregable/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: formData,
      },
    );
    uploadFile.value = null;
    uploadDescripcion.value = '';
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    uploading.value = false;
  }
}

function startReview(entregableId: number, action: 'approve' | 'reject') {
  reviewingId.value = entregableId;
  reviewAction.value = action;
  reviewNotes.value = '';
}

function cancelReview() {
  reviewingId.value = null;
  reviewAction.value = null;
  reviewNotes.value = '';
}

async function submitReview() {
  if (reviewingId.value === null || reviewAction.value === null) return;
  actionLoading.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/review_entregable/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: {
          entregable_id: reviewingId.value,
          approved: reviewAction.value === 'approve',
          notes: reviewNotes.value,
        },
      },
    );
    cancelReview();
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

// ─── Entregable helpers ────────────────────────────────────────────────────────

function getFileType(archivo: string): 'video' | 'foto' | 'documento' {
  if (!archivo) return 'documento';
  const ext = archivo.split('.').pop()?.toLowerCase() || '';
  if (['mp4', 'mov', 'avi', 'webm', 'mkv', 'm4v'].includes(ext)) return 'video';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'heic'].includes(ext))
    return 'foto';
  return 'documento';
}

const FILE_TYPE_CONFIG = {
  video: {
    label: 'Video',
    icon: 'M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z',
    color: 'text-blue-600 bg-blue-50',
  },
  foto: {
    label: 'Foto',
    icon: 'M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z',
    color: 'text-emerald-600 bg-emerald-50',
  },
  documento: {
    label: 'Documento',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    color: 'text-amber-600 bg-amber-50',
  },
};

const reuploadingId = ref<number | null>(null);
const reuploadFile = ref<File | null>(null);
const deletingId = ref<number | null>(null);
const expandedRevisionId = ref<number | null>(null);

function onReuploadFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  reuploadFile.value = target.files?.[0] || null;
}

async function reuploadEntregable(entregableId: number) {
  if (!reuploadFile.value) return;
  actionLoading.value = true;
  try {
    const formData = new FormData();
    formData.append('archivo', reuploadFile.value);
    formData.append('entregable_id', String(entregableId));
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/reupload_entregable/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: formData,
      },
    );
    reuploadingId.value = null;
    reuploadFile.value = null;
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

async function deleteEntregable(entregableId: number) {
  deletingId.value = entregableId;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/delete_entregable/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { entregable_id: entregableId },
      },
    );
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    deletingId.value = null;
  }
}

async function changeEntregableStatus(entregableId: number, newStatus: string) {
  actionLoading.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/change_entregable_status/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { entregable_id: entregableId, status: newStatus },
      },
    );
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    actionLoading.value = false;
  }
}

// ─── Product Tracking ──────────────────────────────────────────────────────────
const fechaLlegadaInput = ref('');
const savingFechaLlegada = ref(false);

const showProductTracking = computed(() => {
  if (!isAdminOrEmployee.value || !project.value) return false;
  // Show when logistics implies shipping and arrival not yet registered
  const logistica = project.value.logistica_producto_name?.toLowerCase() || '';
  return (
    (logistica.includes('envío') || logistica.includes('envio')) &&
    !project.value.fecha_llegada_producto
  );
});

async function saveFechaLlegada() {
  if (!fechaLlegadaInput.value) return;
  savingFechaLlegada.value = true;
  try {
    await $fetch(`${config.public.apiBase}/projects/${route.params.id}/`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { fecha_llegada_producto: fechaLlegadaInput.value },
    });
    await loadProject();
  } catch {
    // silent
  } finally {
    savingFechaLlegada.value = false;
  }
}

// ─── Status Override (Admin) ───────────────────────────────────────────────────
const showOverrideModal = ref(false);
const overrideStatus = ref('');
const overrideReason = ref('');
const overrideSaving = ref(false);

async function submitOverride() {
  if (!overrideStatus.value || !overrideReason.value.trim()) return;
  overrideSaving.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/override_status/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: {
          status: overrideStatus.value,
          reason: overrideReason.value,
        },
      },
    );
    showOverrideModal.value = false;
    overrideStatus.value = '';
    overrideReason.value = '';
    await loadProject();
  } catch {
    // silent
  } finally {
    overrideSaving.value = false;
  }
}

// ─── Mark as Published ─────────────────────────────────────────────────────────
const publishingId = ref<number | null>(null);

async function markAsPublished(entregableId: number) {
  publishingId.value = entregableId;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/mark_published/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: { entregable_id: entregableId },
      },
    );
    await loadEntregables();
    await loadProject();
  } catch {
    // silent
  } finally {
    publishingId.value = null;
  }
}

// ─── Confirm Product Pickup ────────────────────────────────────────────────────
const confirmingPickup = ref(false);

const showPickupConfirmation = computed(() => {
  if (!isAdminOrEmployee.value || !project.value) return false;
  return (
    project.value.status_name === 'Producto a Recoger' &&
    project.value.devolucion_producto
  );
});

async function confirmPickup() {
  confirmingPickup.value = true;
  try {
    await $fetch(
      `${config.public.apiBase}/projects/${route.params.id}/confirm_pickup/`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      },
    );
    await loadProject();
  } catch {
    // silent
  } finally {
    confirmingPickup.value = false;
  }
}

onMounted(() => {
  loadProject();
  if (isAdminOrEmployee.value) {
    projectsStore.fetchFilters();
  }
});

// Load entregables when project loads
watch(
  () => project.value?.id,
  (id) => {
    if (id) loadEntregables();
  },
);
</script>

<template>
  <div class="max-w-7xl mx-auto px-8 py-10 animate-fade-up">
    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center items-center h-64">
      <div
        class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin"
      />
    </div>

    <!-- Not found -->
    <div v-else-if="!project" class="text-center py-20">
      <p class="text-muted">Proyecto no encontrado</p>
      <NuxtLink to="/proyectos" class="text-sm text-gold mt-4 inline-block"
        >← Volver a proyectos</NuxtLink
      >
    </div>

    <!-- Project Detail -->
    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between mb-8">
        <div>
          <NuxtLink
            to="/proyectos"
            class="text-xs text-muted hover:text-gold transition-colors mb-2 inline-flex items-center gap-1"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.75 19.5L8.25 12l7.5-7.5"
              />
            </svg>
            Proyectos
          </NuxtLink>
          <h1 class="text-2xl font-semibold text-ink mt-1">
            {{ project.nombre }}
          </h1>
          <div class="flex items-center gap-2 mt-1">
            <p class="text-sm text-muted">
              <template v-if="!isContentMaker"
                >{{ formatProjectId(project.project_id) }} · </template
              >{{ project.client_name }}
            </p>
            <NuxtLink
              v-if="isAdminOrEmployee && project.client"
              :to="`/dashboard/clientes/${project.client}`"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium text-gold border border-gold/30 hover:bg-gold/10 transition-all"
            >
              <svg
                class="w-3 h-3"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                />
              </svg>
              Ver cliente
            </NuxtLink>
          </div>
        </div>
        <div class="flex items-center gap-2">
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
      <div
        v-if="showDeleteConfirm"
        class="rounded-2xl border border-red-200 bg-red-50/50 p-6 mb-8"
      >
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-red-700">
              ¿Eliminar este proyecto?
            </h3>
            <p class="text-xs text-red-600 mt-1">
              Esta acción no se puede deshacer.
            </p>
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
      <div
        v-if="isEditing"
        class="rounded-2xl border border-gold/30 bg-gold/5 p-6 mb-8 space-y-5"
      >
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-ink">Editar proyecto</h3>
          <div class="flex items-center gap-2">
            <button
              class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all"
              @click="cancelEdit"
            >
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
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Nombre</label
            >
            <input
              v-model="editForm.nombre"
              type="text"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div class="md:col-span-2">
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Descripción</label
            >
            <textarea
              v-model="editForm.descripcion"
              rows="3"
              class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Base imponible (€)</label
            >
            <input
              v-model="editForm.base_imponible"
              type="number"
              step="0.01"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Impuestos (€)</label
            >
            <input
              v-model="editForm.impuestos"
              type="number"
              step="0.01"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Fecha de venta</label
            >
            <input
              v-model="editForm.fecha_venta"
              type="date"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Fecha de servicio</label
            >
            <input
              v-model="editForm.fecha_servicio"
              type="date"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Fecha fin</label
            >
            <input
              v-model="editForm.fecha_fin"
              type="date"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            />
          </div>
          <div>
            <label class="text-[11px] text-muted font-medium mb-1 block"
              >Estado</label
            >
            <select
              v-model="editForm.status"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
            >
              <option :value="null">Sin estado</option>
              <option
                v-for="s in projectsStore.filters.statuses"
                :key="s.id"
                :value="s.id"
              >
                {{ s.nombre }}
              </option>
            </select>
          </div>
        </div>

        <!-- CM Selection Mode -->
        <div class="border-t border-border/40 pt-5 space-y-4">
          <label class="block text-xs font-medium text-muted"
            >¿Cómo se asignará la Content Maker?</label
          >
          <div class="grid grid-cols-1 gap-2">
            <label
              v-for="opt in [
                {
                  value: 'defined',
                  label: 'Ya está definida',
                  desc: 'Seleccionas directamente la content maker',
                },
                {
                  value: 'recommended',
                  label: 'Recomendar opciones',
                  desc: 'Sugieres varias opciones al cliente',
                },
                {
                  value: 'client_chooses',
                  label: 'El cliente elige',
                  desc: 'El cliente explora y selecciona por sí mismo',
                },
              ]"
              :key="opt.value"
              class="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200"
              :class="
                editForm.cm_selection_mode === opt.value
                  ? 'border-gold/40 bg-gold/5'
                  : 'border-border/60 bg-white hover:border-border'
              "
            >
              <input
                v-model="editForm.cm_selection_mode"
                type="radio"
                :value="opt.value"
                class="mt-0.5 accent-[#c9a84c]"
              />
              <div>
                <p class="text-sm font-medium text-ink">{{ opt.label }}</p>
                <p class="text-xs text-muted mt-0.5">{{ opt.desc }}</p>
              </div>
            </label>
          </div>

          <!-- Defined: search and select -->
          <div
            v-if="editForm.cm_selection_mode === 'defined'"
            class="space-y-3"
          >
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Buscar y añadir Content Makers</label
            >
            <input
              v-model="editCMSearch"
              type="text"
              placeholder="Nombre o @instagram…"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
              @input="onEditCMSearch"
            />
            <div
              v-if="editCMResults.length"
              class="rounded-xl border border-border/60 max-h-48 overflow-auto bg-white"
            >
              <button
                v-for="cm in editCMResults"
                :key="cm.id"
                class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                @click="addEditDefinedCM(cm)"
              >
                <span class="font-medium text-ink"
                  >{{ cm.nombre }} {{ cm.apellidos }}</span
                >
                <span v-if="cm.instagram_handle" class="text-muted ml-2 text-xs"
                  >@{{ cm.instagram_handle }}</span
                >
              </button>
            </div>
            <div v-if="editSelectedCMs.length" class="space-y-1.5">
              <p class="text-xs text-muted font-medium">
                Seleccionadas ({{ editSelectedCMs.length }}):
              </p>
              <div
                v-for="cm in editSelectedCMs"
                :key="cm.id"
                class="flex items-center justify-between px-3 py-2 rounded-lg bg-white border border-border/40"
              >
                <span class="text-xs text-ink font-medium"
                  >{{ cm.nombre }}
                  <span v-if="cm.instagram_handle" class="text-muted"
                    >@{{ cm.instagram_handle }}</span
                  ></span
                >
                <button
                  class="text-xs text-red-400 hover:text-red-600 transition-colors"
                  @click="removeEditDefinedCM(cm.id)"
                >
                  Quitar
                </button>
              </div>
            </div>
          </div>

          <!-- Recommended: search and add -->
          <div
            v-if="editForm.cm_selection_mode === 'recommended'"
            class="space-y-3"
          >
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Buscar y añadir recomendaciones</label
            >
            <input
              v-model="editCMSearch"
              type="text"
              placeholder="Nombre o @instagram…"
              class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
              @input="onEditCMSearch"
            />
            <div
              v-if="editCMResults.length"
              class="rounded-xl border border-border/60 max-h-48 overflow-auto bg-white"
            >
              <button
                v-for="cm in editCMResults"
                :key="cm.id"
                class="w-full text-left px-4 py-2.5 text-sm hover:bg-panel/60 transition-colors border-b border-border/20 last:border-0"
                @click="addEditRecommendedCM(cm)"
              >
                <span class="font-medium text-ink"
                  >{{ cm.nombre }} {{ cm.apellidos }}</span
                >
                <span v-if="cm.instagram_handle" class="text-muted ml-2 text-xs"
                  >@{{ cm.instagram_handle }}</span
                >
              </button>
            </div>
            <div v-if="editRecommendedCMs.length" class="space-y-1.5">
              <p class="text-xs text-muted font-medium">
                Recomendadas ({{ editRecommendedCMs.length }}):
              </p>
              <div
                v-for="cm in editRecommendedCMs"
                :key="cm.id"
                class="flex items-center justify-between px-3 py-2 rounded-lg bg-white border border-border/40"
              >
                <span class="text-xs text-ink font-medium"
                  >{{ cm.nombre }}
                  <span v-if="cm.instagram_handle" class="text-muted"
                    >@{{ cm.instagram_handle }}</span
                  ></span
                >
                <button
                  class="text-xs text-red-400 hover:text-red-600 transition-colors"
                  @click="removeEditRecommendedCM(cm.id)"
                >
                  Quitar
                </button>
              </div>
            </div>
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
            <h3 class="text-sm font-semibold text-ink">
              ¿Aceptas este proyecto?
            </h3>
            <p class="text-xs text-muted mt-1">
              Tienes una solicitud pendiente para participar en esta campaña.
            </p>
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
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <!-- Main Content (left 2/3) -->
        <div class="lg:col-span-2 space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Details Card -->
            <div
              class="rounded-2xl border border-border/60 bg-white p-6 space-y-4"
            >
              <h2 class="text-sm font-semibold text-ink">
                Detalles del proyecto
              </h2>
              <div class="space-y-3 text-xs">
                <div class="flex justify-between">
                  <span class="text-muted">Tipo de servicio</span
                  ><span class="text-ink font-medium">{{
                    project.service_type_name || '—'
                  }}</span>
                </div>
                <div v-if="!isContentMaker" class="flex justify-between">
                  <span class="text-muted">Base imponible</span
                  ><span class="text-ink font-medium"
                    >{{ project.base_imponible }} €</span
                  >
                </div>
                <div v-if="!isContentMaker" class="flex justify-between">
                  <span class="text-muted">Impuestos</span
                  ><span class="text-ink font-medium"
                    >{{ project.impuestos }} €</span
                  >
                </div>
                <div
                  v-if="!isContentMaker"
                  class="flex justify-between border-t border-border/40 pt-3"
                >
                  <span class="text-muted font-medium">Total</span
                  ><span class="text-ink font-bold"
                    >{{ project.precio_total }} €</span
                  >
                </div>
              </div>
            </div>

            <!-- Dates Card -->
            <div
              class="rounded-2xl border border-border/60 bg-white p-6 space-y-4"
            >
              <h2 class="text-sm font-semibold text-ink">Fechas</h2>
              <div class="space-y-3 text-xs">
                <div class="flex justify-between">
                  <span class="text-muted">Fecha de venta</span
                  ><span class="text-ink font-medium">{{
                    formatDate(project.fecha_venta)
                  }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted">Fecha de servicio</span
                  ><span class="text-ink font-medium">{{
                    formatDate(project.fecha_servicio)
                  }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted">Fecha fin</span
                  ><span class="text-ink font-medium">{{
                    formatDate(project.fecha_fin)
                  }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted">Creado</span
                  ><span class="text-ink font-medium">{{
                    formatDate(project.created_at)
                  }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Description -->
          <div
            v-if="project.descripcion"
            class="rounded-2xl border border-border/60 bg-white p-6"
          >
            <h2 class="text-sm font-semibold text-ink mb-3">Descripción</h2>
            <p class="text-sm text-muted leading-relaxed">
              {{ project.descripcion }}
            </p>
          </div>

          <!-- Content Maker Section -->
          <div class="rounded-2xl border border-border/60 bg-white p-6">
            <h2 class="text-sm font-semibold text-ink mb-4">Content Makers</h2>

            <!-- Accepted/Assigned CMs -->
            <div v-if="acceptedCMs.length" class="space-y-2 mb-4">
              <div
                v-for="cm in acceptedCMs"
                :key="cm.content_maker_id"
                class="flex items-center justify-between p-3 rounded-xl bg-emerald-50/50 border border-emerald-200/50"
              >
                <NuxtLink
                  :to="`/dashboard/content-makers/${cm.content_maker_id}`"
                  class="flex items-center gap-3 hover:opacity-80 transition-opacity"
                >
                  <div class="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0">
                    <img
                      v-if="cm.foto_url"
                      :src="cm.foto_url"
                      :alt="cm.nombre"
                      class="w-full h-full object-cover"
                    />
                    <div
                      v-else
                      class="w-full h-full bg-emerald-100 flex items-center justify-center text-[10px] font-bold text-emerald-600"
                    >
                      {{
                        cm.nombre
                          ?.split(' ')
                          .map((n: string) => n[0])
                          .join('')
                          .slice(0, 2)
                      }}
                    </div>
                  </div>
                  <div>
                    <p
                      class="text-sm font-medium text-ink hover:text-gold transition-colors"
                    >
                      {{ cm.nombre }}
                    </p>
                    <p class="text-[11px] text-emerald-600">
                      Asignada al proyecto
                    </p>
                  </div>
                </NuxtLink>
                <button
                  v-if="isAdminOrEmployee"
                  :disabled="actionLoading"
                  class="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-red-200 text-red-500 hover:bg-red-50 transition-all disabled:opacity-50"
                  @click="unlinkCM(cm.content_maker_id)"
                >
                  Desvincular
                </button>
              </div>
            </div>

            <!-- Client pending CMs (invited, waiting response) -->
            <div v-if="clientWaitingForCM" class="space-y-2 mb-4">
              <p class="text-xs text-muted font-medium">
                Invitadas (esperando respuesta):
              </p>
              <div
                v-for="cm in project.content_makers.filter(
                  (c: any) => c.status === 'pending',
                )"
                :key="cm.content_maker_id"
                class="flex items-center justify-between p-3 rounded-xl bg-amber-50/50 border border-amber-200/50"
              >
                <NuxtLink
                  :to="`/dashboard/content-makers/${cm.content_maker_id}`"
                  class="flex items-center gap-3 hover:opacity-80 transition-opacity"
                >
                  <div class="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0">
                    <img
                      v-if="cm.foto_url"
                      :src="cm.foto_url"
                      :alt="cm.nombre"
                      class="w-full h-full object-cover"
                    />
                    <div
                      v-else
                      class="w-full h-full bg-amber-100 flex items-center justify-center text-[10px] font-bold text-amber-600"
                    >
                      {{
                        cm.nombre
                          ?.split(' ')
                          .map((n: string) => n[0])
                          .join('')
                          .slice(0, 2)
                      }}
                    </div>
                  </div>
                  <div>
                    <p
                      class="text-sm font-medium text-ink hover:text-gold transition-colors"
                    >
                      {{ cm.nombre }}
                    </p>
                    <p class="text-[11px] text-amber-600">
                      Pendiente de confirmación
                    </p>
                  </div>
                </NuxtLink>
              </div>
            </div>

            <!-- Client CM Selector -->
            <div v-if="clientNeedsToSelectCM" class="space-y-4">
              <div
                class="rounded-xl bg-blue-50/50 border border-blue-200/50 p-4 mb-4"
              >
                <p class="text-sm font-medium text-ink">
                  Selecciona Content Makers para este proyecto
                </p>
                <p class="text-[11px] text-blue-600 mt-1">
                  {{
                    project.cm_selection_mode === 'recommended'
                      ? 'Te hemos recomendado las siguientes Content Makers. Selecciona las que prefieras para esta campaña.'
                      : 'Explora nuestras Content Makers y selecciona las que quieras para esta campaña. Puedes seleccionar varias.'
                  }}
                </p>
              </div>

              <!-- Recommended CMs (shown when mode is recommended) -->
              <div
                v-if="
                  project.cm_selection_mode === 'recommended' &&
                  project.content_makers?.length
                "
                class="space-y-2"
              >
                <p class="text-xs text-muted font-medium">
                  Recomendadas para ti:
                </p>
                <div
                  v-for="cm in project.content_makers.filter(
                    (c: any) => c.is_recommended && c.status !== 'rejected',
                  )"
                  :key="cm.content_maker_id"
                  class="flex items-center justify-between p-3 rounded-xl border border-gold/20 bg-gold/5 hover:border-gold/40 transition-all"
                >
                  <NuxtLink
                    :to="`/dashboard/content-makers/${cm.content_maker_id}`"
                    class="flex items-center gap-3 hover:opacity-80 transition-opacity"
                  >
                    <div
                      class="w-9 h-9 rounded-lg overflow-hidden flex-shrink-0"
                    >
                      <img
                        v-if="cm.foto_url"
                        :src="cm.foto_url"
                        :alt="cm.nombre"
                        class="w-full h-full object-cover"
                      />
                      <div
                        v-else
                        class="w-full h-full bg-gold/10 flex items-center justify-center text-[10px] font-bold text-gold"
                      >
                        {{
                          cm.nombre
                            ?.split(' ')
                            .map((n: string) => n[0])
                            .join('')
                            .slice(0, 2)
                        }}
                      </div>
                    </div>
                    <div>
                      <p
                        class="text-xs font-medium text-ink hover:text-gold transition-colors"
                      >
                        {{ cm.nombre }}
                      </p>
                      <p
                        v-if="cm.instagram_handle"
                        class="text-[10px] text-muted"
                      >
                        @{{ cm.instagram_handle }} ·
                        {{ cm.seguidores_instagram?.toLocaleString() }} seg.
                      </p>
                    </div>
                  </NuxtLink>
                  <button
                    v-if="cm.status === 'recommended'"
                    :disabled="actionLoading"
                    class="px-3 py-1.5 rounded-lg text-[11px] font-medium bg-gold text-white hover:bg-gold/90 transition-all disabled:opacity-50"
                    @click="selectCM(cm.content_maker_id)"
                  >
                    Seleccionar
                  </button>
                  <span
                    v-else
                    class="px-3 py-1.5 rounded-lg text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
                  >
                    ✓ Invitación enviada
                  </span>
                </div>

                <div class="pt-2 border-t border-border/40 mt-4">
                  <p class="text-[11px] text-muted">
                    ¿Ninguna te convence? Busca otra Content Maker:
                  </p>
                </div>
              </div>

              <!-- Find CM button -->
              <button
                class="w-full py-3 rounded-xl bg-gold text-white font-medium text-sm hover:bg-gold/90 transition-all flex items-center justify-center gap-2"
                @click="openCMBrowser"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                  />
                </svg>
                Encuentra a tu Content Maker
              </button>
            </div>

            <!-- CM candidates (visible to admins/employees) -->
            <div
              v-if="isAdminOrEmployee && project.content_makers?.length"
              class="mt-4 space-y-2"
            >
              <p class="text-xs text-muted font-medium mb-2">
                Candidatas / Recomendadas:
              </p>
              <div
                v-for="cm in project.content_makers"
                :key="cm.id"
                class="flex items-center justify-between p-3 rounded-xl border border-border/40 bg-panel/30"
              >
                <NuxtLink
                  :to="`/dashboard/content-makers/${cm.content_maker_id}`"
                  class="flex items-center gap-3 hover:opacity-80 transition-opacity"
                >
                  <div class="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
                    <img
                      v-if="cm.foto_url"
                      :src="cm.foto_url"
                      :alt="cm.nombre"
                      class="w-full h-full object-cover"
                    />
                    <div
                      v-else
                      class="w-full h-full bg-panel flex items-center justify-center text-[10px] font-bold text-muted"
                    >
                      {{
                        cm.nombre
                          ?.split(' ')
                          .map((n: string) => n[0])
                          .join('')
                          .slice(0, 2)
                      }}
                    </div>
                  </div>
                  <div>
                    <p
                      class="text-xs font-medium text-ink hover:text-gold transition-colors"
                    >
                      {{ cm.nombre }}
                    </p>
                    <p
                      v-if="cm.instagram_handle"
                      class="text-[10px] text-muted"
                    >
                      @{{ cm.instagram_handle }}
                    </p>
                  </div>
                </NuxtLink>
                <span
                  class="px-2 py-0.5 rounded-md text-[10px] font-medium border"
                  :class="
                    STATUS_COLORS[cm.status] ||
                    'bg-gray-50 text-gray-600 border-gray-200'
                  "
                  >{{ STATUS_LABELS[cm.status] || cm.status }}</span
                >
              </div>
            </div>

            <!-- No CM yet (only for admin when no candidates) -->
            <div
              v-if="
                !acceptedCMs.length &&
                !project.content_makers?.length &&
                !clientNeedsToSelectCM &&
                !clientWaitingForCM
              "
              class="text-center py-6"
            >
              <p class="text-xs text-muted">
                Aún no se ha asignado una Content Maker
              </p>
            </div>
          </div>

          <!-- Briefing Section -->
          <div
            v-if="needsBriefing || project.briefings?.length"
            class="rounded-2xl border border-border/60 bg-white p-6"
          >
            <h2 class="text-sm font-semibold text-ink mb-4">Briefing</h2>

            <div class="space-y-5">
              <div v-for="cm in acceptedCMs" :key="cm.content_maker_id">
                <!-- Briefing already submitted -->
                <div
                  v-if="hasBriefing(cm.content_maker_id)"
                  class="rounded-xl border border-emerald-200/50 bg-emerald-50/30 p-4"
                >
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-2">
                      <div
                        class="w-6 h-6 rounded-md bg-emerald-100 flex items-center justify-center"
                      >
                        <svg
                          class="w-3 h-3 text-emerald-600"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4.5 12.75l6 6 9-13.5"
                          />
                        </svg>
                      </div>
                      <p class="text-xs font-medium text-ink">
                        Briefing para {{ cm.nombre }}
                      </p>
                    </div>
                    <button
                      v-if="
                        isAdminOrEmployee &&
                        editingBriefingCmId !== cm.content_maker_id
                      "
                      class="px-2.5 py-1 rounded-lg text-[11px] font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
                      @click="startEditBriefing(cm.content_maker_id)"
                    >
                      Editar
                    </button>
                  </div>

                  <!-- Edit mode -->
                  <div
                    v-if="editingBriefingCmId === cm.content_maker_id"
                    class="space-y-4 pl-8"
                  >
                    <!-- Links -->
                    <div>
                      <div class="flex items-center justify-between mb-1.5">
                        <label class="text-[11px] text-muted font-medium"
                          >Enlaces de referencia</label
                        >
                        <button
                          type="button"
                          class="text-[11px] text-gold hover:text-gold/80 font-medium transition-colors"
                          @click="addEditBriefingLink"
                        >
                          + Añadir enlace
                        </button>
                      </div>
                      <div class="space-y-2">
                        <div
                          v-for="(link, li) in editBriefingForm.links"
                          :key="li"
                          class="flex items-center gap-2"
                        >
                          <input
                            v-model="link.url"
                            type="url"
                            placeholder="https://..."
                            class="flex-1 h-8 px-3 rounded-lg border border-border/60 bg-white text-xs text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
                          />
                          <input
                            v-model="link.titulo"
                            type="text"
                            placeholder="Título (opcional)"
                            class="w-32 h-8 px-3 rounded-lg border border-border/60 bg-white text-xs text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
                          />
                          <button
                            v-if="editBriefingForm.links.length > 1"
                            type="button"
                            class="p-1 text-red-400 hover:text-red-600 transition-colors"
                            @click="removeEditBriefingLink(li)"
                          >
                            <svg
                              class="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              viewBox="0 0 24 24"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Existing photos (legacy) -->
                    <div v-if="editBriefingForm.existingPhotos.length">
                      <label
                        class="text-[11px] text-muted font-medium mb-1.5 block"
                        >Fotografías existentes</label
                      >
                      <div class="flex flex-wrap gap-2">
                        <div
                          v-for="photo in editBriefingForm.existingPhotos"
                          :key="photo.id"
                          class="relative w-16 h-16 rounded-lg overflow-hidden border border-border/40 group"
                        >
                          <img
                            :src="photo.imagen_url"
                            :alt="photo.descripcion"
                            class="w-full h-full object-cover"
                          />
                          <button
                            type="button"
                            class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                            @click="markExistingPhotoForRemoval(photo.id)"
                          >
                            <svg
                              class="w-4 h-4 text-white"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              viewBox="0 0 24 24"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Comments -->
                    <div>
                      <label
                        class="text-[11px] text-muted font-medium mb-1 block"
                        >Comentarios</label
                      >
                      <textarea
                        v-model="editBriefingForm.comentarios"
                        rows="3"
                        placeholder="Instrucciones, referencias, tono, estilo, etc."
                        class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none"
                      />
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center gap-2">
                      <button
                        :disabled="briefingSaving[cm.content_maker_id]"
                        class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                        @click="saveEditBriefing(cm.content_maker_id)"
                      >
                        {{
                          briefingSaving[cm.content_maker_id]
                            ? 'Guardando...'
                            : 'Guardar cambios'
                        }}
                      </button>
                      <button
                        class="px-3 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all"
                        @click="cancelEditBriefing"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>

                  <!-- View mode -->
                  <div v-else class="space-y-3 text-xs pl-8">
                    <!-- Links -->
                    <div v-if="getBriefing(cm.content_maker_id)?.links?.length">
                      <span class="text-muted font-medium"
                        >Enlaces de referencia:</span
                      >
                      <div class="mt-1 space-y-1">
                        <div
                          v-for="link in getBriefing(cm.content_maker_id).links"
                          :key="link.id"
                          class="flex items-center gap-2"
                        >
                          <svg
                            class="w-3 h-3 text-gold flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.02a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364L4.25 8.81"
                            />
                          </svg>
                          <a
                            :href="link.url"
                            target="_blank"
                            class="text-gold hover:underline truncate"
                            >{{ link.titulo || link.url }}</a
                          >
                        </div>
                      </div>
                    </div>
                    <!-- Photos -->
                    <div
                      v-if="getBriefing(cm.content_maker_id)?.photos?.length"
                    >
                      <span class="text-muted font-medium">Fotografías:</span>
                      <div class="mt-2 grid grid-cols-3 gap-2">
                        <a
                          v-for="photo in getBriefing(cm.content_maker_id)
                            .photos"
                          :key="photo.id"
                          :href="photo.imagen_url"
                          target="_blank"
                          class="aspect-square rounded-lg overflow-hidden border border-border/40 hover:border-gold/40 transition-all"
                        >
                          <img
                            :src="photo.imagen_url"
                            :alt="photo.descripcion"
                            class="w-full h-full object-cover"
                          />
                        </a>
                      </div>
                    </div>
                    <!-- Comments -->
                    <div v-if="getBriefing(cm.content_maker_id)?.comentarios">
                      <span class="text-muted font-medium">Comentarios:</span>
                      <p class="text-ink mt-0.5 whitespace-pre-line">
                        {{ getBriefing(cm.content_maker_id).comentarios }}
                      </p>
                    </div>
                  </div>
                </div>

                <!-- Briefing form (client fills in) -->
                <div
                  v-else-if="isClient"
                  class="rounded-xl border border-blue-200/50 bg-blue-50/30 p-4"
                >
                  <p class="text-xs font-medium text-ink mb-3">
                    Briefing para {{ cm.nombre }}
                  </p>
                  <div class="space-y-4">
                    <!-- Links -->
                    <div>
                      <div class="flex items-center justify-between mb-1.5">
                        <label class="text-[11px] text-muted font-medium"
                          >Enlaces de referencia</label
                        >
                        <button
                          type="button"
                          class="text-[11px] text-gold hover:text-gold/80 font-medium transition-colors"
                          @click="addLink(cm.content_maker_id)"
                        >
                          + Añadir enlace
                        </button>
                      </div>
                      <div class="space-y-2">
                        <div
                          v-for="(link, li) in briefingForms[
                            cm.content_maker_id
                          ]?.links || []"
                          :key="li"
                          class="flex items-center gap-2"
                        >
                          <input
                            v-model="link.url"
                            type="url"
                            placeholder="https://..."
                            class="flex-1 h-8 px-3 rounded-lg border border-border/60 bg-white text-xs text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
                            @focus="initBriefingForm(cm.content_maker_id)"
                          />
                          <input
                            v-model="link.titulo"
                            type="text"
                            placeholder="Título (opcional)"
                            class="w-32 h-8 px-3 rounded-lg border border-border/60 bg-white text-xs text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
                          />
                          <button
                            v-if="
                              (briefingForms[cm.content_maker_id]?.links
                                .length || 0) > 1
                            "
                            type="button"
                            class="p-1 text-red-400 hover:text-red-600 transition-colors"
                            @click="removeLink(cm.content_maker_id, li)"
                          >
                            <svg
                              class="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              viewBox="0 0 24 24"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Comments -->
                    <div>
                      <label
                        class="text-[11px] text-muted font-medium mb-1 block"
                        >Comentarios</label
                      >
                      <textarea
                        :value="
                          briefingForms[cm.content_maker_id]?.comentarios || ''
                        "
                        rows="3"
                        placeholder="Instrucciones, referencias, tono, estilo, etc."
                        class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none"
                        @focus="initBriefingForm(cm.content_maker_id)"
                        @input="
                          initBriefingForm(cm.content_maker_id);
                          briefingForms[cm.content_maker_id].comentarios = (
                            $event.target as HTMLTextAreaElement
                          ).value;
                        "
                      />
                    </div>

                    <button
                      :disabled="briefingSaving[cm.content_maker_id]"
                      class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                      @click="submitBriefing(cm.content_maker_id)"
                    >
                      {{
                        briefingSaving[cm.content_maker_id]
                          ? 'Enviando...'
                          : 'Enviar briefing'
                      }}
                    </button>
                  </div>
                </div>

                <!-- Admin/employee sees pending briefing -->
                <div
                  v-else-if="isAdminOrEmployee"
                  class="rounded-xl border border-amber-200/50 bg-amber-50/30 p-4"
                >
                  <p class="text-xs text-amber-700">
                    Pendiente: briefing para {{ cm.nombre }} (el cliente debe
                    completarlo)
                  </p>
                </div>

                <!-- CM sees waiting state -->
                <div
                  v-else-if="isContentMaker"
                  class="rounded-xl border border-amber-200/50 bg-amber-50/30 p-4"
                >
                  <p class="text-xs text-amber-700">
                    Esperando briefing del cliente para este proyecto.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Product Arrival Tracking (Admin/Employee) -->
          <div
            v-if="showProductTracking"
            class="rounded-2xl border border-amber-200/50 bg-amber-50/30 p-6"
          >
            <h2 class="text-sm font-semibold text-ink mb-3">
              Registrar llegada del producto
            </h2>
            <p class="text-xs text-muted mb-4">
              El producto fue enviado. Registra la fecha de llegada para avanzar
              el proyecto.
            </p>
            <div class="flex items-end gap-3">
              <div class="flex-1">
                <label class="text-[11px] text-muted font-medium mb-1 block"
                  >Fecha de llegada</label
                >
                <input
                  v-model="fechaLlegadaInput"
                  type="date"
                  class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
                />
              </div>
              <button
                :disabled="!fechaLlegadaInput || savingFechaLlegada"
                class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                @click="saveFechaLlegada"
              >
                Registrar
              </button>
            </div>
          </div>

          <!-- Product Pickup Confirmation -->
          <div
            v-if="showPickupConfirmation"
            class="rounded-2xl border border-amber-200/50 bg-amber-50/30 p-6"
          >
            <div class="flex items-center gap-3 mb-3">
              <div
                class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center"
              >
                <svg
                  class="w-4 h-4 text-amber-700"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H18.75m-7.5 0h7.5m-7.5 0l-1 3m8.5-3h2.25A1.125 1.125 0 0121 12.75v-1.5c0-.621-.504-1.125-1.125-1.125H18M3.375 14.25h3.75m0 0l1-3m0 0h7.5"
                  />
                </svg>
              </div>
              <div>
                <h2 class="text-sm font-semibold text-ink">
                  Producto pendiente de recogida
                </h2>
                <p class="text-xs text-muted mt-0.5">
                  Este proyecto requiere devolución del producto. Confirma
                  cuando se haya recogido.
                </p>
              </div>
            </div>
            <button
              :disabled="confirmingPickup"
              class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
              @click="confirmPickup"
            >
              {{
                confirmingPickup
                  ? 'Confirmando...'
                  : 'Confirmar recogida del producto'
              }}
            </button>
          </div>
        </div>
        <!-- end main content col -->

        <!-- Right Sidebar: Status & Roadmap -->
        <div class="lg:col-span-1">
          <div class="sticky top-8 space-y-5">
            <!-- Status Card -->
            <div class="rounded-2xl border border-border/60 bg-white p-5">
              <!-- Current Status -->
              <div class="flex items-center justify-between mb-4">
                <h3
                  class="text-xs font-semibold text-muted uppercase tracking-wide"
                >
                  Estado actual
                </h3>
                <div
                  v-if="project.retrasado"
                  class="flex items-center gap-1 px-2 py-0.5 rounded-md bg-red-50 border border-red-200"
                >
                  <div
                    class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"
                  />
                  <span class="text-[10px] font-medium text-red-700"
                    >Retrasado</span
                  >
                </div>
              </div>
              <div class="flex items-center gap-3 mb-4">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center bg-gold/10"
                >
                  <svg
                    class="w-5 h-5 text-gold"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
                    />
                  </svg>
                </div>
                <div>
                  <p class="text-base font-semibold text-ink">
                    {{ project.status_name || 'Sin estado' }}
                  </p>
                  <p v-if="project.is_draft" class="text-[11px] text-muted">
                    Borrador
                  </p>
                </div>
              </div>

              <!-- Override button (admin only) -->
              <button
                v-if="isAdminOrEmployee && !isEditing"
                class="w-full px-3 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all text-center"
                @click="showOverrideModal = true"
              >
                Cambiar estado manualmente
              </button>
            </div>

            <!-- Roadmap Card -->
            <div
              v-if="pipelineSteps.length && !project.is_draft"
              class="rounded-2xl border border-border/60 bg-white p-5"
            >
              <h3
                class="text-xs font-semibold text-muted uppercase tracking-wide mb-4"
              >
                Roadmap
              </h3>
              <div class="relative">
                <!-- Vertical line -->
                <div
                  class="absolute left-[11px] top-3 bottom-3 w-0.5 bg-gray-100"
                />

                <div class="space-y-0">
                  <div
                    v-for="(step, i) in pipelineSteps"
                    :key="step"
                    class="relative flex items-start gap-3 py-2"
                  >
                    <!-- Circle indicator -->
                    <div
                      class="relative z-10 flex-shrink-0 w-[22px] h-[22px] rounded-full flex items-center justify-center border-2 transition-all"
                      :class="{
                        'border-emerald-400 bg-emerald-50':
                          i < currentStepIndex,
                        'border-gold bg-gold/10 ring-4 ring-gold/10':
                          i === currentStepIndex,
                        'border-gray-200 bg-white': i > currentStepIndex,
                      }"
                    >
                      <!-- Completed check -->
                      <svg
                        v-if="i < currentStepIndex"
                        class="w-3 h-3 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M4.5 12.75l6 6 9-13.5"
                        />
                      </svg>
                      <!-- Current dot -->
                      <div
                        v-else-if="i === currentStepIndex"
                        class="w-2 h-2 rounded-full bg-gold animate-pulse"
                      />
                      <!-- Future empty -->
                      <div
                        v-else
                        class="w-1.5 h-1.5 rounded-full bg-gray-200"
                      />
                    </div>

                    <!-- Step label -->
                    <span
                      class="text-xs leading-[22px] transition-all"
                      :class="{
                        'text-emerald-700 font-medium': i < currentStepIndex,
                        'text-ink font-semibold': i === currentStepIndex,
                        'text-muted': i > currentStepIndex,
                      }"
                      >{{ step }}</span
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- Client Info Card -->
            <div
              v-if="isAdminOrEmployee"
              class="rounded-2xl border border-border/60 bg-white p-5"
            >
              <h3
                class="text-xs font-semibold text-muted uppercase tracking-wide mb-3"
              >
                Cliente
              </h3>
              <div class="space-y-2.5 text-xs">
                <div class="flex justify-between">
                  <span class="text-muted">Nombre</span
                  ><span class="text-ink font-medium">{{
                    project.client_name
                  }}</span>
                </div>
                <div v-if="project.brand_name" class="flex justify-between">
                  <span class="text-muted">Marca</span
                  ><span class="text-ink font-medium">{{
                    project.brand_name
                  }}</span>
                </div>
                <div
                  v-if="project.created_by_name"
                  class="flex justify-between"
                >
                  <span class="text-muted">Creado por</span
                  ><span class="text-ink font-medium">{{
                    project.created_by_name
                  }}</span>
                </div>
              </div>
              <NuxtLink
                v-if="project.client"
                :to="`/dashboard/clientes/${project.client}`"
                class="mt-3 w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-[11px] font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                  />
                </svg>
                Ver ficha del cliente
              </NuxtLink>
            </div>
          </div>
        </div>
        <!-- end sidebar col -->
      </div>
      <!-- end grid -->

      <!-- Entregables Section (full width) -->
      <div
        v-if="showEntregables || canUploadEntregable"
        class="rounded-2xl border border-border/60 bg-white p-6 mt-8"
      >
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-sm font-semibold text-ink">Entregables</h2>
          <span v-if="entregables.length" class="text-[11px] text-muted"
            >{{ entregables.length }} archivo{{
              entregables.length !== 1 ? 's' : ''
            }}</span
          >
        </div>

        <!-- Upload form (CM only) -->
        <div
          v-if="canUploadEntregable"
          class="rounded-xl border border-blue-200/50 bg-blue-50/30 p-4 mb-5"
        >
          <p class="text-xs font-medium text-ink mb-3">Subir entregable</p>
          <div class="flex items-end gap-3">
            <div class="flex-1">
              <label class="text-[11px] text-muted font-medium mb-1 block"
                >Archivo</label
              >
              <input
                type="file"
                class="w-full text-xs text-ink file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-gold/10 file:text-gold hover:file:bg-gold/20 cursor-pointer"
                @change="onFileChange"
              />
            </div>
            <div class="flex-1">
              <label class="text-[11px] text-muted font-medium mb-1 block"
                >Descripción (opcional)</label
              >
              <input
                v-model="uploadDescripcion"
                type="text"
                placeholder="Describe brevemente el contenido..."
                class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
              />
            </div>
            <button
              :disabled="!uploadFile || uploading"
              class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50 whitespace-nowrap"
              @click="uploadEntregable"
            >
              {{ uploading ? 'Subiendo...' : 'Subir' }}
            </button>
          </div>
        </div>

        <!-- Entregables Table -->
        <div v-if="entregables.length" class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-border/60">
                <th class="text-left py-2.5 px-3 text-muted font-medium">
                  Tipo
                </th>
                <th class="text-left py-2.5 px-3 text-muted font-medium">
                  Contenido
                </th>
                <th class="text-left py-2.5 px-3 text-muted font-medium">
                  Content Maker
                </th>
                <th class="text-left py-2.5 px-3 text-muted font-medium">
                  Fecha
                </th>
                <th class="text-left py-2.5 px-3 text-muted font-medium">
                  Estado
                </th>
                <th class="text-right py-2.5 px-3 text-muted font-medium">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border/40">
              <template v-for="ent in entregables" :key="ent.id">
                <tr class="hover:bg-panel/30 transition-colors">
                  <!-- Type -->
                  <td class="py-3 px-3">
                    <div class="flex items-center gap-2">
                      <div
                        class="w-7 h-7 rounded-lg flex items-center justify-center"
                        :class="
                          FILE_TYPE_CONFIG[getFileType(ent.archivo)].color
                        "
                      >
                        <svg
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            :d="FILE_TYPE_CONFIG[getFileType(ent.archivo)].icon"
                          />
                        </svg>
                      </div>
                      <span class="text-[11px] font-medium text-ink">{{
                        FILE_TYPE_CONFIG[getFileType(ent.archivo)].label
                      }}</span>
                    </div>
                  </td>
                  <!-- Content / Description -->
                  <td class="py-3 px-3">
                    <p
                      class="text-xs text-ink font-medium truncate max-w-[200px]"
                    >
                      {{
                        ent.descripcion ||
                        ent.archivo?.split('/').pop() ||
                        'Sin título'
                      }}
                    </p>
                    <!-- Revision warning badge -->
                    <button
                      v-if="ent.revision_notes && ent.status === 'revision'"
                      class="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition-all"
                      @click="
                        expandedRevisionId =
                          expandedRevisionId === ent.id ? null : ent.id
                      "
                    >
                      <svg
                        class="w-3 h-3 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                        />
                      </svg>
                      Cambios solicitados
                      <svg
                        class="w-3 h-3 transition-transform"
                        :class="{ 'rotate-180': expandedRevisionId === ent.id }"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                        />
                      </svg>
                    </button>
                  </td>
                  <!-- Content Maker -->
                  <td class="py-3 px-3">
                    <span class="text-xs text-ink">{{
                      ent.content_maker_name
                    }}</span>
                  </td>
                  <!-- Date -->
                  <td class="py-3 px-3">
                    <span class="text-[11px] text-muted">{{
                      formatDate(ent.uploaded_at)
                    }}</span>
                  </td>
                  <!-- Status -->
                  <td class="py-3 px-3">
                    <div class="flex items-center gap-1.5">
                      <!-- Admin/Employee: dropdown to change status -->
                      <select
                        v-if="isAdminOrEmployee"
                        :value="ent.status"
                        class="text-[10px] px-2 py-0.5 rounded-md font-medium border cursor-pointer focus:outline-none focus:ring-2 focus:ring-gold/20"
                        :class="{
                          'bg-emerald-100 text-emerald-700 border-emerald-200':
                            ent.status === 'approved',
                          'bg-amber-100 text-amber-700 border-amber-200':
                            ent.status === 'pending',
                          'bg-orange-100 text-orange-700 border-orange-200':
                            ent.status === 'revision',
                          'bg-red-100 text-red-700 border-red-200':
                            ent.status === 'rejected',
                        }"
                        @change="
                          changeEntregableStatus(
                            ent.id,
                            ($event.target as HTMLSelectElement).value,
                          )
                        "
                      >
                        <option value="pending">Pendiente</option>
                        <option value="approved">Aprobado</option>
                        <option value="revision">Revisión</option>
                        <option value="rejected">Rechazado</option>
                      </select>
                      <!-- Others: static badge -->
                      <span
                        v-else
                        class="text-[10px] px-2 py-0.5 rounded-md font-medium"
                        :class="{
                          'bg-emerald-100 text-emerald-700':
                            ent.status === 'approved',
                          'bg-amber-100 text-amber-700':
                            ent.status === 'pending',
                          'bg-orange-100 text-orange-700':
                            ent.status === 'revision',
                          'bg-red-100 text-red-700': ent.status === 'rejected',
                        }"
                      >
                        {{
                          ent.status === 'approved'
                            ? 'Aprobado'
                            : ent.status === 'pending'
                              ? 'Pendiente'
                              : ent.status === 'revision'
                                ? 'Revisión'
                                : 'Rechazado'
                        }}
                      </span>
                      <span
                        v-if="ent.published_at"
                        class="text-[10px] px-2 py-0.5 rounded-md font-medium bg-purple-100 text-purple-700"
                        >Publicado</span
                      >
                    </div>
                  </td>
                  <!-- Actions -->
                  <td class="py-3 px-3">
                    <div class="flex items-center justify-end gap-1">
                      <!-- View -->
                      <a
                        :href="ent.archivo"
                        target="_blank"
                        class="p-1.5 rounded-lg hover:bg-panel transition-colors"
                        title="Ver"
                      >
                        <svg
                          class="w-4 h-4 text-muted hover:text-ink"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                          />
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                        </svg>
                      </a>
                      <!-- Download -->
                      <a
                        :href="ent.archivo"
                        download
                        class="p-1.5 rounded-lg hover:bg-panel transition-colors"
                        title="Descargar"
                      >
                        <svg
                          class="w-4 h-4 text-muted hover:text-ink"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                          />
                        </svg>
                      </a>
                      <!-- Edit/Reupload (CM for revision, admin/employee always) -->
                      <button
                        v-if="isContentMaker && ent.status === 'revision'"
                        class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium bg-orange-100 text-orange-700 border border-orange-200 hover:bg-orange-200 transition-all"
                        title="Resubir con cambios realizados"
                        @click="
                          reuploadingId =
                            reuploadingId === ent.id ? null : ent.id
                        "
                      >
                        <svg
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                          />
                        </svg>
                        Resubir
                      </button>
                      <button
                        v-else-if="!isClient"
                        class="p-1.5 rounded-lg hover:bg-panel transition-colors"
                        title="Resubir contenido"
                        @click="
                          reuploadingId =
                            reuploadingId === ent.id ? null : ent.id
                        "
                      >
                        <svg
                          class="w-4 h-4 text-muted hover:text-ink"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                          />
                        </svg>
                      </button>
                      <!-- Delete (admin/employee only) -->
                      <button
                        v-if="isAdminOrEmployee"
                        :disabled="deletingId === ent.id"
                        class="p-1.5 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                        title="Eliminar"
                        @click="deleteEntregable(ent.id)"
                      >
                        <svg
                          class="w-4 h-4 text-red-400 hover:text-red-600"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                          />
                        </svg>
                      </button>
                      <!-- Review actions (Admin/Employee only) -->
                      <button
                        v-if="
                          isAdminOrEmployee &&
                          (ent.status === 'pending' ||
                            ent.status === 'revision')
                        "
                        class="p-1.5 rounded-lg hover:bg-emerald-50 transition-colors"
                        title="Aprobar"
                        @click="startReview(ent.id, 'approve')"
                      >
                        <svg
                          class="w-4 h-4 text-emerald-500 hover:text-emerald-700"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4.5 12.75l6 6 9-13.5"
                          />
                        </svg>
                      </button>
                      <button
                        v-if="
                          isAdminOrEmployee &&
                          (ent.status === 'pending' ||
                            ent.status === 'revision')
                        "
                        class="p-1.5 rounded-lg hover:bg-orange-50 transition-colors"
                        title="Pedir cambios"
                        @click="startReview(ent.id, 'reject')"
                      >
                        <svg
                          class="w-4 h-4 text-orange-500 hover:text-orange-700"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
                          />
                        </svg>
                      </button>
                      <!-- Publish action -->
                      <button
                        v-if="
                          isAdminOrEmployee &&
                          ent.status === 'approved' &&
                          !ent.published_at
                        "
                        :disabled="publishingId === ent.id"
                        class="p-1.5 rounded-lg hover:bg-purple-50 transition-colors disabled:opacity-50"
                        title="Marcar como publicado"
                        @click="markAsPublished(ent.id)"
                      >
                        <svg
                          class="w-4 h-4 text-purple-500 hover:text-purple-700"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"
                          />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
                <!-- Expanded revision notes row -->
                <tr
                  v-if="expandedRevisionId === ent.id && ent.revision_notes"
                  class="bg-orange-50/40"
                >
                  <td colspan="6" class="px-4 py-3">
                    <div
                      class="flex items-start gap-3 rounded-xl border border-orange-200/60 bg-white p-4"
                    >
                      <div
                        class="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center flex-shrink-0"
                      >
                        <svg
                          class="w-4 h-4 text-orange-600"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
                          />
                        </svg>
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-semibold text-orange-800 mb-1">
                          Cambios solicitados
                        </p>
                        <p
                          class="text-sm text-ink leading-relaxed whitespace-pre-line"
                        >
                          {{ ent.revision_notes }}
                        </p>
                        <p
                          v-if="ent.reviewed_by_name"
                          class="text-[11px] text-muted mt-2"
                        >
                          — {{ ent.reviewed_by_name }}
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>

          <!-- Reupload inline form -->
          <div
            v-if="reuploadingId"
            class="mt-4 rounded-xl border border-orange-200/50 bg-orange-50/30 p-4"
          >
            <div class="flex items-center gap-2 mb-3">
              <div
                class="w-6 h-6 rounded-md bg-orange-100 flex items-center justify-center"
              >
                <svg
                  class="w-3.5 h-3.5 text-orange-600"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                  />
                </svg>
              </div>
              <div>
                <p class="text-xs font-medium text-ink">
                  Resubir contenido con los cambios realizados
                </p>
                <p class="text-[11px] text-muted">
                  El archivo anterior será reemplazado y el entregable volverá a
                  revisión.
                </p>
              </div>
            </div>
            <!-- Show the revision notes for context -->
            <div
              v-if="
                entregables.find((e) => e.id === reuploadingId)?.revision_notes
              "
              class="mb-3 rounded-lg border border-orange-200/60 bg-white p-3"
            >
              <p class="text-[11px] text-orange-700 font-medium mb-0.5">
                Cambios que te pidieron:
              </p>
              <p class="text-xs text-ink whitespace-pre-line">
                {{
                  entregables.find((e) => e.id === reuploadingId)
                    ?.revision_notes
                }}
              </p>
            </div>
            <div class="flex items-end gap-3">
              <div class="flex-1">
                <input
                  type="file"
                  class="w-full text-xs text-ink file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-gold/10 file:text-gold hover:file:bg-gold/20 cursor-pointer"
                  @change="onReuploadFileChange"
                />
              </div>
              <button
                :disabled="!reuploadFile || actionLoading"
                class="px-4 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                @click="reuploadEntregable(reuploadingId)"
              >
                Subir
              </button>
              <button
                class="px-3 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all"
                @click="
                  reuploadingId = null;
                  reuploadFile = null;
                "
              >
                Cancelar
              </button>
            </div>
          </div>

          <!-- Review form (shown below table) -->
          <div
            v-if="reviewingId"
            class="mt-4 rounded-xl border border-border/60 bg-panel/30 p-4"
          >
            <p class="text-xs font-medium text-ink mb-2">
              {{
                reviewAction === 'approve'
                  ? 'Confirmar aprobación'
                  : 'Solicitar cambios'
              }}
            </p>
            <div v-if="reviewAction === 'reject'" class="mb-3">
              <label class="text-[11px] text-muted font-medium mb-1 block"
                >Notas para la creadora</label
              >
              <textarea
                v-model="reviewNotes"
                rows="2"
                placeholder="Describe qué cambios necesitas..."
                class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none"
              />
            </div>
            <div class="flex items-center gap-2">
              <button
                :disabled="actionLoading"
                class="px-4 py-1.5 rounded-lg text-xs font-medium text-white transition-all disabled:opacity-50"
                :class="
                  reviewAction === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-orange-600 hover:bg-orange-700'
                "
                @click="submitReview"
              >
                {{
                  reviewAction === 'approve'
                    ? 'Confirmar aprobación'
                    : 'Enviar revisión'
                }}
              </button>
              <button
                class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all"
                @click="cancelReview"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>

        <!-- No entregables yet -->
        <div v-else-if="!canUploadEntregable" class="text-center py-8">
          <svg
            class="w-10 h-10 mx-auto text-muted/30 mb-3"
            fill="none"
            stroke="currentColor"
            stroke-width="1"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
          <p class="text-xs text-muted">Aún no se han subido entregables</p>
        </div>
      </div>
    </template>

    <!-- Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="confirmAction.show"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="absolute inset-0 bg-black/40 backdrop-blur-sm"
          @click="cancelConfirmAction"
        />
        <div
          class="relative w-full max-w-sm bg-white rounded-2xl shadow-elevated p-6 animate-scale-in"
        >
          <div class="flex items-center gap-3 mb-4">
            <div
              class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0"
            >
              <svg
                class="w-5 h-5 text-amber-600"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
            </div>
            <h3 class="text-sm font-semibold text-ink">
              {{ confirmAction.title }}
            </h3>
          </div>
          <p class="text-xs text-muted leading-relaxed mb-6">
            {{ confirmAction.message }}
          </p>
          <div class="flex items-center justify-end gap-3">
            <button
              class="px-4 py-2 rounded-xl text-sm font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
              @click="cancelConfirmAction"
            >
              Cancelar
            </button>
            <button
              :disabled="actionLoading"
              class="px-5 py-2 rounded-xl text-sm font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
              @click="executeConfirmAction"
            >
              Confirmar
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- CM Browser Modal -->
    <Teleport to="body">
      <div
        v-if="showCMBrowser"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="absolute inset-0 bg-black/40 backdrop-blur-sm"
          @click="showCMBrowser = false"
        />
        <div
          class="relative w-full max-w-2xl max-h-[80vh] bg-white rounded-2xl shadow-elevated flex flex-col animate-scale-in"
        >
          <!-- Header -->
          <div
            class="p-5 border-b border-border/40 flex items-center justify-between flex-shrink-0"
          >
            <div v-if="!selectedCMProfile" class="flex items-center gap-3">
              <h3 class="text-sm font-semibold text-ink">
                Encuentra a tu Content Maker
              </h3>
            </div>
            <div v-else class="flex items-center gap-3">
              <button
                class="p-1.5 rounded-lg hover:bg-panel transition-colors"
                @click="backToGrid"
              >
                <svg
                  class="w-4 h-4 text-muted"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.75 19.5L8.25 12l7.5-7.5"
                  />
                </svg>
              </button>
              <h3 class="text-sm font-semibold text-ink">
                {{ selectedCMProfile.nombre }}
              </h3>
            </div>
            <button
              class="p-1.5 rounded-lg hover:bg-panel transition-colors"
              @click="showCMBrowser = false"
            >
              <svg
                class="w-4 h-4 text-muted"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <!-- Grid View -->
          <div
            v-if="!selectedCMProfile"
            class="flex-1 overflow-auto p-5 space-y-4"
          >
            <!-- Search bar inside modal -->
            <div class="relative">
              <div
                class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
              >
                <svg
                  class="w-4 h-4 text-muted/50"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                  />
                </svg>
              </div>
              <input
                v-model="cmBrowserSearch"
                type="text"
                placeholder="Buscar por nombre o Instagram..."
                class="w-full h-10 pl-10 pr-4 rounded-xl border border-border/60 bg-panel/30 text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 transition-all"
                @input="onCMBrowserSearchInput"
              />
            </div>

            <!-- Loading -->
            <div v-if="cmBrowserLoading" class="flex justify-center py-8">
              <div
                class="w-6 h-6 rounded-full border-2 border-gold/30 border-t-gold animate-spin"
              />
            </div>

            <!-- Photo Grid -->
            <div
              v-else-if="cmBrowserResults.length > 0"
              class="grid grid-cols-3 sm:grid-cols-4 gap-3"
            >
              <div
                v-for="cm in cmBrowserResults"
                :key="cm.id"
                class="group cursor-pointer"
                @click="viewCMProfile(cm)"
              >
                <div
                  class="aspect-square rounded-xl overflow-hidden border border-border/40 group-hover:border-gold/60 group-hover:shadow-md transition-all"
                >
                  <img
                    v-if="cm.foto_url"
                    :src="cm.foto_url"
                    :alt="cm.nombre"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div
                    v-else
                    class="w-full h-full bg-gradient-to-br from-gold/10 to-gold/5 flex items-center justify-center"
                  >
                    <span class="text-lg font-bold text-gold/60">{{
                      cm.nombre
                        ?.split(' ')
                        .map((n: string) => n[0])
                        .join('')
                        .slice(0, 2)
                    }}</span>
                  </div>
                </div>
                <p
                  class="mt-1.5 text-[11px] font-medium text-ink text-center truncate group-hover:text-gold transition-colors"
                >
                  {{ cm.nombre }}
                </p>
              </div>
            </div>

            <!-- No results -->
            <div v-else class="text-center py-8">
              <p class="text-xs text-muted">No se encontraron Content Makers</p>
            </div>
          </div>

          <!-- CM Profile View -->
          <div v-else class="flex-1 overflow-auto p-5">
            <div class="flex flex-col items-center text-center space-y-4">
              <!-- Photo -->
              <div
                class="w-32 h-32 rounded-2xl overflow-hidden border-2 border-gold/20 shadow-lg"
              >
                <img
                  v-if="selectedCMProfile.foto_url"
                  :src="selectedCMProfile.foto_url"
                  :alt="selectedCMProfile.nombre"
                  class="w-full h-full object-cover"
                />
                <div
                  v-else
                  class="w-full h-full bg-gradient-to-br from-gold/10 to-gold/5 flex items-center justify-center"
                >
                  <span class="text-3xl font-bold text-gold/60">{{
                    selectedCMProfile.nombre
                      ?.split(' ')
                      .map((n: string) => n[0])
                      .join('')
                      .slice(0, 2)
                  }}</span>
                </div>
              </div>

              <!-- Name -->
              <div>
                <h4 class="text-lg font-semibold text-ink">
                  {{ selectedCMProfile.nombre }}
                </h4>
                <p
                  v-if="selectedCMProfile.instagram_handle"
                  class="text-sm text-muted mt-1"
                >
                  @{{ selectedCMProfile.instagram_handle }}
                </p>
              </div>

              <!-- Stats -->
              <div
                v-if="selectedCMProfile.seguidores_instagram"
                class="flex items-center gap-1 text-sm text-muted"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"
                  />
                </svg>
                <span
                  >{{
                    selectedCMProfile.seguidores_instagram?.toLocaleString()
                  }}
                  seguidores</span
                >
              </div>

              <!-- Action buttons -->
              <div class="mt-4 flex items-center gap-3">
                <NuxtLink
                  :to="`/dashboard/content-makers/${selectedCMProfile.id}?fromProject=${route.params.id}`"
                  class="px-5 py-2.5 rounded-xl text-sm font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
                >
                  Ver perfil
                </NuxtLink>
                <button
                  v-if="!selectedCMIds.includes(selectedCMProfile.id)"
                  :disabled="actionLoading"
                  class="px-6 py-2.5 rounded-xl text-sm font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                  @click="selectCM(selectedCMProfile.id)"
                >
                  Seleccionar
                </button>
                <span
                  v-else
                  class="px-4 py-2.5 rounded-xl text-sm font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
                >
                  ✓ Invitación enviada
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Status Override Modal -->
    <Teleport to="body">
      <div
        v-if="showOverrideModal"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="absolute inset-0 bg-black/40 backdrop-blur-sm"
          @click="showOverrideModal = false"
        />
        <div
          class="relative w-full max-w-md bg-white rounded-2xl shadow-elevated p-6 animate-scale-in"
        >
          <h3 class="text-sm font-semibold text-ink mb-4">
            Cambiar estado manualmente
          </h3>
          <p class="text-xs text-muted mb-4">
            Este cambio quedará registrado en la auditoría. El motivo es
            obligatorio.
          </p>
          <div class="space-y-4">
            <div>
              <label class="text-[11px] text-muted font-medium mb-1 block"
                >Nuevo estado</label
              >
              <select
                v-model="overrideStatus"
                class="w-full h-9 px-3 rounded-lg border border-border/60 bg-white text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40"
              >
                <option value="">Selecciona un estado</option>
                <option
                  v-for="s in projectsStore.filters.statuses"
                  :key="s.id"
                  :value="s.nombre"
                >
                  {{ s.nombre }}
                </option>
              </select>
            </div>
            <div>
              <label class="text-[11px] text-muted font-medium mb-1 block"
                >Motivo del cambio *</label
              >
              <textarea
                v-model="overrideReason"
                rows="3"
                placeholder="Explica por qué se cambia el estado manualmente..."
                class="w-full px-3 py-2 rounded-lg border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 resize-none"
              />
            </div>
            <div class="flex items-center justify-end gap-3 pt-2">
              <button
                class="px-4 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink transition-all"
                @click="showOverrideModal = false"
              >
                Cancelar
              </button>
              <button
                :disabled="
                  !overrideStatus || !overrideReason.trim() || overrideSaving
                "
                class="px-5 py-2 rounded-xl text-xs font-medium bg-gold text-white hover:bg-gold/90 shadow-gold-sm transition-all disabled:opacity-50"
                @click="submitOverride"
              >
                {{ overrideSaving ? 'Guardando...' : 'Cambiar estado' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
