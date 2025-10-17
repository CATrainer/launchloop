/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark Mode + Neon Accent Palette (Distinctive, Not Generic)
        'dark-navy': '#0A0E27',
        'dark-surface': '#12172E',
        'dark-elevated': '#1A2038',
        'neon-cyan': '#00D9FF',
        'neon-purple': '#B794F6',
        'neon-pink': '#FF6B9D',
        'electric-blue': '#4D7CFF',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
        'glass-bg': 'rgba(255, 255, 255, 0.05)',
        // Keep primary for backward compatibility
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      backgroundImage: {
        'gradient-user': 'linear-gradient(135deg, #B794F6 0%, #4D7CFF 100%)',
        'gradient-ai': 'linear-gradient(135deg, #00D9FF 0%, #4D7CFF 100%)',
        'gradient-animated': 'linear-gradient(135deg, #0A0E27 0%, #1A2038 50%, #0A0E27 100%)',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'gradient-shift': 'gradientShift 8s ease infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 217, 255, 0.3)',
        'glow-purple': '0 0 20px rgba(183, 148, 246, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
    },
  },
  plugins: [],
}
