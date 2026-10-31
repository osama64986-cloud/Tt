import json, copy
RP="AnimePowers/RP"; BP="AnimePowers/BP"
D="query.modified_distance_moved*"
def walkrot(f,a): return f"math.cos({D}{f}) * {a} * query.modified_move_speed"
anims={}
# ── الذئب ──
h="animation.sh_hound."
anims[h+"idle"]={"loop":True,"animation_length":3.0,"bones":{
 "tail":{"rotation":[0,"math.sin(query.anim_time*360)*16",0]},"tail2":{"rotation":[0,"math.sin(query.anim_time*360-50)*24",0]},"tail3":{"rotation":[0,"math.sin(query.anim_time*360-100)*32","math.sin(query.anim_time*360-100)*8"]},
 "head":{"rotation":["math.sin(query.anim_time*120)*3","math.sin(query.anim_time*60)*6",0]},
 "body":{"position":[0,"math.sin(query.anim_time*240)*0.15",0]}}}
anims[h+"walk"]={"loop":True,"bones":{
 "leg_fl":{"rotation":[walkrot(42,60),0,0]},"leg_br":{"rotation":[walkrot(42,60),0,0]},
 "leg_fr":{"rotation":[walkrot(42,-60),0,0]},"leg_bl":{"rotation":[walkrot(42,-60),0,0]},
 "body":{"rotation":["math.cos("+D+"84)*3",0,0],"position":[0,"math.abs(math.sin("+D+"42))*0.5*query.modified_move_speed",0]},
 "tail":{"rotation":[0,"math.sin("+D+"42)*18",0]},"tail2":{"rotation":[0,"math.sin("+D+"42-50)*26",0]},"tail3":{"rotation":[0,"math.sin("+D+"42-100)*34",0]}}}
anims[h+"windup"]={"loop":False,"animation_length":0.6,"bones":{
 "body":{"rotation":{"0.0":[0,0,0],"0.6":[-16,0,0]},"position":{"0.0":[0,0,0],"0.6":[0,0.8,0.5]}},
 "head":{"rotation":{"0.0":[0,0,0],"0.6":[-62,0,0]},"position":{"0.0":[0,0,0],"0.6":[0,1.0,1.5]}},
 "leg_fl":{"rotation":[-12,0,0]},"leg_fr":{"rotation":[-12,0,0]},
 "tail":{"rotation":[-20,"math.sin(query.life_time*600)*14",0]},"tail2":{"rotation":[0,"math.sin(query.life_time*600-60)*18",0]}}}
anims[h+"pounce"]={"loop":True,"bones":{
 "body":{"rotation":[-16,0,0],"position":[0,0.8,0.5]},
 "head":{"rotation":["-62 + math.sin(query.life_time*900)*4",0,0],"position":[0,1.0,1.5]},
 "leg_fl":{"rotation":[-12,0,0]},"leg_fr":{"rotation":[-12,0,0]},
 "tail":{"rotation":[-24,"math.sin(query.life_time*700)*16",0]},"tail2":{"rotation":[0,"math.sin(query.life_time*700-60)*20",0]},"tail3":{"rotation":[0,"math.sin(query.life_time*700-120)*28",0]}}}
anims[h+"bite"]={"loop":True,"animation_length":0.6,"bones":{
 "head":{"rotation":{"0.0":[0,0,0],"0.12":[-22,0,0],"0.22":[16,0,0],"0.32":[0,0,0],"0.42":[-22,0,0],"0.5":[16,0,0],"0.6":[0,0,0]},
         "position":{"0.0":[0,0,0],"0.12":[0,0,-2.5],"0.22":[0,0,0.5],"0.32":[0,0,0],"0.42":[0,0,-2.5],"0.5":[0,0,0.5],"0.6":[0,0,0]}},
 "body":{"rotation":{"0.0":[0,0,0],"0.12":[10,0,0],"0.32":[0,0,0],"0.42":[10,0,0],"0.6":[0,0,0]}}}}
# ── العقرب ──
s="animation.sh_scorpion."
anims[s+"idle"]={"loop":True,"animation_length":3.0,"bones":{
 "tail1":{"rotation":["math.sin(query.anim_time*120)*4",0,0]},"tail2":{"rotation":["math.sin(query.anim_time*120+40)*6",0,0]},
 "tail3":{"rotation":["math.sin(query.anim_time*120+80)*8",0,0]},"tail4":{"rotation":["math.sin(query.anim_time*120+110)*8",0,0]},"sting":{"rotation":["math.sin(query.anim_time*120+140)*8",0,0]},
 "claw_l":{"rotation":[0,"math.sin(query.anim_time*240)*6",0]},"claw_r":{"rotation":[0,"math.sin(query.anim_time*240+90)*-6",0]},
 "fing_l":{"rotation":[0,"math.sin(query.anim_time*360)*8",0]},"fing_r":{"rotation":[0,"math.sin(query.anim_time*360)*-8",0]}}}
anims[s+"walk"]={"loop":True,"bones":{
 "legs_l":{"rotation":[0,walkrot(60,18),"math.abs(math.cos("+D+"60))*6"]},
 "legs_r":{"rotation":[0,walkrot(60,-18),"math.abs(math.sin("+D+"60))*-6"]},
 "body":{"rotation":[0,"math.sin("+D+"60)*3",0]}}}
anims[s+"windup"]={"loop":True,"bones":{
 "tail1":{"rotation":[-20,0,0]},"tail2":{"rotation":[-26,0,0]},"tail3":{"rotation":[-30,0,0]},"tail4":{"rotation":[-30,0,0]},"sting":{"rotation":[-30,"math.sin(query.life_time*1200)*8",0]},
 "body":{"rotation":[-6,0,0],"position":[0,-0.4,0]},
 "claw_l":{"rotation":[0,-25,0]},"claw_r":{"rotation":[0,25,0]}}}
