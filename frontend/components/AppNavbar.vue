<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore } from "~/stores/notifications";

const auth = useAuthStore();
const notifStore = useNotificationsStore();
const route = useRoute();

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  stimada_employee: "Empleado",
  client: "Cliente",
  content_maker: "Content Maker",
};

interface NavLink {
  label: string;
  href: string;
}

const navLinks = computed<NavLink[]>(() => {
  const role = auth.user?.role;
  if (role === "admin" || role === "stimada_employee") {
    return [
      { label: "Inicio", href: "/inicio" },
      { label: "Dashboard", href: "/dashboard" },
      { label: "Proyectos", href: "/proyectos" },
    ];
  }
  if (role === "client") {
    return [
      { label: "Inicio", href: "/inicio" },
      { label: "Mis proyectos", href: "/proyectos" },
    ];
  }
  if (role === "content_maker") {
    return [
      { label: "Inicio", href: "/inicio" },
      { label: "Mis campañas", href: "/proyectos" },
    ];
  }
  return [{ label: "Inicio", href: "/inicio" }];
});

function isActive(href: string) {
  if (href === "/inicio") return route.path === "/inicio";
  return route.path.startsWith(href);
}

const initials = computed(() => {
  const name = auth.user?.full_name ?? "?";
  return name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
});

// Notifications
const showNotifications = ref(false);
const unreadCount = computed(() => notifStore.unreadCount);

function toggleNotifications() {
  showNotifications.value = !showNotifications.value;
  if (showNotifications.value) notifStore.fetchAll();
}

// Close notifications dropdown on outside click
function closeNotifications() {
  showNotifications.value = false;
}

const router = useRouter();

function handleNotificationClick(notif: any) {
  notifStore.markRead(notif.id);
  showNotifications.value = false;
  if (notif.project) {
    router.push(`/proyectos/${notif.project}`);
  }
}

// Load unread count on mount
onMounted(() => {
  notifStore.fetchUnreadCount();
});

// Profile dropdown
const showProfileMenu = ref(false);
let profileTimeout: ReturnType<typeof setTimeout> | null = null;

function toggleProfile() {
  if (profileTimeout) clearTimeout(profileTimeout);
  showProfileMenu.value = !showProfileMenu.value;
}
function startCloseProfile() {
  profileTimeout = setTimeout(() => {
    showProfileMenu.value = false;
  }, 300);
}
function cancelCloseProfile() {
  if (profileTimeout) clearTimeout(profileTimeout);
}

// Notifications delay
let notifTimeout: ReturnType<typeof setTimeout> | null = null;
function startCloseNotifications() {
  notifTimeout = setTimeout(() => {
    showNotifications.value = false;
  }, 300);
}
function cancelCloseNotifications() {
  if (notifTimeout) clearTimeout(notifTimeout);
}
</script>

