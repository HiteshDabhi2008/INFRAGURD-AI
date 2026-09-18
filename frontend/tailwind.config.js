/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        government: {
          blue: '#1e3a8a', // Deep navy
          teal: '#0d9488',
          green: '#15803d',
          amber: '#d97706',
          red: '#b91c1c',
          light: '#f8fafc',
          card: '#ffffff'
        }
      },
      fontFamily: {
        sans: ['Atkinson Hyperlegible', 'Segoe UI', 'Tahoma', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
