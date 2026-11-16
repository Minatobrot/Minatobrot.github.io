# Minatobrot.github.io

Source of https://panumic.com

| Path | What it is |
|---|---|
| `index.html` | Home page with the project list |
| `assets/` | Shared stylesheet (`site.css`) and self-hosted fonts |
| `favicon/` | Site icons (the cat) |
| `podcasts/` | Class chooser, plus `m2a/` and `s2e/` with the episodes |
| `grades/` | Panum Grades landing page, legal pages, its own icons and screenshots |
| `lehrplan/` | Lehrplan KSA topic overview (single page, images in `img/`) |
| `podcast_dashboard.py` | Desktop tool to add, edit and delete podcast episodes |

## Podcasts

Run `python podcast_dashboard.py` from the repo root. It writes the
`<article class="podcast-card">` blocks in `podcasts/m2a/index.html` and
`podcasts/s2e/index.html`. The player, the filter, the jump list and the
overview on `podcasts/` are all built from those blocks by
`podcasts/podcasts.js`, so nothing else needs editing when an episode changes.
