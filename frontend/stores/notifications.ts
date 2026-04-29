import { defineStore } from "pinia";
import { useAuthStore } from "~/stores/auth";

export interface NotificationItem {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  project: number | null;
  project_id_display: string | null;
  read: boolean;
  created_at: string;
}

interface NotificationsState {
  items: NotificationItem[];
  unreadCount: number;
}

export const useNotificationsStore = defineStore("notifications", {
  state: (): NotificationsState => ({
    items: [],
    unreadCount: 0,
  }),

  actions: {
    async fetchUnreadCount() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (!auth.accessToken) return;

      try {
        const data = await $fetch<{ count: number }>(
          `${config.public.apiBase}/notifications/unread_count/`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.unreadCount = data.count;
      } catch {
        // silent
      }
    },

    async fetchAll() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();
      if (!auth.accessToken) return;

      try {
        const data = await $fetch<{ count: number; results: NotificationItem[] }>(
          `${config.public.apiBase}/notifications/`,
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        );
        this.items = data.results;
        this.unreadCount = data.results.filter((n) => !n.read).length;
      } catch {
        // silent
      }
    },

    async markRead(id: number) {
      const auth = useAuthStore();
      const config = useRuntimeConfig();

      try {
        await $fetch(`${config.public.apiBase}/notifications/${id}/mark_read/`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        });
        const item = this.items.find((n) => n.id === id);
        if (item) item.read = true;
        this.unreadCount = this.items.filter((n) => !n.read).length;
      } catch {
        // silent
      }
    },

    async markAllRead() {
      const auth = useAuthStore();
      const config = useRuntimeConfig();

      try {
        await $fetch(`${config.public.apiBase}/notifications/mark_all_read/`, {
          method: "POST",
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        });
        this.items.forEach((n) => (n.read = true));
        this.unreadCount = 0;
      } catch {
        // silent
      }
    },
  },
});
