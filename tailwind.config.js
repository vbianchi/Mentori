/** @type {import('tailwindcss').Config} */
export default {
  // This 'content' array tells Tailwind to scan all of these files
  // for class names. This is the fix.
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
