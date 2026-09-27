from PIL import Image,ImageDraw,ImageFont
import json,math,os
W,H,FPS,D=1080,1920,30,24
os.makedirs("frames",exist_ok=True)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
j=json.load(open("selected_job.json")); scenes=j["scenes"]
for n in range(FPS*D):
 t=n/FPS; idx=min(len(scenes)-1,int(t/(D/len(scenes)))); hook=scenes[idx]["hook"]; sub=scenes[idx]["sub"]
 im=Image.new("RGB",(W,H),(12,16,32)); d=ImageDraw.Draw(im)
 cx=int(540+300*math.sin(t*.9+idx)); cy=int(850+240*math.cos(t*.7+idx))
 for r in range(500,30,-30):
  shade=max(20,100-r//7); d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(shade,min(255,shade+35),min(255,shade+70)),width=8)
 for i in range(9):
  x=int((80+i*135+t*(40+i*2))%1200)-60; y=680+(i%4)*135
  d.ellipse((x-30,y-30,x+30,y+30),fill=(80+i*16,145+idx*8,215))
 f=ImageFont.truetype(B,64); box=d.multiline_textbbox((0,0),hook,font=f,align="center",spacing=8)
 d.multiline_text(((W-(box[2]-box[0]))/2,250),hook,font=f,fill="white",align="center",spacing=8)
 f2=ImageFont.truetype(R,38); box=d.textbbox((0,0),sub,font=f2); d.text(((W-(box[2]-box[0]))/2,1390),sub,font=f2,fill=(230,238,255))
 d.rounded_rectangle((90,1570,90+int(900*t/D),1594),12,fill=(255,210,85))
 im.save(f"frames/{n:05d}.png")
