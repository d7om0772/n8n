import os, sys, json, time, urllib.request
KEY = os.environ["KIE_AI_API_KEY"]
STYLE = ("Hand-drawn notebook doodle illustration. Simple black ink pen line art with slightly wobbly, "
         "confident strokes of even thickness, like a sketchnote. Flat color accents only in soft warm yellow "
         "(#F6CF4E) and light beige (#E8D9BC), filled loosely inside some shapes. Pure plain white background, "
         "single isolated subject centered with generous empty margin, no paper texture, no shadows, no gradients, "
         "no shading, no hatching. ABSOLUTELY no text, no letters, no numbers, no logos. No people, no hands, "
         "no faces, no animals, no characters, no living creatures. Subject: ")
SUBJECTS = {
 "hero":  "a prepaid digital gift card (rounded rectangle with a chip and a few line stripes) floating slightly tilted above a smartphone, with three tiny sparkles around it.",
 "globe": "a globe of the earth with simple continent outlines and one big map location pin on top, and a small prepaid card leaning against the globe.",
 "tag":   "a price tag on a string with a big question mark drawn on it, next to a small warning triangle with an exclamation mark.",
 "store": "a small online-shop storefront with a striped awning, and a large shield with a checkmark standing in front of it.",
 "lock":  "a closed padlock next to a prepaid card whose code area is hidden by a row of dots (asterisks), with a small key nearby.",
 "outro": "a smartphone whose screen shows one big checkmark inside a circle, with a prepaid card slightly behind it and three tiny sparkles.",
}
def call(path, body=None):
    req = urllib.request.Request("https://api.kie.ai" + path, data=json.dumps(body).encode() if body else None,
        method="POST" if body else "GET", headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))
names = sys.argv[1:] or list(SUBJECTS)
tasks = {}
for n in names:
    r = call("/api/v1/jobs/createTask", {"model": "gpt-image-2-text-to-image",
        "input": {"prompt": STYLE + SUBJECTS[n], "aspect_ratio": "1:1", "resolution": "1K", "background": "opaque"}})
    print(n, r.get("code"), r.get("msg"), flush=True)
    tasks[n] = r["data"]["taskId"]
done = {}
t0 = time.time()
while len(done) < len(tasks) and time.time() - t0 < 600:
    time.sleep(8)
    for n, tid in tasks.items():
        if n in done: continue
        d = call(f"/api/v1/jobs/recordInfo?taskId={tid}")["data"]
        if d["state"] == "success":
            url = json.loads(d["resultJson"])["resultUrls"][0]
            urllib.request.urlretrieve(url, f"images/{n}.png"); done[n] = url; print("done", n, flush=True)
        elif d["state"] == "fail":
            done[n] = None; print("FAIL", n, d.get("failMsg"), flush=True)
print(json.dumps(done, indent=1))
