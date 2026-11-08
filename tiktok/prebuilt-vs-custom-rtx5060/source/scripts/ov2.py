import json, sys, urllib.request, urllib.parse, time
q = sys.argv[1]; pages = int(sys.argv[2])
out = []
for p in range(1, pages+1):
    url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": q, "page_size": 20, "page": p, "source": "wikimedia_audio", "license": "cc0,by"})
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "video-sfx-fetch/1.0"}), timeout=60))
    except Exception as e:
        print("ERR", e, file=sys.stderr); break
    out += d["results"]
    if p >= d["page_count"]: break
    time.sleep(1.2)
for r in out:
    print(json.dumps({"id": r["id"], "title": r["title"], "dur": r.get("duration"), "lic": r["license"], "lv": r.get("license_version"), "url": r["url"], "creator": r.get("creator"), "land": r.get("foreign_landing_url")}, ensure_ascii=False))
