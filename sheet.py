from PIL import Image, ImageDraw, ImageFont
import sys
names=["front","rear","left","right"]; ims=[Image.open(f"{n}.png").convert("RGB") for n in names]
w,h=ims[0].size; S=Image.new("RGB",(w*2,h*2+0),"white"); d=ImageDraw.Draw(S)
try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(20,w//22))
except: f=ImageFont.load_default()
for i,(n,im) in enumerate(zip(names,ims)):
    x,y=(i%2)*w,(i//2)*h; S.paste(im,(x,y)); d.text((x+w//30,y+h//30),n.upper(),fill="black",font=f)
    d.rectangle([x,y,x+w-1,y+h-1],outline=(180,180,180),width=2)
S.save("four_views.png")
