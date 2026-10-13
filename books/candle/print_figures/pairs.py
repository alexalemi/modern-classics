import sys,os
from PIL import Image, ImageDraw
old='/home/alemi/projects/modern-classics/site/images/candle/'
new='/home/alemi/projects/modern-classics/build/print_images/candle/'
figs=[int(a) for a in sys.argv[2:]]
W,H=230,260; cols=4
rows=(len(figs)+cols-1)//cols
sheet=Image.new('L',(cols*2*W+cols*10,rows*(H+16)),200); d=ImageDraw.Draw(sheet)
for k,i in enumerate(figs):
    on=[f for f in os.listdir(old) if os.path.splitext(f)[0]==f'fig{i}'][0]
    a=Image.open(old+on).convert('L'); b=Image.open(new+on).convert('L')
    x=(k%cols)*(2*W+10); y=(k//cols)*(H+16)
    for j,im in enumerate((a,b)):
        im=im.copy(); im.thumbnail((W-6,H)); t=Image.new('L',(W-4,H),255); t.paste(im,(0,0))
        sheet.paste(t,(x+j*W,y+16))
    d.text((x+2,y+2),f'fig{i} {b.size}',fill=0)
sheet.save(sys.argv[1])
