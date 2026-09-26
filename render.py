from PIL import Image,ImageDraw,ImageFont
import math,os
W,H,FPS,D=1080,1920,30,20
os.makedirs("frames",exist_ok=True)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for n in range(FPS*D):
 t=n/FPS; im=Image.new("RGB",(W,H),(9,14,31)); d=ImageDraw.Draw(im)
 for i in range(55):
  x=(i*193+int(t*(22+i%4*9)))%W; y=(i*307)%H; r=2+i%3
  d.ellipse((x-r,y-r,x+r,y+r),fill=(130,175,240))
 cx,cy=540,850; a=t*1.25
 d.ellipse((180,490,900,1210),outline=(80,125,205),width=9)
 d.ellipse((cx-85,cy-85,cx+85,cy+85),fill=(255,190,60))
 x=cx+360*math.cos(a); y=cy+360*math.sin(a); d.ellipse((x-58,y-58,x+58,y+58),fill=(230,145,75))
 hook="A YEAR SHORTER\nTHAN A ROTATION?" if t<5 else ("243 DAYS TO ROTATE" if t<10 else ("225 DAYS TO ORBIT" if t<15 else "VENUS IS WEIRD."))
 f=ImageFont.truetype(B,70); box=d.multiline_textbbox((0,0),hook,font=f,align="center",spacing=8)
 d.multiline_text(((W-(box[2]-box[0]))/2,260),hook,font=f,fill="white",align="center",spacing=8)
 sub="Watch the planet move — then hear why." if t<5 else ("Its rotation is incredibly slow." if t<10 else ("Its orbit finishes first." if t<15 else "Follow for more surprising science."))
 f2=ImageFont.truetype(R,42); box=d.textbbox((0,0),sub,font=f2); d.text(((W-(box[2]-box[0]))/2,1390),sub,font=f2,fill=(230,238,255))
 d.rounded_rectangle((90,1570,90+int(900*t/D),1594),12,fill=(255,210,85))
 im.save(f"frames/{n:05d}.png")
