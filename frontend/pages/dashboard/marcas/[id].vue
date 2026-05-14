<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useBrandsStore, type BrandDetail } from "~/stores/brands";
import { useClientsStore } from "~/stores/clients";
import { formatBrandId } from "~/utils/formatId";

definePageMeta({ middleware: ["auth", "role"] });

const route = useRoute();
const router = useRouter();
const store = useBrandsStore();
const clientsStore = useClientsStore();
const auth = useAuthStore();

const brand = ref<BrandDetail | null>(null);
const isLoading = ref(true);
const error = ref("");

// Edit state
const isEditing = ref(false);
const isSaving = ref(false);
const editData = ref<Record<string, unknown>>({});
const saveError = ref("");

// Delete
const showDeleteModal = ref(false);
const isDeleting = ref(false);

const canEdit = computed(() => {
  return auth.user?.role === "admin" || auth.user?.role === "stimada_employee";
});

async function load() {
  isLoading.value = true;
  try {
    brand.value = await store.fetchDetail(route.params.id as string);
  } catch {
    error.value = "No se pudo cargar la marca.";
  } finally {
    isLoading.value = false;
  }
}

function startEditing() {
  if (!brand.value) return;
  editData.value = { ...brand.value };
  isEditing.value = true;
  saveError.value = "";
}

function cancelEditing() {
  isEditing.value = false;
  editData.value = {};
}

async function saveChanges() {
  if (!brand.value) return;
  isSaving.value = true;
  saveError.value = "";
  try {
    const payload: Record<string, unknown> = {};
    const editableKeys = ["nombre", "tipo_marca", "web_instagram", "notas", "estado"];
    for (const key of editableKeys) {
      if (editData.value[key] !== (brand.value as Record<string, unknown>)[key]) {
        payload[key] = editData.value[key];
      }
    }
    if (Object.keys(payload).length === 0) {
      isEditing.value = false;
      return;
    }
    brand.value = await store.update(route.params.id as string, payload);
    isEditing.value = false;
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      const firstField = Object.keys(e.data)[0];
      saveError.value = Array.isArray(e.data[firstField]) ? e.data[firstField][0] : "Error al guardar.";
    } else {
      saveError.value = "Error al guardar los cambios.";
    }
  } finally {
    isSaving.value = false;
  }
}

async function handleDelete() {
  isDeleting.value = true;
  try {
    await store.deleteBrand(route.params.id as string);
    router.push("/dashboard/marcas");
  } catch {
    showDeleteModal.value = false;
  } finally {
    isDeleting.value = false;
  }
}

onMounted(() => clientsStore.fetchTypes());
load();
</script>

