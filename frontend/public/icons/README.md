# PWA icon placeholders

The installable PWA manifest intentionally points to placeholder icon paths so the final brand assets can be added later without committing generated binary PNG files in this repository.

Add the production icons with these exact filenames before publishing the PWA:

- `icon-192-placeholder.png` — 192×192 PNG, maskable-safe padding recommended.
- `icon-512-placeholder.png` — 512×512 PNG, maskable-safe padding recommended.

After adding final assets, keep the paths in `frontend/public/manifest.json` or update the manifest and HTML metadata to match the production filenames.
