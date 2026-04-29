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

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  stimada_employee: "Empleado",
  client: "Cliente",
  content_maker: "Creator",
};

const ROLE_BADGE: Record<string, string> = {
  admin: "text-gold border-gold/30 bg-gold/10",
  stimada_employee: "text-blue-400 border-blue-400/30 bg-blue-400/10",
  client: "text-green-400 border-green-400/30 bg-green-400/10",
  content_maker: "text-orange-400 border-orange-400/30 bg-orange-400/10",
};

const visibleRoles = computed(() =>
  auth.isAdmin
    ? Object.keys(ROLE_LABELS)
    : ["client", "content_maker"]
);

async function fetchUsers() {
  isLoading.value = true;
  try {
    const data = await $fetch<User[]>(`${config.public.apiBase}/users/`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    });
    users.value = data;
  } finally {
    isLoading.value = false;
  }
}

const filteredUsers = computed(() => {
  return users.value.filter((u) => {
    const roleOk = !filterRole.value || u.role === filterRole.value;
    const statusOk =
      filterStatus.value === ""
        ? true
        : filterStatus.value === "active"
        ? u.is_active
        : !u.is_active;
    return roleOk && statusOk;
  });
});

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

onMounted(fetchUsers);
</script>

<template>
  <div class="fade-enter space-y-6">
    <!-- Cabecera -->
    <div class="flex items-center justify-between">
      <div>
        <p class="font-sans text-xs tracking-editorial uppercase text-gold/50 mb-1">
          Gestión
        </p>
        <h1 class="font-display text-4xl font-light text-cream">Usuarios</h1>
      </div>
      <button
        class="flex items-center gap-2 bg-gold text-ink font-sans text-xs font-medium px-5 py-2.5 hover:opacity-85 transition-opacity duration-200"
        @click="showCreateModal = true"
      >
        <svg
          class="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Nuevo usuario
      </button>
    </div>

    <!-- Filtros -->
    <div class="flex gap-3 flex-wrap">
      <select
        v-model="filterRole"
        class="bg-transparent border border-border text-sm text-gray-muted font-sans px-3 py-2 focus:outline-none focus:border-gold transition-colors"
      >
        <option value="">Todos los roles</option>
        <option
          v-for="r in visibleRoles"
          :key="r"
          :value="r"
        >
          {{ ROLE_LABELS[r] }}
        </option>
      </select>
      <select
        v-model="filterStatus"
        class="bg-transparent border border-border text-sm text-gray-muted font-sans px-3 py-2 focus:outline-none focus:border-gold transition-colors"
      >
        <option value="">Todos los estados</option>
        <option value="active">Activos</option>
        <option value="inactive">Inactivos</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="border border-border overflow-hidden" style="background-color: #0f0f0f">
      <div v-if="isLoading" class="flex items-center justify-center h-40">
        <svg class="animate-spin w-5 h-5 text-gold" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-border">
            <th
              v-for="col in ['Nombre', 'Email', 'Rol', 'Estado', 'Creado por', 'Fecha']"
              :key="col"
              class="text-left px-5 py-3 text-xs font-sans text-gray-muted uppercase tracking-widest font-normal"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-if="filteredUsers.length === 0"
          >
            <td colspan="6" class="text-center py-12 text-sm text-gray-muted font-sans">
              No hay usuarios con estos filtros.
            </td>
          </tr>
          <tr
            v-for="user in filteredUsers"
            :key="user.id"
            class="border-b border-border/50 hover:bg-white/2 transition-colors"
          >
            <td class="px-5 py-3.5 text-sm font-sans text-cream">
              {{ user.full_name }}
            </td>
            <td class="px-5 py-3.5 text-sm font-sans text-gray-muted">
              {{ user.email }}
            </td>
            <td class="px-5 py-3.5">
              <span
                class="inline-block text-xs font-sans px-2 py-0.5 border rounded-sm"
                :class="ROLE_BADGE[user.role] ?? 'text-cream border-border'"
              >
                {{ ROLE_LABELS[user.role] ?? user.role }}
              </span>
            </td>
            <td class="px-5 py-3.5">
              <span
                class="inline-block text-xs font-sans"
                :class="user.is_active ? 'text-green-400' : 'text-gray-muted'"
              >
                {{ user.is_active ? "Activo" : "Inactivo" }}
              </span>
            </td>
            <td class="px-5 py-3.5 text-xs font-sans text-gray-muted">
              {{ user.created_by ?? "—" }}
            </td>
            <td class="px-5 py-3.5 text-xs font-sans text-gray-muted">
              {{ formatDate(user.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <CreateUserModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="fetchUsers(); showCreateModal = false"
    />
  </div>
</template>
