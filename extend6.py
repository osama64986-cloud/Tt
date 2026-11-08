"""أيقونات المهارات: لكل قدرة شكل إطار مختلف، ولكل مهارة رمز واضح."""
from PIL import Image, ImageDraw
import math
OUT="AnimePowers/RP/textures/items/sh_%s.png"
PAL={"iron":((205,210,222),(84,90,104),(34,38,48)),"wind":((170,255,170),(36,128,70),(12,56,32)),"acc":((255,214,90),(120,76,20),(60,36,8)),"law":((200,150,255),(88,48,150),(36,18,70)),
     "dist":((130,200,255),(36,84,170),(12,34,80)),"echo":((110,255,225),(20,130,125),(6,56,60)),
     "crys":((255,200,235),(170,60,140),(70,16,64)),"bor":((255,215,120),(160,90,30),(70,36,10))}
def frame(d,kind,hi,mid,lo):
    if kind=="acc":   # عملة مربعة بزوايا مقطوعة
        pts=[(7,2),(24,2),(29,7),(29,24),(24,29),(7,29),(2,24),(2,7)]
        d.polygon(pts,fill=lo); d.polygon([(8,4),(23,4),(27,8),(27,23),(23,27),(8,27),(4,23),(4,8)],fill=mid)
        d.polygon(pts,outline=hi)
    elif kind=="law": # لوح/مخطوطة بحواف ملفوفة
        d.rectangle([5,3,26,28],fill=mid,outline=hi); d.rectangle([6,4,25,27],outline=lo)
        d.rectangle([3,2,28,5],fill=hi); d.rectangle([3,26,28,29],fill=hi)
        d.rectangle([3,2,28,2],fill=lo); d.rectangle([3,29,28,29],fill=lo)
    elif kind=="dist": # معيّن
        d.polygon([(15,0),(30,15),(15,30),(0,15)],fill=lo); d.polygon([(15,3),(27,15),(15,27),(3,15)],fill=mid)
        d.polygon([(15,0),(30,15),(15,30),(0,15)],outline=hi)
    elif kind=="iron":  # صفيحة حديد بمسامير
        d.rectangle([3,3,28,28],fill=lo); d.rectangle([5,5,26,26],fill=mid); d.rectangle([3,3,28,28],outline=hi)
        for x,y in ((6,6),(25,6),(6,25),(25,25)): d.rectangle([x-1,y-1,x,y],fill=hi)
    elif kind=="wind":  # ورقة/قطرة
        d.polygon([(15,1),(28,12),(24,27),(15,30),(6,27),(3,12)],fill=lo); d.polygon([(15,4),(25,13),(22,25),(15,27),(9,25),(6,13)],fill=mid)
        d.polygon([(15,1),(28,12),(24,27),(15,30),(6,27),(3,12)],outline=hi)
    elif kind=="crys":  # سداسي بلوري
        pts=[(15,0),(28,8),(28,23),(15,31),(3,23),(3,8)]
        d.polygon(pts,fill=lo); d.polygon([(15,3),(25,9),(25,22),(15,28),(6,22),(6,9)],fill=mid); d.polygon(pts,outline=hi)
        d.line([(15,3),(15,28)],fill=lo); d.line([(6,9),(25,22)],fill=lo); d.line([(25,9),(6,22)],fill=lo)
    elif kind=="bor":   # شارة بحواف مسننة
        pts=[(15,1),(21,4),(28,3),(28,11),(30,16),(28,21),(28,29),(21,27),(15,30),(9,27),(2,29),(2,21),(0,16),(2,11),(2,3),(9,4)]
        d.polygon(pts,fill=lo); d.polygon([(15,4),(20,7),(25,6),(25,12),(27,16),(25,20),(25,26),(20,24),(15,27),(10,24),(5,26),(5,20),(3,16),(5,12),(5,6),(10,7)],fill=mid); d.polygon(pts,outline=hi)
    else:             # دائرة بحلقات صدى
        d.ellipse([1,1,30,30],fill=lo); d.ellipse([3,3,28,28],fill=mid); d.ellipse([1,1,30,30],outline=hi)
        d.arc([-2,-2,33,33],-40,40,fill=hi); d.arc([-2,-2,33,33],140,220,fill=hi)
def L(d,pts,c,w=2): d.line(pts,fill=c,width=w)
def arrow(d,x1,y1,x2,y2,c,w=2):
    d.line([(x1,y1),(x2,y2)],fill=c,width=w)
    a=math.atan2(y2-y1,x2-x1)
    for s in (2.5,-2.5):
        d.line([(x2,y2),(x2-5*math.cos(a+s*0.3),y2-5*math.sin(a+s*0.3))],fill=c,width=w)
