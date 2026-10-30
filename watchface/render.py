#!/usr/bin/env python3
"""Rendert Raupi aus der Raupenbuch-App (index.html) zu den Bildern des Zifferblatts.
Aufruf (im Repo-Hauptordner):  python3 watchface/render.py
Braucht: pip install playwright pillow && playwright install chromium"""
import asyncio, glob, os, sys, threading, functools, http.server, socketserver, tempfile
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "watchface/src/main/res/drawable-nodpi")
TMP = tempfile.mkdtemp()
CROP, SIZE, POS = (0, 140, 640, 404), (360, 149), (45, 238)

SETUP = r"""
(() => {
  _praf = 1; window.petLoop = () => {};
  const sc = document.querySelector('.petscene');
  sc.style.cssText = 'background:transparent;box-shadow:none;border-radius:0;width:640px;height:525px;aspect-ratio:auto;margin:0;position:fixed;left:0;top:0;z-index:9999';
  document.querySelectorAll('.pstage,.poops').forEach(e => e.remove());
  document.body.appendChild(sc);
  [...document.body.children].forEach(c => { if(c !== sc) c.style.display = 'none'; });
  document.body.style.background = 'transparent'; document.documentElement.style.background = 'transparent';
  window.__noTO = f => { const st = window.setTimeout; window.setTimeout = () => 0; try { f(); } finally { window.setTimeout = st; } };
  return true;
})()
"""
FRAME = r"""
(t) => {
  const S = window.__SEG; let s = S[S.length-1]; for(const x of S){ if(t < x.t0 + x.d){ s = x; break; } }
  const wrap = document.querySelector('#petWrap'), fx = document.querySelector('#petFx');
  if(window.__cur !== s){
    wrap.classList.remove('dance','play','wiggle'); fx.innerHTML = '';
    _pw.x = s.k==='walk' ? s.x0 : s.x; _pw.dir = s.dir;
    if(s.k==='dance') __noTO(() => petFx('dance'));
    if(s.k==='ball') __noTO(() => petFx('ball'));
    if(s.k==='love'){ __noTO(() => petFx('love')); wrap.classList.remove('wiggle'); }
    window.__cur = s;
  }
  const lt = t - s.t0;
  if(s.k==='walk'){ _pw.x = s.x0 + (s.x1 - s.x0)*Math.min(1, lt/s.d); _pw.dir = s.x1 > s.x0 ? 1 : -1; } else { _pw.x = s.x; _pw.dir = s.dir; }
  document.querySelector('#pmv').setAttribute('transform', petMv(_pet));
  const still = s.k==='rest'; wrap.classList.toggle('still', still);
  if(!still) window.__crawl += t - window.__lastT; window.__lastT = t;
  for(const a of document.getAnimations()){ a.pause(); a.currentTime = (a.animationName==='crawl') ? window.__crawl*1000 : lt*1000; }
  return s.k;
}
"""
def segs():
    sp = 28*1.06; S=[]; t=0
    def add(**k):
        nonlocal t
        if k['k']=='walk': k['d']=abs(k['x1']-k['x0'])/sp
        k['t0']=t; t+=k['d']; S.append(k)
    add(k='rest',x=330,dir=-1,d=1.5)
    add(k='walk',x0=330,x1=200,dir=-1)
    add(k='rest',x=200,dir=-1,d=1.5)
    add(k='dance',x=200,dir=-1,d=3.8)
    add(k='rest',x=200,dir=-1,d=1.5)
    add(k='walk',x0=200,x1=300,dir=1)
    add(k='rest',x=300,dir=1,d=1.0)
    add(k='ball',x=300,dir=1,d=2.8)
    add(k='rest',x=300,dir=1,d=1.5)
    add(k='walk',x0=300,x1=330,dir=1)
    return S,t

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=ROOT)
    s = socketserver.TCPServer(("127.0.0.1", 0), h); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s.server_address[1]

