import json, os, sys, urllib.request, subprocess
from concurrent.futures import ThreadPoolExecutor
ids = sys.argv[1:]
os.makedirs("footage/prev", exist_ok=True)
def get(i):
    req = urllib.request.Request(f"https://api.pexels.com/videos/videos/{i}", headers={"Authorization": os.environ["PEXELS_API_KEY"], "User-Agent": "video-tool"})
    v = json.load(urllib.request.urlopen(req, timeout=60))
    files = sorted([f for f in v["video_files"] if f.get("width")], key=lambda f: f["width"]*f["height"])
    small = [f for f in files if min(f["width"], f["height"]) >= 360][0]
    big = [f for f in files if min(f["width"], f["height"]) >= 1080]
    big = big[0] if big else files[-1]
    json.dump({"id": i, "dur": v["duration"], "w": v["width"], "h": v["height"], "url": v["url"], "user": v["user"]["name"], "user_url": v["user"]["url"], "small": small["link"], "big": big["link"], "bw": big["width"], "bh": big["height"]}, open(f"footage/prev/{i}.json", "w"))
    p = f"footage/prev/{i}.mp4"
    if not os.path.exists(p):
        subprocess.run(["curl", "-sS", "-A", "Mozilla/5.0", "-o", p, small["link"]], check=True)
    d = v["duration"]
    for k, frac in enumerate([0.08, 0.35, 0.62, 0.92]):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(d*frac), "-i", p, "-frames:v", "1", "-vf", "scale=-2:240", f"footage/prev/{i}_{k}.jpg"])
    return i
with ThreadPoolExecutor(6) as ex:
    for r in ex.map(lambda i: (lambda: get(i))() if True else None, ids): print("ok", r)
