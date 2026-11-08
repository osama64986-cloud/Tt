import json, math, os
from PIL import Image, ImageDraw
RP="AnimePowers/RP"; BP="AnimePowers/BP"
COLS=[(255,210,90),(185,120,255),(110,185,255),(100,255,220),(245,245,255),(255,95,80)]

def save_geo(name,bones,tw,th):
    g={"format_version":"1.12.0","minecraft:geometry":[{"description":{"identifier":f"geometry.sh_fx_{name}","texture_width":tw,"texture_height":th,
       "visible_bounds_width":40,"visible_bounds_height":8,"visible_bounds_offset":[0,1,0]},"bones":bones}]}
    json.dump(g,open(f"{RP}/models/entity/sh_fx_{name}.geo.json","w"),indent=1)

# ── دائرة رونية على الأرض: وجه علوي 32x32 ──
def circle_tex(c,path):
    im=Image.new("RGBA",(128,64),(0,0,0,0)); fc=Image.new("RGBA",(32,32),(0,0,0,0)); d=ImageDraw.Draw(fc)
    cx=cy=15.5
    for y in range(32):
        for x in range(32):
            r=math.hypot(x-cx,y-cy)
            a=0
            if r<=15.6: a=34 if r<12 else 70
            if 14<=r<=15.6: a=235
            if 11.2<=r<12.4: a=200
            ang=math.degrees(math.atan2(y-cy,x-cx))%360
            if 12.4<=r<14 and (ang%45<7 or ang%45>38): a=255
            # معيّن داخلي
            if abs(abs(x-cx)+abs(y-cy)-8)<0.8: a=230
            if abs(abs(x-cx)+abs(y-cy)-4.5)<0.7: a=170
            if r<1.6: a=255
            if a: fc.putpixel((x,y),(*c,a))
    im.paste(fc,(32,0)); im.paste(fc,(64,0)); im.save(path)
# ── بوابة عمودية: حلقة ثمانية ──
def solid_tex(c,path,size=(16,16),frame=True):
    im=Image.new("RGBA",size,(0,0,0,0)); d=ImageDraw.Draw(im)
    for y in range(size[1]):
        for x in range(size[0]):
            t=y/max(1,size[1]-1)
            im.putpixel((x,y),tuple(int(v*(0.8+0.4*(1-t))) if i<3 else 235 for i,v in enumerate((*c,235))) if False else (min(255,int(c[0]*(0.75+0.45*(1-t)))),min(255,int(c[1]*(0.75+0.45*(1-t)))),min(255,int(c[2]*(0.75+0.45*(1-t)))),235))
    im.save(path)
def plate_tex(c,path):
    im=Image.new("RGBA",(32,16),(0,0,0,0))
    for y in range(16):
        for x in range(32):
            e=min(x%16,15-(x%16),y,15-y)
            col=(min(255,c[0]+30),min(255,c[1]+30),min(255,c[2]+30),255) if e<=1 else (int(c[0]*0.35),int(c[1]*0.35),int(c[2]*0.35),215)
            cxy=abs((x%16)-7.5)+abs(y-7.5)
            if abs(cxy-4)<1: col=(*c,255)
            im.putpixel((x,y),col)
    im.save(path)
os.makedirs(RP+"/textures/entity",exist_ok=True)
for i,c in enumerate(COLS):
    circle_tex(c,f"{RP}/textures/entity/sh_fx_circle_{i}.png")
    solid_tex(c,f"{RP}/textures/entity/sh_fx_portal_{i}.png")
    plate_tex(c,f"{RP}/textures/entity/sh_fx_plate_{i}.png")
# هندسة
save_geo("circle",[{"name":"root","pivot":[0,0,0]},{"name":"disc","parent":"root","pivot":[0,0,0],"cubes":[{"origin":[-16,0.2,-16],"size":[32,0.5,32],"uv":[0,0]}]}],128,64)
segs=[]
R=13
for i in range(8):
    a=math.radians(i*45); cx,cy=R*math.cos(a),R*math.sin(a)+16
    segs.append({"origin":[cx-5.6,cy-1,-1],"size":[11.2,2,2],"uv":[0,0],"rotation":[0,0,i*45+90],"pivot":[cx,cy,0]})
