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
        apple: {
          blue: {
            DEFAULT: '#007AFF',
            dark: '#0A84FF',
            50: '#F0F6FF',
            100: '#E0EEFF',
            500: '#007AFF',
            600: '#0062CC',
          },
          green: {
            DEFAULT: '#34C759',
            dark: '#30D158',
            50: '#F2FDF5',
            500: '#34C759',
            600: '#28A745',
          },
          orange: {
            DEFAULT: '#FF9500',
            dark: '#FF9F0A',
            50: '#FFF9F0',
            500: '#FF9500',
          },
          red: {
            DEFAULT: '#FF3B30',
            dark: '#FF453A',
            500: '#FF3B30',
          },
          purple: {
            DEFAULT: '#AF52DE',
            dark: '#BF5AF2',
            500: '#AF52DE',
          },
          indigo: {
            DEFAULT: '#5856D6',
            dark: '#5E5CE6',
            500: '#5856D6',
          },
          teal: {
            DEFAULT: '#5AC8FA',
            dark: '#64D2FF',
          },
          canvas: {
            light: '#F5F5F7',
            dark: '#0B0D11',
          },
          surface: {
            light: 'rgba(255, 255, 255, 0.85)',
            dark: 'rgba(22, 24, 29, 0.85)',
          },
        },
        cricket: {
          pitch: '#10b981',
          wicket: '#e11d48',
          gold: '#f59e0b',
          navy: {
            950: '#070b14',
            900: '#0d1322',
            850: '#121a2d',
            800: '#18223c',
            700: '#233054',
          },
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"SF Pro"',
          'Inter',
          'system-ui',
          'sans-serif',
        ],
        mono: [
          '"SF Mono"',
          'ui-monospace',
          'Menlo',
          'Monaco',
          'Consolas',
          '"JetBrains Mono"',
          'monospace',
        ],
      },
      borderRadius: {
        'squircle': '18px',
        'squircle-lg': '24px',
        'squircle-xl': '32px',
      },
      boxShadow: {
        'apple-sm': '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
        'apple-card': '0 2px 14px -2px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.04)',
        'apple-card-dark': '0 4px 20px -2px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.08)',
        'apple-float': '0 12px 32px -4px rgba(0,0,0,0.08), 0 4px 12px -2px rgba(0,0,0,0.04)',
        'apple-modal': '0 24px 64px -12px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.06)',
      },
    },
  },
  plugins: [],
}
