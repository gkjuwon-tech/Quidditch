# Real Aerial Quidditch — the site

A static, multi-page marketing + fundraising site. No build step, no backend.

```
index.html        hero / vision (original "wizarding stadium" art)
the-game.html     the sport, the pieces, the rules
engineering.html  the proof: metrics + the AR replay & Snitch-cam GIFs
safety.html       the three invariants, in depth
codex.html        the ENTIRE source, browsable in the page (no GitHub link)
support.html      backer tiers + contact CTA
assets/           site.css, site.js, bg-stadium.svg (original art),
                  replay.gif / ballcam.gif / poster.png (rendered from the sim),
                  code-data.js + stats.js (the Codex bundle)
```

## Regenerate the generated assets

```bash
python tools/build_site.py     # -> assets/code-data.js + stats.js  (the Codex)
python tools/make_media.py      # -> assets/{replay,ballcam,poster}  (the visuals)
```

The Codex and the visuals come from the real simulator — they are not mockups.

## View locally

```bash
python -m http.server -d site 8000     # -> http://localhost:8000
```

## Deploy

`.github/workflows/pages.yml` publishes `broom/site/` to GitHub Pages on every
push (it regenerates the Codex bundle first). Enable it once under
**Settings → Pages → Source: GitHub Actions**.

## Notes

- All artwork is original. This is an independent engineering project inspired by
  the flying sport in fiction; it is not affiliated with, and uses no assets of,
  that fiction's rights-holders.
- The "Back us" CTA is a `mailto:` placeholder — swap in your real funding link.