async def render(port):
    os.makedirs(TMP + "/day"); os.makedirs(TMP + "/hearts")
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width":700,"height":600}, device_scale_factor=1, locale="de-DE")
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:{port}/index.html"); await pg.wait_for_timeout(2000)
        await pg.evaluate("(async()=>{await store.setMeta('pet',{...petNew(),stage:'L4',mood:100,hunger:80,health:100})})()")
        await pg.evaluate("ACTS.openPet()"); await pg.wait_for_timeout(800)
        await pg.evaluate(SETUP); await pg.wait_for_timeout(300)
        S, T = segs(); await pg.evaluate("s=>{window.__SEG=s;window.__crawl=0;window.__lastT=0;window.__cur=null}", S)
        fps = 12; n = round(T*fps)
        for i in range(n):
            await pg.evaluate(FRAME, i/fps)
            await pg.screenshot(path=f"{TMP}/day/{i:04d}.png", clip={"x":0,"y":0,"width":640,"height":525}, omit_background=True)
        await pg.evaluate("()=>{document.querySelector('#pmv').style.display='none'; window.__SEG=[{k:'love',x:300,dir:1,d:1.5,t0:0}]; window.__cur=null; window.__crawl=0; window.__lastT=0}")
        for i in range(int(1.5*15)):
            await pg.evaluate(FRAME, i/15)
            await pg.screenshot(path=f"{TMP}/hearts/{i:04d}.png", clip={"x":0,"y":0,"width":640,"height":525}, omit_background=True)
        await b.close()
        if errs: sys.exit("Fehler in der App: " + "; ".join(errs))
        print(f"{n} Bilder gerendert")

def font(bold, size):
    for f in (f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",):
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def assets():
    os.makedirs(RES, exist_ok=True)
    prep = lambda f: Image.open(f).convert("RGBA").crop(CROP).resize(SIZE, Image.LANCZOS)
    day = [prep(f) for f in sorted(glob.glob(TMP + "/day/*.png"))]
    day[0].save(RES + "/raupi_day.webp", save_all=True, append_images=day[1:], duration=83, loop=0, quality=80, method=3)
    day[0].save(RES + "/raupi_thumb.png")
    hearts = [prep(f) for f in sorted(glob.glob(TMP + "/hearts/*.png"))]
    hearts[0].save(RES + "/raupi_hearts.webp", save_all=True, append_images=hearts[1:], duration=67, loop=0, quality=85, method=3)
    hearts[0].save(RES + "/raupi_hearts_thumb.png")
    g = day[0].copy(); px = g.load()
    for y in range(g.height):
        for x in range(g.width):
            r, gg, bb, al = px[x, y]; v = int((r*0.3 + gg*0.59 + bb*0.11)*0.55); px[x, y] = (v, v, v, al)
    g.save(RES + "/raupi_ambient.png")
    W, ground = 450, 350
    bg = Image.new("RGB", (W, W)); d = ImageDraw.Draw(bg)
    for y in range(W):
        if y < ground: t = y/ground; c = tuple(int(a + (b-a)*t) for a, b in zip((214,236,222), (156,205,178)))
        else: t = (y-ground)/(W-ground); c = tuple(int(a + (b-a)*t) for a, b in zip((127,176,143), (96,145,112)))
        d.line([(0, y), (W, y)], fill=c)
    m = Image.new("L", (W, W), 0); ImageDraw.Draw(m).ellipse((-120, ground-14, W+120, ground+60), fill=255)
    bg = Image.composite(Image.new("RGB", (W, W), (127,176,143)), bg, m.filter(ImageFilter.GaussianBlur(6)))
    for (cx, cy, ang, s) in [(70,395,-25,1.0), (372,392,20,0.9), (118,418,10,0.7), (330,420,-15,0.75)]:
        L = Image.new("RGBA", (80, 40), (0,0,0,0)); ld = ImageDraw.Draw(L)
        ld.ellipse((4, 8, 76, 32), fill=(63,122,53,255)); ld.line((8, 20, 72, 20), fill=(156,196,110,255), width=2)
        L = L.resize((int(80*s), int(40*s))).rotate(ang, expand=True, resample=Image.BICUBIC)
        bg.paste(L, (cx - L.width//2, cy - L.height//2), L)
    bg.save(RES + "/raupi_bg.png")
    pv = bg.convert("RGBA"); pv.alpha_composite(day[0], POS); pd = ImageDraw.Draw(pv)
    pd.text((225, 125), "10:08", font=font(True, 96), fill=(31,61,45), anchor="mm")
    pd.text((225, 200), "Fr., 30. Okt.", font=font(False, 28), fill=(47,90,67), anchor="mm")
    mk = Image.new("L", (W, W), 0); ImageDraw.Draw(mk).ellipse((0, 0, W-1, W-1), fill=255)
    out = Image.new("RGB", (W, W), (0,0,0)); out.paste(pv.convert("RGB"), (0, 0), mk); out.save(RES + "/preview.png")
    for f in sorted(os.listdir(RES)): print(f, os.path.getsize(RES + "/" + f))

if __name__ == "__main__":
    asyncio.run(render(serve())); assets()
