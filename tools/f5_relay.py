"""Urdu voice clone with SPRING_F5 (F5-TTS fine-tuned on 23 Indian languages incl. Urdu, Apache-2.0).
Script: scripts_f5/<file>.json  {"videos":[{"name","ref":"voices/x.wav","lines":[{"say_ur"}]}]}  (ref text in voices/x.txt)
Output: audio/<name>/NN.wav + manifest.json
"""
import hashlib, json, pathlib, sys, time
import numpy as np, soundfile as sf
from transformers import AutoModel

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main(paths):
    model = None
    for p in paths:
        data = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        for v in data["videos"]:
            name = v["name"]; vdir = ROOT / "audio" / name; vdir.mkdir(parents=True, exist_ok=True)
            mf = vdir / "manifest.json"; old = json.loads(mf.read_text()) if mf.exists() else {}
            ref = ROOT / v["ref"]; ref_text = v.get("ref_text") or ref.with_suffix(".txt").read_text(encoding="utf-8").strip()
            new = {}
            for i, ln in enumerate(v["lines"]):
                text = ln.get("say_tts") or ln["say_ur"]
                key = hashlib.sha1(json.dumps([text, v["ref"], ref_text], ensure_ascii=False).encode()).hexdigest()
                out = vdir / f"{i:02d}.wav"
                new[str(i)] = {"file": out.name, "text": text, "engine": "spring_f5", "ref": v["ref"], "hash": key}
                if old.get(str(i), {}).get("hash") == key and out.exists():
                    continue
                if model is None:
                    t0 = time.time()
                    model = AutoModel.from_pretrained("SPRINGLab/SPRING_F5", trust_remote_code=True)
                    print(f"model loaded in {time.time()-t0:.0f}s", flush=True)
                t0 = time.time()
                audio = model(text, ref_audio_path=str(ref), ref_text=ref_text, lang="ur")
                audio = np.asarray(audio)
                if audio.dtype == np.int16: audio = audio.astype(np.float32) / 32768.0
                audio = audio.astype(np.float32).squeeze()
                sf.write(str(out), audio, 24000)
                print(f"{name} #{i:02d} {len(audio)/24000:.1f}s in {time.time()-t0:.0f}s: {text[:40]}", flush=True)
            mf.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main(sys.argv[1:] or [str(x) for x in sorted((ROOT / "scripts_f5").glob("*.json"))])
