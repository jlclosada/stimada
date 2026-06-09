import { useAuthStore } from "~/stores/auth";

export default defineNuxtRouteMiddleware(async (to) => {
  // Skip during SSR — localStorage is not available on the server
  if (import.meta.server) return;

  const auth = useAuthStore();

  if (!auth.accessToken) {
    auth.initFromStorage();
  }

  if (!auth.user && auth.accessToken) {
    await auth.fetchMe();
  }

  const publicRoutes = ["/", "/login"];
  const isPublic = publicRoutes.includes(to.path);

  if (!auth.isAuthenticated && !isPublic) {
    return navigateTo("/login");
  }

  if (auth.isAuthenticated && to.path === "/login") {
    return navigateTo("/inicio");
  }
});
