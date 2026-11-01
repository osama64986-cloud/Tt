import sys, numpy as np
exec(open(sys.argv[1]).read().split("base_arm, base_bow")[0])
def pose_anim(name, t):
    env = {"q": {"modified_distance_moved": 0, "modified_move_speed": 0, "life_time": t, "anim_time": t, "property": lambda *a: 0}}
    return R.pose_from_anims([A['animation.sh_archer.idle'], A[name]], t, env)
D = "animation.sh_archer.draw"
for t in (0.32, 0.4, 0.5, 0.6, 0.65, 0.68, 0.7, 0.72, 0.73, 0.9, 1.2, 1.6):
    p = pose_anim(D, t)
    vis = ["bow"] + (["hand_arrow"] if 0.31 <= t <= 0.72 else []) + (["arrow"] if t >= 0.73 else [])
    out = {}
    for bn in vis:
        pts = samples(cube_frames(p, [bn]))
        for part in BODY:
            k = inside_count(pts, cube_frames(p, [part]), margin=0.0)
            if k: out[(bn, part)] = k
    print(f"t={t:.2f}", out or "نظيف")
