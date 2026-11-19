import os, json, time, urllib.request, sys
KEY=os.environ['KIE_AI_API_KEY']; OUT=sys.argv[1]
H={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'}
NO=" Strictly no people, no humans, no hands, no faces, no animals, no birds, no living creatures, no text, no letters, no numbers, no logos, no watermark."
GLASS="premium 3D render, made of clear frosted glass with soft iridescent pastel light-blue and lavender refractions, glossy white highlights, soft studio lighting, subtle inner glow, clean minimal style, isolated object centered,"
jobs={
 'bg':      dict(prompt="Ultra soft dreamy abstract background for a tech motion graphic. Bright high-key pastel gradient of baby blue, light lavender violet and pure white. Large blurred glowing light orbs, gentle bokeh, a few out-of-focus translucent frosted glass panels floating at different depths, smooth silky light waves, airy and luminous, very light colors, lots of empty space in the center."+NO, aspect_ratio='9:16', resolution='2K'),
 'card':    dict(prompt="A single floating digital gift card, "+GLASS+" rounded rectangle card shape with a small glass chip and a contactless wave symbol, holographic light-blue to violet gradient edge glow, slight 3/4 tilt, transparent background."+NO, aspect_ratio='3:2', resolution='1K', background='transparent'),
 'gamepad': dict(prompt="A single game controller icon, "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
 'bag':     dict(prompt="A single shopping bag icon, "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
 'play':    dict(prompt="A single rounded media play button icon (streaming), "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
 'shield':  dict(prompt="A single security shield icon with a checkmark in the middle, "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
 'bolt':    dict(prompt="A single lightning bolt icon, "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
 'phone':   dict(prompt="A single modern smartphone icon floating with a glowing glass notification bubble above its screen, "+GLASS+" transparent background."+NO, aspect_ratio='1:1', resolution='1K', background='transparent'),
}
def post(url,data):
    r=urllib.request.Request(url,data=json.dumps(data).encode(),headers=H,method='POST'); return json.load(urllib.request.urlopen(r,timeout=60))
def get(url):
    r=urllib.request.Request(url,headers=H); return json.load(urllib.request.urlopen(r,timeout=60))
tasks={}
for name,inp in jobs.items():
    p=os.path.join(OUT,name+'.png')
    if os.path.exists(p): continue
    res=post('https://api.kie.ai/api/v1/jobs/createTask',{'model':'gpt-image-2-text-to-image','input':inp})
    print(name,res,flush=True)
    if res.get('code')==200: tasks[name]=res['data']['taskId']
t0=time.time()
while tasks and time.time()-t0<900:
    time.sleep(10)
    for name,tid in list(tasks.items()):
        d=get('https://api.kie.ai/api/v1/jobs/recordInfo?taskId='+tid)['data']
        st=d.get('state')
        if st=='success':
            url=json.loads(d['resultJson'])['resultUrls'][0]
            urllib.request.urlretrieve(url,os.path.join(OUT,name+'.png')); print('done',name,flush=True); del tasks[name]
        elif st=='fail':
            print('FAIL',name,d.get('failCode'),d.get('failMsg'),flush=True); del tasks[name]
print('remaining',tasks)
