import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0c1222", 900: "#111827", 700: "#374151", 500: "#6b7280" },
        accent: { DEFAULT: "#2563eb", hover: "#1d4ed8" },
      },
    },
  },
  plugins: [],
};
export default config;
