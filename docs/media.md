# Media assets

What to capture for the README, and how to wire it in. The hero GIF is the
single highest-leverage asset in the repo — the sub-second cache hit *is* the
product, and it's invisible in prose.

## Hero GIF — `images/rf-digital-twin-demo.gif`

**What to show, in ~15–20 seconds.** The point is the *speed* of the flip, so
don't cut the moment between click and render:

1. Open on the app with Config 1 (8×2 TX) already loaded — Scene render tab.
2. Tab across **SINR association → Users → CDFs** so the outputs are visible.
3. Back to the sidebar: change TX rows/cols to **16 × 16** and click **Render**.
   This is the money shot — the render lands in under a second.
4. Flip once more (e.g. pattern `tr38901` → `iso`) to show it wasn't a one-off.
5. Optionally end on the **Status** tab showing the `config_hash`.

**Capture settings.** Keep it under ~8 MB so GitHub renders it inline rather
than forcing a click-through:

- Window ~1440×900, then downscale to 1200px wide.
- 12–15 fps is plenty for UI motion.
- Trim dead air at both ends. No cursor hunting.

On macOS, record with `⌘⇧5` (or Kap / Gifski for better palettes), then:

```bash
# mp4 -> gif at 1200px / 14fps with a good palette
ffmpeg -i recording.mp4 -vf "fps=14,scale=1200:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
  -loop 0 images/rf-digital-twin-demo.gif

# check the size — under 8MB keeps it inline on GitHub
du -h images/rf-digital-twin-demo.gif
```

If it lands over ~10 MB, drop to 10 fps or 1000px before sacrificing length.

**Wiring it in.** Uncomment the image line near the top of `README.md`:

```markdown
![RF Digital Twin demo](images/rf-digital-twin-demo.gif)
```

Committing the GIF to the repo keeps the README self-contained (this is what
[pixels](https://github.com/databricks-industry-solutions/pixels) does). The
alternative — dragging the file into a GitHub issue and using the
`user-attachments` URL it generates — keeps the repo smaller but means the
README depends on an external asset.

## Worth adding later

- `images/rf-agent-showcase-demo.gif` — the Chapter 0 narrative auto-plays, so
  a capture of the alarm → zoom → agent-console → recommendation sequence sells
  it better than the static description does.
- `images/architecture.png` — a rendered version of the ASCII diagram in
  [architecture.md](architecture.md). The ASCII is fine in a terminal but reads
  poorly on the GitHub landing page.
- Static screenshots of the SINR coverage map and CDF tabs, for slide decks
  where a GIF won't play.

## Existing images

`notebooks/explore/images/` holds the six screenshots referenced by the original
exploratory notebook (scene render, per-config SINR maps, association plots, CDF
comparison). Those are notebook illustrations — keep them where they are rather
than promoting them to the README.
