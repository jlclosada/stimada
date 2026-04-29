<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

definePageMeta({ middleware: ["auth", "role"] });

const auth = useAuthStore();
const config = useRuntimeConfig();

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  created_by: string | null;
}

const users = ref<User[]>([]);
const isLoading = ref(true);
const filterRole = ref("");
const filterStatus = ref("");
const showCreateModal = ref(false);

const currentPage = ref(1);
const pageSize = 20;
const totalPages = ref(1);
const totalCount = ref(0);

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  stimada_employee: "Empleado",
  client: "Cliente",
  content_maker: "Creator",
};

const ROLE_BADGE: Record<string, string> = {
  admin: "text-gold border-gold/30 bg-gold/10",
  stimada_employee: "text-blue-600 border-blue-200 bg-blue-50",
  client: "text-emerald-600 border-emerald-200 bg-emerald-50",
  content_maker: "text-orange-600 border-orange-200 bg-orange-50",
};

const visibleRoles = computed(() =>
  auth.isAdmin
    ? Object.keys(ROLE_LABELS)
    : ["client", "content_maker"]
);

async function fetchUsers(page?: number) {
  isLoading.value = true;
  try {
    const p = page ?? currentPage.value;
    const query = new URLSearchParams({
      page: String(p),
      page_size: String(pageSize),
    });
    if (filterRole.value) query.set("role", filterRole.value);
    if (filterStatus.value) query.set("status", filterStatus.value);

    const data = await $fetch<{ count: number; results: User[] }>(
      `${config.public.apiBase}/users/?${query.toString()}`,
      { headers: { Authorization: `Bearer ${auth.accessToken}` } }
    );
    users.value = data.results;
    totalCount.value = data.count;
    currentPage.value = p;
    totalPages.value = Math.ceil(data.count / pageSize);
  } finally {
    isLoading.value = false;
  }
}

watch([filterRole, filterStatus], () => {
  currentPage.value = 1;
  fetchUsers(1);
});

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return;
  fetchUsers(page);
}

const visiblePages = computed(() => {
  const total = totalPages.value;
  const current = currentPage.value;
  const pages: (number | string)[] = [];
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    if (current > 3) pages.push("...");
    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (current < total - 2) pages.push("...");
    pages.push(total);
  }
  return pages;
});

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

onMounted(() => fetchUsers());
</script>

<template>
  <div class="space-y-6 animate-fade-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Usuarios</h1>
        <p class="text-sm text-muted mt-0.5">Gestión de accesos</p>
      </div>
      <button
        class="group flex items-center gap-2 h-10 px-5 rounded-xl bg-ink text-white text-sm font-medium
               hover:bg-ink/80 hover:shadow-soft active:scale-[0.97] transition-all duration-200"
        @click="showCreateModal = true"
      >
        <svg class="w-4 h-4 transition-transform duration-200 group-hover:rotate-90" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Nuevo empleado
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 animate-fade-up delay-100">
      <select v-model="filterRole" class="select-field min-w-[180px] max-w-[200px]">
        <option value="">Todos los roles</option>
        <option v-for="r in visibleRoles" :key="r" :value="r">{{ ROLE_LABELS[r] }}</option>
      </select>

      <select v-model="filterStatus" class="select-field min-w-[180px] max-w-[200px]">
        <option value="">Todos los estados</option>
        <option value="active">Activos</option>
        <option value="inactive">Inactivos</option>
      </select>

      <button
        v-if="filterRole || filterStatus"
        class="h-11 px-4 rounded-xl text-sm text-muted hover:text-ink border border-border/70 hover:border-ink/20 hover:bg-panel/80 hover:shadow-sm active:scale-[0.97] transition-all duration-300"
        @click="filterRole = ''; filterStatus = ''"
      >
        Limpiar
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl border border-border/60 bg-white shadow-card overflow-hidden">
      <div v-if="isLoading" class="flex justify-center items-center h-48">
        <div class="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
      </div>
      <template v-else>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border/60 bg-panel/50">
              <th v-for="col in ['Nombre', 'Email', 'Rol', 'Estado', 'Creado por', 'Fecha']"
                  :key="col"
                  class="text-left px-5 py-3 text-xs font-medium text-muted uppercase tracking-wider">
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!users.length">
              <td colspan="6" class="text-center py-16 text-sm text-muted">
                No hay usuarios con estos filtros.
              </td>
            </tr>
            <tr
              v-for="user in users"
              :key="user.id"
              class="border-b border-border/30 table-row-hover transition-colors"
            >
              <td class="px-5 py-3.5 text-sm text-ink font-medium">{{ user.full_name }}</td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ user.email }}</td>
              <td class="px-5 py-3.5">
                <span
                  class="inline-block text-xs px-2.5 py-1 border rounded-lg font-medium"
                  :class="ROLE_BADGE[user.role] ?? 'text-ink border-border'"
                >
                  {{ ROLE_LABELS[user.role] ?? user.role }}
                </span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  class="inline-flex items-center gap-1.5 text-xs font-medium"
                  :class="user.is_active ? 'text-emerald-600' : 'text-muted'"
                >
                  <div class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-emerald-500' : 'bg-muted/40'" />
                  {{ user.is_active ? "Activo" : "Inactivo" }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ user.created_by ?? "—" }}</td>
              <td class="px-5 py-3.5 text-sm text-muted">{{ formatDate(user.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex items-center justify-between px-5 py-4 border-t border-border/40 bg-panel/30">
          <p class="text-sm text-muted">
            Mostrando <span class="font-medium text-ink">{{ (currentPage - 1) * pageSize + 1 }}</span>–<span class="font-medium text-ink">{{ Math.min(currentPage * pageSize, totalCount) }}</span> de <span class="font-medium text-ink">{{ totalCount }}</span>
          </p>
          <div class="flex items-center gap-1">
            <button
              :disabled="currentPage <= 1"
              class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
              @click="goToPage(currentPage - 1)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="w-9 h-9 flex items-center justify-center text-xs text-muted">…</span>
              <button
                v-else
                class="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-medium transition-all duration-150"
                :class="p === currentPage
                  ? 'bg-ink text-white shadow-sm'
                  : 'text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border'"
                @click="goToPage(p as number)"
              >
                {{ p }}
              </button>
            </template>
            <button
              :disabled="currentPage >= totalPages"
              class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-white border border-transparent hover:border-border disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
              @click="goToPage(currentPage + 1)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal -->
    <UsersCreateUserModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="fetchUsers(currentPage); showCreateModal = false"
    />
  </div>
</template>
