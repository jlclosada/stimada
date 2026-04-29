import { useAuthStore } from "~/stores/auth";

const ROUTE_ROLES: Record<string, string[]> = {
  "/dashboard/usuarios": ["admin", "stimada_employee"],
  "/dashboard/content-makers": ["admin", "stimada_employee"],
  "/dashboard/clientes": ["admin", "stimada_employee"],
  "/dashboard/admin": ["admin"],
  "/dashboard/mis-proyectos": ["client"],
  "/dashboard/mis-contenidos": ["content_maker"],
};

export default defineNuxtRouteMiddleware((to) => {
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
