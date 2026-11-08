import json, sys, urllib.request, urllib.parse, subprocess, os, time
ids = sys.argv[1:]
os.makedirs("sfx/raw", exist_ok=True); os.makedirs("sfx/wav", exist_ok=True)
meta = {}
if os.path.exists("sfx/meta.json"): meta = json.load(open("sfx/meta.json"))
for pid in ids:
    if any(k.startswith(pid) for k in meta): continue
    # resolve full id via search of local jsonl or API
    url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": pid, "page_size": 1})
    found = None
    for l in open("sfx/all.jsonl"):
        d = json.loads(l)
        if d["id"].startswith(pid): found = d; break
    if not found: print("notfound", pid); continue
    det = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.openverse.org/v1/audio/{found['id']}/", headers={"User-Agent": "video-sfx-fetch/1.0"}), timeout=60))
    ext = det["url"].split("?")[0].rsplit(".", 1)[-1]
    raw = f"sfx/raw/{pid}.{ext}"
    for attempt in range(8):
        code = subprocess.run(["curl", "-sS", "-L", "-A", "video-sfx-fetch/1.0 (short-video SFX download via Openverse)", "-o", raw, "-w", "%{http_code}", det["url"]], capture_output=True, text=True).stdout
        if code == "200": break
        print("retry", pid, code); time.sleep(25 * (attempt + 1))
    else:
        print("fail", pid); continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-ar", "48000", "-ac", "2", f"sfx/wav/{pid}.wav"], check=True)
    meta[found["id"]] = {"short": pid, "title": det["title"], "creator": det.get("creator"), "license": det["license"], "license_version": det.get("license_version"), "license_url": det.get("license_url"), "landing": det.get("foreign_landing_url"), "url": det["url"], "attribution": det.get("attribution")}
    print("ok", pid, det["title"], det["license"], det.get("license_version"))
    time.sleep(20.0)
    json.dump(meta, open('sfx/meta.json', 'w'), ensure_ascii=False, indent=1)
json.dump(meta, open("sfx/meta.json", "w"), ensure_ascii=False, indent=1)
