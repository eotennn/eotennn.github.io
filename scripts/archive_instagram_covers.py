#!/usr/bin/env python3
"""Archive public Instagram reel cover images locally; no credentials required."""
import json, pathlib, re, urllib.request, urllib.parse, html, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT = ROOT / "catalog.json"
DEST = ROOT / "assets" / "instagram"
DEST.mkdir(parents=True, exist_ok=True)
data = json.loads(CAT.read_text(encoding="utf-8"))
headers = {"User-Agent": "Mozilla/5.0 (compatible; EoTeN-CoverArchiver/1.0)", "Accept": "text/html,image/avif,image/webp,image/*,*/*"}
def download(url, limit=8_000_000):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=18) as resp:
        payload = resp.read(limit + 1)
        if len(payload) > limit: raise ValueError("Too large")
        return payload, resp.headers.get("Content-Type", "")
changed = 0
for item in data.get("items", []):
    if item.get("platform") != "Instagram": continue
    image = item.get("image") or ""
    if image.startswith("assets/instagram/") and (ROOT / image).is_file(): continue
    ident = item.get("id", "")
    if not re.fullmatch(r"instagram-[0-9a-f]{14,64}", ident): continue
    candidates = [image] if image.startswith("https://") and "cdninstagram.com" in urllib.parse.urlparse(image).hostname else []
    reel = item.get("url", "")
    if re.fullmatch(r"https://www\.instagram\.com/(?:reel|p)/[\w-]+/?", reel):
        try:
            page, _ = download(reel, 2_000_000)
            match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page.decode("utf-8", "replace"))
            if match: candidates.insert(0, html.unescape(match.group(1)))
        except Exception as e: print("Page unavailable:", ident, str(e)[:100])
    for candidate in candidates:
        try:
            blob, ctype = download(candidate)
            if not ctype.lower().startswith("image/") or len(blob) < 1024: continue
            if blob.startswith(b"\xff\xd8\xff"): ext = "jpg"
            elif blob.startswith(b"\x89PNG\r\n\x1a\n"): ext = "png"
            elif blob[:4] == b"RIFF" and blob[8:12] == b"WEBP": ext = "webp"
            else: continue
            path = DEST / (ident + "." + ext)
            path.write_bytes(blob)
            item["image"] = path.relative_to(ROOT).as_posix()
            changed += 1
            print("Saved", path.name)
            break
        except Exception as e: print("Image unavailable:", ident, str(e)[:100])
    time.sleep(0.4)
if changed:
    CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Archived:", changed)
