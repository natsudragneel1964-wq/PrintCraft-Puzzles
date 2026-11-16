"""Genera voz (Piper), música original y efectos; escribe work/<id>.wav y work/<id>.json (línea de tiempo)."""
import json, os, re, sys, wave
import numpy as np
from piper import PiperVoice, SynthesisConfig
from videos import VIDEOS, SAY, CHANNEL

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
VOICE = os.environ.get("VOICE", os.path.join(HERE, "..", "voices", "es_ES-davefx-medium.onnx"))
SPEED = float(os.environ.get("SPEED", "0.9"))  # <1 = más rápido
BEAT_GAP, SCENE_TAIL, LEAD = 0.14, 0.28, 0.30

voice = PiperVoice.load(VOICE)
cfg = SynthesisConfig(length_scale=SPEED, noise_scale=0.6, noise_w_scale=0.8)


def to_say(text):
    for pat, rep in SAY:
        text = re.sub(pat, rep, text)
    return text.replace("«", "").replace("»", "")


def tts(text):
    parts = []
    for ch in voice.synthesize(text, syn_config=cfg):
        a = ch.audio_float_array.astype(np.float32)
        parts.append(a)
        parts.append(np.zeros(int(ch.sample_rate * 0.08), np.float32))
    a = np.concatenate(parts[:-1])
    src = voice.config.sample_rate
    n = int(len(a) * SR / src)
    a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    idx = np.where(np.abs(a) > 0.01)[0]  # recorta silencios
    if len(idx):
        a = a[max(0, idx[0] - 400): idx[-1] + 2500]
    return a / (np.max(np.abs(a)) + 1e-6) * 0.85


def words_timing(cap, t0, t1):
    ws = cap.split()
    wts = [len(re.sub(r"\W", "", w)) + 1.5 + (2.5 if re.search(r"[.,:;?!]$", w) else 0) for w in ws]
    tot, out, c = sum(wts), [], 0.0
    for w, wt in zip(ws, wts):
        a = t0 + (t1 - t0) * c / tot
        c += wt
        out.append(dict(w=w, t0=round(a, 3), t1=round(t0 + (t1 - t0) * c / tot, 3)))
    return out