anims[s+"strike"]={"loop":True,"bones":{
 "tail1":{"rotation":[30,0,0]},"tail2":{"rotation":[34,0,0]},"tail3":{"rotation":[34,0,0]},"tail4":{"rotation":[30,0,0]},"sting":{"rotation":[26,0,0]},
 "body":{"rotation":[8,0,0]}}}
anims[s+"pinch"]={"loop":True,"animation_length":0.7,"bones":{
 "claw_l":{"rotation":{"0.0":[0,0,0],"0.15":[0,-30,0],"0.3":[0,15,0],"0.7":[0,0,0]}},
 "claw_r":{"rotation":{"0.0":[0,0,0],"0.15":[0,30,0],"0.3":[0,-15,0],"0.7":[0,0,0]}},
 "fing_l":{"rotation":{"0.0":[0,0,0],"0.15":[0,40,0],"0.28":[0,-6,0],"0.4":[0,40,0],"0.55":[0,-6,0],"0.7":[0,0,0]}},
 "fing_r":{"rotation":{"0.0":[0,0,0],"0.15":[0,-40,0],"0.28":[0,6,0],"0.4":[0,-40,0],"0.55":[0,6,0],"0.7":[0,0,0]}},
 "body":{"rotation":{"0.0":[0,0,0],"0.15":[6,0,0],"0.7":[0,0,0]}}}}
json.dump({"format_version":"1.8.0","animations":anims},open(RP+"/animations/sh3.animation.json","w"),indent=1)

def controller(name,anim_names):
    def st(cur):
        t=[]
        for k,v in (("default",0),("windup",1),("attack",2),("close",3)):
            if k!=cur: t.append({k:f"query.property('sh:state') == {v}"})
        return t
    return {"format_version":"1.10.0","animation_controllers":{f"controller.animation.{name}.state":{"initial_state":"default","states":{
        "default":{"transitions":st("default")},
        "windup":{"animations":["windup"],"transitions":st("windup")},
        "attack":{"animations":["attack"],"transitions":st("attack")},
        "close":{"animations":["close"],"transitions":st("close")}}}}}
for n in ("sh_hound","sh_scorpion"):
    json.dump(controller(n,None),open(f"{RP}/animation_controllers/{n}.ac.json","w"),indent=1)

def client(ident,geo,tex,n,scale,egg):
    anim={"idle":f"animation.{n}.idle","walk":f"animation.{n}.walk","state":f"controller.animation.{n}.state","look":"animation.sh.look","windup":f"animation.{n}.windup"}
    if n=="sh_hound": anim.update({"attack":"animation.sh_hound.pounce","close":"animation.sh_hound.bite"})
    else: anim.update({"attack":"animation.sh_scorpion.strike","close":"animation.sh_scorpion.pinch"})
    return {"format_version":"1.10.0","minecraft:client_entity":{"description":{"identifier":ident,"materials":{"default":"entity_alphatest"},
      "textures":{"default":f"textures/entity/{tex}"},"geometry":{"default":f"geometry.{geo}"},"animations":anim,
      "scripts":{"animate":["idle","walk","state","look"],"scale":str(scale)},"render_controllers":["controller.render.sh_default"],
      "spawn_egg":{"base_color":egg[0],"overlay_color":egg[1]}}}}
json.dump(client("sh:shadow_hound","sh_hound","sh_hound","sh_hound",1.9,("#262230","#8a50ff")),open(RP+"/entity/shadow_hound.entity.json","w"),indent=1)
json.dump(client("sh:sand_scorpion","sh_scorpion","sh_scorpion","sh_scorpion",1.15,("#96602e","#96ff5a")),open(RP+"/entity/sand_scorpion.entity.json","w"),indent=1)

base=json.load(open(BP+"/entities/ember_imp.json"))
def bp(ident,hp,speed,dmg,w,h,fam=("sh_monster","sh_rank0")):
    e=copy.deepcopy(base); d=e["minecraft:entity"]; d["description"]["identifier"]=ident
    c=d["components"]; c["minecraft:type_family"]["family"]=list(fam)
    c["minecraft:health"]={"value":hp,"max":hp}; c["minecraft:movement"]={"value":speed}
    c["minecraft:attack"]={"damage":dmg}; c["minecraft:collision_box"]={"width":w,"height":h}
    return e
json.dump(bp("sh:shadow_hound",40,0.34,5,1.3,1.7),open(BP+"/entities/shadow_hound.json","w"),indent=1)
json.dump(bp("sh:sand_scorpion",36,0.24,5,1.1,0.8),open(BP+"/entities/sand_scorpion.json","w"),indent=1)
for f,extra in (("en_US",("Shadow Hound","Sand Scorpion")),("ar_SA",("ذئب الظل","عقرب الرمل"))):
    p=f"{RP}/texts/{f}.lang"; s=open(p,encoding="utf-8").read()
    if "sh:shadow_hound" not in s:
        s=s.rstrip("\n")+f"\nentity.sh:shadow_hound.name={extra[0]}\nentity.sh:sand_scorpion.name={extra[1]}\nitem.spawn_egg.entity.sh:shadow_hound.name={'بيضة '+extra[0] if f=='ar_SA' else extra[0]+' Egg'}\nitem.spawn_egg.entity.sh:sand_scorpion.name={'بيضة '+extra[1] if f=='ar_SA' else extra[1]+' Egg'}\n"
        open(p,"w",encoding="utf-8").write(s)
