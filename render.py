from PIL import Image,ImageDraw,ImageFont
import json,math,os,hashlib
W,H,FPS,D=1080,1920,30,24
os.makedirs("frames",exist_ok=True)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
j=json.load(open("selected_job.json")); scenes=j["scenes"]
key=j["job_key"]; seed=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)
mode=seed%6
def bg(draw,t,idx):
 if mode==0:
  for y in range(0,H,80): draw.rectangle((0,y,W,y+80),fill=(10+(y//80)%2*10,18,35+(y//80)%3*8))
  for i in range(10):
   x=int((i*137+t*(35+i))%1250)-80; draw.ellipse((x,620+(i%5)*150,x+55,675+(i%5)*150),fill=(55+i*12,120,205))
 elif mode==1:
  for i in range(14):
   a=t*.35+i*.45; r=110+i*42; x=540+int(math.cos(a)*r); y=900+int(math.sin(a)*r)
   draw.rounded_rectangle((x-34,y-34,x+34,y+34),16,outline=(80+i*9,160,220),width=8)
 elif mode==2:
  for i in range(18):
   x=(i*83+seed%170)%W; h=int(180+150*math.sin(t*.8+i))
   draw.rectangle((x,1250-h,x+42,1250),fill=(35+i*7,100+i*5,155+i*4))
 elif mode==3:
  for i in range(7):
   r=110+i*95+int(25*math.sin(t+i)); draw.arc((540-r,900-r,540+r,900+r),int(t*40+i*25),int(t*40+i*25)+210,fill=(70+i*18,135+i*10,220),width=18)
 elif mode==4:
  for i in range(12):
   y=520+i*85; off=int(90*math.sin(t*.7+i*.8)); draw.line((80+off,y,1000-off,y),fill=(60+i*12,120+i*7,205),width=18)
 else:
  for i in range(8):
   a=t*.6+i*.8; x=540+int(360*math.sin(a)); y=880+int(420*math.cos(a*1.2))
   draw.polygon([(x,y-55),(x+50,y+35),(x-50,y+35)],fill=(65+i*16,130,210-i*7))
for n in range(FPS*D):
 t=n/FPS; idx=min(len(scenes)-1,int(t/(D/len(scenes)))); hook=scenes[idx]["hook"]; sub=scenes[idx]["sub"]
 im=Image.new("RGB",(W,H),(10+(seed%18),14+(seed%12),28+(seed%20))); d=ImageDraw.Draw(im); bg(d,t,idx)
 f=ImageFont.truetype(B,64); box=d.multiline_textbbox((0,0),hook,font=f,align="center",spacing=8)
 d.rounded_rectangle((70,180,1010,520),40,fill=(5,8,18))
 d.multiline_text(((W-(box[2]-box[0]))/2,250),hook,font=f,fill="white",align="center",spacing=8)
 f2=ImageFont.truetype(R,38); box=d.textbbox((0,0),sub,font=f2); d.text(((W-(box[2]-box[0]))/2,1390),sub,font=f2,fill=(230,238,255))
 d.rounded_rectangle((90,1570,990,1594),12,fill=(45,55,75)); d.rounded_rectangle((90,1570,90+int(900*t/D),1594),12,fill=(240,220,100))
 im.save(f"frames/{n:05d}.png")
open("visual_signature.txt","w").write(f"{key}:mode-{mode}")
