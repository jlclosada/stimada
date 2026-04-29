<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const route = useRoute();

interface NavItem { label: string; href: string; icon: string }

const navItems = computed<NavItem[]>(() => {
  const role = auth.user?.role;
  if (role === "admin") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: "grid" },
      { label: "Content Makers", href: "/dashboard/content-makers", icon: "star" },
      { label: "Clientes", href: "/dashboard/clientes", icon: "briefcase" },
      { label: "Usuarios", href: "/dashboard/usuarios", icon: "users" },
    ];
  }
  if (role === "stimada_employee") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: "grid" },
      { label: "Content Makers", href: "/dashboard/content-makers", icon: "star" },
      { label: "Clientes", href: "/dashboard/clientes", icon: "briefcase" },
      { label: "Usuarios", href: "/dashboard/usuarios", icon: "users" },
    ];
  }
  if (role === "client") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: "grid" },
      { label: "Mis proyectos", href: "/dashboard/mis-proyectos", icon: "folder" },
    ];
  }
  if (role === "content_maker") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: "grid" },
      { label: "Mis contenidos", href: "/dashboard/mis-contenidos", icon: "file" },
    ];
  }
  return [{ label: "Dashboard", href: "/dashboard", icon: "grid" }];
});

function isActive(href: string) {
  if (href === "/dashboard") return route.path === "/dashboard";
  return route.path.startsWith(href);
}
</script>

<template>
  <div class="min-h-screen bg-panel">
    <!-- Top App Navbar -->
    <AppNavbar />

    <div class="flex" style="height: calc(100vh - 4rem);">
      <!-- Sidebar -->
      <aside class="w-[240px] flex-shrink-0 flex flex-col border-r border-border/60 bg-white">
      <!-- Nav -->
      <nav class="flex-1 py-4 px-3 space-y-0.5 overflow-auto">
        <NuxtLink
          v-for="item in navItems"
          :key="item.href"
          :to="item.href"
          class="group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 relative"
          :class="isActive(item.href)
            ? 'bg-gold/10 text-gold'
            : 'text-muted hover:text-ink hover:bg-panel/80'"
        >
          <!-- Icons -->
          <svg class="w-[18px] h-[18px] flex-shrink-0" :class="isActive(item.href) ? 'text-gold' : 'text-muted group-hover:text-ink'" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path v-if="item.icon === 'grid'" stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            <path v-else-if="item.icon === 'users'" stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
            <path v-else-if="item.icon === 'star'" stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            <path v-else-if="item.icon === 'folder'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
            <path v-else-if="item.icon === 'briefcase'" stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          {{ item.label }}
        </NuxtLink>
      </nav>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Breadcrumb -->
      <header class="h-12 flex items-center px-8 border-b border-border/40 flex-shrink-0 bg-white/60">
        <nav class="flex items-center gap-1.5 text-sm text-muted">
          <span class="text-muted/60">Dashboard</span>
          <svg class="w-3.5 h-3.5 text-muted/40" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
          <span class="text-ink font-medium">{{ navItems.find(n => isActive(n.href))?.label ?? "Dashboard" }}</span>
        </nav>
      </header>

      <!-- Content -->
      <main class="flex-1 p-8 overflow-auto">
        <slot />
      </main>
    </div>
    </div>
  </div>
</template>
