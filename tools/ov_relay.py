"""Urdu voice with OmniVoice (free, open source) on the GitHub runner.

Script format (scripts_ov/<file>.json) is the same as scripts/: {"videos":[{"name", "lines":[{"say_ur"}]}]}.
Voice per video:
  "ref": "voices/me.wav"   + "ref_text" (or voices/me.txt)  -> clone that voice
  "instruct": "male, young adult, low pitch"                -> designed voice
  neither                                                     -> model picks a voice
Optional: "speed" (1.0), "seed", "num_step" (32). Output: audio/<name>/NN.wav + manifest.json
"""
import hashlib, json, pathlib, sys, time
import numpy as np, soundfile as sf, torch
from omnivoice import OmniVoice

ROOT = pathlib.Path(__file__).resolve().parents[1]
torch.set_num_threads(max(1, torch.get_num_threads()))

def videos(d):
    return d["videos"] if isinstance(d, dict) and "videos" in d else (d if isinstance(d, list) else [d])

_ASR = None
def transcribe(path):
    global _ASR
    from transformers import pipeline
    if _ASR is None:
        _ASR = pipeline("automatic-speech-recognition", "openai/whisper-large-v3-turbo", device="cpu")
    wav, sr = sf.read(str(path), dtype="float32")
    if wav.ndim > 1: wav = wav.mean(1)
    if sr != 16000:
        import torchaudio
        wav = torchaudio.functional.resample(torch.from_numpy(wav), sr, 16000).numpy()
    out = _ASR({"raw": wav, "sampling_rate": 16000}, generate_kwargs={"language": "urdu", "task": "transcribe"})
    return out["text"].strip()

import re, unicodedata
def norm(t):
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", t)          # harakat
    for a, b in (("ي", "ی"), ("ى", "ی"), ("ك", "ک"), ("ه", "ہ"), ("ة", "ہ"), ("ۃ", "ہ"), ("ئ", "ی"), ("ۓ", "ے"), ("أ", "ا"), ("إ", "ا"), ("آ", "ا")):
        t = t.replace(a, b)
    t = re.sub(r"[^\w]", "", t)
    return t

def cer(ref, hyp):
    a, b = norm(ref), norm(hyp)
    if not a: return 1.0
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j-1] + 1, prev + (ca != cb))
    return d[len(b)] / len(a)

def main(paths):
    paths = [p for p in paths if pathlib.Path(p).exists()]
    model = None
    for p in paths:
        for v in videos(json.loads(pathlib.Path(p).read_text(encoding="utf-8"))):
            name = v["name"]; vdir = ROOT / "audio" / name; vdir.mkdir(parents=True, exist_ok=True)
            mf = vdir / "manifest.json"
            old = json.loads(mf.read_text()) if mf.exists() else {}
            ref = v.get("ref"); ref_text = v.get("ref_text")
            if ref and not ref_text:
                t = (ROOT / ref).with_suffix(".txt")
                if t.exists():
                    ref_text = t.read_text(encoding="utf-8").strip()
                else:
                    ref_text = transcribe(ROOT / ref)
                    t.write_text(ref_text + "\n", encoding="utf-8")
                print(f"ref {ref}: {ref_text}", flush=True)
            elif ref:
                print(f"ref {ref} (given): {ref_text} | asr: {transcribe(ROOT / ref)}", flush=True)
            cfg = {k: v.get(k) for k in ("ref", "instruct", "speed", "seed", "num_step", "takes")}
            new = {}
            prompt = None
            for i, ln in enumerate(v.get("lines", [])):
                text = ln.get("say_ur") or ln.get("say")
                if not text:
                    continue
                key = hashlib.sha1(json.dumps([text, cfg, ref_text], ensure_ascii=False).encode()).hexdigest()
                out = vdir / f"{i:02d}.wav"
                new[str(i)] = {"file": out.name, "text": text, "engine": "omnivoice", "hash": key, **cfg}
                if old.get(str(i), {}).get("hash") == key and out.exists():
                    continue
                if model is None:
                    t0 = time.time()
                    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cpu", dtype=torch.float32)
                    print(f"model loaded in {time.time()-t0:.0f}s", flush=True)
                if ref and prompt is None:
                    prompt = model.create_voice_clone_prompt(ref_audio=str(ROOT / ref), ref_text=ref_text)
                kw = dict(text=ln.get("say_tts", text), language="ur", num_step=int(v.get("num_step", 32)))
                if prompt is not None: kw["voice_clone_prompt"] = prompt
                elif v.get("instruct"): kw["instruct"] = v["instruct"]
                if ln.get("speed", v.get("speed")): kw["speed"] = float(ln.get("speed", v.get("speed")))
                takes = int(ln.get("takes", v.get("takes", 1)))
                best = None
                for k in range(takes):
                    torch.manual_seed(int(ln.get("seed", v.get("seed", 7))) + 101 * k)
                    t0 = time.time()
                    audio = np.asarray(model.generate(**kw)[0], dtype=np.float32).squeeze()
                    sc, hyp = 0.0, ""
                    if takes > 1 or v.get("score"):
                        tmp = vdir / f"_take.wav"; sf.write(str(tmp), audio, model.sampling_rate)
                        hyp = transcribe(tmp); tmp.unlink(); sc = cer(text, hyp)
                    print(f"{name} #{i:02d} take{k} {len(audio)/model.sampling_rate:.1f}s in {time.time()-t0:.0f}s cer={sc:.3f} asr: {hyp}", flush=True)
                    if best is None or sc < best[0]:
                        best = (sc, audio, hyp)
                    if sc <= 0.02:
                        break
                sf.write(str(out), best[1], model.sampling_rate)
                new[str(i)].update(cer=round(best[0], 3), asr=best[2])
            mf.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main(sys.argv[1:] or [str(x) for x in sorted((ROOT / "scripts_ov").glob("*.json"))])
