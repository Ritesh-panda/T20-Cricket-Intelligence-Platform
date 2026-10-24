/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cricket: {
          pitch: '#10b981',      // Emerald/turf accent
          wicket: '#e11d48',     // Crimson wicket alert
          gold: '#f59e0b',       // Boundary gold
          navy: {
            950: '#070b14',      // Deepest background
            900: '#0d1322',      // Shell/Sidebar background
            850: '#121a2d',      // Surface / Card background
            800: '#18223c',      // Elevated surface / border
            700: '#233054',      // Active border / subtle hover
          },
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'Consolas',
          'monospace',
        ],
      },
    },
  },
  plugins: [],
}
