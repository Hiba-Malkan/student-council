# Tailwind CSS Setup Instructions

## What Changed?

We moved from Tailwind CDN (which loads the entire ~3MB framework) to a proper build setup that only includes the CSS classes you actually use (~10-50KB).

## Setup Steps

### 1. Install Node.js (if not already installed)
Check if you have Node.js:
```bash
node --version
npm --version
```

If not installed, download from: https://nodejs.org/ (LTS version)

### 2. Install Tailwind Dependencies
```bash
cd /Users/hiba/student-council/frontend
npm install
```

This will install:
- `tailwindcss` - The core framework
- `@tailwindcss/forms` - Form styling plugin
- `@tailwindcss/typography` - Typography plugin

### 3. Build the CSS

**For development (watches for changes):**
```bash
npm run dev
```
This will watch your HTML files and rebuild CSS whenever you make changes.

**For production (one-time build):**
```bash
npm run build:css
```
This creates a minified CSS file for production.

### 4. Django Static Files Setup

Make sure your Django settings.py has:
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'static',
]
```

### 5. Collect Static Files (for production)
```bash
cd /Users/hiba/student-council/backend
python manage.py collectstatic
```

## File Structure

```
frontend/
├── package.json              # Node dependencies & scripts
├── tailwind.config.js        # Your color config is here now!
├── static/
│   ├── src/
│   │   └── input.css        # Tailwind source file
│   └── dist/
│       └── output.css       # Generated CSS (gitignored)
└── templates/
    └── base.html            # Now uses compiled CSS
```

## How to Change Colors

Edit `tailwind.config.js` instead of `base.html`:
```javascript
colors: {
  'card-light': '#F1F3E0',  // Change here
  'sidebar': '#aec8a4',     // Change here
  // etc...
}
```

Then rebuild:
```bash
npm run build:css
```

## Benefits

✅ **Much smaller file size** - Only includes classes you use (~10-50KB vs ~3MB)
✅ **Faster page loads** - Smaller CSS = faster downloads
✅ **Better caching** - CSS file can be cached by browser
✅ **Production ready** - Minified and optimized
✅ **Better development** - Separation of concerns

## Development Workflow

1. Start the CSS watcher:
   ```bash
   npm run dev
   ```

2. Start Django dev server (in another terminal):
   ```bash
   cd /Users/hiba/student-council/backend
   python manage.py runserver
   ```

3. Edit your HTML templates - CSS rebuilds automatically!

## Troubleshooting

**CSS not loading?**
- Run `npm run build:css` first
- Check that `frontend/static/dist/output.css` exists
- Make sure Django STATICFILES_DIRS includes frontend/static

**Changes not showing?**
- Hard refresh browser (Cmd+Shift+R)
- Make sure `npm run dev` is running
- Check browser console for 404 errors

**npm command not found?**
- Install Node.js from https://nodejs.org/
