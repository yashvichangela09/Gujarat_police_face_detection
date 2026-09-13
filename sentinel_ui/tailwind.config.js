/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        command: {
          bg: '#060810',
          card: '#0c1220',
          panel: '#10182b',
          border: '#1a2744',
          subtle: '#25375c',
          text: '#e2e8f0',
          muted: '#64748b',
          cyan: '#00f2fe',
          emerald: '#00f5d4',
          amber: '#ffb703',
          alert: '#ff2a6d',
          purple: '#9d4edd',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 15px rgba(0, 242, 254, 0.25)',
        'glow-emerald': '0 0 15px rgba(0, 245, 212, 0.25)',
        'glow-alert': '0 0 20px rgba(255, 42, 109, 0.35)',
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'radar-sweep': 'radar 4s linear infinite',
      },
      keyframes: {
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      }
    },
  },
  plugins: [],
}