def glyphs(d,k,c):
    cx=cy=15.5
    if k=="seal":    # ختم
        d.rectangle([12,6,19,11],fill=c); d.rectangle([14,11,17,15],fill=c); d.rectangle([8,16,23,19],fill=c); d.rectangle([7,21,24,23],fill=c)
    elif k=="subtract": d.rectangle([7,14,24,17],fill=c); d.rectangle([13,8,14,9],fill=c); d.rectangle([17,8,18,9],fill=c)
    elif k=="transfer":
        d.rectangle([5,11,11,19],outline=c,width=2); d.rectangle([20,11,26,19],outline=c,width=2); arrow(d,12,15,19,15,c)
    elif k=="divide": d.rectangle([7,14,24,16],fill=c); d.ellipse([13,7,18,12],fill=c); d.ellipse([13,19,18,24],fill=c)
    elif k=="zero": d.ellipse([9,6,22,25],outline=c,width=3); d.line([(11,22),(20,9)],fill=c,width=2)
    elif k=="weight":
        d.rectangle([8,6,23,17],fill=c); d.rectangle([11,9,20,14],fill=(60,30,110)); arrow(d,15,19,15,28,c)
    elif k=="silence":
        d.rectangle([8,12,12,19],fill=c); d.polygon([(12,12),(18,7),(18,24),(12,19)],fill=c); L(d,[(21,9),(27,22)],c,2); L(d,[(27,9),(21,22)],c,2)
    elif k=="reflect":
        d.rectangle([15,5,16,26],fill=c)
        L(d,[(4,8),(13,16)],c,2); d.polygon([(13,16),(8,15),(12,11)],fill=c)
        L(d,[(27,8),(18,16)],c,2); d.polygon([(18,16),(23,15),(19,11)],fill=c)
        L(d,[(4,24),(13,17)],c,1); L(d,[(27,24),(18,17)],c,1)
    elif k=="boundary":
        d.rectangle([7,7,24,24],outline=c,width=2)
        for i in range(8,24,4): d.rectangle([i,15,i+1,16],fill=c)
        d.rectangle([14,13,17,18],fill=c)
    elif k=="absolute":
        d.polygon([(15,4),(18,13),(27,15),(18,18),(15,27),(13,18),(4,15),(13,13)],fill=c); d.ellipse([13,13,18,18],fill=(255,255,255))
    elif k=="ironskin":
        d.polygon([(7,6),(24,6),(24,17),(15,27),(7,17)],fill=c); d.polygon([(10,9),(21,9),(21,16),(15,23),(10,16)],fill=(70,76,92)); d.rectangle([14,10,16,20],fill=c)
    elif k=="ironfist":
        d.rectangle([8,10,22,20],fill=c)
        for x in (9,12,15,18): d.rectangle([x,7,x+2,10],fill=c)
        d.rectangle([22,12,26,18],fill=c); arrow(d,28,15,31,15,c,1)
    elif k=="windrun":
        L(d,[(5,10),(24,10)],c,2); L(d,[(3,16),(26,16)],c,2); L(d,[(7,22),(22,22)],c,2); d.polygon([(24,6),(29,16),(24,26)],fill=c)
    elif k=="windleap":
        arrow(d,15,27,15,5,c,3); d.arc([6,16,24,30],200,340,fill=c,width=2)
    elif k=="gale":
        for r in (3,7,11): d.arc([15-r,15-r,15+r,15+r],20+r*10,300+r*10,fill=c,width=2)
        d.ellipse([14,14,17,17],fill=c)
    elif k=="time":
        d.ellipse([7,7,24,24],outline=c,width=2); L(d,[(15,15),(15,9)],c,2); L(d,[(15,15),(20,17)],c,2); d.rectangle([13,4,18,6],fill=c)
    elif k=="pull": arrow(d,3,15,12,15,c); arrow(d,28,15,19,15,c); d.ellipse([13,13,18,18],fill=c)
    elif k=="push": arrow(d,12,15,3,15,c); arrow(d,19,15,28,15,c); d.rectangle([14,9,17,22],fill=c)
    elif k=="swap": arrow(d,6,10,25,10,c); arrow(d,25,21,6,21,c)
    elif k=="fold": L(d,[(4,22),(10,8),(16,22),(22,8),(28,22)],c,2)
    elif k=="spacecollapse":
        for r in (8,5,2): d.rectangle([15-r,15-r,15+r,15+r],outline=c)
        d.rectangle([14,14,17,17],fill=c)
    elif k=="echostrike":
        d.ellipse([6,12,12,18],fill=c)
        for r in (7,12): d.arc([9-r,15-r,9+r,15+r],-50,50,fill=c,width=2)
    elif k=="echoseal":
        d.ellipse([8,8,23,23],outline=c,width=2); d.ellipse([13,13,18,18],fill=c); d.arc([3,3,28,28],200,340,fill=c)
    elif k=="sonar":
        d.arc([3,10,28,35],180,360,fill=c,width=2); d.arc([8,15,23,30],180,360,fill=c,width=2); d.ellipse([14,22,17,25],fill=c); L(d,[(15,23),(24,8)],c,2)
    elif k=="echowave":
        for i,r in enumerate((5,9,13)): d.arc([4-r+8,15-r,4+r+8,15+r],-55,55,fill=c,width=2)
        d.ellipse([5,13,9,17],fill=c)
    elif k=="shards":
        for dx in (-7,0,7): d.polygon([(15+dx,6),(17+dx,22),(15+dx,27),(13+dx,22)],fill=c)
    elif k=="crystalshield":
        d.polygon([(15,5),(25,9),(23,21),(15,27),(7,21),(5,9)],outline=c,width=2); d.polygon([(15,10),(19,13),(18,19),(15,22),(12,19),(11,13)],fill=c)
    elif k=="prison":
        for x in (7,12,17,22): d.rectangle([x,6,x+2,25],fill=c)
        d.rectangle([5,6,25,8],fill=c); d.rectangle([5,23,25,25],fill=c); d.ellipse([13,13,17,17],fill=(255,255,255))
    elif k=="burst":
        d.polygon([(15,3),(18,12),(27,8),(20,15),(28,20),(18,19),(15,28),(12,19),(3,20),(10,15),(3,8),(12,12)],fill=c); d.ellipse([13,13,18,18],fill=(255,255,255))
    elif k=="rockskin":
        d.polygon([(8,9),(15,5),(23,8),(26,16),(21,25),(11,26),(5,18)],fill=c); L(d,[(10,12),(16,16),(14,23)],(90,60,30),1); L(d,[(16,16),(23,13)],(90,60,30),1)
    elif k=="fangs":
        d.polygon([(5,5),(12,5),(8,26)],fill=c); d.polygon([(19,5),(26,5),(22,26)],fill=c); d.rectangle([5,4,26,5],fill=c)
    elif k=="windwings":
        d.polygon([(15,20),(3,8),(8,22)],fill=c); d.polygon([(15,20),(27,8),(22,22)],fill=c); d.polygon([(15,8),(18,22),(12,22)],fill=(255,255,255))
    elif k=="huntereye":
        d.polygon([(2,15),(15,6),(28,15),(15,24)],fill=c); d.ellipse([11,11,19,19],fill=(70,36,10)); d.ellipse([14,14,16,16],fill=(255,255,255))
    elif k=="adapt":
        d.ellipse([4,9,16,21],outline=c,width=3); d.ellipse([14,9,26,21],outline=c,width=3)
    elif k=="spacerewind":
        d.arc([6,6,25,25],40,320,fill=c,width=3); d.polygon([(21,3),(27,12),(17,11)],fill=c); L(d,[(15,11),(15,15),(19,17)],c,2)
    elif k=="chorus":
        for r in (4,8,12): d.arc([15-r,15-r,15+r,15+r],200,340,fill=c,width=2); d.arc([15-r,15-r,15+r,15+r],20,160,fill=c,width=2)
        d.ellipse([13,13,18,18],fill=(255,255,255))
MAP={"iron":["ironskin","ironfist"],"wind":["windrun","windleap","gale"],"acc":["seal","subtract","transfer","divide","zero"],"law":["weight","silence","reflect","boundary","time","absolute"],
     "dist":["pull","push","swap","fold","spacecollapse","spacerewind"],"echo":["echostrike","echoseal","echowave","chorus"],
     "crys":["shards","crystalshield","prison","burst"],"bor":["rockskin","fangs","windwings","huntereye","adapt"]}
sheet=Image.new("RGBA",(7*136,8*136),(40,40,46,255))
for r,(p,ks) in enumerate(MAP.items()):
    hi,mid,lo=PAL[p]
    for i,k in enumerate(ks):
        im=Image.new("RGBA",(32,32),(0,0,0,0)); d=ImageDraw.Draw(im)
        frame(d,p,hi,mid,lo); glyphs(d,k,tuple(min(255,v+30) for v in hi))
        im.save(OUT%k); b=im.resize((128,128),Image.NEAREST); sheet.paste(b,(i*136+4,r*136+4),b)
sheet.save("sv/skill_icons_new.png")
