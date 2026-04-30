<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth", "role"] });

const auth = useAuthStore();
const config = useRuntimeConfig();

interface DashboardData {
  total_projects: number;
  draft_projects: number;
  active_projects: number;
  completed_projects: number;
  total_facturado: string;
  total_clients: number;
  clients_with_active: number;
  total_cms: number;
  cms_active: number;
  status_breakdown: Record<string, number>;
  service_breakdown: Record<string, number>;
  pending_actions: {
    type: string;
    label: string;
    count: number;
    items: {
      project_id: number;
      project_name: string;
      project_code: string;
      client_name?: string | null;
      cm_name?: string;
      cm_id?: number;
    }[];
  }[];
  project_ranges: {
    id: number;
    nombre: string;
    project_id: string;
    client_name: string | null;
    cm_name: string | null;
    fecha_inicio: string | null;
    fecha_servicio: string | null;
    fecha_fin: string | null;
    status_name: string | null;
    service_type: string | null;
  }[];
  todays_tasks: {
    id: number;
    project_id: string;
    nombre: string;
    event: string;
    client_name: string | null;
    status_name: string | null;
  }[];
  upcoming_events: {
    id: number;
    project_id: string;
    nombre: string;
    event: string;
    date: string;
    client_name: string | null;
  }[];
  recent_projects: {
    id: number;
    project_id: string;
    nombre: string;
    client_name: string | null;
    status_name: string | null;
    service_type: string | null;
    fecha_servicio: string | null;
    created_at: string;
  }[];
  top_cms: {
    id: number;
    nombre: string;
    instagram_handle: string;
    projects_count: number;
  }[];
  top_clients: {
    id: number;
    nombre: string;
    projects_count: number;
  }[];
}

const loading = ref(true);
const data = ref<DashboardData | null>(null);
const expandedAction = ref<string | null>(null);

function toggleAction(action: DashboardData["pending_actions"][number]) {
  if (action.count === 1 && action.items.length === 1) {
    navigateTo(`/proyectos/${action.items[0].project_id}`);
    return;
  }
  expandedAction.value = expandedAction.value === action.type ? null : action.type;
}

// Calendar state
const calendarMonth = ref(new Date());

const calendarDays = computed(() => {
  const month = calendarMonth.value;
  const year = month.getFullYear();
  const m = month.getMonth();
  const firstDay = new Date(year, m, 1);
  const lastDay = new Date(year, m + 1, 0);
  const startPad = (firstDay.getDay() + 6) % 7; // Monday = 0

  const days: { date: Date; inMonth: boolean }[] = [];
  for (let i = startPad - 1; i >= 0; i--) {
    const d = new Date(year, m, -i);
    days.push({ date: d, inMonth: false });
  }
  for (let d = 1; d <= lastDay.getDate(); d++) {
    days.push({ date: new Date(year, m, d), inMonth: true });
  }
  const remaining = 7 - (days.length % 7);
  if (remaining < 7) {
    for (let d = 1; d <= remaining; d++) {
      days.push({ date: new Date(year, m + 1, d), inMonth: false });
    }
  }
  return days;
});

function dateStr(d: Date) {
  return d.toISOString().split("T")[0];
}

function getEventsForDate(d: Date) {
  if (!data.value) return [];
  const ds = dateStr(d);
  return data.value.project_ranges.filter(
    (p) => p.fecha_inicio === ds || p.fecha_servicio === ds || p.fecha_fin === ds
  );
}

function isToday(d: Date) {
  const today = new Date();
  return d.toDateString() === today.toDateString();
}

function prevMonth() {
  const m = calendarMonth.value;
  calendarMonth.value = new Date(m.getFullYear(), m.getMonth() - 1, 1);
}
function nextMonth() {
  const m = calendarMonth.value;
  calendarMonth.value = new Date(m.getFullYear(), m.getMonth() + 1, 1);
}

const monthLabel = computed(() => {
  return calendarMonth.value.toLocaleDateString("es-ES", { month: "long", year: "numeric" });
});

// Status colors
const STATUS_COLORS: Record<string, string> = {
  "Propuesta enviada": "bg-blue-100 text-blue-700",
  "Selección CM": "bg-purple-100 text-purple-700",
  "Briefing": "bg-amber-100 text-amber-700",
  "En producción": "bg-emerald-100 text-emerald-700",
  "Finalizado": "bg-gray-100 text-gray-600",
  "Cancelado": "bg-red-100 text-red-600",
};

function statusColor(name: string | null) {
  return STATUS_COLORS[name ?? ""] ?? "bg-gray-100 text-gray-600";
}

