/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        teal: {
          950: "#0A322E",
          900: "#0F4C46",
          800: "#166059",
          100: "#E4F0EE",
        },
        clay: {
          600: "#E88D67",
          500: "#EFA07E",
          100: "#FBEAE1",
        },
        cream: "#FAF6EF",
      },
      fontFamily: {
        display: ["Sora", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
      keyframes: {
      fadeIn: {
        "0%": { opacity: "0", transform: "translateY(4px)" },
        "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
}