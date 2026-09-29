"""
Pull REAL public channel + recent-video stats from the YouTube Data API v3
for Moonbug IPs and kids-content competitors.

Usage:
    export YOUTUBE_API_KEY="..."   # or put it in .env
    python scripts/fetch_youtube.py

Quota cost is tiny (~3 units per channel; the free daily quota is 10,000).
Handles below are best guesses - if one is reported as NOT FOUND, look up the
channel on YouTube, copy its @handle, and fix it here.
"""
import csv
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "raw_youtube"
API = "https://www.googleapis.com/youtube/v3/"
RECENT_VIDEOS_PER_CHANNEL = 50

CHANNELS = [
    # handle,                 owner_group,  brand
    ("@CoComelon",            "Moonbug",    "CoComelon"),
    ("@Blippi",               "Moonbug",    "Blippi"),
    ("@LittleBabyBum",        "Moonbug",    "Little Baby Bum"),
    ("@LittleAngel",          "Moonbug",    "Little Angel"),
    ("@Oddbods",              "Moonbug",    "Oddbods"),
    ("@GeckosGarage",         "Moonbug",    "Gecko's Garage"),
    ("@Pinkfong",    "Competitor", "Pinkfong"),
    ("@msrachel",             "Competitor", "Ms Rachel"),
    ("@SuperSimpleSongs",     "Competitor", "Super Simple Songs"),
    ("@ChuChuTV",             "Competitor", "ChuChu TV"),
    ("@BlueyOfficialChannel", "Competitor", "Bluey"),
]


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def main():
    load_env()
    if not os.environ.get("YOUTUBE_API_KEY"):
        raise SystemExit("Set YOUTUBE_API_KEY (in .env or your shell) first.")
    OUT.mkdir(parents=True, exist_ok=True)
    pulled_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    channels, videos = [], []

    for handle, group, brand in CHANNELS:
        res = get("channels", part="snippet,statistics,contentDetails", forHandle=handle)
        items = res.get("items", [])
        if not items:
            print(f"  NOT FOUND: {handle}  (fix the handle in CHANNELS)")
            continue
        ch = items[0]
        st = ch["statistics"]
        channels.append(dict(
            channel_id=ch["id"], handle=handle, channel_title=ch["snippet"]["title"],
            owner_group=group, brand=brand,
            subscriber_count=st.get("subscriberCount", ""), view_count=st.get("viewCount", ""),
            video_count=st.get("videoCount", ""), pulled_at=pulled_at))

        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        pl = get("playlistItems", part="contentDetails", playlistId=uploads,
                 maxResults=RECENT_VIDEOS_PER_CHANNEL)
        ids = [i["contentDetails"]["videoId"] for i in pl.get("items", [])]
        if ids:
            vres = get("videos", part="snippet,statistics,contentDetails,status", id=",".join(ids))
            for v in vres.get("items", []):
                s = v.get("statistics", {})
                videos.append(dict(
                    video_id=v["id"], channel_id=ch["id"], title=v["snippet"]["title"],
                    published_at=v["snippet"]["publishedAt"].replace("T", " ").replace("Z", ""),
                    duration_iso=v["contentDetails"].get("duration", ""),
                    made_for_kids=v.get("status", {}).get("madeForKids", ""),
                    # likes/comments are often hidden or disabled on made-for-kids videos
                    view_count=s.get("viewCount", ""), like_count=s.get("likeCount", ""),
                    comment_count=s.get("commentCount", ""), pulled_at=pulled_at))
        print(f"  {brand:20s} {int(st.get('subscriberCount', 0)):>13,} subs, {len(ids)} recent videos")

    for name, rows in (("channels", channels), ("videos", videos)):
        if rows:
            with open(OUT / f"{name}.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    print(f"Wrote {len(channels)} channels, {len(videos)} videos to {OUT}")


if __name__ == "__main__":
    main()
