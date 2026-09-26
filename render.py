from PIL import Image,ImageDraw,ImageFont
import math,os
W,H,FPS,D=1080,1920,30,24
os.makedirs("frames",exist_ok=True)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
scenes=[("YOUR BRAIN CAN\nMISS THE OBVIOUS","Attention has a hidden limit."),
("FOCUS IS A\nSPOTLIGHT","You process far less than you see."),
("COUNT THE\nPASSES","A demanding task narrows attention."),
("THEN SOMETHING\nUNEXPECTED APPEARS","It can happen right in front of you."),
("THIS IS\nINATTENTIONAL BLINDNESS","Visible does not always mean noticed."),
("ATTENTION ≠\nA CAMERA","Your brain selects what gets priority."),
("WHAT DID YOU\nMISS TODAY?","Follow for more psychology facts.")]
for n in range(FPS*D):
 t=n/FPS; idx=min(len(scenes)-1,int(t/(D/len(scenes)))); hook,sub=scenes[idx]
 im=Image.new("RGB",(W,H),(12,16,32)); d=ImageDraw.Draw(im)
 # animated spotlight and moving objects
 sx=int(540+310*math.sin(t*1.2)); sy=int(820+260*math.cos(t*.8))
 for r in range(500,20,-25):
  shade=max(18,90-r//7); d.ellipse((sx-r,sy-r,sx+r,sy+r),outline=(shade,shade+20,min(255,shade+55)),width=8)
 for i in range(8):
  x=int((120+i*145+t*(45+i*3))%1200)-60; y=700+(i%3)*150
  d.ellipse((x-35,y-35,x+35,y+35),fill=(90+i*15,155,220))
 f=ImageFont.truetype(B,68); box=d.multiline_textbbox((0,0),hook,font=f,align="center",spacing=8)
 d.multiline_text(((W-(box[2]-box[0]))/2,250),hook,font=f,fill="white",align="center",spacing=8)
 f2=ImageFont.truetype(R,40); box=d.textbbox((0,0),sub,font=f2); d.text(((W-(box[2]-box[0]))/2,1390),sub,font=f2,fill=(230,238,255))
 d.rounded_rectangle((90,1570,90+int(900*t/D),1594),12,fill=(255,210,85))
 im.save(f"frames/{n:05d}.png")
