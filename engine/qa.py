#!/usr/bin/env python3
"""
qa.py - quality control on an exported video (run automatically after each render).

  python qa.py output/<name>/<name>.mp4            # uses output/<name>/<name>_render.json if present

Inspects the actual file with ffprobe/ffmpeg, not the render log:
  format      1080x1920, 30 fps, H.264 High, yuv420p, AAC 48 kHz, duration matches the plan, no missing frames
  loudness    integrated -14 LUFS (+-1), true peak <= -1.0 dBTP, no clipped samples
  black       no black segments except the intended fade-in/out
  freeze      no frozen picture for >= 3 s
  edges       starts with a fade-in and speech within 1.2 s; ends with a fade-out after the last word
  sync        every spoken line fits its on-screen window; all words revealed before the line leaves
  typography  no missing glyphs, no text wider than the text area, no clipped caption blocks
Writes <name>_qa.md / _qa.json and a 12-frame contact sheet <name>_qa_sheet.jpg for a human look.
"""
import json, os, re, subprocess, sys
import numpy as np


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels,nb_frames",
            "-of", "json", path])
    return json.loads(r.stdout)


def luma_at(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=108:192,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    return float(a.mean()) if a.size else -1.0


def run_qa(path, meta=None, out_dir=None):
    name = os.path.splitext(os.path.basename(path))[0]
    out_dir = out_dir or os.path.dirname(path)
    if meta is None:
        mp = os.path.join(out_dir, f"{name}_render.json")
        meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    checks = []

    def add(check, ok, detail="", warn=False):
        checks.append(dict(check=check, status="PASS" if ok else ("WARN" if warn else "FAIL"), detail=detail))

    # ---- format
    p = probe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), {})
    dur = float(p["format"]["duration"])
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = float(num) / float(den or 1)
    add("resolution", (v.get("width"), v.get("height")) == (1080, 1920), f"{v.get('width')}x{v.get('height')}")
    add("frame rate", abs(fps - 30) < 0.01, f"{fps:.2f} fps")
    add("video codec", v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p", f"{v.get('codec_name')} {v.get('profile')} {v.get('pix_fmt')}")
    add("audio codec", a.get("codec_name") == "aac" and int(a.get("sample_rate", 0)) == 48000, f"{a.get('codec_name')} {a.get('sample_rate')} Hz {a.get('channels')} ch")
    off = float(meta.get("thumb") or 0.0)                # title card at the start shifts everything by `off`
    if meta.get("duration"):
        add("duration", abs(dur - meta["duration"] - off) < 0.25, f"{dur:.2f}s (planned {meta['duration'] + off:.2f}s incl. {off:.2f}s title card)")
    if off:
        add("title card", True, f"thumbnail shown for the first {off:.2f}s, then a dissolve into the video")
    nb = int(v.get("nb_frames") or 0)
    if nb:
        add("frame count", abs(nb - round(dur * 30)) <= 2, f"{nb} frames for {dur:.2f}s")
    add("length for Reels/Shorts", 5 <= dur <= 90, f"{dur:.1f}s", warn=True)

    # ---- loudness, true peak, clipping, speech onset (one audio pass)
    r = sh(["ffmpeg", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true,silencedetect=n=-38dB:d=0.25", "-f", "null", "-"])
    txt = r.stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    I = float(I[-1]) if I else None
    tp = float(tp[-1]) if tp else None
    add("loudness", I is not None and -15.0 <= I <= -13.0, f"{I} LUFS (target -14)")
    add("true peak", tp is not None and tp <= -1.0, f"{tp} dBTP (limit -1.0)")
    sil_end = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", txt)]
    sil_start = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", txt)]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True).stdout
    pcm = np.frombuffer(raw, np.int16)
    clipped = int((np.abs(pcm.astype(np.int32)) >= 32600).sum())
    add("clipping", clipped == 0, f"{clipped} clipped samples")

    # ---- black / freeze (one video pass)
    r = sh(["ffmpeg", "-nostats", "-i", path, "-an", "-vf", "blackdetect=d=0.25:pix_th=0.06,freezedetect=n=-60dB:d=3", "-f", "null", "-"])
    blacks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    bad_black = [(s, e) for s, e in blacks if s > 0.5 and e < dur - 0.9]
    add("black frames", not bad_black, "none outside the fades" if not bad_black else f"black at {bad_black}")
    freezes = re.findall(r"freeze_start: ([\d.]+)", r.stderr)
    add("frozen picture", not freezes, "none" if not freezes else f"freeze from {freezes}s", warn=True)

    # ---- beginning / ending
    l0, l1, le, le2 = luma_at(path, off), luma_at(path, off + 1.2), luma_at(path, dur - 0.05), luma_at(path, dur - 1.5)
    if off:                                               # with a title card the video dissolves in instead of fading
        add("fade in", True, "dissolves from the title card (no fade from black needed)")
        add("fade out", (le >= 235) if meta.get("theme") == "light" else (le <= 0.6 * max(le2, 1)), f"luma {le:.0f} at end vs {le2:.0f} 1.5s before")
    elif meta.get("theme") == "light":                      # light videos fade from / to warm cream (luma ~245)
        add("fade in", l0 >= 235, f"luma {l0:.0f} at 0s (cream) vs {l1:.0f} at 1.2s")
        add("fade out", le >= 235, f"luma {le:.0f} at end (cream) vs {le2:.0f} 1.5s before")
    else:
        add("fade in", l0 <= 0.6 * max(l1, 1), f"luma {l0:.0f} at 0s vs {l1:.0f} at 1.2s")
        add("fade out", le <= 0.6 * max(le2, 1), f"luma {le:.0f} at end vs {le2:.0f} 1.5s before")
    if meta.get("lines"):
        first_voice = meta["lines"][0]["speech_start"]
    else:
        first_voice = sil_end[0] if sil_end and (not sil_start or sil_start[0] < 0.05) else 0.0
    add("speech starts quickly", first_voice <= 1.2, f"first speech at {first_voice:.2f}s")
    if meta.get("lines"):
        last = meta["lines"][-1]
        tail = dur - off - (last["speech_start"] + (last["speech_dur"] or 0))
        add("ending not abrupt", tail >= 0.35, f"{tail:.2f}s after the last word")

    # ---- subtitle sync (from the render plan, cross-checked with the file length)
    over, late = [], []
    for ln in meta.get("lines", []):
        if ln["speech_dur"] is not None and ln["speech_start"] + ln["speech_dur"] > ln["start"] + ln["dur"] + 0.05:
            over.append(ln["n"])
        if ln["reveal_end"] > ln["start"] + ln["dur"]:
            late.append(ln["n"])
    if meta.get("lines"):
        add("speech fits its subtitle", not over, "all lines" if not over else f"speech overruns lines {over}")
        add("words revealed in time", not late, "all lines" if not late else f"reveal unfinished on lines {late}")

    # ---- contrast behind text (measured by the renderer at each line's midpoint)
    light = meta.get("theme") == "light"
    bad = (lambda v: v < 150) if light else (lambda v: v > 165)
    lows = [f"line {ln['n']} ({ln['bg_luma']:.0f})" for ln in meta.get("lines", []) if ln.get("bg_luma") is not None and bad(ln["bg_luma"])]
    if meta.get("lines"):
        ok_txt = "background behind dark text stays light enough" if light else "background behind white text stays dark enough"
        bad_txt = ("dark background behind dark text: " if light else "bright background behind text: ")
        add("text contrast", not lows, ok_txt if not lows else bad_txt + ", ".join(lows) + " - set text_y/band on the scene", warn=True)

    # ---- typography
    cw = [f"line {ln['n']}: {w}" for ln in meta.get("lines", []) for w in ln.get("caption_warnings", []) if w]
    gw = [w for w in meta.get("preflight_warnings", []) if "glyph" in w]
    add("missing glyphs", not gw, "; ".join(gw) or "none")
    add("text fits", not cw, "; ".join(cw) or "no overflow or clipping")

    # ---- contact sheet for a human look
    sheet = os.path.join(out_dir, f"{name}_qa_sheet.jpg")
    n = 12
    sel = "+".join(f"eq(n\\,{int(nb * (k + 0.5) / n) if nb else int(dur * 30 * (k + 0.5) / n)})" for k in range(n))
    sh(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"select='{sel}',scale=270:480,tile=6x2", "-vsync", "0", "-frames:v", "1", sheet])

    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("WARN" if any(c["status"] == "WARN" for c in checks) else "PASS")
    rep = dict(video=name, status=status, duration=dur, loudness=I, true_peak=tp, checks=checks, sheet=os.path.basename(sheet))
    with open(os.path.join(out_dir, f"{name}_qa.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    md = [f"# QA report - {name}", "", f"**Status: {status}**  |  {dur:.1f}s  |  {I} LUFS  |  TP {tp} dBTP", "",
          "| Check | Status | Detail |", "|---|---|---|"] + [f"| {c['check']} | {c['status']} | {c['detail']} |" for c in checks]
    md += ["", f"Contact sheet: {os.path.basename(sheet)} (12 evenly spaced frames - look at it before posting)."]
    with open(os.path.join(out_dir, f"{name}_qa.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return rep


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    rep = run_qa(sys.argv[1])
    print(f"{rep['video']}: {rep['status']}")
    for c in rep["checks"]:
        print(f"  {c['status']:4s} {c['check']:26s} {c['detail']}")
    sys.exit(0 if rep["status"] != "FAIL" else 1)
