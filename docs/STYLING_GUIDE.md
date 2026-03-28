# Styling Guide

This project uses Tailwind CSS for responsive design and light/dark mode support. This guide explains the styling patterns, how to extend them, and how to avoid common pitfalls.

## Architecture

The frontend uses three layers of styling:

1. **Base styles** — Tailwind utility classes for layout, spacing, and responsive behavior
2. **Component styles** — Reusable CSS patterns for modals, cards, tables, and forms
3. **Theme variables** — CSS custom properties for colors that change with dark mode

## Working with Tailwind CSS

### Building CSS

Tailwind CSS must be rebuilt whenever you add or modify templates:```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

For development, use watch mode to rebuild automatically:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

Watch mode runs in the background and rebuilds on every save. This is the preferred way to work during development.

### Class Naming

Use lowercase class names with hyphens. Tailwind classes follow this pattern:

- Spacing: `px-4` (padding horizontal), `py-6` (padding vertical), `mb-4` (margin bottom)
- Display: `flex`, `grid`, `block`, `hidden`, `absolute`
- Colors: `bg-green-600`, `text-white`, `border-gray-200`
- Sizing: `w-full`, `h-auto`, `max-w-lg`
- Responsive: `md:grid`, `lg:flex` (apply at medium/large breakpoints)
- Dark mode: `dark:bg-gray-900`, `dark:text-white`

Do not mix custom class names with Tailwind utilities in the same element. Choose one approach per component.

## Light and Dark Mode

The application supports automatic light and dark mode switching based on system settings or user preference.

### Dark Mode Syntax

Use the `dark:` prefix on any Tailwind class to define dark mode styles:```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
    Content
</div>
```

This div shows a white background with dark text in light mode, and a dark gray background with white text in dark mode.

### Color Palette

**Light Mode:**
- Backgrounds: white, light gray (`#f9fafb`)
- Text: dark gray (`#111827`), medium gray (`#6b7280`)
- Borders: light gray (`#e5e7eb`)
- Accents: green (`#16a34a`)

**Dark Mode:**
- Backgrounds: gray-900 (`#111827`), gray-800 (`#1f2937`)
- Text: white, light gray (`#f3f4f6`)
- Borders: gray-700 (`#374151`)
- Accents: green (`#4ade80`)

Consistent pairing ensures readability in both modes:

```html
<!-- Good: consistent light/dark pairs -->
<p class="text-gray-900 dark:text-white">Readable in both modes</p>

<!-- Bad: only one mode covered -->
<p class="text-gray-900">Invisible in dark mode</p>
```

## Modal Styling Pattern

Modals are the most complex styled elements in the project. They require a specific pattern to work reliably in both light and dark modes.

### Structure

Modals use fixed positioning to overlay the page:```html
<!-- Outer container: fixed overlay -->
<div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-6">
    
    <!-- Inner modal: white background, dark mode gray -->
    <div class="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-lg border border-gray-200 dark:border-gray-700">
        
        <!-- Header section -->
        <div style="padding: 32px 40px; border-bottom: 1px solid #e5e7eb;" class="dark:border-gray-700">
            <!-- Title here -->
        </div>
        
        <!-- Body section -->
        <div style="padding: 32px 40px;">
            <!-- Content here -->
        </div>
        
        <!-- Footer section -->
        <div style="padding: 24px 40px; display: flex; justify-content: center; gap: 16px;">
            <!-- Buttons here -->
        </div>
        
    </div>
</div>
```

### Why This Pattern Works

This pattern combines inline styles with Tailwind classes for a specific reason: **CSS specificity**.

Tailwind padding utilities sometimes don't apply due to CSS cascade order. By using inline `style` attributes for layout properties (padding, font-size, borders), we guarantee those styles apply. Tailwind classes are then used only for colors that change with dark mode.

This is not ideal CSS architecture, but it solves a real browser rendering problem where Tailwind utility classes get overridden by other stylesheets.

### Inline Styles

Use inline styles for these properties only:

- `padding` — Define spacing inside sections
- `font-size` — Control text sizing
- `font-weight` — Make text bold or semibold
- `border-bottom` — Add dividers between sections
- `display` — Layout behavior (flex, block, etc.)
- `justify-content` — Align flex items
- `gap` — Space between flex items
- `width` — Fixed sizes like button width
- `color` — Used only for accent colors (like red text for names)

Example button styling:

```html
<button 
    style="width: 140px; padding: 12px; border-radius: 12px; font-weight: 600; font-size: 1rem; border: none; cursor: pointer;" 
    class="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition">
    Cancel
</button>
```

The inline `style` defines layout and sizing. The Tailwind `class` defines colors with dark mode variants.

### Text Colors in Dark Mode

All text must have a dark mode variant to avoid disappearing:```html
<!-- Good: light and dark variants -->
<p class="text-gray-900 dark:text-white">Visible in both modes</p>

<!-- Bad: only light mode -->
<p class="text-gray-900">Invisible in dark mode</p>

<!-- Bad: hardcoded color -->
<p style="color: #111827;">Invisible in dark mode</p>
```

