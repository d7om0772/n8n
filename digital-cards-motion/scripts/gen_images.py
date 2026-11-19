"""Generate collage elements with kie.ai GPT Image-2 (transparent PNG cutouts)."""
import json, os, sys, time, requests, concurrent.futures as cf

KEY = os.environ["KIE_AI_API_KEY"]
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

STYLE = (
    "Single isolated object cutout for a modern digital collage (NOT paper collage: no paper texture, "
    "no torn edges, no tape, no cardboard). Materials: glossy plastic, frosted acrylic, iridescent holographic "
    "foil, soft chrome. Light airy pastel palette only: baby blue, lilac, mint, peach, butter yellow, pearl white. "
    "Soft diffused studio light, clean crisp silhouette, centered with generous margin, fully transparent background, "
    "no shadow on the ground. Absolutely no text, no letters, no numbers, no logos, no people, no hands, no faces, "
    "no animals, no living creatures."
)

ITEMS = {
    "card_hero": "A floating digital gift card (credit-card proportions, rounded corners) tilted in 3/4 perspective, "
                 "iridescent holographic lilac-to-baby-blue surface with a subtle embossed geometric wave pattern and a small pearl chip shape.",
    "phone": "A modern frameless smartphone floating at a slight 3/4 angle, pearl white body; its screen shows a soft pastel "
             "gradient with a glowing simple gift-card shape and a mint check circle icon (pure shapes, no text).",
    "gift_box": "A small glossy pastel peach gift box with a translucent lilac acrylic ribbon and bow, 3/4 view.",
    "bolt": "A puffy inflatable glossy lightning bolt in butter yellow with soft chrome highlights, slightly tilted.",
    "shield": "A frosted glass security shield with a glossy mint padlock embedded in its center, 3/4 view.",
    "envelope": "A translucent frosted acrylic envelope, slightly open, with a small holographic card sliding out of it, 3/4 view.",
    "cards_fan": "Three digital gift cards fanned out like a hand of cards (no hand visible): one baby blue with an embossed game "
                 "controller icon, one peach with an embossed shopping bag icon, one lilac with an embossed play button icon. Glossy plastic.",
    "cursor": "A chunky glossy 3D mouse pointer arrow in pearl white with a lilac iridescent edge, tilted slightly.",
    "check": "A glossy puffy mint green circular badge with a white 3D check mark, slight 3/4 tilt.",
    "sparkles": "A cluster of three soft chrome four-pointed sparkle stars of different sizes with pastel iridescent reflections.",
    "gamepad": "A glossy pastel lilac 3D video game controller with mint buttons and soft chrome highlights, 3/4 view.",
    "play": "A puffy glossy rounded-square app tile in baby blue with a white 3D play triangle in the center, slight tilt.",
    "cart": "A small glossy pastel baby-blue shopping cart with rounded shapes and lilac wheels, 3/4 view.",
}

def create(name, desc):
    body = {"model": "gpt-image-2-text-to-image",
            "input": {"prompt": f"{desc} {STYLE}", "aspect_ratio": "1:1", "resolution": "1K", "background": "transparent"}}
    r = requests.post("https://api.kie.ai/api/v1/jobs/createTask", headers=H, json=body, timeout=60).json()
    if r.get("code") != 200:
        raise RuntimeError(f"{name}: {r}")
    tid = r["data"]["taskId"]
    for _ in range(120):
        time.sleep(5)
        q = requests.get("https://api.kie.ai/api/v1/jobs/recordInfo", headers=H, params={"taskId": tid}, timeout=60).json()
        st = q.get("data", {}).get("state")
        if st == "success":
            url = json.loads(q["data"]["resultJson"])["resultUrls"][0]
            img = requests.get(url, timeout=120).content
            path = os.path.join(OUT, f"{name}.png")
            open(path, "wb").write(img)
            return f"{name}: ok ({len(img)//1024} KB)"
        if st == "fail":
            raise RuntimeError(f"{name}: fail {q['data'].get('failMsg')}")
    raise RuntimeError(f"{name}: timeout")

names = sys.argv[1:] or list(ITEMS)
with cf.ThreadPoolExecutor(6) as ex:
    futs = {ex.submit(create, n, ITEMS[n]): n for n in names}
    for f in cf.as_completed(futs):
        try: print(f.result(), flush=True)
        except Exception as e: print("ERR", e, flush=True)
