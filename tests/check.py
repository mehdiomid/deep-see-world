#!/usr/bin/env python3
"""Zero-dependency sanity checks for Deep See World.

Run with: python3 tests/check.py
Optionally runs the page in headless Chrome (if installed) to catch JavaScript errors.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
failures = 0


def ok(label):
    print("  ✓ " + label)


def bad(label, detail=""):
    global failures
    failures += 1
    print("  ✗ " + label)
    if detail:
        print("      " + str(detail).replace("\n", "\n      "))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def load_messages():
    """Evaluate the dictionary file as JSON (it is a JSON object literal after the assignment)."""
    src = read("deep-see-world.en.js")
    start = src.index('window.__dswMessages["en"] =') + len('window.__dswMessages["en"] =')
    body = src[start:].strip().rstrip(";").strip()
    return json.loads(body)


def lookup(messages, path):
    node = messages
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


html = read("index.html")
print("Deep See World checks")

# 1. Dictionary parses and every referenced message exists.
try:
    M = load_messages()
    ok("message dictionary parses")
except Exception as e:  # noqa: BLE001
    bad("message dictionary parses", e)
    sys.exit(1)

script = "\n".join(re.findall(r"<script>([\s\S]*?)</script>", html))
keys = set(re.findall(r'\bt\("([\w.]+)"(?!\s*\+)', script)) | set(re.findall(r'data-t(?:-title)?="([\w.]+)"', html))
missing = sorted(k for k in keys if not isinstance(lookup(M, k), str))
# Keys built at runtime from fixed parts.
dynamic = ["zones." + r for r in ("reef", "twilight", "midnight")]
dynamic += ["reef.clue." + a for a in ("clownfish", "anemone", "shrimp", "eel", "pistol", "goby")]
dynamic += ["twilight." + k for k in ("night", "day", "goodNight", "badNight", "goodDay", "badDay")]
missing += [k for k in dynamic if not isinstance(lookup(M, k), str)]
if missing:
    bad("all referenced messages exist", ", ".join(missing))
else:
    ok("all %d referenced messages exist" % (len(keys) + len(dynamic)))

# 2. Facts: every fact has a title and text, is listed once in the journal, and can be earned.
facts = M["facts"]
broken = [k for k, v in facts.items() if not (v.get("title") and v.get("text"))]
if broken:
    bad("every fact has a title and text", ", ".join(broken))
else:
    ok("every fact has a title and text (%d facts)" % len(facts))

zones_src = re.search(r"const FACT_ZONES = \{([\s\S]*?)\};", script).group(1)
listed = re.findall(r'"(\w+)"', zones_src)
dupes = sorted({k for k in listed if listed.count(k) > 1})
if set(listed) != set(facts) or dupes:
    bad("journal lists every fact exactly once",
        "missing: %s; unknown: %s; duplicated: %s" % (sorted(set(facts) - set(listed)), sorted(set(listed) - set(facts)), dupes))
else:
    ok("journal lists every fact exactly once")

earnable = set(re.findall(r'data-fact="(\w+)"', html))
earnable |= set(re.findall(r'showFact\("(\w+)"', script))
for block in re.findall(r"(?:ARRIVAL_FACT|PAIR_FACT) = \{([^}]*)\}", script):
    earnable |= set(re.findall(r':\s*"(\w+)"', block))
earnable |= set(re.findall(r'showFact\([^)]*\?\s*"(\w+)"', script))
unearnable = sorted(set(facts) - earnable)
if unearnable:
    bad("every fact can be earned in the game", ", ".join(unearnable))
else:
    ok("every fact can be earned in the game")

# 3. SVG group tags are balanced in each scene (a dropped </g> silently breaks everything after it).
for m in re.finditer(r'<svg id="(scene-\w+)"[\s\S]*?</svg>', html):
    body = m.group(0)
    opens, closes = len(re.findall(r"<g\b", body)), len(re.findall(r"</g>", body))
    if opens == closes:
        ok("%s: <g> tags balanced (%d)" % (m.group(1), opens))
    else:
        bad("%s: <g> tags balanced" % m.group(1), "%d open vs %d close" % (opens, closes))

# 4. Everything stays in the browser: no external resources.
external = re.findall(r'(?:src|href)="(https?:[^"]+)"', html) + re.findall(r'url\((https?:[^)]+)\)', html)
external += re.findall(r'\bfetch\(', script)
if external:
    bad("no external resources", external)
else:
    ok("no external resources")

# 5. Every clickable thing has an accessible label.
hits = re.findall(r'<g[^>]*class="hit"[^>]*>', html)
unlabeled = [h for h in hits if "aria-label" not in h]
if unlabeled:
    bad("every clickable has an aria-label", unlabeled)
else:
    ok("all %d clickables have aria-labels" % len(hits))

# 6. Headless Chrome smoke test: load each room and fail on any JavaScript error.
chrome = next((p for p in [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "",
] if p and os.path.exists(p)), None)
if not chrome:
    print("  - headless Chrome not found; skipping smoke test")
else:
    import time
    page = "file://" + os.path.abspath(os.path.join(ROOT, "index.html"))
    shots = os.environ.get("DSW_SHOTS")  # set to a folder to keep the screenshots
    for room in ("reef", "twilight", "midnight"):
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(shots or tmp, room + ".png")
            if os.path.exists(png):
                os.remove(png)
            log = open(os.path.join(tmp, "log.txt"), "w+")
            # Chrome may not exit by itself on macOS once the screenshot is written, so stop it then.
            proc = subprocess.Popen([chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                                     "--user-data-dir=" + os.path.join(tmp, "profile"),
                                     "--enable-logging=stderr", "--v=0", "--window-size=1200,900",
                                     "--virtual-time-budget=3000", "--screenshot=" + png,
                                     page + "#" + room], stdout=subprocess.DEVNULL, stderr=log)
            deadline = time.time() + 150
            while time.time() < deadline and proc.poll() is None and not os.path.exists(png):
                time.sleep(0.5)
            time.sleep(1)
            proc.kill()
            proc.wait()
            log.seek(0)
            errors = [l for l in log.read().splitlines() if "CONSOLE" in l and ("Uncaught" in l or "Error" in l)]
            if not os.path.exists(png):
                bad("%s renders in headless Chrome" % room, "no screenshot produced")
            elif errors:
                bad("%s loads without JavaScript errors" % room, "\n".join(errors[:5]))
            else:
                ok("%s loads without JavaScript errors" % room)

    # Full playthrough: tests/play.html solves every puzzle (including wrong answers) and logs "PLAY ..." lines.
    with tempfile.TemporaryDirectory() as tmp:
        log = open(os.path.join(tmp, "log.txt"), "w+")
        proc = subprocess.Popen([chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                                 "--user-data-dir=" + os.path.join(tmp, "profile"), "--allow-file-access-from-files",
                                 "--autoplay-policy=no-user-gesture-required",
                                 "--enable-logging=stderr", "--v=0", "--window-size=1200,900",
                                 "--virtual-time-budget=120000", "--screenshot=" + os.path.join(tmp, "play.png"),
                                 "file://" + os.path.abspath(os.path.join(ROOT, "tests", "play.html"))],
                                stdout=subprocess.DEVNULL, stderr=log)
        deadline, lines = time.time() + 240, []
        while time.time() < deadline and proc.poll() is None:
            time.sleep(1)
            log.seek(0)
            lines = [re.search(r'"PLAY (.*?)"', l).group(1) for l in log.read().splitlines() if '"PLAY ' in l]
            if any(l.startswith("DONE") for l in lines):
                break
        proc.kill()
        proc.wait()
        if not any(l.startswith("DONE") for l in lines):
            bad("playthrough finished", "last steps: %s" % lines[-3:])
        for l in lines:
            if l.startswith("OK "):
                ok("play: " + l[3:])
            elif l.startswith("DEBUG "):
                print("      " + l)
            elif l.startswith("FAIL "):
                bad("play: " + l[5:])

print("\n%s" % ("All checks passed." if not failures else "%d check(s) failed." % failures))
sys.exit(1 if failures else 0)