Use these text color pairs:

- Headings: `text-gray-900 dark:text-white`
- Body text: `text-gray-900 dark:text-white`
- Secondary text: `text-gray-600 dark:text-gray-400`
- Accents: `text-red-600 dark:text-red-400`

### Button Styling

Buttons need both normal and hover states for both modes:

```html
<!-- Primary button (delete/confirm) -->
<button 
    style="width: 140px; padding: 12px; background: #dc2626; color: white; border-radius: 12px; font-weight: 600; font-size: 1rem; border: none; cursor: pointer;" 
    class="hover:bg-red-700 transition">
    Delete
</button>

<!-- Secondary button (cancel) -->
<button 
    style="width: 140px; padding: 12px; border-radius: 12px; font-weight: 600; font-size: 1rem; border: none; cursor: pointer;" 
    class="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition">
    Cancel
</button>
```

## Tables

Table styling uses Tailwind for layout with careful dark mode support:

### Header Row

```html
<thead class="bg-green-600 dark:bg-green-700 border-b border-green-700 dark:border-green-800">
    <tr>
        <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Column Name</th>
    </tr>
</thead>
```

The header has a green background that changes shade in dark mode. White text ensures readability in both modes.

### Body Rows

```html
<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
        <td class="px-6 py-4 font-medium text-white">Data</td>
    </tr>
</tbody>
```

Body rows have dividers that change color in dark mode. Hover states use semi-transparent backgrounds.

### Action Buttons

```html
<button class="text-red-300 hover:text-red-100 text-sm font-medium transition flex items-center gap-1">
    <span class="material-icons-round text-base align-middle">delete</span>
</button>
```

Action buttons use icon buttons with text color changes on hover. The color changes between light and dark variants (red-300 in light, adjusted for dark).

## Cards

Cards are used for sections of content with consistent styling:

```html
<div class="bg-card-light dark:bg-card-dark rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-800">
    <!-- Content -->
</div>
```

The `card-light` and `card-dark` classes are custom CSS variables defined in the theme that automatically adjust background colors.

## Forms

Form inputs should match the dark mode theme:

```html
<input 
    type="text"
    class="w-full px-4 py-3 bg-input-bg-light dark:bg-input-bg-dark border border-gray-300 dark:border-gray-600 rounded-lg text-lbg-main-light dark:text-lbg-main-dark focus:ring-2 focus:ring-primary focus:border-transparent"
    placeholder="Enter text"
>
```

This uses custom input background colors that adjust for dark mode and includes focus states with a colored ring.

## Responsive Design

Use Tailwind breakpoints to adjust layouts on different screen sizes:

```html
<!-- Full width on mobile, grid on larger screens -->
<div class="flex flex-col md:flex-row lg:grid lg:grid-cols-3 gap-4">
    <!-- Items -->
</div>
```

Breakpoint prefixes:
- `sm:` — 640px and up
- `md:` — 768px and up  
- `lg:` — 1024px and up
- `xl:` — 1280px and up

Always design mobile-first. Start with mobile layout, then add responsive classes for larger screens.

## Common Patterns

### Centered Content

```html
<div class="flex items-center justify-center min-h-screen">
    <div class="w-full max-w-lg">
        <!-- Content -->
    </div>
</div>
```

### Section with Padding

```html
<section class="px-6 py-8 md:px-12 md:py-12">
    <!-- Content with responsive padding -->
</section>
```

### Grid Layout

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Items: 1 column on mobile, 2 on tablet, 3 on desktop -->
</div>
```

### Flex Spacing

```html
<div class="flex items-center justify-between gap-4">
    <div>Left content</div>
    <div>Right content</div>
</div>
```

## Testing Dark Mode

To test dark mode during development:

1. In most browsers, open DevTools (F12)
2. Go to Rendering tab
3. Find "Emulate CSS media feature prefers-color-scheme"
4. Select "dark"

The page will instantly switch to dark mode. Test all components to ensure text is readable and colors look correct.

## Common Mistakes

**Don't:**
- Mix Tailwind classes with custom CSS class names in the same element
- Use hardcoded colors in `style` attributes without dark mode variants
- Forget `dark:` prefix for text colors (text becomes invisible)
- Use only light mode colors for backgrounds (cards become invisible)
- Override Tailwind with custom CSS unless necessary

**Do:**
- Use Tailwind classes as much as possible
- Pair light mode colors with dark mode variants: `bg-white dark:bg-gray-900`
- Use inline styles only for layout properties (padding, sizing, borders)
- Test in dark mode before committing changes
- Keep color changes consistent across similar components

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Dark Mode with Tailwind](https://tailwindcss.com/docs/dark-mode)
- [Tailwind Color Palette](https://tailwindcss.com/docs/customizing-colors)
- [Responsive Design](https://tailwindcss.com/docs/responsive-design)

## Questions?

For styling questions or to report styling issues, check the design patterns used in existing components before creating new ones. Consistency matters more than perfection.