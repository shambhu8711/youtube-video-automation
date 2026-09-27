from PIL import Image, ImageDraw, ImageFont
import json, math, os, hashlib, textwrap

W,H,FPS,D=1080,1920,30,24
os.makedirs("frames",exist_ok=True)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
j=json.load(open("selected_job.json",encoding="utf-8")); scenes=j["scenes"]
key=j["job_key"]; seed=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)
F1=ImageFont.truetype(B,70); F2=ImageFont.truetype(B,48); F3=ImageFont.truetype(R,34)

def palette(i):
    ps=[((15,31,55),(32,82,149),(255,190,64)),((37,20,55),(118,55,160),(80,220,190)),
        ((12,52,48),(23,125,110),(255,205,80)),((54,25,24),(164,67,54),(255,190,95)),
        ((19,31,28),(60,125,78),(240,220,120)),((24,28,62),(62,76,170),(255,115,145))]
    return ps[(seed+i)%len(ps)]

def words(s,n=18):
    return "\n".join(textwrap.wrap(s.upper(),n))

def icon(d,visual,cx,cy,t,accent):
    v=visual.lower()
    pulse=1+.06*math.sin(t*3)
    if any(x in v for x in ["tower","landmark","eiffel"]):
        d.polygon([(cx,cy-360),(cx-210,cy+330),(cx+210,cy+330)],outline=accent,width=24)
        for y,w in [(cy-150,90),(cy+40,140),(cy+230,190)]: d.line((cx-w,y,cx+w,y),fill=accent,width=18)
    elif any(x in v for x in ["banana","food","berry"]):
        d.arc((cx-270,cy-230,cx+270,cy+230),15,155,fill=accent,width=80)
        for i in range(8): d.ellipse((cx-330+i*90,cy+220+int(18*math.sin(t*2+i)),cx-285+i*90,cy+265+int(18*math.sin(t*2+i))),fill=accent)
    elif any(x in v for x in ["shark","ocean","fish"]):
        x=cx+int(90*math.sin(t*1.5)); d.ellipse((x-260,cy-120,x+230,cy+120),fill=accent)
        d.polygon([(x+210,cy),(x+390,cy-150),(x+370,cy+150)],fill=accent); d.polygon([(x-20,cy-90),(x+70,cy-250),(x+110,cy-70)],fill=accent)
    elif any(x in v for x in ["brain","memory","sleep"]):
        for k in range(9):
            a=k*.7+t*.15; x=cx+int(math.cos(a)*150); y=cy+int(math.sin(a*1.4)*150)
            d.ellipse((x-100,y-80,x+100,y+80),outline=accent,width=22)
    elif any(x in v for x in ["wombat","animal"]):
        d.ellipse((cx-230,cy-180,cx+230,cy+230),fill=accent)
        d.ellipse((cx-170,cy-270,cx-40,cy-110),fill=accent); d.ellipse((cx+40,cy-270,cx+170,cy-110),fill=accent)
        d.ellipse((cx-95,cy-30,cx+95,cy+100),fill=(30,30,35)); d.ellipse((cx-100,cy-100,cx-60,cy-60),fill="white"); d.ellipse((cx+60,cy-100,cx+100,cy-60),fill="white")
    elif any(x in v for x in ["ai","chat","words","verification"]):
        for k in range(3):
            y=cy-190+k*150; off=int(35*math.sin(t*2+k))
            d.rounded_rectangle((cx-300+off,y,cx+300+off,y+105),30,outline=accent,width=18)
        d.ellipse((cx+190,cy-330,cx+330,cy-190),fill=accent); d.text((cx+235,cy-315),"?",font=F2,fill=(20,20,30))
    elif any(x in v for x in ["retail","membership","costco","store"]):
        d.rounded_rectangle((cx-300,cy-220,cx+300,cy+250),35,outline=accent,width=25)
        for k in range(4): d.rectangle((cx-230+k*125,cy-100,cx-150+k*125,cy+180),fill=accent)
        d.arc((cx-190,cy-360,cx+190,cy-80),190,350,fill=accent,width=30)
    else:
        for k in range(6):
            a=t*.6+k*math.pi/3; x=cx+int(math.cos(a)*260); y=cy+int(math.sin(a)*260)
            d.rounded_rectangle((x-55,y-55,x+55,y+55),20,fill=accent)

for n in range(FPS*D):
    t=n/FPS; idx=min(len(scenes)-1,int(t/(D/len(scenes))))
    sc=scenes[idx]; hook=sc.get("hook") or sc.get("text") or ""; sub=sc.get("sub") or sc.get("visual") or ""
    base,mid,accent=palette(idx)
    im=Image.new("RGB",(W,H),base); d=ImageDraw.Draw(im)
    # scene-specific animated gradient bands and particles
    for k in range(9):
        y=int((k*240+t*(30+idx*7))%(H+300))-150
        d.rounded_rectangle((-120,y,W+120,y+120),60,fill=mid)
    for k in range(12):
        a=t*.45+k*.7+idx; x=540+int(math.sin(a)*500); y=850+int(math.cos(a*1.27)*620)
        d.ellipse((x-10,y-10,x+10,y+10),fill=accent)
    icon(d,sub,540,850,t,accent)
    # headline card moves slightly between scenes
    top=120+int(18*math.sin(t*1.7+idx))
    d.rounded_rectangle((55,top,1025,top+350),45,fill=(8,10,18))
    txt=words(hook,20); bb=d.multiline_textbbox((0,0),txt,font=F1,align="center",spacing=10)
    d.multiline_text(((W-(bb[2]-bb[0]))/2,top+65),txt,font=F1,fill="white",align="center",spacing=10)
    # scene counter replaces repetitive bottom progress-only look
    d.rounded_rectangle((70,1660,1010,1790),35,fill=(8,10,18))
    label=f"SCENE {idx+1}/{len(scenes)}  •  "+words(sub,42).replace("\n"," ")
    d.text((105,1700),label[:48],font=F3,fill=(235,240,250))
    for q in range(len(scenes)):
        x=105+q*110; d.rounded_rectangle((x,1815,x+80,1835),10,fill=accent if q==idx else (85,90,105))
    im.save(f"frames/{n:05d}.png")
open("visual_signature.txt","w").write(f"{key}:topic-scenes-v2:{seed%997}")
