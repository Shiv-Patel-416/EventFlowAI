import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      colors: {
        "bg-base": "#050816",
        "bg-surface": "#0B1020",
        "bg-elevated": "#111827",
        blue: {
          DEFAULT: "#3B82F6",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
        },
        cyan: {
          DEFAULT: "#06B6D4",
          400: "#22D3EE",
          500: "#06B6D4",
        },
        emerald: {
          DEFAULT: "#10B981",
          400: "#34D399",
          500: "#10B981",
        },
        yellow: {
          DEFAULT: "#FACC15",
          400: "#FDE047",
          500: "#FACC15",
        },
        orange: {
          DEFAULT: "#FB923C",
          400: "#FDBA74",
          500: "#FB923C",
        },
        red: {
          DEFAULT: "#EF4444",
          400: "#F87171",
          500: "#EF4444",
        },
        purple: {
          DEFAULT: "#A78BFA",
          400: "#C4B5FD",
          500: "#A78BFA",
        },
        slate: {
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
        },
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
        "3xl": "20px",
      },
      backdropBlur: {
        xs: "4px",
      },
      animation: {
        "glow-pulse": "glow-pulse 3s ease infinite",
        "spin-slow": "spin-slow 8s linear infinite",
        "float": "float 4s ease-in-out infinite",
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        "spin-slow": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
