/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0805",
        coal: "#100c07",
        parchment: "#e9dcc0",
        gold: {
          DEFAULT: "#d9a441",
          soft: "#e6c277",
          bright: "#f4d98b",
          deep: "#a9741f",
        },
        ember: "#ff8a3d",
        snitch: "#f6c945",
        bludger: "#3a4655",
        quaffle: "#b5402f",
      },
      fontFamily: {
        display: ['"Cinzel"', "serif"],
        deco: ['"Cinzel Decorative"', "serif"],
        serif: ['"EB Garamond"', "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        gold: "0 0 40px -8px rgba(217,164,65,0.45)",
        glow: "0 0 80px -10px rgba(246,201,69,0.35)",
      },
      keyframes: {
        floaty: {
          "0%,100%": { transform: "translateY(0) rotate(-2deg)" },
          "50%": { transform: "translateY(-18px) rotate(2deg)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "200% 50%" },
        },
        pulseGlow: {
          "0%,100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        floaty: "floaty 7s ease-in-out infinite",
        shimmer: "shimmer 6s linear infinite",
        pulseGlow: "pulseGlow 4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
