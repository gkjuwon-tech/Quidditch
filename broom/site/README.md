# Real Quidditch — landing page

A single static page (`index.html`, no build step, no backend) to show the
project and take backers. Open it directly:

```bash
xdg-open site/index.html      # or just double-click it
# or serve it:
python -m http.server -d site 8000   # -> http://localhost:8000
```

The visuals in `assets/` are generated from the actual simulator — they are not
mockups:

```bash
python tools/make_media.py    # -> assets/{replay,ballcam,poster}.{gif,png}
```

- `replay.gif`  — top-down AR replay of a live match (every dot flown by the real stack)
- `ballcam.gif` — first-person Snitch-cam with AR range markers
- `poster.png`  — hero still pulled from the replay

Deploy anywhere static (GitHub Pages, Netlify, an S3 bucket). The "Back us"
button is a `mailto:` — swap it for your real funding link before launch.
