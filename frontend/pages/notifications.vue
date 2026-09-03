<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore, type NotificationItem } from "~/stores/notifications";

definePageMeta({
  layout: "app",
  middleware: ["auth"],
});

const auth = useAuthStore();
const notificationsStore = useNotificationsStore();
const config = useRuntimeConfig();
const router = useRouter();

const notifications = ref<NotificationItem[]>([]);
const isLoading = ref(true);
const totalCount = ref(0);
const currentPage = ref(1);
const pageSize = 20;

// Filters
const searchQuery = ref("");
const selectedType = ref<string>("");
const selectedRead = ref<string>("");

const typeOptions = [
  { value: "", label: "Todos los tipos" },
  { value: "project_cm_select", label: "Seleccionar Content Maker" },
  { value: "project_cm_request", label: "Solicitud de campaña" },
  { value: "project_cm_accepted", label: "Campaña aceptada" },
  { value: "project_cm_rejected", label: "Campaña rechazada" },
  { value: "briefing_submitted", label: "Briefing recibido" },
];

const readOptions = [
  { value: "", label: "Todas" },
  { value: "false", label: "Sin leer" },
  { value: "true", label: "Leídas" },
];

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

async function fetchNotifications() {
  isLoading.value = true;
  try {
    const params: Record<string, string> = {
      page: String(currentPage.value),
      page_size: String(pageSize),
    };
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim();
    if (selectedType.value) params.type = selectedType.value;
    if (selectedRead.value) params.read = selectedRead.value;

    const data = await $fetch<{ count: number; results: NotificationItem[] }>(
      `${config.public.apiBase}/notifications/`,
      {
        params,
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      }
    );
    notifications.value = data.results;
    totalCount.value = data.count;
  } catch {
    notifications.value = [];
  } finally {
    isLoading.value = false;
  }
}

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1;
    fetchNotifications();
  }, 300);
}

function onFilterChange() {
  currentPage.value = 1;
  fetchNotifications();
}

function nextPage() {
  if (currentPage.value * pageSize < totalCount.value) {
    currentPage.value++;
    fetchNotifications();
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchNotifications();
  }
}

async function handleClick(notif: NotificationItem) {
  if (!notif.read) {
    await notificationsStore.markRead(notif.id);
    const item = notifications.value.find((n) => n.id === notif.id);
    if (item) item.read = true;
  }
  if (notif.project) {
    router.push(`/projects/${notif.project}`);
  }
}

async function markAllRead() {
  await notificationsStore.markAllRead();
  notifications.value.forEach((n) => (n.read = true));
}

function formatTimeAgo(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Ahora";
  if (mins < 60) return `Hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Hace ${days}d`;
  return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
}

function getTypeIcon(type: string) {
  switch (type) {
    case "project_cm_request": return "campaign";
    case "project_cm_select": return "select";
    case "project_cm_accepted": return "accepted";
    case "project_cm_rejected": return "rejected";
    case "briefing_submitted": return "briefing";
    default: return "default";
  }
}

function getTypeLabel(type: string) {
  return typeOptions.find((t) => t.value === type)?.label || type;
}

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize));
const hasUnread = computed(() => notifications.value.some((n) => !n.read));

onMounted(fetchNotifications);
</script>