<template>
  <nav class="h-16 flex items-center justify-between px-8 border-b border-border/40 bg-white/90 backdrop-blur-xl sticky top-0 z-50">
    <!-- Left: Logo + Nav links -->
    <div class="flex items-center gap-10">
      <NuxtLink to="/inicio" class="flex items-center gap-2.5 flex-shrink-0">
        <img src="~/assets/images/stimada_logo.png" alt="Stimada" class="h-7 w-auto" />
      </NuxtLink>

      <div class="flex items-center gap-1">
        <NuxtLink
          v-for="link in navLinks"
          :key="link.href"
          :to="link.href"
          class="relative px-4 py-2 rounded-lg text-[13px] font-medium transition-all duration-200"
          :class="isActive(link.href)
            ? 'text-ink'
            : 'text-muted hover:text-ink hover:bg-panel/60'"
        >
          {{ link.label }}
          <!-- Active indicator -->
          <span
            v-if="isActive(link.href)"
            class="absolute bottom-0 left-1/2 -translate-x-1/2 w-5 h-[2px] bg-gold rounded-full"
          />
        </NuxtLink>
      </div>
    </div>

    <!-- Right: Notifications + Profile -->
    <div class="flex items-center gap-3">
      <!-- Notifications -->
      <div class="relative" @mouseleave="startCloseNotifications" @mouseenter="cancelCloseNotifications">
        <button
          class="relative w-9 h-9 rounded-xl flex items-center justify-center text-muted hover:text-ink hover:bg-panel/60 transition-all duration-200"
          @click="toggleNotifications"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          <!-- Badge -->
          <span
            v-if="unreadCount > 0"
            class="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center ring-2 ring-white"
          >
            {{ unreadCount > 9 ? "9+" : unreadCount }}
          </span>
        </button>

        <!-- Notifications dropdown -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 scale-95 -translate-y-1"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 -translate-y-1"
        >
          <div
            v-if="showNotifications"
            class="absolute right-0 top-full mt-2 w-80 rounded-2xl border border-border/60 bg-white shadow-elevated overflow-hidden"
          >
            <div class="px-4 py-3 border-b border-border/40 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-ink">Notificaciones</h3>
              <button v-if="unreadCount > 0" class="text-[10px] text-gold hover:text-gold/80 font-medium" @click="notifStore.markAllRead()">Marcar leídas</button>
            </div>
            <div class="max-h-72 overflow-auto">
              <div v-if="notifStore.items.length === 0" class="px-4 py-8 text-center">
                <svg class="w-8 h-8 text-muted/30 mx-auto mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
                <p class="text-xs text-muted">No tienes notificaciones</p>
              </div>
              <div
                v-for="notif in notifStore.items"
                :key="notif.id"
                class="px-4 py-3 border-b border-border/20 last:border-0 hover:bg-panel/40 transition-colors cursor-pointer"
                :class="{ 'bg-gold/5': !notif.read }"
                @click="handleNotificationClick(notif)"
              >
                <div class="flex items-start gap-2.5">
                  <span
                    v-if="!notif.read"
                    class="w-2 h-2 rounded-full bg-gold flex-shrink-0 mt-1.5"
                  />
                  <div>
                    <p class="text-xs font-medium text-ink">{{ notif.title }}</p>
                    <p class="text-[11px] text-muted mt-0.5 leading-relaxed">{{ notif.message }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Profile -->
      <div class="relative" @mouseleave="startCloseProfile" @mouseenter="cancelCloseProfile">
        <button
          class="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl hover:bg-panel/60 transition-all duration-200"
          @click="toggleProfile"
        >
          <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-gold/20 to-gold/10 border border-gold/20 flex items-center justify-center text-gold text-[11px] font-bold flex-shrink-0">
            {{ initials }}
          </div>
          <svg class="w-3 h-3 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </button>

        <!-- Profile dropdown -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 scale-95 -translate-y-1"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 -translate-y-1"
        >
          <div
            v-if="showProfileMenu"
            class="absolute right-0 top-full mt-2 w-56 rounded-2xl border border-border/60 bg-white shadow-elevated overflow-hidden"
          >
            <div class="px-4 py-3 border-b border-border/40">
              <p class="text-sm font-medium text-ink truncate">{{ auth.user?.full_name }}</p>
              <p class="text-[11px] text-muted mt-0.5">{{ ROLE_LABELS[auth.user?.role ?? ""] }}</p>
            </div>
            <div class="py-1.5">
              <NuxtLink
                to="/dashboard/perfil"
                class="flex items-center gap-2.5 px-4 py-2 text-xs text-muted hover:text-ink hover:bg-panel/60 transition-colors"
                @click="closeProfile"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                Mi perfil
              </NuxtLink>
              <button
                class="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-muted hover:text-red-500 hover:bg-red-50/60 transition-colors"
                @click="auth.logout()"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                </svg>
                Cerrar sesión
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </nav>
</template>
