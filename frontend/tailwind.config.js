/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        void: '#000000',
        depth: {
          1: '#030305',
          2: '#08080d',
          3: '#0f0f16',
        },
        surface: {
          DEFAULT: '#14141c',
          elevated: '#1a1a24',
        },
        neural: {
          DEFAULT: '#4deeea',
          dim: 'rgba(77, 238, 234, 0.15)',
          glow: 'rgba(77, 238, 234, 0.08)',
        },
        swarm: {
          DEFAULT: '#a78bfa',
          dim: 'rgba(167, 139, 250, 0.15)',
          glow: 'rgba(167, 139, 250, 0.08)',
        },
        signal: {
          green: {
            DEFAULT: '#4ade80',
            dim: 'rgba(74, 222, 128, 0.15)',
            glow: 'rgba(74, 222, 128, 0.08)',
          },
          orange: '#fb923c',
          red: '#f87171',
        },
        cyan: '#4deeea',
        blue: '#5e5ce6',
        purple: '#a78bfa',
        pink: '#f87171',
        orange: '#fb923c',
        green: '#4ade80',
        glass: {
          bg: 'rgba(255, 255, 255, 0.03)',
          border: 'rgba(255, 255, 255, 0.06)',
          'border-hover': 'rgba(255, 255, 255, 0.12)',
          highlight: 'rgba(255, 255, 255, 0.08)',
          shadow: 'rgba(0, 0, 0, 0.5)',
        },
        text: {
          primary: '#f0f0f5',
          secondary: 'rgba(240, 240, 245, 0.6)',
          tertiary: 'rgba(240, 240, 245, 0.35)',
          quaternary: 'rgba(240, 240, 245, 0.2)',
        }
      },
      fontFamily: {
        sans: ['Instrument Sans', 'system-ui', 'sans-serif'],
        display: ['Sora', 'sans-serif'],
        mono: ['JetBrains Mono', 'Space Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease forwards',
        'slide-up': 'slideUp 0.5s ease forwards',
        'glow-pulse': 'pulse-glow 3s ease-in-out infinite',
        'float': 'float 4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(100, 210, 255, 0.15)' },
          '50%': { boxShadow: '0 0 40px rgba(100, 210, 255, 0.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
      backdropBlur: {
        'liquid': '40px',
      }
    },
  },
  plugins: [],
}