import type { Config } from "tailwindcss";

export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#09090b",
        surface: "#0f0f11",
        panel: "#141417",
        raised: "#1c1c1f",
        border: "#27272a",
        "border-subtle": "#1f1f22",
        cream: "#fafafa",
        muted: "#71717a",
        subtle: "#3f3f46",
        gold: "#c9a84c",
        "gold-dim": "#a07c30",
        "gold-glow": "rgba(201,168,76,0.18)",
        roles: {
          admin: "#c9a84c",
          employee: "#60a5fa",
          client: "#4ade80",
          content: "#fb923c",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
        "3xl": "24px",
      },
      boxShadow: {
        "gold-sm": "0 0 0 3px rgba(201,168,76,0.18)",
        "gold-md": "0 0 0 4px rgba(201,168,76,0.22)",
        card: "0 1px 3px rgba(0,0,0,0.5), 0 8px 32px rgba(0,0,0,0.3)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blob: {
          "0%,100%": { transform: "translate(0,0) scale(1)" },
          "33%": { transform: "translate(40px,-30px) scale(1.08)" },
          "66%": { transform: "translate(-20px,20px) scale(0.96)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.16,1,0.3,1) both",
        "fade-in": "fade-in 0.4s ease both",
        "scale-in": "scale-in 0.45s cubic-bezier(0.16,1,0.3,1) both",
        "slide-down": "slide-down 0.5s cubic-bezier(0.16,1,0.3,1) both",
        blob: "blob 18s ease-in-out infinite",
        "blob-slow": "blob 26s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
