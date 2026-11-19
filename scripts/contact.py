import sys,glob
from PIL import Image
fs=sys.argv[2:] or sorted(glob.glob("work/preview/p_*.png"))
sc=float(sys.argv[1]) if len(sys.argv)>1 else 0.42
ims=[Image.open(f) for f in fs]; w,h=int(1080*sc),int(1920*sc)
sheet=Image.new("RGB",(w*len(ims),h))
for i,im in enumerate(ims): sheet.paste(im.resize((w,h)),(w*i,0))
sheet.save("work/preview/sheet.png"); print(len(ims),sheet.size)
