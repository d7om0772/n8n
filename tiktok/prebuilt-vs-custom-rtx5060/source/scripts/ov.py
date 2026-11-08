import json, sys, urllib.request, urllib.parse, time
q = sys.argv[1]
params = {"q": q, "page_size": 20, "license": "cc0,by", "source": sys.argv[2] if len(sys.argv)>2 else "wikimedia_audio"}
url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "video-sfx-fetch/1.0"})
d = json.load(urllib.request.urlopen(req, timeout=60))
for r in d["results"]:
    print(json.dumps({"id": r["id"], "title": r["title"][:50], "dur": r.get("duration"), "lic": r["license"], "src": r["source"], "url": r["url"], "creator": r.get("creator"), "land": r.get("foreign_landing_url"), "tags": [t["name"] for t in (r.get("tags") or [])][:8], "fmt": r.get("filetype")}, ensure_ascii=False))
