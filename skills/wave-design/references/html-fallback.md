# HTML fallback design

Use this when the Artifact tool or the Design type is unavailable, or when a Claude Design snapshot could not be exported. It produces the same thing the rest of the pipeline needs: one file, `docs/waves/design/snapshot.html`, with a section per screen id.

## Rules

- One self-contained file. Inline CSS, no external fonts, scripts, images or CDNs, so it renders offline and workers can read it as text.
- One `<section>` per screen, with `id` equal to the screen id (`screen-cart`), plus one `<section id="tokens">`.
- Tokens are CSS custom properties on `:root`, and every screen uses them. Do not hardcode colours or spacing inside screens.
- Static markup is enough. Show realistic copy and the states that matter (empty, filled, error) as separate screens only when the specs need them.
- Keep it small enough to read in one pass. This is a reference for building, not a prototype.

## Skeleton

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Design snapshot</title>
<style>
  :root {
    --color-bg: #ffffff;
    --color-text: #111827;
    --color-accent: #2563eb;
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 16px;
    --font-body: system-ui, sans-serif;
    --font-size-base: 16px;
  }
  body { font-family: var(--font-body); color: var(--color-text); background: var(--color-bg); }
  section { padding: var(--space-3); border-bottom: 1px solid #e5e7eb; }
</style>
</head>
<body>
<section id="tokens">
  <h2>Tokens</h2>
  <p>Colours, spacing and type shown as swatches and samples.</p>
</section>
<section id="screen-cart">
  <h2>Cart</h2>
  <p>Markup for the cart screen using only the tokens above.</p>
</section>
</body>
</html>
```

After the user approves, write `docs/waves/design/DESIGN.md` exactly as in the Claude Design reference, with `Source: HTML fallback`.
