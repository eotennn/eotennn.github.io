#!/usr/bin/env python3
"""EoTeN social Reels companion. Default: DRY RUN, never posts without opt-in.

Uses GitHub Releases already created by the separate Shorts workflow.
A durable 'started' ledger is written before any network publication.
Uncertain attempts are never automatically retried to prevent duplicates.
"""
import base64
import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

QUEUE = Path("shorts-publish-queue")
REPO = os.getenv("GITHUB_REPOSITORY", "eotennn/eotennn.github.io")
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v24.0")
LIVE = os.getenv("META_REELS_LIVE", "").lower() == "true"
FB_LIVE = os.getenv("META_FB_REELS_LIVE", "").lower() == "true"
CUTOFF = dt.datetime.fromisoformat(os.getenv("META_CUTOFF") or "2026-11-08T00:00:00+03:00")
MAX_JOBS = max(1, min(5, int(os.getenv("META_MAX_JOBS_PER_RUN", "1"))))
MEDIA_PREFIX = "https://github.com/eotennn/eotennn.github.io/releases/download/"

def log(message):
    print(message, flush=True)

def request_json(url, data=None, headers=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=75) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode(errors="replace")
        raise RuntimeError("Meta API error {}: {}".format(exc.code, detail)) from None

def meta(path, data=None):
    url = "https://graph.facebook.com/{}/{}".format(GRAPH_VERSION, path.lstrip("/"))
    return request_json(url, data, {"Authorization": "Bearer " + os.environ["META_PAGE_ACCESS_TOKEN"]})

def gh(*args):
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True,
                          check=True, timeout=70).stdout

def state_path(video_id, platform):
    return "social-publish-state/{}-{}.json".format(video_id, platform)

def existing_state(video_id, platform):
    path = state_path(video_id, platform)
    proc = subprocess.run(["gh", "api", "repos/{}/contents/{}".format(REPO, path)],
                          capture_output=True, text=True, timeout=45)
    if proc.returncode == 0:
        return json.loads(proc.stdout)
    if "404" in proc.stderr or "Not Found" in proc.stderr:
        return None
    raise RuntimeError("Unable to verify prior publication state for " + path)

def save_state(video_id, platform, state, previous=None):
    path = state_path(video_id, platform)
    payload = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    args = ["repos/{}/contents/{}".format(REPO, path), "-X", "PUT",
            "-f", "message=Track EoTeN {} Reel {}".format(platform, video_id),
            "-f", "content=" + base64.b64encode(payload.encode()).decode(),
            "-f", "branch=main"]
    if previous:
        args += ["-f", "sha=" + previous["sha"]]
    gh(*args)

def caption(job):
    return "{} 🎶\n\nEoTeN AI Music Production\n🎧 Tüm şarkılar profilimizde.\n\n#EoTeN #AnadoluRock #TurkceMuzik #AIMusic".format(job["title"].strip())

def publish_instagram(job):
    account_id = os.environ["META_IG_USER_ID"]
    response = meta(account_id + "/media", {
        "media_type": "REELS", "video_url": job["mediaUrl"],
        "caption": caption(job), "share_to_feed": "true"
    })
    container_id = str(response["id"])
    log("Instagram container created: " + container_id)
    for _ in range(50):
        time.sleep(12)
        status = meta(container_id + "?fields=status_code,status").get("status_code")
        if status == "FINISHED":
            result = meta(account_id + "/media_publish", {"creation_id": container_id})
            return {"id": str(result["id"]), "container_id": container_id}
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError("Instagram media container failed: " + str(status))
    raise RuntimeError("Instagram processing timeout: must reconcile manually")

def publish_facebook(job):
    account_id = os.environ["META_FB_PAGE_ID"]
    token = os.environ["META_PAGE_ACCESS_TOKEN"]
    session = meta(account_id + "/video_reels", {"upload_phase": "start"})
    video_id = str(session["video_id"])
    url = session["upload_url"]
    if not url.startswith("https://rupload.facebook.com/"):
        raise RuntimeError("Unexpected Facebook upload host")
    with urllib.request.urlopen(job["mediaUrl"], timeout=120) as response:
        video_bytes = response.read(200 * 1024 * 1024 + 1)
    if not (100000 < len(video_bytes) <= 200 * 1024 * 1024):
        raise RuntimeError("Unexpected media size")
    req = urllib.request.Request(url, data=video_bytes, method="POST", headers={
        "Authorization": "OAuth " + token, "offset": "0",
        "file_size": str(len(video_bytes)), "Content-Type": "application/octet-stream"
    })
    with urllib.request.urlopen(req, timeout=240) as response:
        result = json.loads(response.read().decode())
    if not result.get("success"):
        raise RuntimeError("Facebook upload not confirmed")
    complete = meta(account_id + "/video_reels", {
        "upload_phase": "finish", "video_id": video_id,
        "video_state": "PUBLISHED", "title": job["title"][:100],
        "description": caption(job)
    })
    if not complete.get("success"):
        raise RuntimeError("Facebook publish was not submitted")
    return {"id": video_id, "state": "submitted_processing"}

def valid_job(job):
    vid = job.get("sourceVideoId", "")
    url = job.get("mediaUrl", "")
    if not isinstance(vid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        return False
    if job.get("status") != "published":
        return False
    if not isinstance(url, str) or not url.startswith(MEDIA_PREFIX) or "?" in url or "#" in url:
        return False
    created = dt.datetime.fromisoformat(job["createdAt"].replace("Z", "+00:00"))
    return created >= CUTOFF

def main():
    jobs = []
    for filename in sorted(QUEUE.glob("*.json")):
        try:
            job = json.loads(filename.read_text(encoding="utf-8"))
            if valid_job(job):
                jobs.append(job)
        except (TypeError, KeyError, ValueError) as exc:
            log("Skipping malformed entry {}: {}".format(filename.name, exc))
    log("New eligible sources: {}".format(len(jobs)))
    if not LIVE:
        log("DRY RUN: no Meta publication. Enable only after token/rights/crossposting review.")
        for job in jobs[:MAX_JOBS]:
            log("Would prepare: {} ({})".format(job["title"], job["sourceVideoId"]))
        return

    required = ["META_IG_USER_ID", "META_PAGE_ACCESS_TOKEN"]
    if FB_LIVE:
        required.append("META_FB_PAGE_ID")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Publication blocked: missing " + ", ".join(missing))

    handled = 0
    for job in jobs:
        if handled >= MAX_JOBS:
            break
        vid = job["sourceVideoId"]
        targets = [("instagram", publish_instagram)]
        if FB_LIVE:
            targets.append(("facebook", publish_facebook))
        for platform, publish in targets:
            if existing_state(vid, platform):
                log("Already attempted; no automatic retry: {} / {}".format(vid, platform))
                continue
            state = {"sourceVideoId": vid, "platform": platform,
                     "status": "started_requires_manual_reconciliation_if_interrupted",
                     "startedAt": dt.datetime.now(dt.timezone.utc).isoformat()}
            save_state(vid, platform, state)
            try:
                result = publish(job)
                state.update({"status": "submitted", "result": result,
                              "submittedAt": dt.datetime.now(dt.timezone.utc).isoformat()})
                save_state(vid, platform, state, existing_state(vid, platform))
                log("SUBMITTED {} {} {}".format(platform, vid, result["id"]))
            except Exception as exc:
                log("UNCONFIRMED {} {}: {}. No automatic retry.".format(platform, vid, exc))
                raise
        handled += 1

if __name__ == "__main__":
    main()
