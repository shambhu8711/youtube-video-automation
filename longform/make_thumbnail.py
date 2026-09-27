import argparse,json,textwrap
from PIL import Image,ImageDraw,ImageFont,ImageFilter
p=argparse.ArgumentParser();p.add_argument("--job",required=True);p.add_argument("--out",default="thumbnail.jpg");a=p.parse_args()
j=json.load(open(a.job,encoding="utf-8")); W,H=1280,720
im=Image.new("RGB",(W,H),(10,18,38)); d=ImageDraw.Draw(im)
# High-contrast original graphic background.
for i in range(18):
 x=(i*173)%W; y=(i*97)%H; r=35+(i*13)%90
 d.ellipse((x-r,y-r,x+r,y+r),outline=(55+(i*17)%160,95+(i*23)%140,180+(i*11)%70),width=6)
d.rounded_rectangle((55,55,1225,665),radius=42,fill=(8,13,28),outline=(235,240,255),width=4)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
small=ImageFont.truetype(font,34); big=ImageFont.truetype(font,68)
d.text((95,95),"DAILY GROWTH VIDEO",font=small,fill=(255,210,70))
title=j["title"].replace("—","-")
# Fit title to 3-4 lines.
words=title.split(); lines=[]; cur=""
for w in words:
 test=(cur+" "+w).strip()
 if d.textbbox((0,0),test,font=big)[2] > 1010 and cur:
  lines.append(cur); cur=w
 else: cur=test
if cur: lines.append(cur)
lines=lines[:4]
y=205
for line in lines:
 d.text((95,y),line,font=big,fill="white",stroke_width=2,stroke_fill=(0,0,0)); y+=88
d.rounded_rectangle((95,570,545,630),radius=22,fill=(255,210,70))
d.text((125,580),"WATCH THE EXPLANATION",font=ImageFont.truetype(font,25),fill=(10,18,38))
im.save(a.out,"JPEG",quality=92,optimize=True)
print("THUMBNAIL_READY",a.out)
