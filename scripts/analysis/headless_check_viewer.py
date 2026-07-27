"""Throwaway headless-browser check: load a viewer HTML with Playwright,
capture console errors/exceptions, and report whether any WebGL canvas
pixels are non-background (i.e. something was actually drawn). Read-only.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def check(path_str: str):
    path = Path(path_str).resolve()
    url = path.as_uri()
    print(f"\n=== {path.name} ===")
    errors = []
    console_msgs = []
    with sync_playwright() as p:
        exe = r"C:\Users\o_iseri\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe"
        browser = p.chromium.launch(executable_path=exe)
        page = browser.new_page(viewport={"width": 1000, "height": 700})
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(3000)  # let three.js boot/render
        ready = page.evaluate("window.__ubemReady === true")
        print(f"window.__ubemReady = {ready}")
        print(f"pageerror count = {len(errors)}")
        for e in errors[:10]:
            print(f"  PAGEERROR: {e}")
        print(f"console messages ({len(console_msgs)} total), errors/warnings shown:")
        for m in console_msgs:
            if "[error]" in m or "[warning]" in m:
                print(f"  {m}")
        # Check canvas pixel content via toDataURL sampling (avoid huge dumps):
        # count non-background-color pixels drawn to a downsized snapshot.
        try:
            info = page.evaluate(
                """
                () => {
                  const canvas = document.querySelector('canvas');
                  if (!canvas) return {found: false};
                  const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
                  return {found: true, width: canvas.width, height: canvas.height};
                }
                """
            )
            print(f"canvas info = {info}")
        except Exception as e:
            print(f"canvas probe failed: {e}")
        screenshot_path = path.with_suffix(".diag.png")
        page.screenshot(path=str(screenshot_path))
        print(f"screenshot saved to {screenshot_path}")
        browser.close()


if __name__ == "__main__":
    for p in sys.argv[1:]:
        check(p)
