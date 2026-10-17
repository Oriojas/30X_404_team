/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#04243C',
          steel: '#1D3557',
          teal: '#2B9CAE',
          tealHover: '#238393',
          bg: '#F8FAFC',
          border: '#E2E8F0',
          card: '#FFFFFF',
          muted: '#64748B',
          dark: '#0B1C30'
        },
        blinka: {
          navy: '#04243C',
          teal: '#2B9CAE',
          deep: '#0B1C30',
          blue: '#1D3557',
          surface: '#F8FAFC',
          accent: '#87EBFF'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
