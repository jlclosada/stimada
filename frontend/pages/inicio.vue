<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({
  layout: "app",
  middleware: ["auth"],
});

const auth = useAuthStore();
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

// Pending projects for CM/client
const pendingProjects = ref<any[]>([]);
const loadingProjects = ref(false);

async function fetchPendingProjects() {
  if (!auth.accessToken || isAdminOrEmployee.value) return;
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

onMounted(fetchPendingProjects);

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
    ];
  }
  return [];
});
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

    <!-- Pending Projects for CM / Client -->
    <div v-if="(isContentMaker || isClient) && pendingProjects.length > 0" class="space-y-4">
      <h2 class="text-sm font-semibold text-ink">
        {{ isContentMaker ? 'Tus campañas' : 'Tus proyectos' }}
      </h2>
      <div class="space-y-2">
        <NuxtLink
          v-for="proj in pendingProjects.slice(0, 5)"
          :key="proj.id"
          :to="`/proyectos/${proj.id}`"
          class="group flex items-center justify-between p-4 rounded-xl border border-border/60 bg-white hover:shadow-soft hover:-translate-y-0.5 transition-all duration-200"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
              :class="{
                'bg-amber-50': proj.status_name === 'Pendiente',
                'bg-emerald-50': proj.status_name === 'Activo',
                'bg-gray-100': proj.status_name === 'Finalizado',
              }">
              <svg class="w-4 h-4" :class="{
                'text-amber-600': proj.status_name === 'Pendiente',
                'text-emerald-600': proj.status_name === 'Activo',
                'text-gray-500': proj.status_name === 'Finalizado',
              }" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-ink truncate">{{ proj.nombre }}</p>
              <p class="text-[11px] text-muted">{{ proj.project_id }} · {{ proj.client_name }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span
              class="px-2.5 py-0.5 rounded-lg text-[10px] font-medium"
              :class="{
                'bg-amber-50 text-amber-700': proj.status_name === 'Pendiente',
                'bg-emerald-50 text-emerald-700': proj.status_name === 'Activo',
                'bg-gray-100 text-gray-600': proj.status_name === 'Finalizado',
              }"
            >{{ proj.status_name || 'Sin estado' }}</span>
            <svg class="w-4 h-4 text-muted/40 group-hover:text-ink/50 transition-colors" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </div>
        </NuxtLink>
      </div>
      <NuxtLink
        v-if="pendingProjects.length > 5"
        to="/proyectos"
        class="inline-flex items-center gap-1 text-xs text-gold hover:text-gold/80 font-medium transition-colors"
      >
        Ver todos ({{ pendingProjects.length }})
        <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
      </NuxtLink>
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
