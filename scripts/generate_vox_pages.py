#!/usr/bin/env python3
"""Create missing individual VØX pages from the shared artist registry.

Never overwrites already existing artist pages. Run when vox-artists.json changes.
Works with Python 3.9+ and has no third-party dependencies.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "vox-artists.json"
TEMPLATE = ROOT / "vox-m1.html"
IDENTIFIER = re.compile(r"^[MF][1-9][0-9]?$")


def main():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    artists = data.get("profiles", [])
    if not isinstance(artists, list):
        raise ValueError("profiles must be an array")
    template = TEMPLATE.read_text(encoding="utf-8")
    ids = set()
    created = []
    for item in artists:
        code = item.get("id", "")
        if not IDENTIFIER.fullmatch(code) or code in ids:
            raise ValueError("Invalid or duplicate VØX id: {!r}".format(code))
        ids.add(code)
        target = ROOT / ("vox-" + code.lower() + ".html")
        if target.exists():
            continue
        name = "VØX-" + code
        html = template.replace("VØX-M1", name)
        html = html.replace("vox-m1.html", target.name)
        html = html.replace('data-vox="M1"', 'data-vox="' + code + '"')
        target.write_text(html, encoding="utf-8")
        created.append(target.name)
    print("Created: " + (", ".join(created) if created else "no new artist pages"))


if __name__ == "__main__":
    main()
