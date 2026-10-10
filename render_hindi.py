"""Draw recognizable, expressive 2D Hindi family-comedy characters in 9:16."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont

job=json.load(open("selected_job.json",encoding="utf-8"))
scenes=job["scenes"]
W,H,FPS=1080,1920,30
timeline=json.load(open("speech_timeline.json",encoding="utf-8"))
duration=timeline[-1]["end"]
if not (18<=duration<=59): raise SystemExit(f"Speech duration {duration:.1f}s outside Shorts QA limits")
font_path="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
if not os.path.isfile(font_path):
    raise SystemExit("Noto Sans Devanagari font required")
font=ImageFont.truetype(font_path,65)
small=ImageFont.truetype(font_path,43)
headline_font=ImageFont.truetype(font_path,55)
headline=job.get("title","").split("|")[0].strip()
if not headline: raise SystemExit("Missing story-specific headline")
os.makedirs("frames",exist_ok=True)

def wrapped(d,text,max_width):
    lines=[]; line=""
    for word in text.split():
        candidate=(line+" "+word).strip()
        if line and d.textbbox((0,0),candidate,font=font)[2]>max_width:
            lines.append(line); line=word
        else: line=candidate
    if line: lines.append(line)
    return lines

def person(d,who,cx,cy,active,t,mouth_energy=0):
    child=who=="child"
    scale=.86 if child else 1.0
    skin=(240,181,134) if who=="father" else (250,199,156)
    shirt={"child":(250,198,55),"mother":(50,173,156),"father":(232,119,76)}[who]
    hair=(46,34,42) if who!="father" else (57,44,35)
    def xy(x,y): return (int(cx+x*scale),int(cy+y*scale))
    def rect(x1,y1,x2,y2,**kw):d.rounded_rectangle((*xy(x1,y1),*xy(x2,y2)),radius=int(32*scale),**kw)
    def oval(x1,y1,x2,y2,**kw):d.ellipse((*xy(x1,y1),*xy(x2,y2)),**kw)
    bob=int(8*math.sin(t*3+cx/200)) if active else 0
    cy+=bob
    # Shoulders, neck and visible ears
    rect(-125,105,125,445,fill=shirt)
    rect(-32,73,32,146,fill=skin)
    oval(-120,-140,-82,-55,fill=skin)
    oval(82,-140,120,-55,fill=skin)
    if who=="mother":
        oval(-110,-210,110,145,fill=hair)  # long hairstyle
    oval(-99,-232,99,106,fill=skin,outline=(115,69,57),width=4)
    # Hairstyle distinct to each family member
    if who=="father":
        d.pieslice((*xy(-100,-241),*xy(100,-122)),180,360,fill=hair)
        oval(-96,-204,-62,-110,fill=hair)
    elif who=="mother":
        d.pieslice((*xy(-105,-247),*xy(105,-106)),180,355,fill=hair)
        oval(-104,-200,-72,-82,fill=hair)
        oval(74,-200,106,-82,fill=hair)
        oval(85,-63,102,-40,fill=(247,197,56)) # earring
    else:
        d.pieslice((*xy(-102,-249),*xy(103,-119)),170,355,fill=hair)
        oval(-82,-230,-42,-160,fill=hair)
        oval(38,-240,77,-155,fill=hair)
    # Eyebrows and animated eyes
    for side in (-1,1):
        x=side*43
        lift=-12 if active and int(t*3)%3==0 else 0
        d.line([xy(x-23,-107+lift),xy(x+21,-111+lift)],fill=hair,width=9)
        oval(x-19,-96,x+19,-48,fill=(255,255,255))
        oval(x-8,-83,x+8,-55,fill=(52,58,70))
        oval(x-3,-80,x+3,-72,fill=(255,255,255))
    # Nose, cheeks and smile/talking mouth
    d.line([xy(0,-59),xy(-7,-21),xy(8,-18)],fill=(180,109,83),width=5)
    if active:
        opening=2+int(40*mouth_energy)
        oval(-32,4,32,4+opening*2,fill=(115,40,53))
        d.arc((*xy(-23,7),*xy(23,max(8,opening*2+2))),5,175,fill=(255,182,170),width=5)
    else:
        d.arc((*xy(-36,-6),*xy(36,45)),10,170,fill=(123,57,64),width=7)
    if who=="father":
        d.arc((*xy(-45,-14),*xy(0,13)),190,355,fill=hair,width=6)
        d.arc((*xy(0,-14),*xy(45,13)),190,355,fill=hair,width=6)
    if who=="mother":
        oval(-65,-1,-49,11,fill=(237,144,138))
        oval(49,-1,65,11,fill=(237,144,138))
    # Clear active-speaker highlight
    if active:
        d.rounded_rectangle((*xy(-132,-267),*xy(132,462)),radius=42,outline=(255,220,91),width=12)

names={"child":"चिंटू","mother":"माँ","father":"पापा"}
backgrounds=[(33,53,91),(72,48,98),(37,84,82),(90,54,76)]
for frame in range(math.ceil(duration*FPS)):
    t=frame/FPS
    idx=next((i for i,seg in enumerate(timeline) if seg["start"]<=t<seg["end"]),len(timeline)-1)
    scene=timeline[idx]
    speaker=scene.get("speaker","child")
    local=max(0,t-scene["start"])
    envelope=scene["mouth_energy_20ms"]
    energy=envelope[min(len(envelope)-1,int(local/0.02))] if envelope else 0
    im=Image.new("RGB",(W,H),backgrounds[idx%len(backgrounds)])
    d=ImageDraw.Draw(im)
    # Family room, window and floor
    d.rounded_rectangle((65,300,1015,1110),radius=70,fill=(246,227,199))
    d.rounded_rectangle((100,355,350,610),radius=22,fill=(151,205,229),outline=(255,255,255),width=16)
    d.line((225,355,225,610),fill=(255,255,255),width=12)
    d.rectangle((65,1040,1015,1120),fill=(174,125,97))
    d.rounded_rectangle((70,1050,1010,1195),radius=55,fill=(154,103,82))
    person(d,"child",235,770,speaker=="child",t,energy if speaker=="child" else 0)
    person(d,"mother",535,770,speaker=="mother",t,energy if speaker=="mother" else 0)
    person(d,"father",835,770,speaker=="father",t,energy if speaker=="father" else 0)
    d.rounded_rectangle((55,95,1025,242),radius=40,fill=(255,220,115))
    headline_lines=wrapped(d,headline,850)
    for hi,line in enumerate(headline_lines[:2]):
        d.text((100,112+hi*65),line,font=headline_font,fill=(35,35,58))
    d.rounded_rectangle((65,1240,1015,1705),radius=52,fill=(255,252,241))
    d.text((108,1275),names.get(speaker,"परिवार")+":",font=small,fill=(82,55,125))
    for li,line in enumerate(wrapped(d,scene.get("text",""),840)[:4]):
        d.text((108,1365+li*83),line,font=font,fill=(35,39,52))
    d.rounded_rectangle((85,1790,995,1810),radius=10,fill=(255,255,255))
    d.rounded_rectangle((85,1790,85+max(2,int(910*frame/max(1,duration*FPS))),1810),radius=10,fill=(255,204,75))
    im.save(f"frames/{frame:05d}.png")
print("HINDI_EXPRESSIVE_FACES_RENDERED",math.ceil(duration*FPS))
