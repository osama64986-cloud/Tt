import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from mobkit import *
RP = "AnimePowers/RP"; BP = "AnimePowers/BP"
GEO = RP + "/models/entity/{}.geo.json"; TEX = RP + "/textures/entity/{}.png"

# ═══════ ذئب الظل: كلب رباعي بفرو فحمي وعرف بنفسجي حبري ═══════
def build_hound():
    m = Mob("geometry.sh_hound", 96, 96, seed=21)
    FUR=(58,55,72); FUR2=(92,86,114); INK=(112,72,205); EYE=(200,130,255); TEETH=(228,218,200); NOSE=(18,16,22)
    def fur(img, regs):
        for f in ("up","north","east","west","south"):
            patches(img, regs[f], m.rng, FUR2, density=0.25, seed_scale=2)
            patches(img, regs[f], m.rng, mix(FUR,INK,0.35), density=0.06, seed_scale=1)
    def face(img, regs):
        fur(img, regs); x0,y0,w,h = regs["north"]
        for dx in (1,2): glow_px(img, x0+dx, y0+2, EYE, halo=0.0, r=0)
        for dx in (w-2,w-3): glow_px(img, x0+dx, y0+2, EYE, halo=0.0, r=0)
        for dx in (0,w-1): put(img, x0+dx, y0+1, INK)
    def ink(img, regs):
        for x0,y0,w,h in regs.values():
            for yy in range(h):
                for xx in range(w): put(img, x0+xx, y0+yy, mix(INK,(190,150,255),yy/max(1,h-1)*0.6))
    def teeth(img, regs):
        for x0,y0,w,h in regs.values():
            for yy in range(h):
                for xx in range(w): put(img, x0+xx, y0+yy, TEETH)
    m.bone("body",[0,7,0])
    m.cube("body",[-3.2,6.5,-6],[6.4,6,11],FUR,key="torso",detail=fur,grad=0.2)
    m.cube("body",[-3.7,6.2,-7],[7.4,6.4,4.5],FUR,key="chest",detail=fur,grad=0.2)
    m.cube("body",[-3.4,7,2.2],[6.8,5.4,4.6],FUR,key="haunch",detail=fur,grad=0.2)
    for i,z in enumerate((-5,-3,-1,1,3)):
        m.cube("body",[-0.6,12.4,z],[1.2,2.4-i*0.25,1.6],INK,key="crest%d"%i,detail=ink,grad=0.05,noise=3)
    m.cube("body",[-3.5,11.2,-8.2],[7,4,3.5],FUR,key="mane",detail=fur,grad=0.2)
    m.bone("head",[0,11.5,-7.5],"body")
    m.cube("head",[-2.6,9.4,-11],[5.2,4.8,4.6],FUR,key="skull",detail=face,grad=0.2)
    m.cube("head",[-1.6,9.4,-14.8],[3.2,2.4,4],FUR,key="snout",detail=fur,grad=0.2)
    m.cube("head",[-1.0,9.8,-15.2],[2.0,1.0,0.5],NOSE,key="nose",grad=0.05,noise=1)
    m.cube("head",[-1.4,8.1,-14.4],[2.8,1.3,3.6],FUR2,key="jaw",detail=fur,grad=0.2)
    for x in (-1.5,0.9): m.cube("head",[x,9.0,-14.7],[0.6,1.1,0.6],TEETH,key="fang",detail=teeth,grad=0.05,noise=1)
    for s in (-1,1):
        m.cube("head",[(-2.8 if s<0 else 1.4),14.0,-9.5],[1.4,3.2,1.2],FUR,key="ear",detail=fur,rot=[10,0,12*s],pivot=[0,14,-9],grad=0.2)
        m.cube("head",[(-2.5 if s<0 else 1.8),13.2,-8.2],[0.8,1.5,0.8],INK,key="spk",detail=ink,grad=0.05,noise=2)
    # عيون مضيئة بارزة
    for x in (-2.2,0.9):
        m.cube("head",[x,11.6,-11.15],[1.3,1.0,0.4],(225,175,255),key="eyeG",detail=ink,grad=0.0,noise=0)
        m.cube("head",[x+0.3,11.8,-11.3],[0.7,0.6,0.3],(255,245,255),key="eyeC",detail=teeth,grad=0.0,noise=0)
    # ذيل من 3 مفاصل يتحرك
    m.bone("tail",[0,11,5.8],"body",rot=[-30,0,0])
    m.cube("tail",[-1.1,10.2,5.8],[2.2,2.2,4.4],FUR,key="tail",detail=fur,grad=0.2)
    m.bone("tail2",[0,11.3,9.9],"tail",rot=[8,0,0])
    m.cube("tail2",[-0.95,10.4,9.9],[1.9,1.9,4.3],FUR,key="tail2",detail=fur,grad=0.2)
    m.bone("tail3",[0,11.3,13.6],"tail2",rot=[6,0,0])
    m.cube("tail3",[-1.5,9.4,13.4],[3.0,3.8,3.8],INK,key="plume",detail=ink,grad=0.1)
    m.cube("tail3",[-0.7,12.9,14.4],[1.4,2.2,1.6],(190,150,255),key="plumeTip",detail=ink,grad=0.05)
    for nm,x,z in (("leg_fl",2.4,-5),("leg_fr",-2.4,-5),("leg_bl",2.4,4.2),("leg_br",-2.4,4.2)):
        m.bone(nm,[x,7,z],"body")
        m.cube(nm,[x-1.3,2.2,z-1.3],[2.6,5,2.6],FUR,key="leg",detail=fur,grad=0.2)
        m.cube(nm,[x-1.6,0,z-2.0],[3.2,2.4,3.8],FUR2,key="paw",detail=fur,grad=0.2)
        m.cube(nm,[x-1.0,0,z-2.5],[2.0,0.8,0.6],TEETH,key="claw",detail=teeth,grad=0.05,noise=1)
    return m