<template>
  <div class="max-w-3xl mx-auto px-8 py-10 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-ink">Notificaciones</h1>
        <p class="text-sm text-muted mt-1">{{ totalCount }} notificación{{ totalCount !== 1 ? 'es' : '' }}</p>
      </div>
      <button
        v-if="hasUnread"
        class="px-4 py-2 rounded-xl text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all"
        @click="markAllRead"
      >
        Marcar todas como leídas
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
      <!-- Search -->
      <div class="relative flex-1">
        <div class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg class="w-4 h-4 text-muted/50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar notificaciones..."
          class="w-full h-9 pl-10 pr-4 rounded-xl border border-border/60 bg-white text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-gold/20 focus:border-gold/40 transition-all"
          @input="onSearchInput"
        />
      </div>

      <!-- Type filter -->
      <BaseSelect
        v-model="selectedType"
        size="sm"
        class="min-w-[150px] max-w-[200px]"
        :options="typeOptions.map((opt) => ({ value: opt.value, label: opt.label }))"
        @change="onFilterChange"
      />

      <!-- Read filter -->
      <BaseSelect
        v-model="selectedRead"
        size="sm"
        class="min-w-[150px] max-w-[200px]"
        :options="readOptions.map((opt) => ({ value: opt.value, label: opt.label }))"
        @change="onFilterChange"
      />
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="notifications.length === 0" class="text-center py-20">
      <svg class="w-12 h-12 text-muted/20 mx-auto mb-4" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
      </svg>
      <p class="text-sm text-muted">No se encontraron notificaciones</p>
      <p v-if="searchQuery || selectedType || selectedRead" class="text-xs text-muted/70 mt-1">Prueba a cambiar los filtros</p>
    </div>

    <!-- Notifications List -->
    <div v-else class="space-y-2">
      <div
        v-for="notif in notifications"
        :key="notif.id"
        class="group flex items-start gap-4 p-4 rounded-xl border transition-all duration-200 cursor-pointer"
        :class="notif.read
          ? 'border-border/40 bg-white hover:border-border/60 hover:shadow-soft'
          : 'border-gold/20 bg-gold/5 hover:border-gold/30 hover:shadow-soft'"
        @click="handleClick(notif)"
      >
        <!-- Icon -->
        <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          :class="notif.read ? 'bg-panel' : 'bg-gold/10'">
          <!-- Campaign request -->
          <svg v-if="getTypeIcon(notif.notification_type) === 'campaign'" class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-gold'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
          </svg>
          <!-- Select CM -->
          <svg v-else-if="getTypeIcon(notif.notification_type) === 'select'" class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-blue-600'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <!-- Accepted -->
          <svg v-else-if="getTypeIcon(notif.notification_type) === 'accepted'" class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-emerald-600'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Rejected -->
          <svg v-else-if="getTypeIcon(notif.notification_type) === 'rejected'" class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-red-500'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Briefing -->
          <svg v-else-if="getTypeIcon(notif.notification_type) === 'briefing'" class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-blue-600'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <!-- Default -->
          <svg v-else class="w-5 h-5" :class="notif.read ? 'text-muted' : 'text-gold'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm font-medium text-ink" :class="{ 'font-semibold': !notif.read }">{{ notif.title }}</p>
              <p class="text-xs text-muted mt-1 line-clamp-2">{{ notif.message }}</p>
            </div>
            <div class="flex flex-col items-end gap-1 flex-shrink-0">
              <span class="text-[10px] text-muted">{{ formatTimeAgo(notif.created_at) }}</span>
              <span v-if="!notif.read" class="w-2 h-2 rounded-full bg-gold" />
            </div>
          </div>
          <div class="flex items-center gap-2 mt-2">
            <span class="px-2 py-0.5 rounded-md text-[10px] font-medium bg-panel border border-border/40 text-muted">
              {{ getTypeLabel(notif.notification_type) }}
            </span>
            <span v-if="notif.project_id_display" class="text-[10px] text-muted/70">
              {{ notif.project_id_display }}
            </span>
          </div>
        </div>

        <!-- Arrow -->
        <svg v-if="notif.project" class="w-4 h-4 text-muted/30 group-hover:text-muted/60 flex-shrink-0 mt-2 transition-colors" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-8 pt-6 border-t border-border/40">
      <p class="text-xs text-muted">
        Página {{ currentPage }} de {{ totalPages }}
      </p>
      <div class="flex items-center gap-2">
        <button
          :disabled="currentPage <= 1"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          @click="prevPage"
        >
          Anterior
        </button>
        <button
          :disabled="currentPage >= totalPages"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/60 text-muted hover:text-ink hover:border-ink/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          @click="nextPage"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>
