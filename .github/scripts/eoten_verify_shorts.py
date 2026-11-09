#!/usr/bin/env python3
"""Verify queued GitHub Release MP4s on GitHub-hosted runners, not the ChatGPT network.
Only successful, downloaded, probed assets receive a durable verification receipt.
Never schedules, publishes, or changes the pending queue.
"""
import base64
import datetime
import json
import os
import pathlib
import re
import subprocess
import tempfile

REPO = os.environ.get("GITHUB_REPOSITORY", "eotennn/eotennn.github.io")
MAX = 3

def run(args, check=True, timeout=600):
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=timeout)

def api(path):
    return json.loads(run(["gh", "api", path]).stdout)

def main():
    processed = 0
    for path in sorted(pathlib.Path("shorts-publish-queue").glob("*.json")):
        if processed >= MAX:
            break
        try:
            queue = json.loads(path.read_text(encoding="utf-8"))
            vid = path.stem
            if queue.get("status") != "pending" or queue.get("sourceVideoId") != vid or not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                continue
            tag = "eoten-auto-short-" + vid
            release = api(f"repos/{REPO}/releases/tags/{tag}")
            assets = [a for a in release.get("assets", []) if a.get("name", "").endswith(".mp4")]
            if len(assets) != 1:
                raise ValueError("Expected exactly one MP4 release asset")
            asset = assets[0]
            expected = f"https://github.com/{REPO}/releases/download/{tag}/{asset['name']}"
            if queue.get("mediaUrl") != expected:
                raise ValueError("Queue mediaUrl differs from actual release asset")
            receipt_path = f".github/shorts-verified/{vid}.json"
            receipt_file = pathlib.Path(receipt_path)
            previous = json.loads(receipt_file.read_text(encoding="utf-8")) if receipt_file.exists() else {}
            if previous.get("verified") is True and previous.get("assetId") == asset["id"] and previous.get("assetSize") == asset["size"] and previous.get("mediaUrl") == expected:
                continue
            processed += 1
            with tempfile.TemporaryDirectory() as tmp:
                destination = pathlib.Path(tmp) / asset["name"]
                # Use GitHub API with binary Accept header; do not scrape YouTube.
                run(["gh", "release", "download", tag, "--repo", REPO, "--pattern", asset["name"], "--dir", tmp], timeout=900)
                if not destination.is_file() or destination.stat().st_size != asset["size"] or destination.stat().st_size < 100000:
                    raise ValueError("MP4 download incomplete or wrong size")
                probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(destination)]).stdout)
                duration = float(probe["format"]["duration"])
                video = next(s for s in probe["streams"] if s["codec_type"] == "video")
                audio = any(s["codec_type"] == "audio" for s in probe["streams"])
                if not (29.7 < duration < 30.35 and video["width"] == 1080 and video["height"] == 1920 and audio):
                    raise ValueError("MP4 failed 30-second, 1080x1920, audio verification")
            receipt = {
                "verified": True, "sourceVideoId": vid, "releaseTag": tag,
                "mediaUrl": expected, "assetId": asset["id"], "assetSize": asset["size"],
                "durationSeconds": duration, "width": 1080, "height": 1920, "hasAudio": True,
                "verifiedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            content = base64.b64encode((json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()).decode()
            payload = {"message": f"Verify EoTeN Shorts release asset {vid}", "content": content, "branch": "main"}
            if receipt_file.exists():
                existing = api(f"repos/{REPO}/contents/{receipt_path}?ref=main")
                payload["sha"] = existing["sha"]
            # Send JSON on stdin using the API; no shell interpolation.
            subprocess.run(["gh", "api", "-X", "PUT", f"repos/{REPO}/contents/{receipt_path}", "--input", "-"],
                           input=json.dumps(payload), text=True, capture_output=True, check=True, timeout=60)
            print(f"VERIFIED {vid} {expected}", flush=True)
        except Exception as exc:
            print(f"NOT VERIFIED {path.stem}: {exc}", flush=True)
    print(f"Verification attempts this run: {processed}", flush=True)

if __name__ == "__main__":
    main()
