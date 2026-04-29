import { useAuthStore } from "~/stores/auth";

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore();

  if (!auth.accessToken && import.meta.client) {
    auth.initFromStorage();
  }

  if (!auth.user && auth.accessToken) {
    await auth.fetchMe();
  }

  const publicRoutes = ["/login"];
  const isPublic = publicRoutes.includes(to.path);

  if (!auth.isAuthenticated && !isPublic) {
    return navigateTo("/login");
  }

  if (auth.isAuthenticated && isPublic) {
    return navigateTo("/dashboard");
  }
});
