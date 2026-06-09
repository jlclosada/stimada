import { useAuthStore } from "~/stores/auth";

const ROUTE_ROLES: Record<string, string[]> = {
  // Most specific routes first (startsWith matching)
  "/dashboard/admin": ["admin"],
  "/dashboard/usuarios": ["admin", "stimada_employee"],
  "/dashboard/clientes": ["admin", "stimada_employee"],
  "/dashboard/content-makers/me": ["content_maker"],
  "/dashboard/content-makers": ["admin", "stimada_employee", "client"],
  "/dashboard/mis-proyectos": ["client"],
  "/dashboard/mis-contenidos": ["content_maker"],
  "/dashboard/perfil": ["admin", "stimada_employee", "client", "content_maker"],
  // General dashboard (KPIs) — only admin/employee
  "/dashboard": ["admin", "stimada_employee"],
  // Projects (all roles, backend filters by queryset)
  "/proyectos": ["admin", "stimada_employee", "client", "content_maker"],
  // Notifications (all roles)
  "/notificaciones": ["admin", "stimada_employee", "client", "content_maker"],
};

export default defineNuxtRouteMiddleware((to) => {
  // Skip during SSR — auth state is not available on the server
  if (import.meta.server) return;

  const auth = useAuthStore();
  for (const [prefix, roles] of Object.entries(ROUTE_ROLES)) {
    if (to.path.startsWith(prefix)) {
      if (!auth.user || !roles.includes(auth.user.role)) {
        return navigateTo("/403");
      }
      break;
    }
  }
});
