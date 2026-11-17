"""Synthesised fight sounds (original, made from scratch with numpy): heavy punch, whoosh, ground-shaking boom,
domain gong and the Black Flash crack. Writes RP/sounds/ab/*.ogg and RP/sounds/sound_definitions.json."""
import json
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
ROOT = os.path.join(os.path.dirname(__file__), "..", "RP")


def t_(sec):
    return np.arange(int(SR * sec)) / SR


def noise(sec, rng):
    return rng.uniform(-1, 1, int(SR * sec))


def band(x, lo, hi):
    """Brick-wall band-pass in the frequency domain."""
    f = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(x))


def sweep_band(x, c0, c1, width=0.6, chunk=1024):
    """Band-pass whose centre glides from c0 to c1 (Hz) — the 'whoosh'."""
    out = np.zeros_like(x)
    n = len(x)
    win = np.hanning(chunk * 2)
    for i in range(0, n - chunk, chunk):
        seg = x[i:i + chunk * 2]
        if len(seg) < chunk * 2:
            break
        c = c0 * (c1 / c0) ** (i / n)
        out[i:i + chunk * 2] += band(seg * win, c * (1 - width), c * (1 + width))
    return out


def env(sec, attack, decay_k):
    t = t_(sec)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t * decay_k)


def norm(x, peak=0.92):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def reverb(x, rng, tail=0.6, mix=0.25):
    ir = noise(tail, rng) * np.exp(-t_(tail) * 7)
    wet = np.convolve(x, ir)[:len(x) + int(SR * tail * 0.5)]
    y = np.concatenate([x, np.zeros(len(wet) - len(x))])
    return y + norm(wet, np.max(np.abs(x))) * mix


def impact(rng, pitch=1.0):
    sec = 0.7
    t = t_(sec)
    f = 70 * pitch * np.exp(-t * 6) + 34 * pitch
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(sec, 0.002, 7)
    body = band(noise(sec, rng), 120, 1100) * env(sec, 0.001, 16)
    crack = band(noise(sec, rng), 1800, 9000) * env(sec, 0.0005, 70)
    x = 1.2 * sub + 0.9 * body + 0.6 * crack
    return norm(np.tanh(x * 2.2))


def whoosh(rng):
    sec = 0.45
    t = t_(sec)
    x = sweep_band(noise(sec, rng), 350, 3200, 0.45)
    shape = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 1.5
    return norm(x * shape, 0.8)


def boom(rng):
    sec = 2.2
    t = t_(sec)
    rumble = band(noise(sec, rng), 25, 260) * env(sec, 0.004, 1.9)
    sub = np.sin(2 * np.pi * np.cumsum(48 * np.exp(-t * 1.5) + 26) / SR) * env(sec, 0.003, 2.6)
    crack = band(noise(sec, rng), 900, 6000) * env(sec, 0.001, 18)
    debris = np.zeros(len(t))
    for _ in range(26):  # stones landing
        at = int(SR * rng.uniform(0.25, 1.8))
        n = int(SR * 0.04)
        if at + n < len(t):
            debris[at:at + n] += band(noise(0.04, rng), 500, 4000)[:n] * np.exp(-np.arange(n) / SR * 90) * rng.uniform(0.1, 0.35)
    x = 1.1 * rumble + 1.0 * sub + 0.7 * crack + debris
    return norm(np.tanh(x * 1.6))


def domain(rng):
    sec = 3.6
    t = t_(sec)
    swell_len = 0.7
    swell = band(noise(swell_len, rng), 200, 3000) * (t_(swell_len) / swell_len) ** 3
    partials = [(55, 1.0, 0.9), (82.4, 0.7, 1.1), (131, 0.55, 1.4), (174.6, 0.4, 1.8), (262, 0.3, 2.3), (393, 0.18, 3.0), (588, 0.1, 3.8)]
    gong = sum(a * np.sin(2 * np.pi * f * t * (1 + 0.002 * np.sin(2 * np.pi * 0.7 * t))) * np.exp(-t * k) for f, a, k in partials)
    hit = band(noise(sec, rng), 60, 900) * env(sec, 0.001, 9)
    x = np.concatenate([swell * 0.6, gong * 0.9 + hit * 0.8])
    x = np.tanh(x * 1.4)
    k = int(SR * 0.8)
    x[-k:] *= np.linspace(1, 0, k) ** 2  # let the gong die away before the echo tail
    return norm(reverb(x, rng, 1.2, 0.35))


def blackflash(rng):
    sec = 0.9
    t = t_(sec)
    crack = band(noise(sec, rng), 1500, 12000) * env(sec, 0.0003, 30)
    chirp = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-t * 9) + 90) / SR) * env(sec, 0.001, 6)
    sparks = np.zeros(len(t))
    for _ in range(60):  # electric crackle
        at = int(SR * rng.uniform(0.0, 0.7))
        n = int(SR * 0.006)
        if at + n < len(t):
            sparks[at:at + n] += rng.uniform(-1, 1, n) * rng.uniform(0.3, 1.0) * np.exp(-at / SR * 4)
    thump = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 10) + 40) / SR) * env(sec, 0.002, 8)
    x = 0.9 * crack + 0.6 * chirp + 0.5 * band(sparks, 1000, 10000) + 1.1 * thump
    return norm(np.tanh(x * 3.0))


def write_ogg(x, path):
    x = np.array(x, dtype=float)
    k = min(len(x) // 4, int(SR * 0.12))
    x[-k:] *= np.linspace(1, 0, k) ** 2  # no click where the sound ends
    x[:64] *= np.linspace(0, 1, 64)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4", path], check=True)
    os.remove(tmp)


def build():
    rng = np.random.default_rng(7)
    out = os.path.join(ROOT, "sounds", "ab")
    os.makedirs(out, exist_ok=True)
    defs = {}
    sets = {
        "impact": [lambda: impact(rng, 1.0), lambda: impact(rng, 0.85), lambda: impact(rng, 1.15)],
        "whoosh": [lambda: whoosh(rng), lambda: whoosh(rng)],
        "boom": [lambda: boom(rng)],
        "domain": [lambda: domain(rng)],
        "blackflash": [lambda: blackflash(rng)],
    }
    for name, makers in sets.items():
        files = []
        for i, mk in enumerate(makers):
            fn = f"{name}{i + 1}"
            write_ogg(mk(), os.path.join(out, fn + ".ogg"))
            files.append({"name": f"sounds/ab/{fn}", "volume": 1.0, "load_on_low_memory": True})
        defs[f"ab.{name}"] = {"category": "hostile", "min_distance": 4.0, "max_distance": 64.0, "sounds": files}
    with open(os.path.join(ROOT, "sounds", "sound_definitions.json"), "w") as f:
        json.dump({"format_version": "1.20.20", "sound_definitions": defs}, f, indent=2)


if __name__ == "__main__":
    build()