segs.append({"origin":[-1.5,14.5,-0.5],"size":[3,3,1],"uv":[0,0]})
save_geo("portal",[{"name":"root","pivot":[0,0,0]},{"name":"ring","parent":"root","pivot":[0,16,0],"cubes":segs}],16,16)
save_geo("plate",[{"name":"root","pivot":[0,0,0]},{"name":"plate","parent":"root","pivot":[0,6,0],"cubes":[{"origin":[-4,2,-0.5],"size":[8,8,1],"uv":[0,0],"rotation":[0,0,45],"pivot":[0,6,0]}]}],32,16)
anims={
 "animation.sh_fx.circle":{"loop":True,"bones":{"root":{"scale":["query.property('sh:r')","1","query.property('sh:r')"]},
        "disc":{"rotation":[0,"query.life_time*40",0]}}},
 "animation.sh_fx.portal":{"loop":True,"bones":{"root":{"scale":"query.property('sh:r')*math.min(1,query.life_time*5)"},
        "ring":{"rotation":[0,0,"query.life_time*240"]}}},
 "animation.sh_fx.plate":{"loop":True,"bones":{"root":{"scale":"query.property('sh:r')*math.min(1,query.life_time*4)","position":[0,"math.sin(query.life_time*180)*0.8",0]},
        "plate":{"rotation":[0,"query.life_time*150",0]}}},
}
json.dump({"format_version":"1.8.0","animations":anims},open(RP+"/animations/sh_fx.animation.json","w"),indent=1)
rc={"format_version":"1.8.0","render_controllers":{}}
for k in ("circle","portal","plate"):
    rc["render_controllers"][f"controller.render.sh_fx_{k}"]={"arrays":{"textures":{"Array.t":[f"Texture.c{i}" for i in range(6)]}},
        "geometry":"Geometry.default","materials":[{"*":"Material.default"}],"textures":["Array.t[query.property('sh:c')]"]}
json.dump(rc,open(RP+"/render_controllers/sh_fx.render_controllers.json","w"),indent=1)
for k in ("circle","portal","plate"):
    ce={"format_version":"1.10.0","minecraft:client_entity":{"description":{"identifier":f"sh:fx_{k}","materials":{"default":"entity_alpha"},
        "textures":{f"c{i}":f"textures/entity/sh_fx_{k}_{i}" for i in range(6)},"geometry":{"default":f"geometry.sh_fx_{k}"},
        "animations":{"fx":f"animation.sh_fx.{k}"},"scripts":{"animate":["fx"]},"render_controllers":[f"controller.render.sh_fx_{k}"]}}}
    json.dump(ce,open(f"{RP}/entity/sh_fx_{k}.entity.json","w"),indent=1)
    be={"format_version":"1.21.50","minecraft:entity":{"description":{"identifier":f"sh:fx_{k}","is_spawnable":False,"is_summonable":True,"is_experimental":False,
        "properties":{"sh:c":{"type":"int","range":[0,5],"default":0,"client_sync":True},"sh:r":{"type":"float","range":[0,40],"default":1,"client_sync":True}}},
        "component_groups":{"sh:gone":{"minecraft:instant_despawn":{}}},
        "components":{"minecraft:type_family":{"family":["sh_fx","inanimate"]},"minecraft:collision_box":{"width":0.1,"height":0.1},
            "minecraft:physics":{"has_gravity":False,"has_collision":False},"minecraft:pushable":{"is_pushable":False,"is_pushable_by_piston":False},
            "minecraft:timer":{"time":30,"looping":False,"time_down_event":{"event":"sh:die"}},
            "minecraft:damage_sensor":{"triggers":[{"cause":"all","deals_damage":"no"}]}},
        "events":{"sh:die":{"add":{"component_groups":["sh:gone"]}}}}}
    json.dump(be,open(f"{BP}/entities/sh_fx_{k}.json","w"),indent=1)
print("ok")
