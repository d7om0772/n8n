import json, os, sys, urllib.request, subprocess
for i in sys.argv[1:]:
    req = urllib.request.Request(f"https://api.pexels.com/videos/videos/{i}", headers={"Authorization": os.environ["PEXELS_API_KEY"], "User-Agent": "video-tool"})
    v = json.load(urllib.request.urlopen(req, timeout=60))
    files = sorted([f for f in v["video_files"] if f.get("width") and max(f["width"], f["height"]) <= 3840], key=lambda f: f["width"]*f["height"])
    b = files[-1]
    out = f"footage/hd_{i}.mp4"
    if not os.path.exists(out):
        subprocess.run(["curl", "-sS", "-o", out, b["link"]], check=True)
    m = json.load(open(f"footage/prev/{i}.json")) if os.path.exists(f"footage/prev/{i}.json") else {}
    m.update({"hd": out, "hdw": b["width"], "hdh": b["height"], "fps": b.get("fps"), "url": v["url"], "user": v["user"]["name"], "user_url": v["user"]["url"]})
    json.dump(m, open(f"footage/prev/{i}.json", "w"))
    print(i, b["width"], b["height"], b.get("fps"), os.path.getsize(out)//1024, "KB")
