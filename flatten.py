from PIL import Image
import sys
for n in sys.argv[1:]:
    im=Image.open(n).convert("RGBA"); bg=Image.new("RGBA",im.size,(255,255,255,255))
    Image.alpha_composite(bg,im).convert("RGB").save(n)
