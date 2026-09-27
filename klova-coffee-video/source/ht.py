from PIL import Image, ImageOps, ImageFilter
import numpy as np
from scipy import ndimage
ESP = np.array([42,23,17], float); PAPER = np.array([244,230,214], float); BORDER = np.array([255,248,238], float)
def halftone(rgba, target=900, cell=9, angle=45, border=16, gamma=0.75, eq=0.5, rf=1.28):
    im = rgba.convert('RGBA'); s = target/max(im.size)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    pad = border+6
    c = Image.new('RGBA',(im.width+2*pad, im.height+2*pad),(0,0,0,0)); c.paste(im,(pad,pad),im); im=c
    a = np.asarray(im.getchannel('A')).astype(float)/255
    rgb = Image.new('RGB', im.size, (255,255,255)); rgb.paste(im,(0,0),im)
    L = rgb.convert('L').filter(ImageFilter.UnsharpMask(radius=6, percent=120, threshold=2))
    L1 = np.asarray(ImageOps.autocontrast(L, cutoff=1)).astype(float)
    L2 = np.asarray(ImageOps.equalize(L, mask=Image.fromarray((a>0.5).astype('uint8')*255))).astype(float)
    g = ((1-eq)*L1 + eq*L2)/255
    g = ndimage.gaussian_filter(g, cell*0.28)**gamma
    Hh,W = g.shape
    yy,xx = np.mgrid[0:Hh,0:W].astype(float)
    th=np.deg2rad(angle); cs,sn=np.cos(th),np.sin(th)
    u=xx*cs+yy*sn; v=-xx*sn+yy*cs
    uc=(np.floor(u/cell)+0.5)*cell; vc=(np.floor(v/cell)+0.5)*cell
    xc=uc*cs-vc*sn; yc=uc*sn+vc*cs
    xi=np.clip(np.round(xc).astype(int),0,W-1); yi=np.clip(np.round(yc).astype(int),0,Hh-1)
    dark=1-g[yi,xi]; r=(cell/2)*rf*np.sqrt(np.clip(dark,0,1))
    ink=np.clip(r-np.hypot(u-uc,v-vc)+0.6,0,1)*(a[yi,xi]>0.5)
    out_rgb = PAPER*(1-ink[...,None]) + ESP*ink[...,None]
    hard=a>0.5
    dil=ndimage.gaussian_filter(ndimage.binary_dilation(hard,np.ones((3,3)),iterations=border).astype(float),1.0)
    inner=ndimage.gaussian_filter(hard.astype(float),0.8)
    o=BORDER*(1-inner[...,None]) + out_rgb*inner[...,None]
    img=Image.fromarray(np.dstack([o,np.clip(dil,0,1)*255]).astype('uint8'),'RGBA')
    return img.crop(img.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox())
