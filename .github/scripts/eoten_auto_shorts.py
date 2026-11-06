#!/usr/bin/env python3
"""EoTeN Shorts: automatically create full-frame 9:16 chorus clips.

Only generates MP4s as GitHub Releases; it does NOT post to YouTube.
State (idempotency) lives in release tags, so re-runs are safe.
"""
from __future__ import annotations

import base64
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL_ID = "UC3yygo9C3RVv2YVjttCddRQ"
YOUTUBE_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
MAX_PER_RUN = max(1, int(os.getenv("MAX_SHORTS_PER_RUN", "3")))
MAX_ATTEMPTS = max(MAX_PER_RUN, int(os.getenv("MAX_VIDEO_ATTEMPTS", "7")))
VIDEO_IDS = [
    "wl4Nfxc4j4E",  # Sana Gec Kaldim
    "Yqn1mvIMsVU",  # Ben Oyle Demek Istemedim
    "ZVLe6t62rFg",  # Seviyorsan Incitme (alternate)
    "PA-NImblBaw",  # Seni Cok Ozluyorum
    "SB9DwnLbniE",  # Gectim O Yoldan
    "nonS5yhpOZI",  # Sensizlige Mahkumum
    "dURsmxd-zq8",  # Yaz Bana Summer Dance Mix
    "jOid9VD5Is4",  # Rolunu Iyi Oynadin Rap
    "RPFBhgngChk",  # Rolunu Iyi Oynadin Rock
    "sUDiSt8GH90",  # Senden Kacamadim
    "uuyr2wMQZFA",  # Geceye Karisan
    "cMOq8Ds_438",  # Yaz Bana
]
# The corrected version for this source has already been created AND published.
ALREADY_DONE = {"UzGcX0cRfbg"}
# Existing Shorts must not become the source of another Short.
ALREADY_SHORTS = {
    "u_SDcWJhLdM", "blyPiWAS6F0", "UVf4jK7QznQ",
    "pIouEExEjWA", "JYxeey7fC_A",
}
REPO = os.environ.get("GITHUB_REPOSITORY", "eotennn/eotennn.github.io")
FFMPEG_PRESET = os.getenv("FFMPEG_PRESET", "veryfast")
YT_DLP = os.getenv("YT_DLP", "yt-dlp")


def log(msg):
    print(msg, flush=True)


def execute(cmd, *, cwd=None, timeout=720, check=True):
    log("RUN: " + " ".join(str(x) for x in cmd if not str(x).startswith("https://")))
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if r.returncode and check:
        raise RuntimeError(
            f"Exit {r.returncode} in {cmd[0]}\nSTDOUT: {r.stdout[-2400:]}\nSTDERR: {r.stderr[-3400:]}"
        )
    return r