<template>
  <div class="max-w-3xl animate-fade-up">
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <div class="w-10 h-10 rounded-full border-2 border-gold/20 border-t-gold animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-sm text-red-400">{{ error }}</p>
    </div>

    <div v-else-if="brand" class="space-y-6">
      <!-- Back -->
      <NuxtLink to="/dashboard/marcas" class="group inline-flex items-center gap-2 text-xs text-muted hover:text-ink transition-colors">
        <svg class="w-4 h-4 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Volver a Marcas
      </NuxtLink>

      <!-- Header -->
      <div class="rounded-2xl border border-border/60 bg-white shadow-card p-7">
        <div class="flex items-start justify-between gap-6">
          <div class="flex items-center gap-5">
            <div class="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-400/20 flex items-center justify-center text-indigo-400 text-xl font-semibold">
              {{ brand.nombre.charAt(0) }}
            </div>
            <div>
              <h1 class="text-2xl font-semibold tracking-tight text-ink">{{ brand.nombre }}</h1>
              <div class="flex items-center gap-2.5 mt-1.5">
                <span class="text-[11px] text-muted/70 font-mono">{{ formatBrandId(brand.brand_id) }}</span>
                <span v-if="brand.tipo_marca_nombre" class="text-[11px] px-2 py-0.5 rounded-full border border-indigo-400/15 text-indigo-400 bg-indigo-400/[0.06] font-medium">
                  {{ brand.tipo_marca_nombre }}
                </span>
                <span
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border"
                  :class="brand.estado === 'activa' ? 'text-emerald-400 bg-emerald-400/[0.06] border-emerald-400/15' : 'text-muted/60 bg-panel border-border/40'"
                >
                  {{ brand.estado === 'activa' ? 'Activa' : 'Inactiva' }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="canEdit && !isEditing" class="flex items-center gap-2">
            <button class="px-4 h-9 rounded-xl border border-border/80 text-xs font-medium text-muted hover:text-ink hover:border-ink/20 transition-all" @click="startEditing">
              Editar
            </button>
            <button class="px-4 h-9 rounded-xl border border-red-500/15 text-xs font-medium text-red-400/80 hover:text-red-400 hover:bg-red-500/[0.06] transition-all" @click="showDeleteModal = true">
              Eliminar
            </button>
          </div>
          <div v-if="isEditing" class="flex items-center gap-2">
            <button class="px-4 h-9 rounded-xl border border-border text-xs font-medium text-muted hover:text-ink transition-all" :disabled="isSaving" @click="cancelEditing">
              Cancelar
            </button>
            <button class="px-5 h-9 rounded-xl bg-gold text-ink text-xs font-semibold hover:bg-gold/90 disabled:opacity-60 transition-all" :disabled="isSaving" @click="saveChanges">
              {{ isSaving ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Save error -->
      <div v-if="saveError" class="rounded-2xl border border-red-500/20 px-5 py-3 text-xs text-red-400">
        {{ saveError }}
      </div>

      <!-- VIEW MODE -->
      <template v-if="!isEditing">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-3">
            <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Datos de la marca</h3>
            <div class="space-y-2.5 text-xs">
              <div class="flex justify-between"><span class="text-muted">Nombre</span><span class="text-ink font-medium">{{ brand.nombre }}</span></div>
              <div class="flex justify-between"><span class="text-muted">Tipo</span><span class="text-ink">{{ brand.tipo_marca_nombre || '—' }}</span></div>
              <div class="flex justify-between"><span class="text-muted">Web / Instagram</span>
                <a v-if="brand.web_instagram" :href="brand.web_instagram" target="_blank" class="text-gold hover:text-gold/80 truncate max-w-[200px]">{{ brand.web_instagram }}</a>
                <span v-else class="text-muted/50">—</span>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-3">
            <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Cliente asociado</h3>
            <div class="space-y-2.5 text-xs">
              <div class="flex justify-between"><span class="text-muted">Cliente</span>
                <NuxtLink :to="`/dashboard/clientes/${brand.client}`" class="text-ink font-medium hover:text-gold transition-colors">
                  {{ brand.client_name }}
                </NuxtLink>
              </div>
            </div>
          </div>
        </div>

        <div v-if="brand.notas" class="rounded-2xl border border-border/60 bg-white shadow-card p-6">
          <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted mb-3">Notas</h3>
          <p class="text-sm text-muted leading-relaxed whitespace-pre-wrap">{{ brand.notas }}</p>
        </div>

        <!-- Proyectos asociados -->
        <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center">
              <svg class="w-3.5 h-3.5 text-gold" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
            </div>
            <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Proyectos asociados</h3>
            <span v-if="brand.proyectos && brand.proyectos.length" class="ml-auto text-[10px] text-muted/60 bg-panel px-2 py-0.5 rounded-full border border-border/40">{{ brand.proyectos.length }}</span>
          </div>
          <div v-if="brand.proyectos && brand.proyectos.length > 0" class="space-y-2">
            <NuxtLink
              v-for="project in brand.proyectos"
              :key="project.id"
              :to="`/proyectos/${project.id}`"
              class="flex items-center justify-between p-3.5 rounded-xl border border-border/50 hover:border-gold/30 hover:bg-gold/[0.02] transition-all duration-200 group/item"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium text-ink truncate group-hover/item:text-gold transition-colors duration-200">{{ project.nombre }}</p>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-[11px] text-muted/70 font-mono">{{ project.project_id }}</span>
                    <span v-if="project.content_maker_name" class="text-[11px] text-muted/70">· {{ project.content_maker_name }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-3 flex-shrink-0 ml-3">
                <span
                  v-if="project.status_name"
                  class="text-[11px] font-medium px-2 py-0.5 rounded-full border border-border bg-panel text-muted"
                >
                  {{ project.status_name }}
                </span>
                <span v-if="project.fecha_servicio" class="text-[11px] text-muted/60 hidden sm:inline">
                  {{ new Date(project.fecha_servicio).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" }) }}
                </span>
                <svg class="w-4 h-4 text-muted/40 group-hover/item:text-gold transition-colors duration-200" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </div>
            </NuxtLink>
          </div>
          <div v-else class="py-4 text-center">
            <p class="text-xs text-muted/60">Esta marca no tiene proyectos asociados.</p>
          </div>
        </div>
      </template>

      <!-- EDIT MODE -->
      <template v-if="isEditing">
        <div class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4">
          <h3 class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold">Editar marca</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Nombre de la marca</label>
              <input v-model="editData.nombre" type="text" class="input-field" />
            </div>
            <div>
              <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Tipo de marca</label>
              <select v-model="editData.tipo_marca" class="select-field">
                <option :value="null">Sin tipo</option>
                <option v-for="t in clientsStore.types" :key="t.id" :value="t.id">{{ t.nombre }}</option>
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Web / Instagram</label>
              <input v-model="editData.web_instagram" type="url" class="input-field" />
            </div>
            <div>
              <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Estado</label>
              <select v-model="editData.estado" class="select-field">
                <option value="activa">Activa</option>
                <option value="inactiva">Inactiva</option>
              </select>
            </div>
            <div class="md:col-span-2">
              <label class="block text-[11px] font-medium text-muted/70 mb-2 uppercase tracking-wider">Notas</label>
              <textarea v-model="editData.notas" rows="3" class="input-field resize-none" />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- DELETE MODAL -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background: rgba(0,0,0,0.75); backdrop-filter: blur(8px)" @click.self="showDeleteModal = false">
          <div class="w-full max-w-sm rounded-3xl border border-red-500/20 p-8 shadow-2xl" style="background: linear-gradient(180deg, #161619 0%, #111113 100%)">
            <h2 class="text-lg font-semibold text-ink mb-2">Eliminar marca</h2>
            <p class="text-sm text-muted mb-6">¿Estás seguro de que quieres eliminar <strong class="text-ink">{{ brand?.nombre }}</strong>?</p>
            <div class="flex gap-3">
              <button class="flex-1 h-11 rounded-xl border border-border text-sm text-muted hover:text-ink transition-all" :disabled="isDeleting" @click="showDeleteModal = false">Cancelar</button>
              <button class="flex-1 h-11 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-400 disabled:opacity-60 transition-all" :disabled="isDeleting" @click="handleDelete">
                {{ isDeleting ? 'Eliminando…' : 'Eliminar' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
