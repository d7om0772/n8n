import json, os, sys, time, urllib.request
KEY = os.environ["KIE_AI_API_KEY"]
OUT = sys.argv[1]
STYLE = ("Flat vector illustration, clean geometric shapes, minimal infographic style, "
         "light bright palette: sky blue #3B82F6, turquoise #14B8C4, fresh green #22C55E, white, very light navy outlines. "
         "Soft simple shading, no gradients noise, crisp edges, centered object, generous padding. "
         "Absolutely no people, no hands, no faces, no animals, no living beings. No text, no letters, no numbers, no logos. "
         "Isolated object on a fully transparent background.")
PROMPTS = {
 "phone_card": "A modern smartphone standing slightly tilted, its screen showing a glowing digital payment card with a chip shape and contactless wave symbol, small floating geometric circles and plus signs around it.",
 "plastic_card": "A physical plastic bank card with a gold chip, slightly tilted, partly sliding out of a white mail envelope, with a small delivery box beside it.",
 "shield": "A rounded security shield with a padlock in the center and a check mark, surrounded by small hexagons and dots representing encryption.",
 "tap_pay": "A smartphone hovering over a payment terminal with contactless signal waves between them, small green check badge above, simple geometric shapes.",
}
def call(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
tasks = {}
for name, p in PROMPTS.items():
    r = call("https://api.kie.ai/api/v1/jobs/createTask", {"model": "gpt-image-2-text-to-image",
        "input": {"prompt": p + " " + STYLE, "aspect_ratio": "1:1", "resolution": "1K", "background": "transparent"}})
    print(name, r.get("code"), r.get("msg"), flush=True)
    if r.get("code") == 200: tasks[name] = r["data"]["taskId"]
done = {}
for _ in range(120):
    for name, tid in tasks.items():
        if name in done: continue
        r = call(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
        d = r.get("data") or {}
        st = d.get("state")
        if st == "success":
            url = json.loads(d["resultJson"])["resultUrls"][0]
            path = os.path.join(OUT, name + os.path.splitext(url.split("?")[0])[1])
            urllib.request.urlretrieve(url, path); done[name] = path; print("OK", name, path, flush=True)
        elif st == "fail":
            done[name] = None; print("FAIL", name, d.get("failMsg"), flush=True)
    if len(done) == len(tasks): break
    time.sleep(5)
