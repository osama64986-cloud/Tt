import sys, json, glob, copy
sys.path.insert(0,'/home/user/Tt/tools')
import render as R
from PIL import Image, ImageOps, ImageDraw
RP='/home/user/Tt/AnimePowers/RP'
A={}
for f in glob.glob(RP+'/animations/*.json'): A.update(json.load(open(f))['animations'])
m=R.Model(f"{RP}/models/entity/sh_archer.geo.json", f"{RP}/textures/entity/sh_archer.png")
ORIG={k:copy.deepcopy(v.get("cubes",[])) for k,v in m.bones.items()}
N={k:"animation.sh_archer."+k for k in ("idle","walk","rest","aim","draw","release")}; N["move"]="animation.sh_archer.move"
def frame(state, t, yaw, size=330, speed=0.0):
    hid=[]
    if state in ("rest","aim","release"): hid=["arrow","hand_arrow"]
    if state=="draw":
        if not (0.31<=t<=0.72): hid.append("hand_arrow")
        if t<0.73: hid.append("arrow")
    for k in m.bones: m.bones[k]["cubes"]=copy.deepcopy(ORIG[k])
    for b in hid: m.bones[b]["cubes"]=[]
    an=["idle"]+(["walk","move"] if speed else [])+[state]
    env={"q":{"modified_distance_moved":t*4,"modified_move_speed":speed,"life_time":t,"anim_time":t,"property":lambda *a:0}}
    pose=R.pose_from_anims([A[N[k]] for k in an], t, env)
    im=ImageOps.mirror(R.render(m,pose,yaw=yaw,pitch=8,size=size))
    ImageDraw.Draw(im).text((6,6),f"{state} t={t} yaw={yaw}",fill=(255,255,255))
    return im
rows=[[("rest",0.3,y,1.0) for y in (0,90,180,270)],
      [("draw",0.38,y,0) for y in (0,90,180,270)],
      [("aim",0.0,y,0) for y in (0,90,180,270)],
      [("draw",0.3,y,0) for y in (0,90,180,270)],
      [("draw",0.5,y,0) for y in (0,90,180,270)],
      [("draw",0.65,y,0) for y in (0,90,180,270)],
      [("draw",0.72,y,0) for y in (0,90,180,270)],
      [("draw",0.8,y,0) for y in (0,90,180,270)],
      [("draw",1.6,y,0) for y in (0,90,180,270)],
      [("release",0.2,y,0) for y in (0,90,180,270)]]
S=330
sheet=Image.new("RGB",(4*S,len(rows)*S),(40,42,50))
for r,row in enumerate(rows):
    for c,(st,t,yaw,sp) in enumerate(row): sheet.paste(frame(st,t,yaw,S,sp),(c*S,r*S))
sheet.save(sys.argv[1])
for i in range(0,len(rows),2):
    sheet.crop((0,i*S,4*S,min(len(rows),i+2)*S)).save(sys.argv[1].replace(".png",f"_{i//2}.png"))
