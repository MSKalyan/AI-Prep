/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",     // App Router
    "./components/**/*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",     // VERY IMPORTANT for your structure
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
