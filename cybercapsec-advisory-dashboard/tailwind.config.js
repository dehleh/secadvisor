/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand palette — electric blue, matched to the CyberCapSec logo
        brand: {
          50: "#eef2ff",
          100: "#dbe4ff",
          200: "#b8c7ff",
          300: "#8ea4ff",
          400: "#5d77ff",
          500: "#2c4aff",
          600: "#0006ff",
          700: "#0005d6",
          800: "#0004a8",
          900: "#00038a",
        },
        accent: {
          500: "#f59e0b",
          600: "#d97706",
        },
        severity: {
          critical: "#dc2626",
          high: "#ea580c",
          medium: "#ca8a04",
          low: "#65a30d",
          informational: "#0891b2",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
