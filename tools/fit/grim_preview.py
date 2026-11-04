import sys
sys.path.insert(0, "/home/user/Tt/tools")
import render as R
from PIL import Image, ImageOps, ImageDraw
G="/home/user/Tt/AnimePowers/RP/models/entity"; T="/home/user/Tt/AnimePowers/RP/textures/entity"
name=sys.argv[2]; cell=int(sys.argv[3]) if len(sys.argv)>3 else 420
m=R.Model(f"{G}/{name}.geo.json", f"{T}/{name}.png")
views=[(20,10),(110,10),(200,10),(300,25)]
sheet=Image.new("RGB",(len(views)*cell,cell),(40,42,50))
for c,(yaw,pitch) in enumerate(views):
    im=ImageOps.mirror(R.render(m,{},yaw=yaw,pitch=pitch,size=cell))
    sheet.paste(im,(c*cell,0))
sheet.save(sys.argv[1])
