"""Generate Urdu (or English) voice clips with edge-tts for every video script in scripts/.

For each video in scripts/<file>.json, every line with "say_ur" (Urdu) or "say_en" gets
audio/<video name>/<line index>.mp3 plus a manifest.json. Existing clips whose text and
voice are unchanged are skipped, so re-running is cheap.
"""
import asyncio, hashlib, json, pathlib, sys
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_UR = "ur-PK-AsadNeural"
DEFAULT_EN = "en-US-AndrewNeural"

def videos(data):
    if isinstance(data, dict) and "videos" in data:
        return data["videos"]
    return data if isinstance(data, list) else [data]

async def one(text, voice, rate, pitch, out):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await com.save(str(out))

async def main(paths):
    total = 0
    for p in paths:
        data = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        for v in videos(data):
            name = v["name"]
            vdir = ROOT / "audio" / name
            vdir.mkdir(parents=True, exist_ok=True)
            mf = vdir / "manifest.json"
            old = json.loads(mf.read_text()) if mf.exists() else {}
            new = {}
            for i, ln in enumerate(v.get("lines", [])):
                if ln.get("say_ur"):
                    text, voice = ln["say_ur"], v.get("voice_ur", DEFAULT_UR)
                    rate = ln.get("rate", v.get("rate_ur", "-6%"))
                elif ln.get("say_en"):
                    text, voice = ln["say_en"], v.get("voice_en", DEFAULT_EN)
                    rate = ln.get("rate", v.get("rate_en", "-16%"))
                else:
                    continue
                pitch = ln.get("pitch", v.get("pitch", "+0Hz"))
                key = hashlib.sha1(f"{text}|{voice}|{rate}|{pitch}".encode()).hexdigest()
                out = vdir / f"{i:02d}.mp3"
                new[str(i)] = {"file": out.name, "text": text, "voice": voice,
                               "rate": rate, "pitch": pitch, "hash": key}
                if old.get(str(i), {}).get("hash") == key and out.exists():
                    continue
                for attempt in range(3):
                    try:
                        await one(text, voice, rate, pitch, out)
                        break
                    except Exception as e:
                        print(f"retry {attempt+1} {name}#{i}: {e}", file=sys.stderr)
                        await asyncio.sleep(3)
                else:
                    raise SystemExit(f"TTS failed for {name} line {i}")
                total += 1
                print(f"{name} #{i:02d} {voice} {rate}: {text[:50]}")
            mf.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"generated {total} clips")

if __name__ == "__main__":
    args = sys.argv[1:] or [str(x) for x in sorted((ROOT / "scripts").glob("*.json"))]
    asyncio.run(main(args))
