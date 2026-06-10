# PWA icons

The app ships with the vector Beer House Palenque logo used by the manifest, favicon, shortcuts and install metadata:

- `beer-house-logo.svg` — scalable SVG icon declared with `sizes: "any"` and `purpose: "any maskable"`.

For app-store publication or stricter platform requirements, generate branded PNG derivatives (for example 192×192 and 512×512) from this source SVG and update `frontend/public/manifest.json` plus `frontend/index.html` to point to those files.
