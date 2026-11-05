/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        burgundy: { DEFAULT: "#800020", light: "#b3304f", dark: "#5c0017" },
        navy: { DEFAULT: "#12264a", dark: "#0b1730", light: "#1b3a6b" },
      },
    },
  },
  plugins: [],
};
