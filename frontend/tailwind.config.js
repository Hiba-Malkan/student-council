/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Main brand colors
        primary: "#1F4D3C",  // Main green - used for buttons, icons, highlights
        "primary-light": "#E6F0EB",  // Light green background
        "primary-hover": "#173a2e",  // Darker green for hover states

        "sym-logo": "#ffffff",
        
        // Page backgrounds
        "background-light": "#fafaf8",  // Slightly off-white - warm tone
        "background-dark": "#111827",   // Very dark gray - dark mode page background
        
        // Card/panel colors
        "card-light": "#449443",  // Green cards
        "card-dark": "#1F2937",   // Dark gray - dark mode cards/sidebar
        
        // Text colors
        "text-main-light": "#000000",  // Black - main text for default readability
        "text-main-dark": "#F3F4F6",   // Almost white - main text in dark mode
        "text-sub-light": "#4a4a4a",   // Dark gray - secondary text
        "text-sub-dark": "#9CA3AF",    // Light gray - secondary text in dark mode
        "text-on-card": "#ffffff",     // White text specifically for green cards
        "text-on-card-secondary": "#f3f4f6", // Light gray for secondary text on cards
        "lbg-main-light": "#000000",   // Black for labels
        "lbg-sub-light": "#4a4a4a",    // Dark gray for sub-labels
        "lbg-main-dark": "#ffffff",
        "lbg-sub-dark": "#ffffff",

        "sidebar": "#559e54",  // Sage green sidebar

        // Input fields
        "input-bg-light": "#f3f4f6",  // Light gray input backgrounds in light mode
        "input-bg-dark": "#374151",   // Medium gray - input backgrounds in dark mode
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
