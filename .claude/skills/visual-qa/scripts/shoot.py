#!/usr/bin/env python3
"""
Render an HTML file headless, capture errors, and screenshot it for visual QA.

Usage:
    python3 shoot.py <file.html> [--out preview.png] [--width 1200]
                     [--viewport]            # viewport-only shot instead of full page
                     [--slices N]            # also save N stacked section screenshots

Prints a QA summary: console/page errors, per-<svg id> element counts (blank
chart detection), and horizontal-overflow check. Exit code is non-zero if any
console error, page error, or body horizontal overflow is found — so a caller
can gate on it.
"""
import argparse, glob, json, os, sys

def find_chromium():
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium/**/chrome"):
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", default=None)
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--viewport", action="store_true")
    ap.add_argument("--slices", type=int, default=0)
    a = ap.parse_args()

    path = os.path.abspath(a.html)
    if not os.path.exists(path):
        print(f"ERROR: no such file {path}"); sys.exit(2)
    out = a.out or os.path.splitext(path)[0] + "_qa.png"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        os.system(f"{sys.executable} -m pip install -q playwright >/dev/null 2>&1")
        from playwright.sync_api import sync_playwright

    exe = find_chromium()
    errors = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=exe)
        p = b.new_page(viewport={"width": a.width, "height": 1000}, device_scale_factor=1)
        p.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error",) else None)
        p.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        p.goto(f"file://{path}", wait_until="networkidle")
        p.wait_for_timeout(500)
        # scroll to trigger lazy reveals / IntersectionObserver
        total = p.evaluate("document.body.scrollHeight")
        y = 0
        while y < total:
            p.evaluate(f"window.scrollTo(0,{y})"); p.wait_for_timeout(120); y += 800
        p.evaluate("window.scrollTo(0,0)"); p.wait_for_timeout(300)

        # Force-settle entrance animations so the shot shows the FINAL state,
        # not a mid-transition frame (scroll-reveal pages are otherwise flaky):
        # reveal everything and kill transitions/animations.
        p.add_style_tag(content="*{transition:none!important;animation:none!important}"
                                " .reveal{opacity:1!important;transform:none!important}")
        p.evaluate("document.querySelectorAll('.reveal,[data-reveal]')"
                   ".forEach(e=>{e.classList.add('in');e.style.opacity=1;e.style.transform='none';})")
        p.wait_for_timeout(250)

        # blank-chart detection: count children of every svg[id]
        svgs = p.evaluate(
            "Array.from(document.querySelectorAll('svg[id]')).map(s=>({id:s.id,n:s.childElementCount}))")
        # horizontal overflow (page must never scroll sideways)
        overflow = p.evaluate("document.body.scrollWidth > document.body.clientWidth + 2")
        dims = p.evaluate("({w:document.body.scrollWidth, h:document.body.scrollHeight})")

        p.screenshot(path=out, full_page=not a.viewport)
        slices = []
        if a.slices > 0:
            step = dims["h"] // a.slices
            for i in range(a.slices):
                sp = os.path.splitext(out)[0] + f"_s{i+1}.png"
                p.evaluate(f"window.scrollTo(0,{i*step})"); p.wait_for_timeout(200)
                p.screenshot(path=sp, clip={"x": 0, "y": 0, "width": a.width, "height": min(1100, dims['h'])} if a.viewport else None,
                             full_page=False)
                slices.append(sp)
        b.close()

    blank = [s["id"] for s in svgs if s["n"] < 3]
    summary = {
        "screenshot": out,
        "page_px": dims,
        "console_errors": errors,
        "svg_charts": svgs,
        "blank_charts": blank,
        "horizontal_overflow": overflow,
        "slices": slices,
    }
    print(json.dumps(summary, indent=2))
    print("\n" + ("PASS" if not errors and not blank and not overflow else "CHECK") +
          f": {len(errors)} error(s), {len(blank)} blank chart(s), overflow={overflow}")
    print("-> Now Read the screenshot and verify it against the checklist in SKILL.md.")
    sys.exit(1 if (errors or blank or overflow) else 0)

if __name__ == "__main__":
    main()
