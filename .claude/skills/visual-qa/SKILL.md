---
name: visual-qa
description: >
  Close the loop on any generated visual: render the HTML headless, screenshot
  it, and verify the output is accurate and error-free before handing it to the
  user. Use immediately after creating or editing ANY HTML deliverable — an
  Artifact, dashboard, chart page, report, or data-story — and after any command
  that regenerates one. Triggers on "check the visual", "screenshot and verify",
  "make sure it renders", or any build of an .html file meant to be viewed.
license: MIT
metadata:
  version: 1.0.0
  category: quality
---

# visual-qa — render, screenshot, verify

Generated HTML can parse fine yet still be broken on screen: a chart that drew
zero points, text overlapping a bar, a value that contradicts the data, a body
that scrolls sideways on mobile. This skill closes that loop automatically so the
user never receives a broken visual.

## When to run it
Run **after every command that creates or changes an HTML visual** — before you
tell the user it's ready. That includes: writing/editing an `.html` file,
running a generator script that emits one (e.g. `build_story.py`), or publishing
an Artifact.

## Step 1 — render + capture (mechanical)
```bash
python3 .claude/skills/visual-qa/scripts/shoot.py <path/to/file.html>
# options: --width 1200  --viewport  --slices 5  --out preview.png
```
It launches the pre-installed Chromium, scrolls the page (to trigger lazy /
IntersectionObserver reveals), and prints a JSON summary:
- `console_errors` — JS runtime errors (any = fail)
- `svg_charts` / `blank_charts` — child-element count per `<svg id>`; a chart with
  <3 children drew nothing (fail)
- `horizontal_overflow` — body scrolls sideways (fail)
- `screenshot` — the PNG to inspect

Exit code is non-zero if any of those fail, so you can gate on it.

## Step 2 — Read the screenshot and verify (judgement)
**Always Read the PNG** — the mechanical checks catch blank/broken, but only your
eyes catch *wrong*. Check against this list:

- **Charts drew** — every chart has points/bars/lines, not an empty frame.
- **No overlap / clipping** — titles, axis labels, legends, and annotations don't
  collide or run off the edge; nothing important is cut off.
- **Numbers match the data** — headline figures on the page equal what the source
  computed (e.g. N, %, ฿ totals). A visual that renders a stale or wrong number is
  worse than one that crashes.
- **Color semantics are consistent** — the same meaning keeps the same color
  across the page (e.g. red=bad, green=good) and matches the legend.
- **Both themes** — if the page is theme-aware, toggle/`--viewport` a dark and a
  light shot; text must stay legible on both grounds.
- **Reads top-to-bottom** — hierarchy, spacing, and reveal order make sense.

## Step 3 — fix and re-run
If anything fails, fix the source and re-run Step 1. Repeat until the summary is
`PASS` **and** the screenshot looks right. Only then tell the user it's ready,
and share the screenshot so they see what you saw.

## Notes
- Chromium is pre-installed at `/opt/pw-browsers/`; the script finds it. Do not
  run `playwright install`.
- Delete throwaway `*_qa.png` previews before committing (keep the repo clean),
  or point `--out` at the scratchpad directory.
- For a multi-stage / scrolly page, use `--slices N` to also get section shots.
