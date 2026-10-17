/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blinka: {
          navy: '#04243C',
          teal: '#2B9CAE',
          deep: '#0B1C30',
          blue: '#1D3557',
          surface: '#F8F9FF',
          accent: '#87EBFF'
        }
      }
    },
  },
  plugins: [],
}
