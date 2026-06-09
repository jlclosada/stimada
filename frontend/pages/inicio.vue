<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore, type NotificationItem } from "~/stores/notifications";
import { formatProjectId } from "~/utils/formatId";

definePageMeta({
  layout: "app",
  middleware: ["auth"],
});

const auth = useAuthStore();
const notificationsStore = useNotificationsStore();
const config = useRuntimeConfig();

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return "Buenos días";
  if (hour < 20) return "Buenas tardes";
  return "Buenas noches";
});

const isAdminOrEmployee = computed(() =>
  auth.user?.role === "admin" || auth.user?.role === "stimada_employee"
);

const isClient = computed(() => auth.user?.role === "client");
const isContentMaker = computed(() => auth.user?.role === "content_maker");

// Pending projects for client
const pendingProjects = ref<any[]>([]);
const loadingProjects = ref(false);

// Client dashboard metrics
const dashboard = ref<any>(null);
const loadingDashboard = ref(false);

async function fetchPendingProjects() {
  if (!auth.accessToken || isAdminOrEmployee.value) return;
  // Only fetch projects for clients
  if (!isClient.value) return;
  loadingProjects.value = true;
  try {
    const data = await $fetch<{ results: any[] }>(
      `${config.public.apiBase}/projects/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    pendingProjects.value = data.results || [];
  } catch {
    pendingProjects.value = [];
  } finally {
    loadingProjects.value = false;
  }
}

async function fetchClientDashboard() {
  if (!auth.accessToken || !isClient.value) return;
  loadingDashboard.value = true;
  try {
    dashboard.value = await $fetch(
      `${config.public.apiBase}/projects/client_dashboard/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
  } catch {
    dashboard.value = null;
  } finally {
    loadingDashboard.value = false;
  }
}

// Favorite CMs for client
const favoriteCMs = ref<any[]>([]);

async function fetchFavoriteCMs() {
  if (!auth.accessToken || !isClient.value) return;
  try {
    favoriteCMs.value = await $fetch<any[]>(
      `${config.public.apiBase}/clients/me/favorite-cms/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
  } catch {
    favoriteCMs.value = [];
  }
}

// Notifications for CM
const notifications = ref<NotificationItem[]>([]);
const loadingNotifications = ref(false);

async function fetchNotifications() {
  if (!auth.accessToken || !isContentMaker.value) return;
  loadingNotifications.value = true;
  try {
    const data = await $fetch<{ results: NotificationItem[] }>(
      `${config.public.apiBase}/notifications/`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    notifications.value = data.results || [];
  } catch {
    notifications.value = [];
  } finally {
    loadingNotifications.value = false;
  }
}

const unreadNotifications = computed(() => notifications.value.filter((n) => !n.read));
const recentNotifications = computed(() => notifications.value.slice(0, 8));

const router = useRouter();

async function handleNotificationClick(notif: NotificationItem) {
  if (!notif.read) {
    await notificationsStore.markRead(notif.id);
    const item = notifications.value.find((n) => n.id === notif.id);
    if (item) item.read = true;
  }
  if (notif.project) {
    router.push(`/proyectos/${notif.project}`);
  }
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
  return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
}

onMounted(() => {
  fetchPendingProjects();
  fetchClientDashboard();
  fetchFavoriteCMs();
  fetchNotifications();
});

interface QuickAction {
  title: string;
  description: string;
  href: string;
  icon: string;
  color: string;
}

const quickActions = computed<QuickAction[]>(() => {
  if (isAdminOrEmployee.value) {
    return [
      {
        title: "Content Makers",
        description: "Gestiona perfiles, filtros y datos de creadores de contenido",
        href: "/dashboard/content-makers",
        icon: "star",
        color: "from-amber-500/10 to-orange-500/10 border-amber-200/60",
      },
      {
        title: "Clientes",
        description: "Administra clientes, contratos y contactos",
        href: "/dashboard/clientes",
        icon: "briefcase",
        color: "from-emerald-500/10 to-teal-500/10 border-emerald-200/60",
      },
      {
        title: "Proyectos",
        description: "Crea y gestiona proyectos con clientes y content makers",
        href: "/proyectos",
        icon: "folder",
        color: "from-blue-500/10 to-indigo-500/10 border-blue-200/60",
      },
      {
        title: "Usuarios",
        description: "Gestiona empleados y cuentas del equipo",
        href: "/dashboard/usuarios",
        icon: "users",
        color: "from-violet-500/10 to-purple-500/10 border-violet-200/60",
      },
    ];
  }
  if (isClient.value) {
    return [
      {
        title: "Mis proyectos",
        description: "Revisa el estado de tus proyectos activos",
        href: "/proyectos",
        icon: "folder",
        color: "from-blue-500/10 to-indigo-500/10 border-blue-200/60",
      },
      {
        title: "Content Makers",
        description: "Explora perfiles de creadoras de contenido",
        href: "/dashboard/content-makers",
        icon: "star",
        color: "from-amber-500/10 to-orange-500/10 border-amber-200/60",
      },
    ];
  }
  if (isContentMaker.value) {
    return [
      {
        title: "Mis campañas",
        description: "Gestiona tus campañas y solicitudes pendientes",
        href: "/proyectos",
        icon: "folder",
        color: "from-orange-500/10 to-amber-500/10 border-orange-200/60",
      },
      {
        title: "Mi perfil",
        description: "Edita tus datos, redes sociales y tallaje",
        href: "/dashboard/content-makers/me",
        icon: "star",
        color: "from-violet-500/10 to-purple-500/10 border-violet-200/60",
      },
    ];
  }
  return [];
});

// Calendar helpers
const calendarMonth = ref(new Date());

// Color palette for projects
const PROJECT_COLORS = [
  { bg: 'bg-blue-100', border: 'border-blue-300', text: 'text-blue-700', highlight: 'bg-blue-500', light: 'bg-blue-50' },
  { bg: 'bg-emerald-100', border: 'border-emerald-300', text: 'text-emerald-700', highlight: 'bg-emerald-500', light: 'bg-emerald-50' },
  { bg: 'bg-violet-100', border: 'border-violet-300', text: 'text-violet-700', highlight: 'bg-violet-500', light: 'bg-violet-50' },
  { bg: 'bg-amber-100', border: 'border-amber-300', text: 'text-amber-700', highlight: 'bg-amber-500', light: 'bg-amber-50' },
  { bg: 'bg-rose-100', border: 'border-rose-300', text: 'text-rose-700', highlight: 'bg-rose-500', light: 'bg-rose-50' },
  { bg: 'bg-cyan-100', border: 'border-cyan-300', text: 'text-cyan-700', highlight: 'bg-cyan-500', light: 'bg-cyan-50' },
  { bg: 'bg-orange-100', border: 'border-orange-300', text: 'text-orange-700', highlight: 'bg-orange-500', light: 'bg-orange-50' },
  { bg: 'bg-indigo-100', border: 'border-indigo-300', text: 'text-indigo-700', highlight: 'bg-indigo-500', light: 'bg-indigo-50' },
];

function getProjectColor(projectId: number) {
  const ranges = dashboard.value?.project_ranges || [];
  const idx = ranges.findIndex((r: any) => r.id === projectId);
  return PROJECT_COLORS[idx % PROJECT_COLORS.length];
}

interface CalendarDay {
  date: Date;
  dateStr: string;
  inMonth: boolean;
  isToday: boolean;
  projects: { id: number; nombre: string; project_id: string; type: 'range' | 'servicio'; color: any }[];
}

const calendarDays = computed<CalendarDay[]>(() => {
  const year = calendarMonth.value.getFullYear();
  const month = calendarMonth.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDow = (firstDay.getDay() + 6) % 7; // Monday = 0
  const today = new Date();
  const todayStr = today.toISOString().split("T")[0];

  const days: CalendarDay[] = [];

  // Previous month trailing days
  for (let i = startDow - 1; i >= 0; i--) {
    const d = new Date(year, month, -i);
    days.push({ date: d, dateStr: d.toISOString().split("T")[0], inMonth: false, isToday: false, projects: [] });
  }
  // Current month days
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const d = new Date(year, month, i);
    const dateStr = d.toISOString().split("T")[0];
    days.push({ date: d, dateStr, inMonth: true, isToday: dateStr === todayStr, projects: [] });
  }
  // Next month leading days
  const remaining = 7 - (days.length % 7);
  if (remaining < 7) {
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i);
      days.push({ date: d, dateStr: d.toISOString().split("T")[0], inMonth: false, isToday: false, projects: [] });
    }
  }

  // Map project ranges onto days
  const ranges = dashboard.value?.project_ranges || [];
  for (const range of ranges) {
    const start = range.fecha_inicio;
    const end = range.fecha_fin;
    const servicio = range.fecha_servicio;
    const color = getProjectColor(range.id);

    for (const day of days) {
      let isInRange = false;
      let isServicio = false;

      if (start && end) {
        isInRange = day.dateStr >= start && day.dateStr <= end;
      } else if (start && servicio) {
        isInRange = day.dateStr >= start && day.dateStr <= servicio;
      } else if (servicio && end) {
        isInRange = day.dateStr >= servicio && day.dateStr <= end;
      }

      if (servicio && day.dateStr === servicio) {
        isServicio = true;
      }

      if (isServicio) {
        day.projects.push({ id: range.id, nombre: range.nombre, project_id: range.project_id, type: 'servicio', color });
      } else if (isInRange) {
        day.projects.push({ id: range.id, nombre: range.nombre, project_id: range.project_id, type: 'range', color });
      }
    }
  }

  return days;
});

const calendarMonthLabel = computed(() => {
  return calendarMonth.value.toLocaleDateString("es-ES", { month: "long", year: "numeric" });
});

function prevMonth() {
  const d = new Date(calendarMonth.value);
  d.setMonth(d.getMonth() - 1);
  calendarMonth.value = d;
}

function nextMonth() {
  const d = new Date(calendarMonth.value);
  d.setMonth(d.getMonth() + 1);
  calendarMonth.value = d;
}

// Tooltip for calendar hover
const hoveredDay = ref<CalendarDay | null>(null);
const tooltipPos = ref({ x: 0, y: 0 });

function onDayHover(day: CalendarDay, event: MouseEvent) {
  if (day.projects.length) {
    hoveredDay.value = day;
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    tooltipPos.value = { x: rect.left + rect.width / 2, y: rect.top - 8 };
  }
}

function onDayLeave() {
  hoveredDay.value = null;
}

function formatCurrency(value: string | number) {
  return Number(value).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatEventDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-8 py-12 space-y-10 animate-fade-up">
    <!-- Welcome -->
    <div class="space-y-2">
      <p class="text-sm text-muted font-medium">{{ greeting }}</p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">
        {{ auth.user?.full_name?.split(" ")[0] }}
      </h1>
      <p class="text-sm text-muted/80">¿Qué quieres hacer hoy?</p>
    </div>

    <!-- Quick Actions Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <NuxtLink
        v-for="action in quickActions"
        :key="action.href"
        :to="action.href"
        class="group relative rounded-2xl border bg-gradient-to-br p-6 transition-all duration-300 hover:shadow-soft hover:-translate-y-0.5 active:scale-[0.98]"
        :class="action.color"
      >
        <div class="flex items-start gap-4">
          <!-- Icon -->
          <div class="w-10 h-10 rounded-xl bg-white/80 border border-white shadow-sm flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform duration-300">
            <svg class="w-5 h-5 text-ink/70" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path v-if="action.icon === 'star'" stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              <path v-else-if="action.icon === 'briefcase'" stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
              <path v-else-if="action.icon === 'folder'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              <path v-else-if="action.icon === 'users'" stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>

          <!-- Text -->
          <div class="min-w-0 flex-1">
            <h3 class="text-sm font-semibold text-ink group-hover:text-ink/90">{{ action.title }}</h3>
            <p class="text-xs text-muted mt-1 leading-relaxed">{{ action.description }}</p>
          </div>

          <!-- Arrow -->
          <svg class="w-4 h-4 text-muted/40 group-hover:text-ink/50 group-hover:translate-x-0.5 transition-all duration-200 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </div>
      </NuxtLink>
    </div>

    <!-- Client Dashboard Metrics -->
    <div v-if="isClient && dashboard" class="space-y-6">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="rounded-2xl border border-border/60 bg-white p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" /></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ dashboard.total_projects }}</p>
          <p class="text-[11px] text-muted font-medium">Proyectos totales</p>
        </div>

        <div class="rounded-2xl border border-border/60 bg-white p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ dashboard.active_projects }}</p>
          <p class="text-[11px] text-muted font-medium">Activos ahora</p>
        </div>



        <div class="rounded-2xl border border-border/60 bg-white p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-violet-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-violet-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>
            </div>
          </div>
          <p class="text-2xl font-bold text-ink">{{ dashboard.total_content_makers }}</p>
          <p class="text-[11px] text-muted font-medium">Content Makers</p>
        </div>
      </div>

      <!-- Two column: Status breakdown + Service breakdown -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Status breakdown -->
        <div class="rounded-2xl border border-border/60 bg-white p-6">
          <h3 class="text-sm font-semibold text-ink mb-4">Por estado</h3>
          <div class="space-y-3">
            <div v-for="(count, name) in dashboard.status_breakdown" :key="name" class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-2.5 h-2.5 rounded-full" :class="{
                  'bg-emerald-500': name === 'Activo',
                  'bg-amber-500': name === 'Pendiente',
                  'bg-blue-500': name === 'Briefing',
                  'bg-gray-400': name === 'Finalizado',
                  'bg-slate-300': name === 'Borrador',
                  'bg-violet-400': !['Activo','Pendiente','Briefing','Finalizado','Borrador'].includes(name as string),
                }" />
                <span class="text-xs text-ink">{{ name }}</span>
              </div>
              <span class="text-xs font-semibold text-ink">{{ count }}</span>
            </div>
            <div v-if="!Object.keys(dashboard.status_breakdown || {}).length" class="text-xs text-muted text-center py-4">Sin datos</div>
          </div>
        </div>

        <!-- Service type breakdown -->
        <div class="rounded-2xl border border-border/60 bg-white p-6">
          <h3 class="text-sm font-semibold text-ink mb-4">Por tipo de servicio</h3>
          <div class="space-y-3">
            <div v-for="(count, name) in dashboard.service_breakdown" :key="name" class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-2.5 h-2.5 rounded-full bg-gold/70" />
                <span class="text-xs text-ink">{{ name }}</span>
              </div>
              <span class="text-xs font-semibold text-ink">{{ count }}</span>
            </div>
            <div v-if="!Object.keys(dashboard.service_breakdown || {}).length" class="text-xs text-muted text-center py-4">Sin datos</div>
          </div>
        </div>
      </div>

      <!-- Calendar + Content Makers -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Calendar -->
        <div class="lg:col-span-2 rounded-2xl border border-border/60 bg-white p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-ink">Calendario de proyectos</h3>
            <div class="flex items-center gap-1">
              <button class="w-7 h-7 rounded-lg border border-border/60 flex items-center justify-center hover:bg-panel/60 transition-colors" @click="prevMonth">
                <svg class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
              </button>
              <span class="text-xs font-medium text-ink px-2 min-w-[120px] text-center capitalize">{{ calendarMonthLabel }}</span>
              <button class="w-7 h-7 rounded-lg border border-border/60 flex items-center justify-center hover:bg-panel/60 transition-colors" @click="nextMonth">
                <svg class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
              </button>
            </div>
          </div>
          <!-- Day headers -->
          <div class="grid grid-cols-7 mb-1">
            <div v-for="day in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']" :key="day" class="text-center text-[10px] font-medium text-muted/70 py-1">{{ day }}</div>
          </div>
          <!-- Day cells -->
          <div class="grid grid-cols-7 gap-px bg-border/20 rounded-xl overflow-hidden border border-border/40">
            <div
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="relative min-h-[52px] p-1 bg-white transition-colors"
              :class="{ 'bg-panel/30': !day.inMonth }"
              @mouseenter="onDayHover(day, $event)"
              @mouseleave="onDayLeave"
            >
              <span class="text-[10px] leading-none block mb-0.5" :class="{
                'text-muted/40': !day.inMonth,
                'text-ink': day.inMonth && !day.isToday,
                'font-bold text-white bg-gold rounded-full w-4.5 h-4.5 flex items-center justify-center text-[9px]': day.isToday,
              }">{{ day.date.getDate() }}</span>
              <!-- Project indicators -->
              <div v-if="day.projects.length" class="space-y-px">
                <div
                  v-for="proj in day.projects.slice(0, 3)"
                  :key="proj.id"
                  class="w-full h-[5px] rounded-sm transition-all"
                  :class="proj.type === 'servicio' ? [proj.color.highlight, 'ring-1 ring-white shadow-sm'] : proj.color.bg"
                />
                <div v-if="day.projects.length > 3" class="text-[8px] text-muted text-center">+{{ day.projects.length - 3 }}</div>
              </div>
            </div>
          </div>
          <!-- Legend -->
          <div class="mt-4 space-y-2">
            <div class="flex items-center gap-4">
              <div class="flex items-center gap-1.5"><div class="w-6 h-[5px] rounded-sm bg-blue-100" /><span class="text-[10px] text-muted">Duración del proyecto</span></div>
              <div class="flex items-center gap-1.5"><div class="w-3 h-[5px] rounded-sm bg-blue-500 ring-1 ring-white shadow-sm" /><span class="text-[10px] text-muted">Fecha de servicio</span></div>
            </div>
            <!-- Project color legend -->
            <div v-if="dashboard.project_ranges?.length" class="flex flex-wrap gap-x-3 gap-y-1">
              <div v-for="range in dashboard.project_ranges.slice(0, 6)" :key="range.id" class="flex items-center gap-1.5">
                <div class="w-2.5 h-2.5 rounded-sm" :class="getProjectColor(range.id).bg" />
                <span class="text-[10px] text-muted truncate max-w-[100px]">{{ range.nombre }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Content Makers (both sections stacked) -->
        <div class="space-y-4">
        <div class="rounded-2xl border border-border/60 bg-white p-6">
          <h3 class="text-sm font-semibold text-ink mb-4">Tus Content Makers</h3>
          <div v-if="dashboard.content_makers?.length" class="space-y-2.5">
            <NuxtLink
              v-for="cm in dashboard.content_makers.slice(0, 8)"
              :key="cm.id"
              :to="`/dashboard/content-makers/${cm.id}`"
              class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-panel/40 transition-colors group"
            >
              <div class="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
                <img
                  v-if="cm.foto_url"
                  :src="cm.foto_url"
                  :alt="cm.nombre"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full bg-gradient-to-br from-gold/10 to-amber-100 flex items-center justify-center text-[10px] font-bold text-gold">
                  {{ cm.nombre?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) }}
                </div>
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium text-ink truncate group-hover:text-gold transition-colors">{{ cm.nombre }}</p>
                <p class="text-[10px] text-muted truncate">
                  <span v-if="cm.instagram_handle">@{{ cm.instagram_handle }}</span>
                  <span v-else>Sin Instagram</span>
                  · {{ cm.projects_count }} proyecto{{ cm.projects_count !== 1 ? 's' : '' }}
                </p>
              </div>
              <svg class="w-3.5 h-3.5 text-muted/30 group-hover:text-gold/60 transition-colors flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
            </NuxtLink>
          </div>
          <div v-else class="text-center py-8">
            <svg class="w-8 h-8 text-muted/20 mx-auto mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>
            <p class="text-[11px] text-muted">Aún no tienes Content Makers asignadas</p>
          </div>
        </div>

        <!-- Favorite CMs -->
        <div class="rounded-2xl border border-border/60 bg-white p-6">
          <h3 class="text-sm font-semibold text-ink mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-pink-500" fill="currentColor" stroke="currentColor" stroke-width="0.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
            </svg>
            Tus CM favoritas
          </h3>
          <div v-if="favoriteCMs.length" class="space-y-2.5">
            <NuxtLink
              v-for="cm in favoriteCMs.slice(0, 8)"
              :key="cm.id"
              :to="`/dashboard/content-makers/${cm.id}`"
              class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-panel/40 transition-colors group"
            >
              <div class="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
                <img
                  v-if="cm.foto_url"
                  :src="cm.foto_url"
                  :alt="cm.nombre"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full bg-gradient-to-br from-pink-100 to-pink-50 flex items-center justify-center text-[10px] font-bold text-pink-400">
                  {{ cm.nombre?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) }}
                </div>
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium text-ink truncate group-hover:text-gold transition-colors">{{ cm.nombre }}</p>
                <p class="text-[10px] text-muted truncate">
                  <span v-if="cm.instagram_handle">@{{ cm.instagram_handle }}</span>
                  <span v-if="cm.tiktok_handle"> · {{ cm.tiktok_handle }}</span>
                </p>
              </div>
              <svg class="w-3.5 h-3.5 text-muted/30 group-hover:text-gold/60 transition-colors flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
            </NuxtLink>
          </div>
          <div v-else class="text-center py-8">
            <svg class="w-8 h-8 text-muted/20 mx-auto mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
            </svg>
            <p class="text-[11px] text-muted">Aún no tienes Content Makers favoritas</p>
          </div>
        </div>
        </div>
      </div>

      <!-- Tooltip for calendar hover -->
      <Teleport to="body">
        <div
          v-if="hoveredDay && hoveredDay.projects.length"
          class="fixed z-[200] pointer-events-none"
          :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px', transform: 'translate(-50%, -100%)' }"
        >
          <div class="bg-ink text-white rounded-xl px-3 py-2.5 shadow-elevated text-[11px] space-y-1.5 max-w-[220px]">
            <p class="font-medium text-white/70 text-[10px]">{{ new Date(hoveredDay.dateStr).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }) }}</p>
            <div v-for="proj in hoveredDay.projects.slice(0, 4)" :key="proj.id" class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-sm flex-shrink-0" :class="proj.type === 'servicio' ? proj.color.highlight : proj.color.bg" />
              <span class="truncate">{{ proj.nombre }}</span>
              <span class="text-white/50 flex-shrink-0 text-[9px]">{{ proj.type === 'servicio' ? '★ Servicio' : '' }}</span>
            </div>
            <p v-if="hoveredDay.projects.length > 4" class="text-white/50 text-[9px]">+{{ hoveredDay.projects.length - 4 }} más</p>
          </div>
          <div class="w-2 h-2 bg-ink rotate-45 mx-auto -mt-1" />
        </div>
      </Teleport>

      <!-- Upcoming Events -->
      <div v-if="dashboard.calendar_events?.length" class="rounded-2xl border border-border/60 bg-white p-6">
        <h3 class="text-sm font-semibold text-ink mb-4">Próximas fechas</h3>
        <div class="space-y-2">
          <NuxtLink
            v-for="event in dashboard.calendar_events.slice(0, 6)"
            :key="event.id + event.type"
            :to="`/proyectos/${event.id}`"
            class="group flex items-center justify-between p-3 rounded-xl border border-border/40 hover:border-border/60 hover:shadow-sm transition-all"
          >
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center" :class="event.type === 'servicio' ? 'bg-blue-50' : 'bg-emerald-50'">
                <svg v-if="event.type === 'servicio'" class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" /></svg>
                <svg v-else class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <div>
                <p class="text-xs font-medium text-ink">{{ event.nombre }}</p>
                <p class="text-[10px] text-muted">{{ event.type === 'servicio' ? 'Fecha servicio' : 'Fecha fin' }} · {{ formatProjectId(event.project_id) }}</p>
              </div>
            </div>
            <span class="text-xs font-medium text-ink/70 tabular-nums">{{ formatEventDate(event.date) }}</span>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Loading dashboard -->
    <div v-else-if="isClient && loadingDashboard" class="flex justify-center py-12">
      <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
    </div>

    <!-- Notifications / Pending Section for Content Maker -->
    <div v-if="isContentMaker" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold text-ink">Pendiente</h2>
        <NuxtLink to="/notificaciones" class="text-xs text-gold hover:text-gold/80 font-medium transition-colors">
          Ver todas
        </NuxtLink>
      </div>

      <!-- Loading -->
      <div v-if="loadingNotifications" class="flex justify-center py-8">
        <div class="w-6 h-6 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
      </div>

      <!-- Unread count badge -->
      <div v-else-if="unreadNotifications.length > 0" class="space-y-4">
        <div class="rounded-xl bg-emerald-50 border border-emerald-200/60 px-4 py-3 flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <span class="text-xs font-bold text-emerald-600">{{ unreadNotifications.length }}</span>
          </div>
          <p class="text-xs text-emerald-800">
            Tienes <span class="font-semibold">{{ unreadNotifications.length }}</span> notificación{{ unreadNotifications.length !== 1 ? 'es' : '' }} sin leer
          </p>
        </div>

        <!-- Separator -->
        <div class="flex items-center gap-3">
          <div class="flex-1 h-px bg-border/50" />
          <span class="text-[10px] text-muted/60 font-medium uppercase tracking-wider">Actividad reciente</span>
          <div class="flex-1 h-px bg-border/50" />
        </div>

        <!-- Recent notifications -->
        <div class="space-y-1.5">
          <div
            v-for="notif in recentNotifications"
            :key="notif.id"
            class="group flex items-start gap-3 p-3 rounded-xl border transition-all duration-200 cursor-pointer"
            :class="notif.read
              ? 'border-border/40 bg-white hover:border-border/60'
              : 'border-gold/20 bg-gold/5 hover:border-gold/40'"
            @click="handleNotificationClick(notif)"
          >
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
              :class="notif.read ? 'bg-panel' : 'bg-gold/10'">
              <svg v-if="notif.notification_type === 'project_cm_request'" class="w-4 h-4" :class="notif.read ? 'text-muted' : 'text-gold'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
              <svg v-else-if="notif.notification_type === 'briefing_submitted'" class="w-4 h-4" :class="notif.read ? 'text-muted' : 'text-blue-600'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <svg v-else class="w-4 h-4" :class="notif.read ? 'text-muted' : 'text-gold'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <p class="text-xs font-medium text-ink truncate">{{ notif.title }}</p>
                <span class="text-[10px] text-muted flex-shrink-0">{{ formatTimeAgo(notif.created_at) }}</span>
              </div>
              <p class="text-[11px] text-muted mt-0.5 line-clamp-2">{{ notif.message }}</p>
            </div>
            <svg class="w-3.5 h-3.5 text-muted/30 group-hover:text-muted/60 flex-shrink-0 mt-1 transition-colors" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </div>
        </div>
      </div>

      <!-- No notifications -->
      <div v-else class="text-center py-10 rounded-xl border border-border/40 bg-white">
        <svg class="w-8 h-8 text-muted/30 mx-auto mb-3" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        <p class="text-xs text-muted">No tienes notificaciones pendientes</p>
        <p class="text-[11px] text-muted/70 mt-1">¡Todo al día!</p>
      </div>
    </div>

    <!-- Dashboard link for admin/employee -->
    <div v-if="isAdminOrEmployee" class="pt-2">
      <NuxtLink
        to="/dashboard"
        class="inline-flex items-center gap-2 text-sm text-muted hover:text-gold transition-colors duration-200"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
        </svg>
        Ir al panel de administración
      </NuxtLink>
    </div>
  </div>
</template>
