# Woningradar brand assets

Minimal flat geometry — no gradients, no shadows, no raster images, no embedded
fonts. The mark is a house roofline with three concentric radar arcs radiating
upward from its apex; the innermost arc is warm orange, the returning signal.

## Files

| File | Purpose | viewBox | Aspect |
| --- | --- | --- | --- |
| `logo.svg` | The mark alone. Favicon, avatar, app icon. | `0 0 64 64` | 1:1 |
| `logo-wordmark.svg` | Mark plus "Woningradar" beside it. Headers, docs, slides. | `0 0 319 64` | ~5:1 |
| `banner.svg` | Wide README header with the Dutch tagline. | `0 0 1280 320` | 4:1 |

All three have transparent backgrounds and carry no `width`/`height` attributes,
so they scale to whatever box you put them in.

## Palette

Two colours plus one neutral. That is the whole system.

| Role | Hex | Used for | on `#ffffff` | on `#0d1117` |
| --- | --- | --- | --- | --- |
| Slate (primary) | `#4A6E8F` | The roofline, the two outer arcs, the "Woningradar" lettering. | 5.36:1 | 3.52:1 |
| Amber (accent) | `#CC6A10` | The innermost arc only. The one warm note — never a background fill. | 3.73:1 | 5.06:1 |
| Muted (neutral) | `#6B8299` | Banner tagline only. | 3.98:1 | 4.74:1 |

No pure white and no pure black appear anywhere. Every colour clears 3.5:1
against both `#ffffff` and GitHub's dark canvas `#0d1117`, so one theme-agnostic
set of files serves both themes — there are deliberately no `-light` / `-dark`
variants to keep in sync, and no `<picture>` switching is needed in the README.

## Clear space and minimum size

- **Clear space:** keep free margin on all sides equal to at least the height of
  the roofline (16 units in the 64-unit grid, i.e. 25% of the mark's height).
- **Minimum size:** `logo.svg` down to 24 px. It is drawn for 32 px favicon use —
  four shapes, stroke widths of 4.5 and 5.5 in a 64-unit grid (~7–9% of the
  frame), and a 3.5-unit gap between adjacent arcs.
- `logo-wordmark.svg` should not go below 160 px wide, `banner.svg` not below
  640 px, or the monoline lettering thins out.

## Don't

- Don't recolour the mark, and don't drop the amber arc to make it monochrome —
  that single warm arc is the whole idea.
- Don't stretch, squash, skew, or rotate it. Scale proportionally only.
- Don't add gradients, drop shadows, glows, outlines, or bevels.
- Don't put the mark inside a filled circle or rounded square, and don't set it
  over a photo or a busy pattern.
- Don't rebuild the wordmark in a different typeface, and don't re-set the
  lettering as `<text>`.
- Don't add a fourth arc or a fifth shape "for balance".

## Typography note

The lettering in `logo-wordmark.svg` and `banner.svg` is **not** SVG `<text>`.
It is constructed from geometric primitives — straight `<path>` segments,
quadratic curves, `<ellipse>` bowls and `<circle>` tittles, all monoline with
rounded caps. There is therefore no font dependency and no substitution risk:
the files render identically everywhere, including on GitHub.

Visual rendering of these files has not been verified in a browser.
