/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:          '#080c12',
        surface:     '#0d1520',
        'surface-2': '#111e2e',
        border:      '#192637',
        'border-2':  '#243548',
        home:        '#6c63ff',
        'home-h':    '#574fd6',
        away:        '#e63946',
        data:        '#2dd4bf',
        'text-1':    '#e2e8f0',
        'text-2':    '#7a95b0',
        'text-3':    '#3a5068',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
        sans:    ['Inter', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

