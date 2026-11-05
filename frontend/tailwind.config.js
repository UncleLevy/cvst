import animate from "tailwindcss-animate";

/** Design tokens ported from the Base44 version of CVST (navy + wine/burgundy + grey). */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#08111f",
          800: "#0b1730",
          700: "#12264a",
          600: "#1b3a6b",
          500: "#2b5490",
        },
        wine: {
          900: "#4b0013",
          800: "#65001a",
          700: "#800020",
          600: "#9a1030",
          500: "#c0304f",
          400: "#d4607a",
          100: "#fbeaee",
        },
      },
      boxShadow: {
        panel: "0 1px 2px rgba(8, 17, 31, 0.04), 0 18px 40px -24px rgba(8, 17, 31, 0.25)",
        raised: "0 24px 60px -28px rgba(8, 17, 31, 0.45)",
      },
      fontFamily: {
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [animate],
};
