/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:           '#0f1117',
        card:         '#1a1a2e',
        'card-inner': '#12122a',
        border:       '#2a2a4a',
        'border-dim': '#151525',
        accent:       '#6c63ff',
        'accent-h':   '#574fd6',
        danger:       '#e63946',
        muted:        '#555555',
        dim:          '#333333',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['"SF Mono"', '"Fira Code"', 'monospace'],
      },
    },
  },
  plugins: [],
}

