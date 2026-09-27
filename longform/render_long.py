import json, math, os
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,D=1920,1080,30,360
j=json.load(open("longform_job.json"))
os.makedirs("long_frames",exist_ok=True)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
reg="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for n in range(FPS*D):
    t=n/FPS
    idx=min(len(j["chapters"])-1,int(t/(D/len(j["chapters"]))))
    ch=j["chapters"][idx]
    im=Image.new("RGB",(W,H),(12+(idx*17)%35,18+(idx*23)%35,30+(idx*11)%45))
    d=ImageDraw.Draw(im)
    for k in range(14):
        x=int((k*170+t*35*(1+idx%3))%(W+300))-150
        y=100+(k*83)%850
        r=22+(k*7)%55
        d.ellipse((x-r,y-r,x+r,y+r),outline=(80,100,130),width=4)
    title=ch["title"]
    body=ch["onscreen"]
    d.text((120,180),title,font=ImageFont.truetype(font,72),fill="white")
    d.multiline_text((120,330),body,font=ImageFont.truetype(reg,44),fill=(225,230,240),spacing=18)
    d.text((120,950),j["series"],font=ImageFont.truetype(reg,28),fill=(180,190,205))
    im.save(f"long_frames/{n:05d}.jpg",quality=82)
