/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        head: ['Syne', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      colors: {
        bg:      '#0a0e1a',
        bg2:     '#111827',
        bg3:     '#1a2235',
        accent:  '#4f8ef7',
        accent2: '#38d9a9',
        accent3: '#f7954f',
        danger:  '#f75f5f',
        muted:   '#6b7a99',
      },
    },
  },
  plugins: [],
}