# ---------- música original (synthwave, 100 BPM, Am-F-C-G) ----------
def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(dur, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    bpm = 100
    b = 60 / bpm
    out = np.zeros(n, np.float32)
    chords = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    bar = 4 * b
    nb = int(dur / bar) + 1

    def add(sig, at):
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[i:i + len(sig)] += sig

    for k in range(nb):
        root, ch = chords[k % 4]
        t0 = k * bar
        # pad
        L = int(bar * SR)
        tt = np.arange(L) / SR
        pad = sum(np.sin(2 * np.pi * note(m) * d * tt) for m in ch for d in (0.997, 1.003)) / 6
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.4)
        add((pad * env * 0.16).astype(np.float32), t0)
        for s in range(8):  # bajo en corcheas
            L2 = int(b / 2 * SR)
            t2 = np.arange(L2) / SR
            f = note(root - 12)
            bass = sum(np.sin(2 * np.pi * f * h * t2) / h for h in (1, 2, 3, 4)) * np.exp(-t2 * 7)
            add((bass * 0.22).astype(np.float32), t0 + s * b / 2)
        for s in range(16):  # arpegio
            m = ch[s % 3] + (12 if (s // 3) % 2 else 0)
            L3 = int(b / 4 * SR * 1.8)
            t3 = np.arange(L3) / SR
            f = note(m)
            arp = (np.sin(2 * np.pi * f * t3) + 0.3 * np.sin(2 * np.pi * 2 * f * t3)) * np.exp(-t3 * 9)
            add((arp * 0.07).astype(np.float32), t0 + s * b / 4)
            add((arp * 0.03).astype(np.float32), t0 + s * b / 4 + 0.375 * b)
        for s in range(4):  # bombo, caja, charles
            tk = np.arange(int(0.25 * SR)) / SR
            kick = np.sin(2 * np.pi * (45 * tk + 60 * (1 - np.exp(-tk * 30)) / 30)) * np.exp(-tk * 14)
            add((kick * 0.5).astype(np.float32), t0 + s * b)
            if s % 2:
                ts = np.arange(int(0.18 * SR)) / SR
                sn = rng.standard_normal(len(ts)) * np.exp(-ts * 22) + np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 30)
                add((sn * 0.13).astype(np.float32), t0 + s * b)
            for h in range(2):
                th = np.arange(int(0.04 * SR)) / SR
                hat = np.diff(rng.standard_normal(len(th) + 1)) * np.exp(-th * 90)
                add((hat * 0.035).astype(np.float32), t0 + s * b + h * b / 2)
    return out


def whoosh(rng, d=0.38):
    L = int(d * SR)
    x = rng.standard_normal(L)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(L, 1 / SR)
    X *= np.exp(-((f - 2500) / 2200) ** 2)
    y = np.fft.irfft(X, L)
    tt = np.linspace(0, 1, L)
    return (y / np.max(np.abs(y)) * np.sin(np.pi * tt) ** 2 * 0.22).astype(np.float32)


def pop():
    tt = np.arange(int(0.09 * SR)) / SR
    return (np.sin(2 * np.pi * (700 + 2600 * tt) * tt) * np.exp(-tt * 45) * 0.16).astype(np.float32)


def build(v, idx):
    rng = np.random.default_rng(idx)
    cur, scenes, placed, sfx = LEAD, [], [], []
    for typ, data, beats in v["scenes"]:
        sc = dict(type=typ, data=data, start=round(cur - 0.12, 3), beats=[])
        sfx.append(("w", cur - 0.2))
        for bi, bt in enumerate(beats):
            cap, say = bt if isinstance(bt, tuple) else (bt, to_say(bt))
            a = tts(say)
            d = len(a) / SR
            placed.append((cur, a))
            if bi:
                sfx.append(("p", cur))
            sc["beats"].append(dict(start=round(cur, 3), end=round(cur + d, 3), cap=cap,
                                    words=words_timing(cap, cur, cur + d - 0.05)))
            cur += d + BEAT_GAP
        cur += SCENE_TAIL
        sc["end"] = round(cur - 0.12, 3)
        scenes.append(sc)
    dur = cur + 0.9
    scenes[-1]["end"] = round(dur, 3)
    n = int(dur * SR)
    vox = np.zeros(n, np.float32)
    for at, a in placed:
        i = int(at * SR)
        vox[i:i + len(a)] += a[: n - i]
    fx = np.zeros(n, np.float32)
    w, p = whoosh(rng), pop()
    for k, at in sfx:
        s = w if k == "w" else p
        i = max(0, int(at * SR))
        fx[i:i + len(s)] += s[: n - i]
    mus = music(dur, idx)
    # ducking: baja la música cuando hay voz
    env = np.convolve(np.abs(vox), np.ones(4000) / 4000, mode="same")
    duck = 1 - 0.45 * np.clip(env * 12, 0, 1)
    fade = np.minimum(1, np.arange(n) / (0.3 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.8 * SR))
    mix = vox * 1.0 + mus * 0.34 * duck * fade + fx
    mix = np.tanh(mix * 1.15)
    st = np.stack([mix, mix], 1)
    with wave.open(os.path.join(WORK, v["id"] + ".wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32000).astype(np.int16).tobytes())
    tl = dict(id=v["id"], pal=v["pal"], channel=CHANNEL, n=idx + 1, dur=round(dur, 3), scenes=scenes)
    json.dump(tl, open(os.path.join(WORK, v["id"] + ".json"), "w"), ensure_ascii=False)
    print(v["id"], f"{dur:.1f}s")


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    only = sys.argv[1:]
    for i, v in enumerate(VIDEOS):
        if not only or any(o in v["id"] for o in only):
            build(v, i)