def get_video_candidates():
    ids = []
    try:
        req = urllib.request.Request(YOUTUBE_RSS, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as response:
            xml_bytes = response.read()
        root = ET.fromstring(xml_bytes)
        namespace = "{http://www.youtube.com/xml/schemas/2015}"
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            val = entry.findtext(namespace + "videoId", default="")
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", val) and val not in ids:
                ids.append(val)
        log(f"RSS discovered {len(ids)} recent videos.")
    except Exception as exc:
        log(f"RSS temporarily unavailable ({exc}); using seeded long-form videos.")
    for known in VIDEO_IDS:
        if known not in ids:
            ids.append(known)
    return [i for i in ids if i not in ALREADY_DONE and i not in ALREADY_SHORTS]


def has_release(video_id):
    tag = "eoten-auto-short-" + video_id
    return execute(
        ["gh", "release", "view", tag, "--repo", REPO],
        timeout=30, check=False,
    ).returncode == 0



def queue_release(video_id):
    """Write one idempotent, durable publishing job for a ready MP4 release."""
    path = f"shorts-publish-queue/{video_id}.json"
    existing = execute(["gh", "api", "-X", "GET",
                        f"repos/{REPO}/contents/{path}",
                        "-f", "ref=main"], timeout=30, check=False)
    if existing.returncode == 0:
        log(f"Publish queue already registered: {video_id}")
        return
    if "404" not in existing.stderr and "Not Found" not in existing.stderr:
        log(f"Cannot check publishing queue for {video_id}: {existing.stderr[-500:]}")
        raise RuntimeError("Publishing queue verification failed")

    tag = f"eoten-auto-short-{video_id}"
    metadata = execute(
        ["gh", "release", "view", tag, "--repo", REPO, "--json", "name,assets,url"],
        timeout=45
    )
    release = json.loads(metadata.stdout)
    assets = [asset for asset in release.get("assets", [])
              if asset.get("name", "").lower().endswith(".mp4")]
    if not assets:
        raise RuntimeError(f"No release MP4 asset for {video_id}; will not queue.")
    asset = assets[0]
    title = release.get("name", "").replace("EoTeN Shorts: ", "").strip()
    title = re.sub(r"\s*\(" + re.escape(video_id) + r"\)\s*$", "", title)
    media = (f"https://github.com/{REPO}/releases/download/{tag}/"
             + asset["name"])
    payload = {
        "sourceVideoId": video_id,
        "title": title or "EoTeN AI Music Production",
        "releaseUrl": release.get("url", ""),
        "mediaUrl": media,
        "status": "pending",
        "publisher": "Metricool YouTube Shorts",
        "createdAt": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
    }
    encoded = base64.b64encode(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    ).decode("ascii")
    execute(["gh", "api", "-X", "PUT",
             f"repos/{REPO}/contents/{path}",
             "-f", f"message=Queue EoTeN Shorts {video_id} for automatic YouTube publication",
             "-f", f"content={encoded}", "-f", "branch=main"],
            timeout=60)
    log(f"PUBLICATION_QUEUED {video_id} {media}")


def get_metadata(video_id):
    address = "https://www.youtube.com/watch?v=" + video_id
    res = execute([
        YT_DLP, "--dump-single-json", "--skip-download", "--no-playlist",
        "--js-runtimes", "deno", "--remote-components", "ejs:github",
        "--socket-timeout", "25", "--retries", "2", address,
    ], timeout=150)
    return json.loads(res.stdout)


def download_video(video_id, folder):
    address = "https://www.youtube.com/watch?v=" + video_id
    basic = [
        YT_DLP, "--no-playlist", "--js-runtimes", "deno",
        "--remote-components", "ejs:github", "--socket-timeout", "25",
        "--retries", "3", "--fragment-retries", "3",
        "-f", "bv*+ba/b", "--merge-output-format", "mp4",
        "-o", "source.%(ext)s"
    ]
    try:
        execute(basic + [
            "--write-auto-subs", "--write-subs", "--sub-langs", "tr",
            "--sub-format", "vtt", address,
        ], cwd=folder, timeout=1000)
    except Exception as exc:
        log(f"Subtitle-inclusive download failed ({exc}). Trying plain video.")
        for fn in glob.glob(str(folder / "source.*")):
            try:
                os.remove(fn)
            except OSError:
                pass
        execute(basic + [address], cwd=folder, timeout=1000)
    matches = sorted(
        (f for f in folder.glob("source.*") if f.suffix.lower() in
         (".mp4", ".mkv", ".webm", ".mov")),
        key=lambda f: f.stat().st_size, reverse=True
    )
    if not matches:
        raise RuntimeError("yt-dlp reported success but did not produce source video.")
    return matches[0]


def media_probe(filename):
    output = execute([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height", "-of", "json",
        str(filename),
    ], timeout=40)
    result = json.loads(output.stdout)
    duration = float(result["format"]["duration"])
    video = next(s for s in result["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in result["streams"])
    return duration, video["width"], video["height"], has_audio


def normalized(text):
    text = unicodedata.normalize("NFKD", text.casefold().replace("ı", "i"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def read_subtitle_cues(folder):
    """Read timestamped Turkish VTT cues, including captions with rolling text."""
    entries = []
    regex = re.compile(
        r"(?m)^(?:(\d\d):)?(\d\d):(\d\d)\.(\d\d\d)\s+-->\s*[^\n]*\n"
    )
    for filename in folder.glob("source*.vtt"):
        raw = filename.read_text(encoding="utf-8-sig", errors="replace")
        markers = list(regex.finditer(raw))
        for i, match in enumerate(markers):
            hh, mm, ss, ms = match.groups()
            second = int(hh or 0) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000
            stop = markers[i + 1].start() if i + 1 < len(markers) else len(raw)
            fragment = raw[match.end():stop]
            fragment = re.sub(r"<[^>]*>", " ", fragment)
            fragment = re.sub(r"\[[^\]]*\]", " ", fragment)
            fragment = normalized(fragment)
            if len(fragment.split()) >= 3:
                entries.append((second, fragment))
    entries.sort(key=lambda item: item[0])
    deduped = []
    for second, fragment in entries:
        if deduped and abs(second - deduped[-1][0]) < 2 and fragment == deduped[-1][1]:
            continue
        deduped.append((second, fragment))
    return deduped


def chorus_from_subtitles(folder, song_title, duration):
    """Find first title lyric or repeated five-word chorus motif."""
    cues = read_subtitle_cues(folder)
    if not cues:
        return None

    name = re.sub(r"\s*\([^)]*\)", "", song_title)
    title_tokens = [
        token for token in normalized(name).split()
        if token not in ("original", "version", "mix", "acoustics", "eoten")
    ]
    if len(title_tokens) >= 2:
        title_phrase = " ".join(title_tokens)
        for i, (second, _) in enumerate(cues):
            if not 0.14 * duration <= second <= 0.68 * duration:
                continue
            nearby = " ".join(text for _, text in cues[i:i + 3])
            if title_phrase in nearby:
                log(f"Chorus from title lyric at {second:.1f}s.")
                return second, "Turkish caption matching song title"

    # Most choruses recur later in a song. Find repeated five-word lyric
    # phrases at least 45 s apart, avoiding rolling-subtitle duplicates.
    occurrences = {}
    for second, words in cues:
        if not 0.12 * duration <= second <= 0.89 * duration:
            continue
        tokens = words.split()
        for i in range(len(tokens) - 4):
            phrase = tuple(tokens[i:i + 5])
            if len(set(phrase)) < 4:
                continue
            occurrences.setdefault(phrase, []).append(second)

    candidate_weights = {}
    for times in occurrences.values():
        times = sorted(set(times))
        if len(times) < 2:
            continue
        for first in times:
            if not 0.14 * duration <= first <= 0.68 * duration:
                continue
            if any(45 <= other - first <= 240 for other in times):
                bucket = int(first // 8)
                candidate_weights[bucket] = candidate_weights.get(bucket, 0) + 1

    if candidate_weights:
        ranked = sorted(
            candidate_weights.items(),
            key=lambda item: (
                -item[1],
                abs(item[0] * 8 - duration * 0.32),
            ),
        )
        strongest_bucket, score = ranked[0]
        if score >= 3:
            nearby = [sec for sec, _ in cues
                      if int(sec // 8) == strongest_bucket]
            second = min(nearby) if nearby else strongest_bucket * 8
            log(f"Repeated chorus motif at {second:.1f}s ({score} matches).")
            return second, "repeated lyric motif in Turkish captions"

    return None


def first_chorus_position(folder, song_title, duration):
    detected = chorus_from_subtitles(folder, song_title, duration)
    if detected is None:
        guess = duration * 0.28
        log(f"No reliable caption-based chorus; using 28% fallback: {guess:.1f}s.")
        return max(0, min(duration - 30.2, guess - 2.0)), "estimated first chorus"
    detected_second, method = detected
    return max(0, min(duration - 30.2, detected_second - 2.0)), method


def render_clip(source_file, out_file, start):
    # Duplicate the original frames: full 16:9 artwork in the middle;
    # blurred version of the SAME original image fills the 9:16 background.
    video_filter = (
        "[0:v]split=2[base][cover];"
        "[base]scale=360:640:force_original_aspect_ratio=increase,"
        "crop=360:640,boxblur=20:2,scale=1080:1920[blur];"
        "[cover]scale=1080:1920:force_original_aspect_ratio=decrease[full];"
        "[blur][full]overlay=(W-w)/2:(H-h)/2:shortest=1,format=yuv420p[out]"
    )
    execute([
        "ffmpeg", "-nostdin", "-hide_banner", "-y",
        "-ss", f"{start:.3f}", "-i", str(source_file), "-t", "30",
        "-filter_complex", video_filter,
        "-map", "[out]", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", FFMPEG_PRESET,
        "-crf", "21", "-r", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(out_file),
    ], timeout=900)
    duration, width, height, audio = media_probe(out_file)
    if not (29.7 < duration < 30.35 and width == 1080 and height == 1920 and audio):
        raise RuntimeError(f"Bad Shorts output: {duration=}, {width=}, {height=}, {audio=}")
    return duration


def create_release(video_id, title, output_file, cut_start, method):
    tag = "eoten-auto-short-" + video_id
    youtube = "https://www.youtube.com/watch?v=" + video_id
    body = (
        f"Generated EoTeN Shorts draft from {youtube}\n\n"
        "Original video and song audio retained. Centered full-frame video "
        "with blurred background; 9:16 (1080x1920), 30 seconds.\n"
        f"Clip start: {cut_start:.1f}s. Chorus selection: {method}.\n"
        "Not uploaded to YouTube; original source remains unchanged.\n"
    )
    execute([
        "gh", "release", "create", tag, str(output_file),
        "--repo", REPO, "--target", os.environ.get("GITHUB_SHA", "main"),
        "--title", f"EoTeN Shorts: {title} ({video_id})",
        "--notes", body, "--latest=false"
    ], timeout=150)
    link = (
        f"https://github.com/{REPO}/releases/download/{tag}/"
        + output_file.name
    )
    log("SHORTS_READY " + link)
    queue_release(video_id)
    return link


def process(video_id):
    log(f"Processing {video_id}")
    metadata = get_metadata(video_id)
    title = metadata.get("title") or video_id
    # A recently published Short must never become a source of another Short.
    if metadata.get("duration") and float(metadata["duration"]) <= 180:
        log(f"Skipping {video_id}: YouTube duration <=180s (Short-sized upload).")
        return False
    if metadata.get("is_live") or metadata.get("live_status") in ("is_live", "is_upcoming"):
        log("Skipping livestream/upcoming.")
        return False
    with tempfile.TemporaryDirectory(prefix="eoten_short_") as tmp:
        folder = Path(tmp)
        original = download_video(video_id, folder)
        duration, width, height, audio = media_probe(original)
        if not audio:
            log(f"Skipping {video_id}: source lacks original audio.")
            return False
        if duration <= 180 and height > width:
            log(f"Skipping {video_id}: already a vertical short.")
            return False
        if duration < 40:
            log(f"Skipping {video_id}: not long enough.")
            return False
        cut_start, method = first_chorus_position(folder, title, duration)
        output = folder / f"EoTeN_Shorts_{video_id}_30s_Tam_Kadraj.mp4"
        render_clip(original, output, cut_start)
        create_release(video_id, title, output, cut_start, method)
    return True


def main():
    candidates = get_video_candidates()
    generated = 0
    attempts = 0
    failed = []
    for video_id in candidates:
        if has_release(video_id):
            try:
                queue_release(video_id)
            except Exception as exc:
                failed.append(video_id)
                log(f"QUEUE FAILED for {video_id}: {exc}")
            log(f"Skipping already created Shorts: {video_id}")
            continue
        if attempts >= MAX_ATTEMPTS or generated >= MAX_PER_RUN:
            break
        try:
            if process(video_id):
                generated += 1
                attempts += 1
        except Exception as exc:
            attempts += 1
            failed.append(video_id)
            log(f"FAILED for {video_id}: {exc}")
    summary = f"Completed run: {generated} new Shorts, {attempts} attempted, failures: {failed}"
    log(summary)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as fh:
            fh.write("## EoTeN Auto Shorts\n\n" + summary + "\n")
    if attempts > 0 and generated == 0 and failed:
        sys.exit("No Shorts generated: all attempted sources failed; see logs.")


if __name__ == "__main__":
    main()
