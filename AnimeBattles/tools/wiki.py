import json, sys, urllib.parse, urllib.request, os, time
UA = {"User-Agent": "AnimeBattlesResearch/1.0 (reference images for a personal Minecraft add-on)"}
def api(base, **params):
    params["format"] = "json"
    url = base + "/api.php?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return json.load(r)
def images_of(base, title):
    d = api(base, action="query", titles=title, prop="images", imlimit=500)
    out = []
    for p in d["query"]["pages"].values():
        out += [i["title"] for i in p.get("images", [])]
    return out
def urls(base, files, width=480):
    res = {}
    for i in range(0, len(files), 40):
        d = api(base, action="query", titles="|".join(files[i:i+40]), prop="imageinfo", iiprop="url", iiurlwidth=width)
        for p in d["query"]["pages"].values():
            if "imageinfo" in p:
                res[p["title"]] = p["imageinfo"][0].get("thumburl") or p["imageinfo"][0]["url"]
    return res
def download(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        open(path, "wb").write(r.read())
if __name__ == "__main__":
    cmd = sys.argv[1]
    base = sys.argv[2]
    if cmd == "images":
        for t in sys.argv[3:]:
            print("##", t)
            for f in images_of(base, t): print(f)
    elif cmd == "get":
        outdir = sys.argv[3]
        files = sys.argv[4:]
        for title, u in urls(base, files).items():
            name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in title.split(":", 1)[1])
            download(u, os.path.join(outdir, name)); print("saved", name)
            time.sleep(0.3)
