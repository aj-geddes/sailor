# GitHub Pages Setup Instructions

This document explains how to enable and configure GitHub Pages for the Sailor documentation site.

## Automatic Deployment

The documentation site is configured to automatically deploy when changes are pushed to the main branch. The GitHub Actions workflow handles this automatically.

## Manual Setup Steps

If you need to set up GitHub Pages manually:

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** > **Pages**
3. Under "Build and deployment":
   - Source: **GitHub Actions**
   - (The workflow will handle the rest)

### 2. Configure Base URL

The base URL is automatically configured in `_config.yml`:
```yaml
baseurl: "/sailor"
url: "https://aj-geddes.github.io"
```

Update these if your repository or username is different.

### 3. Trigger Deployment

Push to the main branch or manually run the workflow:
```bash
git push origin main
```

Or go to **Actions** > **Deploy Jekyll site to Pages** > **Run workflow**

### 4. Access Your Site

Once deployed, your documentation will be available at:
```
https://aj-geddes.github.io/sailor/
```

## Local Development

To test the site locally before deploying:

### Install Dependencies

```bash
cd docs
bundle install
```

### Run Jekyll Locally

```bash
cd docs
bundle exec jekyll serve --baseurl ""
```

Access at: `http://localhost:4000`

### With Live Reload

```bash
bundle exec jekyll serve --baseurl "" --livereload
```

## Troubleshooting

### Mermaid Diagrams Not Rendering

- Clear browser cache
- Check browser console for JavaScript errors
- Verify Mermaid.js is loading from CDN

### 404 Errors on Navigation

- Check `baseurl` in `_config.yml`
- Ensure all links use `{{ site.baseurl }}` or `relative_url` filter

### Styles Not Applied

- Verify `_includes/head-custom.html` is loaded
- Check browser DevTools for CSS loading issues
- Clear CDN/browser cache

### Build Failures

Check GitHub Actions logs:
1. Go to **Actions** tab
2. Click on failed workflow
3. Review build logs
4. Common issues:
   - Ruby version mismatch
   - Missing dependencies in Gemfile
   - Invalid YAML in front matter

## Site Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── Gemfile                  # Ruby dependencies
├── _includes/
│   └── head-custom.html     # Mermaid + custom styles
├── _layouts/
│   └── default.html         # Page layout with navigation
├── assets/
│   └── css/
│       └── style.scss       # Custom styles (if needed)
├── index.md                 # Home page
├── setup-guide.md           # Setup guide
├── admin-guide.md           # Admin guide
├── operations-guide.md      # Operations guide
├── troubleshooting-guide.md # Troubleshooting guide
├── DOCKER.md                # Docker docs (existing)
├── PRODUCTION.md            # Production docs (existing)
└── archive/                 # Historical documentation
```

## Customization

### Change Theme Colors

Edit the CSS variables in `_includes/head-custom.html`:

```css
:root {
  --sailor-primary: #0066cc;      /* Your color */
  --sailor-secondary: #1e90ff;    /* Your color */
  --sailor-accent: #20b2aa;       /* Your color */
  --sailor-dark: #003366;         /* Your color */
  --sailor-light: #e6f2ff;        /* Your color */
}
```

### Add New Pages

1. Create new `.md` file in `docs/`
2. Add front matter:
   ```yaml
   ---
   layout: default
   title: "Page Title"
   description: "Page description"
   ---
   ```
3. Add to navigation in `_config.yml`:
   ```yaml
   nav_links:
     - title: New Page
       url: /new-page
   ```

### Modify Mermaid Theme

Edit Mermaid configuration in `_includes/head-custom.html`:

```javascript
mermaid.initialize({
  theme: 'dark',  // default, dark, forest, neutral
  themeVariables: {
    primaryColor: '#your-color',
    // ... other variables
  }
});
```

## Support

For issues with GitHub Pages:
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Mermaid.js Documentation](https://mermaid.js.org/)

For Sailor-specific issues:
- [Open an issue](https://github.com/aj-geddes/sailor/issues)
