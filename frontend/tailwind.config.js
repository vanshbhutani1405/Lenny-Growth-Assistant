/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
      colors: { ink: "#172033", muted: "#697386", line: "#e7eaf0", paper: "#f8fafc" },
      boxShadow: { soft: "0 12px 32px rgba(23, 32, 51, 0.06)" },
    },
  },
  plugins: [],
};
