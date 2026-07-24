# Styling Guide

This document describes the Tailwind CSS conventions used across the frontend, including dark mode support and the modal styling pattern.

## Architecture

The frontend uses three layers of styling:

1. **Base styles** — Tailwind utility classes for layout, spacing, and responsive behavior
2. **Component styles** — Reusable patterns for modals, cards, tables, and forms
3. **Theme variables** — CSS custom properties for colors that change with dark mode

## Building Tailwind CSS

Rebuild after any template or style change:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

For active development, use watch mode:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

## Class Naming Conventions

Use lowercase, hyphenated Tailwind classes:

| Category | Examples |
|---|---|
| Spacing | `px-4`, `py-6`, `mb-4` |
| Display | `flex`, `grid`, `block`, `hidden`, `absolute` |
| Colors | `bg-green-600`, `text-white`, `border-gray-200` |
| Sizing | `w-full`, `h-auto`, `max-w-lg` |
| Responsive | `md:grid`, `lg:flex` |
| Dark mode | `dark:bg-gray-900`, `dark:text-white` |

Do not mix custom class names with Tailwind utilities on the same element. Pick one approach per component.

## Dark Mode

Dark mode switches automatically based on system settings or user preference. Apply the `dark:` prefix to any class that needs a dark mode variant:

```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
    Content
</div>
```

### Color Palette

| | Light Mode | Dark Mode |
|---|---|---|
| Background | white, `#f9fafb` | `gray-900` (`#111827`), `gray-800` (`#1f2937`) |
| Text | `#111827`, `#6b7280` | white, `#f3f4f6` |
| Borders | `#e5e7eb` | `gray-700` (`#374151`) |
| Accent | `#16a34a` | `#4ade80` |

Every text element needs both variants:

```html
<!-- Correct -->
<p class="text-gray-900 dark:text-white">Readable in both modes</p>

<!-- Incorrect — invisible in dark mode -->
<p class="text-gray-900">Missing dark variant</p>
<p style="color: #111827;">Hardcoded color, no dark variant</p>
```

Standard text pairs:

| Use | Classes |
|---|---|
| Headings | `text-gray-900 dark:text-white` |
| Body text | `text-gray-900 dark:text-white` |
| Secondary text | `text-gray-600 dark:text-gray-400` |
| Accents | `text-red-600 dark:text-red-400` |

## Modal Pattern

Modals are the most complex styled components in the project and follow a specific pattern to remain reliable across both light and dark modes.

### Structure

```html
<div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-6">
    <div class="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-lg border border-gray-200 dark:border-gray-700">

        <div style="padding: 32px 40px; border-bottom: 1px solid #e5e7eb;" class="dark:border-gray-700">
            <!-- Title -->
        </div>

        <div style="padding: 32px 40px;">
            <!-- Body content -->
        </div>

        <div style="padding: 24px 40px; display: flex; justify-content: center; gap: 16px;">
            <!-- Cancel / Delete buttons -->
        </div>

    </div>
</div>
```

### Why inline styles are mixed with Tailwind

This pattern combines inline `style` attributes with Tailwind classes deliberately, due to a CSS specificity issue: Tailwind padding utilities can be overridden by cascade order in certain contexts. Inline styles are used for layout properties — padding, font size, borders, flex behavior — which guarantees they apply regardless of stylesheet order. Tailwind classes are reserved for colors that need a dark mode variant, since inline styles cannot express `dark:` conditionally.

This is not a preferred long-term architecture, but it resolves a real rendering issue and should be followed consistently for any new modal.

**Use inline styles only for:** `padding`, `font-size`, `font-weight`, `border-bottom`, `display`, `justify-content`, `gap`, `width`, and `color` (accent colors only, such as a red name).

### Buttons

```html
<!-- Primary / destructive action -->
<button
    style="width: 140px; padding: 12px; background: #dc2626; color: white; border-radius: 12px; font-weight: 600; font-size: 1rem; border: none; cursor: pointer;"
    class="hover:bg-red-700 transition">
    Delete
</button>

<!-- Secondary action -->
<button
    style="width: 140px; padding: 12px; border-radius: 12px; font-weight: 600; font-size: 1rem; border: none; cursor: pointer;"
    class="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition">
    Cancel
</button>
```

Every button needs a hover state defined for both light and dark mode.

## Tables

**Header row**

```html
<thead class="bg-green-600 dark:bg-green-700 border-b border-green-700 dark:border-green-800">
    <tr>
        <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Column Name</th>
    </tr>
</thead>
```

**Body rows**

```html
<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
        <td class="px-6 py-4 font-medium text-white">Data</td>
    </tr>
</tbody>
```

**Action buttons**

```html
<button class="text-red-300 hover:text-red-100 text-sm font-medium transition flex items-center gap-1">
    <span class="material-icons-round text-base align-middle">delete</span>
</button>
```

## Cards

```html
<div class="bg-card-light dark:bg-card-dark rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-800">
    <!-- Content -->
</div>
```

`card-light` and `card-dark` are custom theme variables that resolve automatically per mode.

## Forms

```html
<input
    type="text"
    class="w-full px-4 py-3 bg-input-bg-light dark:bg-input-bg-dark border border-gray-300 dark:border-gray-600 rounded-lg text-lbg-main-light dark:text-lbg-main-dark focus:ring-2 focus:ring-primary focus:border-transparent"
    placeholder="Enter text"
>
```

## Responsive Design

| Prefix | Breakpoint |
|---|---|
| `sm:` | 640px+ |
| `md:` | 768px+ |
| `lg:` | 1024px+ |
| `xl:` | 1280px+ |

Design mobile-first: start with the unprefixed (mobile) layout, then layer on responsive classes for larger screens.

```html
<div class="flex flex-col md:flex-row lg:grid lg:grid-cols-3 gap-4">
    <!-- Items -->
</div>
```

## Common Patterns

**Centered content**

```html
<div class="flex items-center justify-center min-h-screen">
    <div class="w-full max-w-lg">
        <!-- Content -->
    </div>
</div>
```

**Section with responsive padding**

```html
<section class="px-6 py-8 md:px-12 md:py-12">
    <!-- Content -->
</section>
```

**Grid layout**

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- 1 column mobile, 2 tablet, 3 desktop -->
</div>
```

**Flex spacing**

```html
<div class="flex items-center justify-between gap-4">
    <div>Left content</div>
    <div>Right content</div>
</div>
```

## Testing Dark Mode

1. Open DevTools (F12)
2. Go to the Rendering tab
3. Find "Emulate CSS media feature prefers-color-scheme"
4. Select "dark"

Verify text remains readable and colors render correctly across every component before merging a styling change.

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Dark Mode with Tailwind](https://tailwindcss.com/docs/dark-mode)
- [Tailwind Color Palette](https://tailwindcss.com/docs/customizing-colors)
- [Responsive Design](https://tailwindcss.com/docs/responsive-design)

---

**Last Updated:** July 2026