# ═══════ عقرب الرمل: درع كهرماني، كماشات، ذيل بسم أخضر ═══════
def build_scorpion():
    m = Mob("geometry.sh_scorpion", 128, 128, seed=33)
    SH=(150,96,48); SH2=(112,66,34); HI=(204,146,76); DK=(50,30,18); VEN=(150,255,90)
    def shell(img, regs):
        for f in ("up","north","east","west","south"):
            patches(img, regs[f], m.rng, HI, density=0.18, seed_scale=2)
            patches(img, regs[f], m.rng, DK, density=0.08, seed_scale=1)
        x0,y0,w,h = regs["up"]
        for xx in range(1,w-1): put(img,x0+xx,y0+h//2,mul(SH2,0.7))
    def head(img, regs):
        shell(img, regs); x0,y0,w,h = regs["north"]
        for dx in (1,w-2): put(img,x0+dx,y0+1,(255,90,40)); put(img,x0+dx,y0+2,(40,10,6))
        for dx in (2,w-3): put(img,x0+dx,y0+2,(30,8,6))
    def venom(img, regs):
        for x0,y0,w,h in regs.values():
            for yy in range(h):
                for xx in range(w): put(img,x0+xx,y0+yy,mix(VEN,(230,255,190),yy/max(1,h-1)*0.6))
    def dark(img, regs):
        for x0,y0,w,h in regs.values():
            for yy in range(h):
                for xx in range(w): put(img,x0+xx,y0+yy,mix(DK,SH2,((xx+yy)%3)/4))
    m.bone("body",[0,4,0])
    m.cube("body",[-4.5,3.2,-5],[9,3,4.2],SH,key="p1",detail=shell,grad=0.2)
    m.cube("body",[-4.2,3.6,-1.2],[8.4,3.2,4],SH,key="p2",detail=shell,grad=0.2)
    m.cube("body",[-3.8,3.8,2.5],[7.6,3.0,4.2],SH2,key="p3",detail=shell,grad=0.2)
    m.cube("body",[-2.6,3.6,-7.4],[5.2,3.2,2.8],SH,key="head",detail=head,grad=0.2)
    m.cube("body",[-1.6,3.0,-8.4],[1.2,1.4,1.8],DK,key="mandL",detail=dark,grad=0.05)
    m.cube("body",[0.4,3.0,-8.4],[1.2,1.4,1.8],DK,key="mandR",detail=dark,grad=0.05)
    for s,nm in ((1,"claw_l"),(-1,"claw_r")):
        px=4.6*s
        m.bone(nm,[px,5,-5],"body")
        m.cube(nm,[px-0.9,3.6,-9.0],[1.8,1.8,4.2],SH2,key="arm",detail=shell,grad=0.2)
        m.cube(nm,[px-(1.7 if s>0 else 1.7),3.2,-13.2],[3.4,2.4,4.4],SH,key="palm",detail=shell,grad=0.2)
        m.cube(nm,[px-(1.7 if s>0 else -0.5),3.2,-15.8],[1.2,2.0,2.8],HI,key="fixed",detail=shell,grad=0.2)
        nf="fing_l" if s>0 else "fing_r"
        m.bone(nf,[px+0.5*(-s),4.2,-13.2],nm)
        m.cube(nf,[px-(-0.5 if s>0 else 1.7)-(0 if s>0 else 0),3.2,-15.8],[1.2,2.0,2.8],HI,key="mov",detail=shell,grad=0.2)
    for s,nm in ((1,"legs_l"),(-1,"legs_r")):
        m.bone(nm,[3.6*s,4,0],"body")
        for z in (-3.6,-1.2,1.2,3.6):
            x0 = 3.8 if s>0 else -8.4
            m.cube(nm,[x0,3.4,z-0.5],[4.6,1.0,1.0],SH2,key="legU",detail=dark,grad=0.1,rot=[0,0,(14 if s>0 else -14)],pivot=[3.8*s,4,z])
            m.cube(nm,[(7.6 if s>0 else -8.6),0,z-0.5],[1.0,4.8,1.0],DK,key="legD",detail=dark,grad=0.1)
    TL=(66,150,58); TL2=(108,205,72); TJ=(26,64,26)
    def tailp(img, regs):
        for f in ("up","north","east","west","south"):
            patches(img, regs[f], m.rng, TL2, density=0.25, seed_scale=2)
            patches(img, regs[f], m.rng, TJ, density=0.07, seed_scale=1)
        x0,y0,w,h = regs["north"]
        for xx in range(w): put(img,x0+xx,y0,TJ)
    def spikeg(img, regs):
        for x0,y0,w,h in regs.values():
            for yy in range(h):
                for xx in range(w): put(img,x0+xx,y0+yy,mix((120,230,70),(230,255,170),yy/max(1,h-1)))
    m.bone("tail1",[0,5.0,6.8],"body",rot=[-6,0,0])
    m.cube("tail1",[-1.9,5.0,5.0],[3.8,3.6,3.8],TL,key="g1",detail=tailp,grad=0.2)
    m.bone("tail2",[0,8.4,6.9],"tail1",rot=[14,0,0])
    m.cube("tail2",[-1.7,8.2,5.2],[3.4,3.4,3.4],TL,key="g2",detail=tailp,grad=0.2)
    m.bone("tail3",[0,11.6,6.9],"tail2",rot=[22,0,0])
    m.cube("tail3",[-1.5,11.4,5.4],[3.0,3.2,3.0],TL2,key="g3",detail=tailp,grad=0.2)
    m.bone("tail4",[0,14.6,6.9],"tail3",rot=[26,0,0])
    m.cube("tail4",[-1.3,14.4,5.6],[2.6,3.0,2.6],TL2,key="g4",detail=tailp,grad=0.2)
    m.bone("sting",[0,17.4,6.9],"tail4",rot=[28,0,0])
    m.cube("sting",[-1.5,17.2,5.4],[3.0,3.0,3.0],(100,215,70),key="g5",detail=tailp,grad=0.2)
    m.cube("sting",[-0.7,19.6,5.9],[1.4,2.2,1.6],(190,255,120),key="hook1",detail=spikeg,grad=0.05)
    m.cube("sting",[-0.5,21.4,6.1],[1.0,1.6,1.0],(230,255,170),key="hook2",detail=spikeg,rot=[-30,0,0],pivot=[0,21.4,6.6],grad=0.05)
    return m

if __name__=="__main__":
    build_hound().save(GEO.format("sh_hound"),TEX.format("sh_hound"))
    build_scorpion().save(GEO.format("sh_scorpion"),TEX.format("sh_scorpion"))
