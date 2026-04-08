import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        body: ['Sora', 'system-ui', 'sans-serif'],
      },
      colors: {
        bg: {
          base: '#080503',
          1: '#130b06',
          2: '#1e1009',
          3: '#2a1810',
        },
        border: { DEFAULT: '#3d2415', light: '#5c3a22' },
        amber: {
          DEFAULT: '#f5a623',
          light: '#fbbf5a',
          dim: '#9b6a1a',
        },
        terra: { DEFAULT: '#c1440e', light: '#e05a20' },
        forest: { DEFAULT: '#2d6a4f', light: '#3d8a65' },
        ink: {
          DEFAULT: '#fdf0e3',
          muted: '#9b7355',
          dim: '#5c3d28',
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.4s ease forwards',
        'fade-in': 'fadeIn 0.3s ease forwards',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'sway': 'sway 5s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        sway: {
          '0%, 100%': { transform: 'rotate(-2deg)' },
          '50%': { transform: 'rotate(2deg)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