async function fetchDashboard() {
  loading.value = true;
  try {
    const res = await fetch(`${config.public.apiBase}/projects/staff_dashboard/`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    if (res.ok) data.value = await res.json();
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDashboard);
</script>

<template>
  <div class="space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.15em] text-gold mb-1">Panel de control</p>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">
          Hola, {{ auth.user?.full_name?.split(" ")[0] }}
        </h1>
      </div>
      <div class="text-sm text-muted">
        {{ new Date().toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long", year: "numeric" }) }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-gold/30 border-t-gold rounded-full animate-spin" />
    </div>

    <template v-else-if="data">
      <!-- Today's Tasks Alert -->
      <div v-if="data.todays_tasks.length > 0" class="rounded-2xl border border-amber-200 bg-amber-50/60 p-5">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-7 h-7 rounded-xl bg-amber-100 flex items-center justify-center">
            <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-amber-800">Tareas de hoy</h3>
          <span class="ml-auto text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
            {{ data.todays_tasks.length }}
          </span>
        </div>
        <div class="space-y-2">
          <NuxtLink
            v-for="task in data.todays_tasks"
            :key="`${task.id}-${task.event}`"
            :to="`/proyectos/${task.id}`"
            class="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/70 hover:bg-white transition-colors border border-amber-100"
          >
            <div class="w-2 h-2 rounded-full bg-amber-500" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-ink truncate">{{ task.nombre }}</p>
              <p class="text-xs text-muted">{{ task.event }} · {{ task.client_name ?? "Sin cliente" }}</p>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-md font-medium" :class="statusColor(task.status_name)">
              {{ task.status_name }}
            </span>
          </NuxtLink>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Projects -->
        <div class="glass-card p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-gold/10 flex items-center justify-center">
              <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
            </div>
            <p class="text-[10px] text-muted uppercase tracking-widest font-medium">Proyectos</p>
          </div>
          <p class="text-2xl font-bold text-ink">{{ data.active_projects }}</p>
          <p class="text-xs text-muted">activos · {{ data.total_projects }} total</p>
        </div>

        <!-- Clients -->
        <div class="glass-card p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p class="text-[10px] text-muted uppercase tracking-widest font-medium">Clientes</p>
          </div>
          <p class="text-2xl font-bold text-ink">{{ data.total_clients }}</p>
          <p class="text-xs text-muted">{{ data.clients_with_active }} con proyectos activos</p>
        </div>

        <!-- Content Makers -->
        <div class="glass-card p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-purple-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
            </div>
            <p class="text-[10px] text-muted uppercase tracking-widest font-medium">Content Makers</p>
          </div>
          <p class="text-2xl font-bold text-ink">{{ data.total_cms }}</p>
          <p class="text-xs text-muted">{{ data.cms_active }} activas en proyectos</p>
        </div>

        <!-- Revenue -->
        <div class="glass-card p-5 space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
              </svg>
            </div>
            <p class="text-[10px] text-muted uppercase tracking-widest font-medium">Facturado</p>
          </div>
          <p class="text-2xl font-bold text-ink">{{ Number(data.total_facturado).toLocaleString("es-ES", { minimumFractionDigits: 0 }) }}€</p>
          <p class="text-xs text-muted">{{ data.completed_projects }} proyectos finalizados</p>
        </div>
      </div>

      <!-- Pending Actions -->
      <div v-if="data.pending_actions.length > 0" class="rounded-2xl border border-orange-200 bg-orange-50/40 p-5">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-7 h-7 rounded-xl bg-orange-100 flex items-center justify-center">
            <svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-orange-800">Acciones pendientes</h3>
        </div>
        <div class="space-y-3">
          <div v-for="action in data.pending_actions" :key="action.type">
            <button
              @click="toggleAction(action)"
              class="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/80 border border-orange-100 hover:border-orange-300 hover:bg-white transition-all cursor-pointer text-left"
            >
              <span class="text-xl font-bold text-orange-600">{{ action.count }}</span>
              <span class="text-xs text-orange-700 flex-1">{{ action.label }}</span>
              <svg
                class="w-4 h-4 text-orange-400 transition-transform duration-200"
                :class="{ 'rotate-180': expandedAction === action.type }"
                fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            <!-- Expanded detail -->
            <div v-if="expandedAction === action.type" class="mt-2 ml-2 space-y-1.5 animate-fade-up">
              <NuxtLink
                v-for="item in action.items"
                :key="`${item.project_id}-${item.cm_id ?? ''}`"
                :to="`/proyectos/${item.project_id}`"
                class="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-white border border-orange-100/60 hover:border-gold/40 hover:shadow-sm transition-all"
              >
                <div class="w-1.5 h-1.5 rounded-full bg-orange-400" />
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-ink truncate">{{ item.project_name }}</p>
                  <p class="text-[10px] text-muted">
                    {{ item.project_code }}
                    <template v-if="item.cm_name"> · CM: {{ item.cm_name }}</template>
                    <template v-else-if="item.client_name"> · {{ item.client_name }}</template>
                  </p>
                </div>
                <svg class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>

      <!-- Main grid: Calendar + Status/Service breakdown -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Calendar -->
        <div class="xl:col-span-2 glass-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-ink">Calendario de proyectos</h3>
            <div class="flex items-center gap-2">
              <button @click="prevMonth" class="w-7 h-7 rounded-lg border border-border/60 flex items-center justify-center hover:bg-panel transition-colors">
                <svg class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
              </button>
              <span class="text-sm font-medium text-ink capitalize min-w-[140px] text-center">{{ monthLabel }}</span>
              <button @click="nextMonth" class="w-7 h-7 rounded-lg border border-border/60 flex items-center justify-center hover:bg-panel transition-colors">
                <svg class="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
              </button>
            </div>
          </div>

          <!-- Day headers -->
          <div class="grid grid-cols-7 mb-1">
            <div v-for="day in ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']" :key="day" class="text-center text-[10px] font-semibold uppercase tracking-wider text-muted py-2">
              {{ day }}
            </div>
          </div>

          <!-- Calendar grid -->
          <div class="grid grid-cols-7 gap-px bg-border/30 rounded-xl overflow-hidden border border-border/40">
            <div
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="bg-white min-h-[70px] p-1.5 relative group"
              :class="{ 'bg-panel/50': !day.inMonth }"
            >
              <span
                class="text-[11px] font-medium block mb-0.5"
                :class="[
                  !day.inMonth ? 'text-muted/30' : 'text-ink',
                  isToday(day.date) ? 'bg-gold text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold' : ''
                ]"
              >
                {{ day.date.getDate() }}
              </span>
              <!-- Events dots -->
              <div v-if="day.inMonth && getEventsForDate(day.date).length > 0" class="space-y-0.5">
                <div
                  v-for="ev in getEventsForDate(day.date).slice(0, 3)"
                  :key="ev.id"
                  class="text-[8px] leading-tight truncate px-1 py-0.5 rounded"
                  :class="ev.fecha_servicio === dateStr(day.date) ? 'bg-emerald-100 text-emerald-700' : ev.fecha_fin === dateStr(day.date) ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'"
                  :title="`${ev.nombre} (${ev.client_name ?? ''})`"
                >
                  {{ ev.nombre.substring(0, 12) }}
                </div>
                <div v-if="getEventsForDate(day.date).length > 3" class="text-[8px] text-muted text-center">
                  +{{ getEventsForDate(day.date).length - 3 }}
                </div>
              </div>
            </div>
          </div>

          <!-- Legend -->
          <div class="flex items-center gap-4 mt-3">
            <div class="flex items-center gap-1.5 text-[10px] text-muted"><div class="w-2.5 h-2.5 rounded-sm bg-blue-100 border border-blue-200" /> Inicio</div>
            <div class="flex items-center gap-1.5 text-[10px] text-muted"><div class="w-2.5 h-2.5 rounded-sm bg-emerald-100 border border-emerald-200" /> Servicio</div>
            <div class="flex items-center gap-1.5 text-[10px] text-muted"><div class="w-2.5 h-2.5 rounded-sm bg-red-100 border border-red-200" /> Fin</div>
          </div>
        </div>

        <!-- Right column: Status + Service breakdown -->
        <div class="space-y-6">
          <!-- Status breakdown -->
          <div class="glass-card p-5">
            <h3 class="text-sm font-semibold text-ink mb-4">Estado de proyectos</h3>
            <div class="space-y-3">
              <div v-for="(count, name) in data.status_breakdown" :key="name" class="flex items-center gap-3">
                <span class="text-[10px] px-2 py-0.5 rounded-md font-medium whitespace-nowrap" :class="statusColor(name as string)">
                  {{ name }}
                </span>
                <div class="flex-1 h-2 bg-panel rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full bg-gold/60 transition-all duration-500"
                    :style="{ width: `${(count / (data!.active_projects + data!.completed_projects)) * 100}%` }"
                  />
                </div>
                <span class="text-xs font-bold text-ink min-w-[20px] text-right">{{ count }}</span>
              </div>
            </div>
          </div>

          <!-- Service type breakdown -->
          <div class="glass-card p-5">
            <h3 class="text-sm font-semibold text-ink mb-4">Tipos de servicio</h3>
            <div class="space-y-2.5">
              <div v-for="(count, name) in data.service_breakdown" :key="name" class="flex items-center justify-between">
                <span class="text-xs text-muted truncate">{{ name }}</span>
                <span class="text-xs font-bold text-ink bg-panel px-2 py-0.5 rounded-md">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Upcoming events -->
      <div v-if="data.upcoming_events.length > 0" class="glass-card p-6">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
          </svg>
          <h3 class="text-sm font-semibold text-ink">Próximos 7 días</h3>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <NuxtLink
            v-for="ev in data.upcoming_events"
            :key="`${ev.id}-${ev.event}`"
            :to="`/proyectos/${ev.id}`"
            class="flex items-center gap-3 px-4 py-3 rounded-xl border border-border/40 hover:border-gold/30 hover:bg-gold/5 transition-all"
          >
            <div class="text-center min-w-[40px]">
              <p class="text-lg font-bold text-ink leading-none">{{ new Date(ev.date).getDate() }}</p>
              <p class="text-[9px] uppercase text-muted font-medium">{{ new Date(ev.date).toLocaleDateString("es-ES", { month: "short" }) }}</p>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium text-ink truncate">{{ ev.nombre }}</p>
              <p class="text-[10px] text-muted">{{ ev.event }} · {{ ev.client_name }}</p>
            </div>
          </NuxtLink>
        </div>
      </div>

      <!-- Bottom grid: Recent projects + Top CMs + Top Clients -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Recent Projects -->
        <div class="xl:col-span-2 glass-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-ink">Proyectos recientes</h3>
            <NuxtLink to="/proyectos" class="text-[11px] text-gold hover:text-gold/80 font-medium">Ver todos →</NuxtLink>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-border/40">
                  <th class="text-[10px] text-muted uppercase tracking-wider font-medium pb-2 pr-4">Proyecto</th>
                  <th class="text-[10px] text-muted uppercase tracking-wider font-medium pb-2 pr-4">Cliente</th>
                  <th class="text-[10px] text-muted uppercase tracking-wider font-medium pb-2 pr-4">Estado</th>
                  <th class="text-[10px] text-muted uppercase tracking-wider font-medium pb-2">Servicio</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in data.recent_projects" :key="p.id" class="border-b border-border/20 last:border-0">
                  <td class="py-2.5 pr-4">
                    <NuxtLink :to="`/proyectos/${p.id}`" class="text-xs font-medium text-ink hover:text-gold transition-colors">
                      {{ p.nombre }}
                    </NuxtLink>
                    <p class="text-[10px] text-muted">{{ p.project_id }}</p>
                  </td>
                  <td class="py-2.5 pr-4 text-xs text-muted">{{ p.client_name ?? "—" }}</td>
                  <td class="py-2.5 pr-4">
                    <span class="text-[10px] px-2 py-0.5 rounded-md font-medium" :class="statusColor(p.status_name)">
                      {{ p.status_name ?? "—" }}
                    </span>
                  </td>
                  <td class="py-2.5 text-xs text-muted">{{ p.fecha_servicio ?? "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right: Top CMs + Top Clients -->
        <div class="space-y-6">
          <!-- Top Content Makers -->
          <div class="glass-card p-5">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-ink">Top Content Makers</h3>
              <NuxtLink to="/dashboard/content-makers" class="text-[10px] text-gold hover:text-gold/80 font-medium">Ver todas</NuxtLink>
            </div>
            <div class="space-y-2">
              <NuxtLink
                v-for="cm in data.top_cms"
                :key="cm.id"
                :to="`/dashboard/content-makers/${cm.id}`"
                class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-panel/60 transition-colors"
              >
                <div class="w-7 h-7 rounded-full bg-purple-50 flex items-center justify-center text-[10px] font-bold text-purple-600">
                  {{ cm.nombre.charAt(0) }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-ink truncate">{{ cm.nombre }}</p>
                  <p class="text-[10px] text-muted">@{{ cm.instagram_handle }}</p>
                </div>
                <span class="text-[10px] font-bold text-gold bg-gold/10 px-2 py-0.5 rounded-full">{{ cm.projects_count }}</span>
              </NuxtLink>
            </div>
          </div>

          <!-- Top Clients -->
          <div class="glass-card p-5">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-ink">Top Clientes</h3>
              <NuxtLink to="/dashboard/clientes" class="text-[10px] text-gold hover:text-gold/80 font-medium">Ver todos</NuxtLink>
            </div>
            <div class="space-y-2">
              <NuxtLink
                v-for="client in data.top_clients"
                :key="client.id"
                :to="`/dashboard/clientes/${client.id}`"
                class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-panel/60 transition-colors"
              >
                <div class="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center text-[10px] font-bold text-blue-600">
                  {{ client.nombre.charAt(0) }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-ink truncate">{{ client.nombre }}</p>
                </div>
                <span class="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">{{ client.projects_count }} proy.</span>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
