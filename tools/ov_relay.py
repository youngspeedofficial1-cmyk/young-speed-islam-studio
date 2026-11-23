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

def main(paths):
    model = None
    for p in paths:
        for v in videos(json.loads(pathlib.Path(p).read_text(encoding="utf-8"))):
            name = v["name"]; vdir = ROOT / "audio" / name; vdir.mkdir(parents=True, exist_ok=True)
            mf = vdir / "manifest.json"
            old = json.loads(mf.read_text()) if mf.exists() else {}
            ref = v.get("ref"); ref_text = v.get("ref_text")
            if ref and not ref_text:
                t = (ROOT / ref).with_suffix(".txt")
                ref_text = t.read_text(encoding="utf-8").strip() if t.exists() else None
            cfg = {k: v.get(k) for k in ("ref", "instruct", "speed", "seed", "num_step")}
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
                torch.manual_seed(int(ln.get("seed", v.get("seed", 7))))
                kw = dict(text=text, language="ur", num_step=int(v.get("num_step", 32)))
                if prompt is not None: kw["voice_clone_prompt"] = prompt
                elif v.get("instruct"): kw["instruct"] = v["instruct"]
                if ln.get("speed", v.get("speed")): kw["speed"] = float(ln.get("speed", v.get("speed")))
                t0 = time.time()
                audio = model.generate(**kw)[0]
                audio = np.asarray(audio, dtype=np.float32).squeeze()
                sf.write(str(out), audio, model.sampling_rate)
                print(f"{name} #{i:02d} {len(audio)/model.sampling_rate:.1f}s audio in {time.time()-t0:.0f}s: {text[:40]}", flush=True)
            mf.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main(sys.argv[1:] or [str(x) for x in sorted((ROOT / "scripts_ov").glob("*.json"))])
