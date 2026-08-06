# Screenshots

The main [`README.md`](../../README.md) references four images from this directory. Capture
them and save with these exact filenames and they'll render automatically.

Start the stack and load data first (README steps 2–5), otherwise the pages render empty
states rather than real data.

| Filename | URL | What to capture |
|---|---|---|
| `dashboard.png` | http://localhost:3000 | Hero + league grid + recent results. Scroll to top; light mode. |
| `standings.png` | http://localhost:3000/team/1 | Full standings table with the points bar chart and goals scatter chart visible. |
| `ai-copilot.png` | http://localhost:3000 | Click the ✦ button (bottom-right), ask *"Who leads the Premier League and by how many points?"*, wait for the answer — capture with the **Source** citation visible under the reply. |
| `dark-mode.png` | http://localhost:3000 | Toggle the theme in the navbar, then capture the dashboard. |

## Guidelines

- **Viewport:** 1440×900 for desktop shots keeps the two-column README table balanced.
- **Format:** PNG. Keep each file under ~500 KB (these land in git history) — resize to
  1440px wide rather than committing a 4K retina capture.
- **Mobile drawer (optional):** the AI panel becomes a bottom drawer under the `lg`
  breakpoint. A ~400×850 capture saved as `ai-copilot-mobile.png` is a nice addition if you
  want to show the responsive behaviour; add it to the README table yourself.

## Capture tips

- **Chrome DevTools:** `F12` → device toolbar (`Ctrl+Shift+M`) → set 1440×900 → `Ctrl+Shift+P`
  → "Capture screenshot". This gives an exact viewport size with no OS chrome.
- **Windows:** `Win+Shift+S` for a region snip.
- Blur or avoid anything you don't want public — these are committed to the repo.
