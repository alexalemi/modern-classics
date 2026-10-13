"""Press-resolution woodcuts for the Candle print editions, cut from the Harper
1861 scan (archive.org courseofsixlectu00fara), named as the epub names them,
into build/print_images/candle/ (build_print copies them over the epub art).
pairs.py makes the old-vs-new contact sheet for checking."""
import sys, glob, numpy as np
from PIL import Image
from scipy import ndimage
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = str(ROOT / 'build/candle_scan/harper/courseofsixlectu00fara_jp2')   # archive.org courseofsixlectu00fara (Harper 1861, 500 ppi), _jp2.zip unpacked
OUT = str(ROOT / 'build/print_images/candle')
EPUBNAMES={f'fig{i}': ('.jpg' if i in (21,36,37,38) else '.png') for i in range(1,39)}
BOX={ # fig: (page index, x0,y0,x1,y1) full-res, generous, excluding caption + text
1:(28,380,1700,1400,2380), 2:(32,160,1700,1320,2720), 3:(34,600,560,1150,1430),
4:(36,640,650,1200,1630), 5:(37,440,1300,1300,2260), 6:(41,150,1920,1640,2710),
7:(44,360,1560,1380,2780), 8:(47,520,1570,1320,2360), 9:(60,400,745,1380,1390),
10:(65,540,600,1380,2050), 11:(70,580,1190,1240,2220), 12:(78,160,1050,1680,2290),
13:(79,540,1575,1300,2120), 14:(84,180,1500,1660,2490), 15:(87,520,1505,1240,2120),
16:(89,180,1465,1600,2190), 17:(91,720,590,1220,1470), 18:(93,280,985,1580,1790),
19:(105,180,1855,1700,2780), 20:(110,480,590,1400,1360), 21:(114,360,1095,1500,1900),
22:(116,820,1630,1100,2460), 23:(120,740,600,1240,1140), 24:(121,760,615,1110,1210),
25:(133,760,1375,1120,2700), 26:(135,540,598,1250,1830), 27:(137,440,850,1540,1410),
28:(138,560,1530,1220,2460), 29:(146,380,592,1500,1720), 30:(154,580,612,1260,1580),
31:(155,260,640,1560,1320), 32:(172,360,568,1640,1300), 33:(174,560,505,1360,1560),
34:(175,620,1880,1260,2700), 35:(177,420,565,1420,1590), 36:(207,180,1560,1680,2395),
37:(208,600,1790,1240,2740), 38:(216,180,590,1560,1730)}
BLANK={1:(780,1660,960,1738),2:(800,1660,980,1738),5:(700,1280,1020,1375),14:(800,1460,1040,1532),20:(850,555,1040,607),27:(880,825,1060,896),36:(820,1535,1020,1602)}
files=sorted(glob.glob(SRC+'/*.jp2'))
which=[int(a) for a in sys.argv[1:]] or sorted(BOX)
for f in which:
    p,x0,y0,x1,y1=BOX[f]
    page=np.asarray(Image.open(files[p]).convert('L'),dtype=float)
    h,w=page.shape
    core=page[int(h*.1):int(h*.9),int(w*.1):int(w*.9)]
    paper=np.percentile(core,75); ink=np.percentile(core,0.5)
    if f in BLANK:
        a,b,cc,dd=BLANK[f]; page[b:dd,a:cc]=255
    c=page[y0:y1,x0:x1]
    # trim: dark mask, drop small specks
    mask=c<(paper-0.45*(paper-ink))
    mask=ndimage.binary_dilation(mask,iterations=6)
    lab,n=ndimage.label(mask)
    sizes=ndimage.sum(mask,lab,range(1,n+1))
    keep=np.isin(lab,1+np.where(sizes>=max(400,0.002*sizes.sum()))[0])
    ys,xs=np.where(keep)
    pad=14
    ty0,ty1=max(ys.min()-pad+6,0),min(ys.max()+pad-6,c.shape[0])
    tx0,tx1=max(xs.min()-pad+6,0),min(xs.max()+pad-6,c.shape[1])
    c=c[ty0:ty1,tx0:tx1]
    white=paper-0.12*(paper-ink); black=ink+0.05*(paper-ink)
    v=np.clip((c-black)/(white-black),0,1)
    v=v**1.15
    out=Image.fromarray((v*255+0.5).astype(np.uint8),'L')
    name=f'fig{f}'+EPUBNAMES[f'fig{f}']
    kw=dict(quality=95,dpi=(500,500)) if name.endswith('.jpg') else dict(dpi=(500,500),optimize=True)
    out.save(f'{OUT}/{name}',**kw)
    touch=[ty0==0,tx0==0,ty1==y1-y0,tx1==x1-x0]
    print(name,out.size,'paper',int(paper),'ink',int(ink),'edge-touch(T,L,B,R)',touch)
