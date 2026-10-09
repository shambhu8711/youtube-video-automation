"""Render dialogue-aware vertical Hindi family-comedy cards with Devanagari text."""
import json,os,math
from PIL import Image,ImageDraw,ImageFont
j=json.load(open("selected_job.json",encoding="utf-8"))
W,H,FPS=1080,1920,30
scenes=j["scenes"]
duration=float(os.environ.get("AUDIO_DURATION","24"))
duration=max(18,min(59,duration))
font_path="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
if not os.path.exists(font_path): raise SystemExit("Missing Noto Devanagari font")
font=ImageFont.truetype(font_path,67)
small=ImageFont.truetype(font_path,45)
os.makedirs("frames",exist_ok=True)
colors=[(35,40,85),(70,40,88),(26,85,83),(100,48,67)]
def wrap(draw,txt,font,max_width):
    words=txt.split(); lines=[]; line=""
    for word in words:
        candidate=(line+" "+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]>max_width and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines
for n in range(math.ceil(duration*FPS)):
    t=n/FPS; idx=min(len(scenes)-1,int(t/duration*len(scenes)))
    sc=scenes[idx]
    im=Image.new("RGB",(W,H),colors[idx%len(colors)])
    d=ImageDraw.Draw(im)
    # Original graphic scene with stable family silhouettes and dialogue cards.
    d.rounded_rectangle((55,80,1025,240),radius=48,fill=(255,220,115))
    d.text((95,116),"हिंदी फैमिली कॉमेडी",font=small,fill=(30,30,55))
    for k,(cx,shirt) in enumerate([(245,(255,205,60)),(540,(55,175,165)),(835,(235,130,90))]):
        cy=800+int(12*math.sin(t*2+k))
        d.ellipse((cx-88,cy-290,cx+88,cy-114),fill=(245,193,151))
        d.rounded_rectangle((cx-122,cy-115,cx+122,cy+225),radius=60,fill=shirt)
        d.ellipse((cx-38,cy-220,cx-24,cy-207),fill=(40,40,40))
        d.ellipse((cx+24,cy-220,cx+38,cy-207),fill=(40,40,40))
    d.rounded_rectangle((60,1170,1020,1670),radius=55,fill=(255,255,245))
    speaker={"mother":"माँ","father":"पापा","child":"चिंटू"}.get(sc.get("speaker"),"परिवार")
    d.text((100,1210),speaker+":",font=small,fill=(65,40,115))
    lines=wrap(d,sc["text"],font,850)
    for li,line in enumerate(lines[:4]):
        d.text((100,1300+li*84),line,font=font,fill=(35,35,45))
    d.rounded_rectangle((80,1790,1000,1810),radius=10,fill=(255,255,255))
    d.rounded_rectangle((80,1790,80+int(920*n/max(1,duration*FPS)),1810),radius=10,fill=(255,190,60))
    im.save(f"frames/{n:05d}.png")
print("HINDI_FRAMES",math.ceil(duration*FPS))
