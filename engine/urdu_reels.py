#!/usr/bin/env python3
"""
urdu_reels.py - Urdu Islamic reminder Reels/Shorts in an animated-anime style.
One 1080x1920 master works for TikTok, Instagram Reels, YouTube Shorts and Facebook Reels.

    python urdu_reels.py                  # renders the built-in video
    python urdu_reels.py videos.json      # batch: every video in the file
    python urdu_reels.py videos_en.json   # English version ("lang": "en": English voice, subtitles, captions)

Each video produces in ./output/<name>/:
    <name>.mp4            master (H.264 High, AAC 48 kHz, -14 LUFS) - upload to all four platforms
    <name>_cover.jpg      cover / thumbnail (1080x1920)
    <name>_captions.txt   title, caption and hashtags per platform

videos.json:
{"videos": [{
   "name": "allah_sab_janta_hai",
   "title": "اللہ سب جانتا ہے",               # cover + YouTube title
   "caption": "...", "hashtags": ["#islamicreminder", ...],
   "lines": [
      {"text": "<Urdu shown on screen>", "say_hi": "<same sentence in Devanagari; *stress* and | pause marks>",
       "mood": "soft",                      # neutral | question | soft | heavy | hope | firm
       "say_ur": "<optional Urdu for the edge voice>", "scene": "sea"},
      {"text": "<Arabic ayah>", "font": "arabic", "sub": "<Urdu translation shown small>",
       "say_hi": "<translation to speak>", "hold": 4.0, "scene": "mosque"}
   ]}]}
Scenes: sea, rain, town, forest, room, meadow, mosque

Voice engines (VOICE_ENGINE):
  "kokoro" - natural offline neural voice (default). Reads "say_hi" (spoken Urdu written in
             Devanagari). Model (~120 MB) downloads once from GitHub.
  "edge"   - Microsoft ur-PK neural voice reading Urdu script directly (needs internet).
  "clips"  - per-line clips from another TTS, e.g. the Urdu Tortoise model (urdu_tortoise_colab.ipynb):
             put them in clips/<video name>/line_01.wav, line_02.wav, ...
  "file"   - YOUR OWN RECORDING: read the lines in order with a short pause between them,
             set VOICE_FILE, and the script splits it and syncs every line automatically.

pip install numpy pillow kokoro-onnx edge-tts      (+ ffmpeg on PATH)
"""
import os, re, sys, json, math, asyncio, subprocess, shutil, tempfile, wave, urllib.request, tarfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, features

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scenes import SCENES, smooth  # noqa: E402
from scenes_topics import TOPIC_SCENES  # noqa: E402
from scenes_explainer import EXPLAINER_SCENES  # noqa: E402
from scenes_batch2 import BATCH2  # noqa: E402
from scenes_light import LIGHT_SCENES  # noqa: E402
SCENES.update(TOPIC_SCENES)
SCENES.update(EXPLAINER_SCENES)
SCENES.update(BATCH2)
SCENES.update(LIGHT_SCENES)

# ============================== CONFIG ==============================
W, H, FPS = 1080, 1920, 30
TEXT_Y = int(H * 0.585)          # subtitle centre; clear of TikTok/Reels UI at the bottom and top
TEXT_MAXW = 860                  # keeps text away from the right-hand icon column
URDU_SIZE, ARABIC_SIZE, SUB_SIZE = 70, 78, 38
GOLD_WORDS = ["اللہ", "اللّٰہ", "رب", "اللَّه", "ﷲ"]   # words drawn in soft gold
GOLD_WORDS_EN = ["allah"]                               # English: any word starting with these

# English videos ("lang": "en" in videos.json)
FONT_EN = os.path.join(HERE, "fonts", "Lora.ttf")
FONT_EN_IT = os.path.join(HERE, "fonts", "Lora-Italic.ttf")
EN_SIZE, EN_SUB_SIZE = 68, 40
EN_WEIGHT = 600                  # Lora weight for English lines (400 regular ... 700 bold)
LABEL_SIZE, LABEL_COLOR = 30, (120, 210, 180)
# Colour themes. A scene declares `theme = "light"` or "dark" (default dark); a script may override with "theme".
# Light = soft cream/sky/sage backgrounds with dark ink text, deep-gold highlights and a cream glow behind the words.
THEMES = {
    "dark": dict(text=(255, 255, 250), gold=(255, 222, 150), stroke=(20, 16, 12, 120), stroke0=(16, 12, 8, 235),
                 halo=(0, 0, 0), halo_a=0.9, sub=(236, 230, 214), sub_stroke=(14, 12, 10, 190), label=(120, 210, 180),
                 label_stroke=(8, 14, 14, 200), tag=(255, 255, 255, 150), band=(0, 0, 0),
                 cover_text=(255, 222, 150), cover_stroke=(30, 20, 10), cover_shade=(0, 0, 0)),
    "light": dict(text=(40, 36, 48), gold=(168, 104, 14), stroke=(255, 252, 244, 170), stroke0=(255, 251, 240, 235),
                  halo=(255, 251, 242), halo_a=0.85, sub=(84, 74, 70), sub_stroke=(255, 251, 242, 200), label=(32, 128, 108),
                  label_stroke=(255, 251, 242, 220), tag=(70, 62, 74, 160), band=(255, 251, 242),
                  cover_text=(150, 92, 10), cover_stroke=(255, 250, 238), cover_shade=(255, 250, 240)),
}
THEME = "dark"
THUMB_ON = True
THUMB_DUR, THUMB_XF = 0.30, 0.25   # title card at the very start (platforms use frame 1 as the default cover), then a dissolve


def TH(k):
    return THEMES[THEME][k]
SECOND_SCALE, SECOND_GAP = 0.62, 14
TEXT_ZONE = (0.165, 0.78)              # default safe zone for subtitles (below the channel tag, above platform UI)
FIT_SCALES = (1.0, 0.9, 0.8, 0.72)     # captions shrink in these steps until the block fits the scene's text_zone   # bilingual second line ("text2"): size relative to main text, gap in px
RUN_QA = True                          # inspect every exported video (qa.py) and log it   # small caps label above a line ("label" in videos.json)
EN_VOICE, EN_LANG = "am_michael", "en-us"   # also good: "am_fenrir", "bm_george" (with EN_LANG "en-gb")
EN_SPEED = 1.06
# English voice engine: "edge" = Microsoft en-US-AndrewNeural (needs internet; falls back to kokoro if unreachable)
EN_ENGINE = "edge"
EN_EDGE_VOICE = "en-US-AndrewNeural"
EN_EDGE_RATE = -16               # percent, like rate="-16%"; moods speed this up/down around it
# Arabic/Islamic words the English voice gets wrong -> phonemes (word lowercase without punctuation)
PRON_EN = {"rahman": "ɹɑːmˈɑːn", "ya": "jˈɑː", "hadith": "hɐdˈiːθ", "qudsi": "kˈʊdsi", "allah": "ɑlˈlɑː", "allah's": "ɑlˈlɑːz", "dua": "dˈuːɑː", "duas": "dˈuːɑːz",
           "sujood": "sʊdʒˈuːd", "quran": "kʊɹˈɑːn", "sabr": "sˈʌbɚ", "deen": "dˈiːn",
           "jannah": "dʒˈænnɑː", "tawakkul": "tɐwˈækkʊl", "alhamdulillah": "ɐlhˈæmdʊlɪllˌɑː"}
DEFAULT_LANG = "ur"              # used when a video doesn't set "lang" ("ur" or "en")
LANG = DEFAULT_LANG               # voice language of the video being rendered (set per video)
TEXT_LANG = DEFAULT_LANG          # on-screen text language (set per video; may differ from LANG)
CHANNEL_TAG = "@YOUNGSPEEDISLAM"  # small handle near the top; "" to hide

FONT_URDU = os.path.join(HERE, "fonts", "NotoNastaliqUrdu.ttf")
FONT_ARABIC = os.path.join(HERE, "fonts", "Amiri-Regular.ttf")
FONT_EMOJI = os.path.join(HERE, "fonts", "NotoColorEmoji.ttf")      # colour emoji (CBDT, drawn at 109 px and scaled)
ARABIC_TOP_SCALE, ARABIC_TOP_GAP = 0.62, 10   # optional "text0": the Arabic wording shown above the English line
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2764\u231A\u231B\u23E9-\u23FA\uFE0F\u200D]+")
FONT_URLS = {
    FONT_URDU: "https://raw.githubusercontent.com/google/fonts/main/ofl/notonastaliqurdu/NotoNastaliqUrdu%5Bwght%5D.ttf",
    FONT_ARABIC: "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf",
    FONT_EN: "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora%5Bwght%5D.ttf",
    FONT_EN_IT: "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora-Italic%5Bwght%5D.ttf",
}

VOICE_ENGINE = "kokoro"          # "kokoro" | "edge" | "file" | "clips"
KOKORO_VOICE = "hm_omega"        # male; "hm_psi" (male), "hf_alpha"/"hf_beta" (female)
KOKORO_SPEED = 1.28
KOKORO_DIR = os.path.join(HERE, "voices", "kokoro")
KOKORO_FILES = {
    "kokoro-v1.0.int8.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
EDGE_VOICE, EDGE_RATE = "ur-PK-AsadNeural", "+0%"
VOICE_FILE = ""                  # for VOICE_ENGINE="file": path to your recording (wav/mp3/m4a)
# VOICE_ENGINE="clips": one ready-made clip per line, e.g. from the Urdu Tortoise Colab notebook:
#   <CLIPS_DIR>/<video name>/line_01.wav, line_02.wav, ...   (moods still adjust pitch/loudness)
CLIPS_DIR = os.path.join(HERE, "clips")
CLIPS_TEMPO = 1.0                # speed up/slow down the clips without changing pitch (e.g. 1.1)
CLIP_MOOD_PITCH = True           # moods shift the pitch of clips; set False (or spec "clip_mood_pitch": false) for cloned voices
# Per video, the spec may override: "voice_engine": "clips", "clips_dir": "clips" (relative to this folder),
# "clips_tempo": 1.0, "clip_mood_pitch": false.  Urdu cloned voice (OmniVoice relay): see skill/ENGINE_NOTES.md.
_VOICE_DEFAULTS = None

# Emotional delivery (kokoro). Each line can set "mood"; inside "say_hi" use
#   |        a dramatic pause         *word*   a stressed word (slower, warmer, louder)
MOODS = {   # speed x KOKORO_SPEED, pitch in semitones, gain dB, tail = dB fade over the last 0.6 s
    "neutral":  dict(speed=1.00, pitch=0.0,  gain=0.0,  tail=0),
    "question": dict(speed=1.00, pitch=0.7,  gain=0.5,  tail=0),
    "soft":     dict(speed=0.98, pitch=-0.5, gain=-2.5, tail=-3),
    "heavy":    dict(speed=0.96, pitch=-1.0, gain=-3.0, tail=-4),
    "hope":     dict(speed=1.04, pitch=0.6,  gain=1.5,  tail=0),
    "firm":     dict(speed=1.00, pitch=0.2,  gain=2.5,  tail=0),
}
STRESS = dict(speed=0.92, pitch=0.6, gain=2.0, gap=0.06)
PAUSE_DRAMATIC = 0.20
MAX_PAUSES = 1                   # dramatic '|' pauses honoured per line (extra ones are ignored)
STRESS_SPLIT = False             # True = synthesise *stressed* words as their own chunk (choppier, more dramatic)
BREATHS = True
BREATH_DB = -30

AMBIENCE_DB = -21                # scene ambience level under the voice
WHOOSH_DB = -24
# Cinematic sound design (no instruments, no melody): low drone bed, impacts, risers, heartbeat.
# Script: "sfx": "dramatic" (default) | "calm" (drone + soft whooshes only) | "off"; per line "sfx": "hit" | "rise" | "heart" | "none".
SFX_MODE = "dramatic"
DRONE_DB, HIT_DB, RISE_DB, HEART_DB = -27, -13, -21, -20
STEPS_DB, SOIL_DB = -15, -17       # story cues: "sfx": "steps" | "soil"
SFX_MIN_GAP = 4.0                # seconds between automatic impacts
BGM_FILE, BGM_DB = "", -20       # optional vocals-only nasheed
TARGET_LUFS = -14
CRF, PRESET = 18, "veryfast"
OUT_ROOT = os.path.join(HERE, "output")
SR = 48000

TRANSITIONS = ["fade", "leak", "blur", "fade", "dip"]
MOVES = ["push", "rise", "drift_r", "pull", "drift_l", "sink"]

DEFAULT_VIDEOS = {"videos": [{
    "name": "allah_sab_janta_hai",
    "title": "اللہ سب جانتا ہے",
    "title_en": "Allah Knows What You're Going Through",
    "caption": "وہ آنسو بھی جانتا ہے جو آپ نے سب سے چھپا لیے… اپنا ہر معاملہ اللہ کے سپرد کر دیں 🤍",
    "hashtags": ["#islamicreminder", "#islamicstatus", "#deenoverdunya", "#urduquotes", "#allah", "#dua", "#tawakkul", "#muslim"],
    "lines": [
        {"text": "اللہ سے بہتر کون جانتا ہے؟", "say_hi": "*अल्लाह* से बेहतर | कौन जानता है?", "mood": "question", "scene": "sea"},
        {"text": "کہ آپ کے دل پر کیا گزر رہی ہے", "say_hi": "कि आपके दिल पर | क्या गुज़र रही है।", "mood": "soft", "scene": "rain"},
        {"text": "وہ آنسو بھی جانتا ہے", "say_hi": "वो *आँसू* भी जानता है,", "mood": "heavy", "scene": "town"},
        {"text": "جو آپ نے سب سے چھپا لیے", "say_hi": "जो आपने | सब से छुपा लिए।", "mood": "heavy", "scene": "town"},
        {"text": "وہ دعا بھی سنتا ہے", "say_hi": "वो *दुआ* भी सुनता है,", "mood": "soft", "scene": "room"},
        {"text": "جو زبان تک نہیں آئی", "say_hi": "जो ज़बान तक | नहीं आई।", "mood": "soft", "scene": "room"},
        {"text": "لوگ نہ سمجھیں تو کوئی بات نہیں", "say_hi": "लोग न समझें, | तो कोई बात नहीं।", "mood": "neutral", "scene": "forest"},
        {"text": "اللہ تو سمجھتا ہے", "say_hi": "*अल्लाह* तो समझता है!", "mood": "hope", "scene": "forest"},
        {"text": "بس سجدے میں سر جھکا دیں", "say_hi": "बस | सजदे में सर झुका दें,", "mood": "soft", "scene": "meadow"},
        {"text": "اور اپنا ہر معاملہ اس کے سپرد کر دیں", "say_hi": "और अपना हर मामला | उसके सुपुर्द कर दें।", "mood": "firm", "scene": "sea"},
        {"text": "وَأُفَوِّضُ أَمْرِي إِلَى اللَّهِ", "font": "arabic",
         "sub": "اور میں اپنا معاملہ اللہ کے سپرد کرتا ہوں (غافر ۴۴)",
         "say_ur": "اور میں اپنا معاملہ اللہ کے سپرد کرتا ہوں", "say_hi": "और मैं अपना मामला | *अल्लाह* के सुपुर्द करता हूँ।",
         "mood": "soft", "hold": 3.0, "scene": "mosque"},
    ]}]}


# ============================== SETUP ==============================
def fetch(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("  downloading", os.path.basename(path))
    urllib.request.urlretrieve(url, path)


def ensure_assets():
    for p, u in FONT_URLS.items():
        if not os.path.exists(p):
            fetch(u, p)
    if VOICE_ENGINE == "kokoro":
        for f, u in KOKORO_FILES.items():
            if not os.path.exists(os.path.join(KOKORO_DIR, f)):
                fetch(u, os.path.join(KOKORO_DIR, f))
    if not features.check("raqm"):
        print("WARNING: Pillow lacks libraqm - Urdu letters will not join. Reinstall Pillow from the official wheels.")


# ============================== AUDIO ==============================
def load_audio(path, sr=SR):
    tmp = path + ".dec.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", str(sr), "-ac", "1", tmp], check=True)
    with wave.open(tmp) as wf:
        a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return a


def save_wav(path, x, sr=SR, ch=1):
    x = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(x.tobytes())


def trim(x, th=0.012, pre=0.03, post=0.08):
    idx = np.where(np.abs(x) > th)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(pre * SR)), min(len(x), idx[-1] + int(post * SR))
    return x[a:b]


_KOKORO = None
_EDGE_DOWN = False


def tts_edge_en(text, tmp, tag, rel_speed):
    import edge_tts
    rate = int(round(((1 + EN_EDGE_RATE / 100) * rel_speed - 1) * 100))
    p = os.path.join(tmp, f"ee{tag}.mp3")
    asyncio.run(edge_tts.Communicate(text, EN_EDGE_VOICE, rate=f"{rate:+d}%").save(p))
    return load_audio(p)


VOICE_USED = set()


def tts_kokoro(text, tmp, tag, speed=None):
    global _KOKORO, _EDGE_DOWN
    if LANG == "en" and EN_ENGINE == "edge" and not _EDGE_DOWN:
        try:
            a = tts_edge_en(text, tmp, tag, (speed or EN_SPEED) / EN_SPEED)
            VOICE_USED.add(f"edge:{EN_EDGE_VOICE} rate {EN_EDGE_RATE:+d}%")
            return a
        except Exception as e:
            _EDGE_DOWN = True
            print(f"  edge voice unavailable ({type(e).__name__}); using kokoro {EN_VOICE} instead")
    from kokoro_onnx import Kokoro
    if _KOKORO is None:
        _KOKORO = Kokoro(os.path.join(KOKORO_DIR, "kokoro-v1.0.int8.onnx"), os.path.join(KOKORO_DIR, "voices-v1.0.bin"))
    VOICE_USED.add(f"kokoro:{EN_VOICE if LANG == 'en' else KOKORO_VOICE}")
    if LANG == "en":
        ph = en_phonemes(text)
        s, sr = _KOKORO.create(ph, voice=EN_VOICE, speed=speed or EN_SPEED, lang=EN_LANG, is_phonemes=True)
    else:
        s, sr = _KOKORO.create(text, voice=KOKORO_VOICE, speed=speed or KOKORO_SPEED, lang="hi")
    p = os.path.join(tmp, f"k{tag}.wav"); save_wav(p, np.asarray(s), sr)
    return load_audio(p)


def en_phonemes(text):
    """Phonemise English as whole phrases (natural connected speech), swapping in fixed
    pronunciations only for the Arabic/Islamic words listed in PRON_EN."""
    toks = re.split(r"([\w']+)", text)
    out, buf = [], ""

    def flush():
        nonlocal buf
        if buf.strip():
            ph = _KOKORO.tokenizer.phonemize(buf, EN_LANG).strip()
            if not re.search(r"[.?!]\s*$", buf):
                ph = ph.rstrip(" .")          # the phonemiser adds a full stop to every chunk
            out.append(ph)
        buf = ""

    for tk in toks:
        if tk.lower() in PRON_EN:
            flush()
            out.append(PRON_EN[tk.lower()])
        else:
            buf += tk
    flush()
    ph = " ".join(o for o in out if o)
    ph = re.sub(r"\s+([,.?!;:])", r"\1", ph)
    return re.sub(r"\s+", " ", ph).strip()


def pitch_shift(x, semitones, tmp, tag):
    """Shift pitch, keep duration (asetrate + atempo)."""
    if abs(semitones) < 0.05:
        return x
    r = 2 ** (semitones / 12)
    a, b = os.path.join(tmp, f"p{tag}.wav"), os.path.join(tmp, f"q{tag}.wav")
    save_wav(a, x)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                    f"asetrate={int(SR * r)},aresample={SR},atempo={1 / r:.5f}", b], check=True)
    return load_audio(b)


def edge_fade(x, ms=6):
    n = min(len(x) // 2, int(ms / 1000 * SR))
    if n > 0:
        x = x.copy(); x[:n] *= np.linspace(0, 1, n); x[-n:] *= np.linspace(1, 0, n)
    return x


def parse_delivery(text):
    """'*word*' = stressed word, '|' = dramatic pause.  -> [(text, stressed) | ('|', False)]"""
    out = []
    for k, seg in enumerate(text.split("|")):
        if k:
            out.append(("|", False))
        for p in re.split(r"(\*[^*]+\*)", seg):
            p = p.strip()
            if p:
                out.append((p.strip("*").strip(), p.startswith("*")))
    # a tiny unstressed lead-in ("वो", "कि") is spoken together with the stressed word that follows
    merged = []
    for txt, st in out:
        if merged and st and not merged[-1][1] and merged[-1][0] != "|" and len(merged[-1][0]) <= 3:
            merged[-1] = (merged[-1][0] + " " + txt, True)
        else:
            merged.append((txt, st))
    return merged


def say_text(ln):
    if LANG == "en":
        return ln.get("say") or ln["text"]
    return ln.get("say_hi")


def plan_chunks(text, one_call=False):
    """Turn a spoken line with | and *marks* into as few TTS calls as possible.
    one_call=True (edge/Andrew): the whole line in one request, | -> comma pause.
    Kokoro: split only at the first MAX_PAUSES '|'; *stress* stays inside its phrase unless STRESS_SPLIT."""
    if one_call:
        t = re.sub(r"\s*\|\s*", ", ", text.replace("*", ""))
        t = re.sub(r"([,.?!;:\u0964])\s*,", r"\1", t)
        return [(re.sub(r"\s+([,.?!;:])", r"\1", t).strip(), False)]
    out, n_pause = [], 0
    for txt, st in parse_delivery(text):
        if txt == "|":
            if n_pause < MAX_PAUSES and out:
                out.append(("|", False)); n_pause += 1
            continue
        if not STRESS_SPLIT and out and out[-1][0] != "|":
            sep = "" if re.match(r"[,.?!;:\u0964]", txt) else " "
            out[-1] = (out[-1][0] + sep + txt, False)
        else:
            out.append((txt, bool(st and STRESS_SPLIT)))
    return out


def speak_emotive(ln, tmp, i):
    """Synthesise one line with its mood + pause marks. Returns (audio, chunk_map)."""
    m = MOODS.get(ln.get("mood", "neutral"), MOODS["neutral"])
    base = EN_SPEED if LANG == "en" else KOKORO_SPEED          # English and Urdu keep separate base speeds
    one_call = LANG == "en" and EN_ENGINE == "edge" and not _EDGE_DOWN
    chunks = plan_chunks(say_text(ln), one_call)
    parts, cmap, pos = [], [], 0
    spoken = [c for c in chunks if c[0] != "|"]
    for k, (txt, stressed) in enumerate(chunks):
        if txt == "|":
            gap = np.zeros(int(PAUSE_DRAMATIC * SR)); parts.append(gap); pos += len(gap); continue
        last = txt is spoken[-1][0]
        say = txt
        if not last and not re.search(r"[,.?!;:\u0964]$", say):
            say += ","                                            # keep the voice "continuing" across a pause
        sp = base * m["speed"] * (STRESS["speed"] if stressed else 1)
        a = trim(tts_kokoro(say, tmp, f"{i}_{k}", sp), pre=0.015, post=0.04)
        a = pitch_shift(a, m["pitch"] + (STRESS["pitch"] if stressed else 0), tmp, f"{i}_{k}")
        a = edge_fade(a) * db(m["gain"] + (STRESS["gain"] if stressed else 0))
        cmap.append((pos / SR, len(a) / SR, len(txt.replace("*", ""))))
        parts.append(a); pos += len(a)
        if stressed:
            g = np.zeros(int(STRESS["gap"] * SR)); parts.append(g); pos += len(g)
    x = np.concatenate(parts)
    if m.get("tail", 0):                                          # soft lines trail off, firm lines hold
        n = min(len(x), int(0.6 * SR))
        x[-n:] *= np.linspace(1, db(m["tail"]), n)
    return x, cmap


def tts_edge(text, tmp, i):
    import edge_tts
    p = os.path.join(tmp, f"e{i}.mp3")
    asyncio.run(edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE).save(p))
    return load_audio(p)


def split_recording(path, n):
    """Split one recording into n phrases at the n-1 longest pauses."""
    x = load_audio(path)
    hop = int(0.02 * SR)
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    th = max(0.01, np.percentile(rms, 95) * 0.08)
    on = rms > th
    segs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or (j + 12 < len(on) and on[j:j + 12].any())):
                j += 1
            segs.append([i, j]); i = j
        else:
            i += 1
    while len(segs) > n:
        gaps = [segs[k + 1][0] - segs[k][1] for k in range(len(segs) - 1)]
        k = int(np.argmin(gaps)); segs[k][1] = segs[k + 1][1]; del segs[k + 1]
    if len(segs) < n:
        print(f"  WARNING: found {len(segs)} phrases in the recording but there are {n} lines; leave a clear pause between lines.")
    clips = [x[max(0, a * hop - int(0.05 * SR)): b * hop + int(0.1 * SR)] for a, b in segs]
    return clips + [None] * (n - len(clips))


def load_clips(lines, tmp, name):
    """Per-line clips made elsewhere (e.g. Urdu Tortoise in Colab); mood pitch/gain/tail still applied."""
    out = []
    for i, ln in enumerate(lines):
        p = os.path.join(CLIPS_DIR, name, f"line_{i + 1:02d}.wav")
        if not os.path.exists(p):
            print(f"  missing {p} - line {i + 1} left silent"); out.append(None); continue
        a = trim(load_audio(p))
        if abs(CLIPS_TEMPO - 1) > 0.01:
            q = os.path.join(tmp, f"t{i}.wav"); save_wav(q, a)
            r = os.path.join(tmp, f"u{i}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", q, "-af", f"atempo={CLIPS_TEMPO}", r], check=True)
            a = load_audio(r)
        m = MOODS.get(ln.get("mood", "neutral"), MOODS["neutral"])
        if CLIP_MOOD_PITCH:
            a = pitch_shift(a, m["pitch"], tmp, f"c{i}")
        a = a * db(m["gain"])
        if m.get("tail", 0):
            n = min(len(a), int(0.6 * SR)); a[-n:] *= np.linspace(1, db(m["tail"]), n)
        out.append(edge_fade(a))
    return out


def make_voice(lines, tmp, name=""):
    """Returns (clips, chunk_maps). chunk_map = [(start_s, dur_s, n_chars), ...] or None."""
    if VOICE_ENGINE == "file":
        return split_recording(VOICE_FILE, len(lines)), [None] * len(lines)
    if VOICE_ENGINE == "clips":
        VOICE_USED.add(f"clips:{os.path.relpath(os.path.join(CLIPS_DIR, name), HERE)}")
        return load_clips(lines, tmp, name), [None] * len(lines)
    clips, maps = [], []
    for i, ln in enumerate(lines):
        c, cm = None, None
        if ln.get("speak", True):
            try:
                if VOICE_ENGINE == "edge":
                    c = trim(tts_edge(ln.get("say_ur", ln["text"]), tmp, i))
                elif say_text(ln):
                    c, cm = speak_emotive(ln, tmp, i)
                else:
                    print(f"  line {i + 1}: no say_hi text, left silent")
            except Exception as e:
                print(f"  voice failed on line {i + 1}: {e}")
        clips.append(c); maps.append(cm)
    return clips, maps


def breath(rng):
    """A soft synthetic inhale (~0.3 s) placed before new sentences."""
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / t[-1]) ** 1.5 * (0.6 + 0.4 * t / t[-1])
    x = shaped_noise(n, rng, 500, 2800, -0.2) * env
    return x / (np.abs(x).max() + 1e-9)


def fft_filter(x, gain_fn):
    n = 1 << (len(x) - 1).bit_length()
    X = np.fft.rfft(x, n)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(X * gain_fn(f), n)[: len(x)]


def db(v):
    return 10 ** (v / 20)


def voice_chain(v):
    """Warm, broadcast-style voice: EQ, gentle compression, short plate-like reverb."""
    def eq(f):
        hp = 1 / np.sqrt(1 + (75 / np.maximum(f, 1)) ** 4)
        warm = 1 + (db(2.5) - 1) * np.exp(-((np.log2(np.maximum(f, 1) / 180)) ** 2) / 0.8)
        mud = 1 + (db(-2) - 1) * np.exp(-((np.log2(np.maximum(f, 1) / 420)) ** 2) / 0.4)
        pres = 1 + (db(2) - 1) * np.exp(-((np.log2(np.maximum(f, 1) / 3200)) ** 2) / 0.6)
        air = 1 + (db(-3) - 1) / (1 + (9000 / np.maximum(f, 1)) ** 2)
        return hp * warm * mud * pres * air
    v = fft_filter(v, eq)
    win = int(0.012 * SR)
    env = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, "same")) + 1e-6
    th = np.percentile(env[env > 1e-3], 80) * 0.6 if (env > 1e-3).any() else 0.1
    g = np.where(env > th, (env / th) ** (1 / 3.0 - 1), 1.0)
    g = np.convolve(g, np.ones(int(0.03 * SR)) / int(0.03 * SR), "same")
    v = v * g
    rng = np.random.default_rng(11)
    n = int(1.1 * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.16 * SR))
    ir[: int(0.028 * SR)] = 0
    ir = fft_filter(ir, lambda f: 1 / (1 + (f / 5000) ** 2) / np.sqrt(1 + (300 / np.maximum(f, 1)) ** 2))
    m = len(v) + n; nf = 1 << (m - 1).bit_length()
    rev = np.fft.irfft(np.fft.rfft(v, nf) * np.fft.rfft(ir, nf), nf)[: len(v)]
    rev *= np.abs(v).max() / (np.abs(rev).max() + 1e-9)
    return v + 0.16 * rev


def shaped_noise(n, rng, lo, hi, tilt=-0.5):
    f = np.fft.rfftfreq(n, 1 / SR)
    g = (np.maximum(f, 20) / 1000) ** tilt / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    x = np.fft.irfft(np.fft.rfft(rng.normal(0, 1, n)) * g, n)
    return x / (np.abs(x).max() + 1e-9)


def slow_env(n, rng, rate, lo=0.3):
    k = max(2, int(n / SR * rate) + 2)
    pts = rng.uniform(lo, 1, k)
    return np.interp(np.arange(n), np.linspace(0, n, k), pts)


def birds(n, rng, rate=0.5):
    out = np.zeros(n)
    t0 = 0.0
    while True:
        t0 += rng.exponential(1 / rate)
        if t0 * SR >= n - SR:
            break
        f0 = rng.uniform(2600, 4800); notes = rng.integers(2, 6); amp = rng.uniform(0.2, 0.6)
        for k in range(notes):
            L = int(rng.uniform(0.05, 0.12) * SR); s = int((t0 + k * rng.uniform(0.09, 0.16)) * SR)
            tt = np.arange(L) / SR
            sweep = f0 + rng.uniform(-1400, 1400) * tt / tt[-1]
            ph = 2 * np.pi * np.cumsum(sweep) / SR
            sig = np.sin(ph + 0.6 * np.sin(2 * np.pi * 60 * tt)) * np.sin(np.pi * tt / tt[-1]) ** 2
            out[s:s + L] += sig[: max(0, n - s)] * amp
    return out


def crickets(n, rng):
    out = np.zeros(n)
    for carrier, period in ((4400, 0.55), (4900, 0.72)):
        t = np.arange(n) / SR
        pulses = ((t % period) < 0.12) * (np.sin(2 * np.pi * 32 * t) > 0.2)
        env = np.convolve(pulses.astype(float), np.ones(80) / 80, "same")
        out += np.sin(2 * np.pi * carrier * t) * env * rng.uniform(0.3, 0.5)
    return out


def drips(n, rng):
    out = np.zeros(n); t0 = 0.0
    while True:
        t0 += rng.exponential(1.6)
        i = int(t0 * SR)
        if i >= n - SR // 4:
            break
        L = int(0.08 * SR); tt = np.arange(L) / SR
        f = rng.uniform(900, 1600) * (1 + 2 * tt)
        out[i:i + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40) * rng.uniform(0.3, 0.7)
    return out


def thunder(n, rng):
    out = np.zeros(n); t0 = rng.uniform(0.5, 2)
    while t0 * SR < n - SR:
        L = int(rng.uniform(2.5, 4.5) * SR); i = int(t0 * SR)
        tt = np.arange(L) / SR
        env = (1 - np.exp(-tt * 8)) * np.exp(-tt * 1.1)
        x = shaped_noise(L, rng, 25, 300, -1.2) * env
        out[i:i + L] += x[: n - i] * rng.uniform(0.6, 1.0)
        t0 += rng.uniform(4, 8)
    return out


def ticks(n, rng):
    out = np.zeros(n)
    L = int(0.012 * SR); tt = np.arange(L) / SR
    for k, i in enumerate(range(int(0.3 * SR), n - L, SR // 2)):
        f = 3200 if k % 2 else 2500
        out[i:i + L] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 500)
    return out


def crackle(n, rng):
    out = np.zeros(n)
    idx = rng.integers(0, n - 200, int(n / SR * 6))
    for i in idx:
        out[i:i + 60] += rng.normal(0, 1, 60) * np.exp(-np.arange(60) / 10) * rng.uniform(0.2, 1)
    return out


def ambience(kind, n, rng):
    st = np.zeros((n, 2))
    for c in range(2):
        r = np.random.default_rng(rng.integers(1 << 30))
        if kind == "sea":
            env = slow_env(n, r, 0.25, 0.15) ** 1.5
            x = shaped_noise(n, r, 60, 1400, -0.9) * env + shaped_noise(n, r, 1500, 7000, 0) * env ** 2 * 0.25
            x += birds(n, r, 0.05) * 0.10
        elif kind in ("rain", "town"):
            x = shaped_noise(n, r, 300, 9000, -0.2) * 0.8 + shaped_noise(n, r, 40, 300, -0.5) * (0.35 if kind == "town" else 0.15)
        elif kind == "forest":
            x = shaped_noise(n, r, 250, 2500, -0.6) * slow_env(n, r, 0.3) * 0.5 + birds(n, r, 0.7) * 0.45
        elif kind == "room":
            x = shaped_noise(n, r, 40, 600, -0.8) * 0.15 + birds(n, r, 0.25) * 0.18
        elif kind == "meadow":
            x = shaped_noise(n, r, 200, 3000, -0.6) * slow_env(n, r, 0.35) * 0.6 + birds(n, r, 0.45) * 0.3
        elif kind == "wind_night":
            x = shaped_noise(n, r, 120, 1400, -0.8) * slow_env(n, r, 0.25, 0.2) * 0.7 + crickets(n, r) * 0.06
        elif kind == "earth":
            x = shaped_noise(n, r, 25, 220, -1.0) * 0.8 + drips(n, r) * 0.25
        elif kind == "heat":
            t_ = np.arange(n) / SR
            x = shaped_noise(n, r, 60, 900, -0.9) * slow_env(n, r, 0.3, 0.4) * 0.6 + (np.sin(2 * np.pi * 55 * t_) + np.sin(2 * np.pi * 55.7 * t_)) * 0.12
        elif kind == "storm_wind":
            x = shaped_noise(n, r, 80, 2000, -0.7) * slow_env(n, r, 0.5, 0.3) * 0.9
        elif kind == "storm":
            x = shaped_noise(n, r, 300, 9000, -0.2) * 0.5 + thunder(n, r) * 0.9
        elif kind == "clock":
            x = shaped_noise(n, r, 40, 500, -0.8) * 0.08 + ticks(n, r) * 0.7
        elif kind == "candle":
            x = shaped_noise(n, r, 40, 400, -0.8) * 0.10 + crackle(n, r) * 0.25
        elif kind == "autumn":
            x = shaped_noise(n, r, 150, 2500, -0.6) * slow_env(n, r, 0.5) * 0.7 + crackle(n, r) * 0.08
        elif kind == "night_room":
            x = shaped_noise(n, r, 40, 500, -0.8) * 0.12 + crickets(n, r) * 0.10
        elif kind == "storm_to_birds":
            e = np.clip(np.arange(n) / (n * 0.35), 0, 1)
            x = shaped_noise(n, r, 300, 9000, -0.2) * 0.5 * (1 - e) + birds(n, r, 0.5) * 0.4 * e
        else:  # night
            x = crickets(n, r) * 0.25 + shaped_noise(n, r, 100, 1500, -0.7) * slow_env(n, r, 0.2) * 0.25
        st[:, c] = x
    return st / (np.abs(st).max() + 1e-9)


def whoosh(rng):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 2 * np.exp(-t * 1.5)
    x = shaped_noise(n, rng, 200, 2500, -0.6) * env
    return x / (np.abs(x).max() + 1e-9)


def sfx_hit(rng):
    """Cinematic impact: low boom (pitch sweep 90->32 Hz) + noise transient + long dark tail."""
    n = int(2.6 * SR); t = np.arange(n) / SR
    f = 32 + 58 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    thump = shaped_noise(n, rng, 30, 180, -1.0) * np.exp(-t * 9) * 0.9
    crack = shaped_noise(n, rng, 800, 6000, -0.4) * np.exp(-t * 40) * 0.25
    tail = shaped_noise(n, rng, 40, 900, -0.9) * np.exp(-t * 1.3) * 0.25
    x = boom + thump + crack + tail
    return x / (np.abs(x).max() + 1e-9)


def sfx_rise(rng, dur=1.6):
    """Tension riser: band-passed noise sweeping up and swelling, cut at the end (the hit lands there)."""
    n = int(dur * SR); t = np.arange(n) / SR; k = t / dur
    lo = shaped_noise(n, rng, 200, 1200, -0.5); hi = shaped_noise(n, rng, 1500, 8000, -0.2)
    x = (lo * (1 - k) + hi * k) * k ** 2.2
    x[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return x / (np.abs(x).max() + 1e-9)


def sfx_heart(dur, rng, bpm=64):
    """Soft heartbeat (lub-dub) thumps for `dur` seconds."""
    n = int(dur * SR); x = np.zeros(n); per = 60.0 / bpm
    tb = np.arange(int(0.25 * SR)) / SR
    beat = np.sin(2 * np.pi * 52 * tb) * np.exp(-tb * 28)
    for k in range(int(dur / per) + 1):
        for off, a in ((0.0, 1.0), (0.22, 0.6)):
            i = int((k * per + off) * SR)
            if i < n:
                x[i:i + len(beat)] += (beat * a)[: n - i]
    return x / (np.abs(x).max() + 1e-9)


def sfx_steps(dur, rng, fade_out=True):
    """Footsteps on earth walking away: soft heel thud + gravel scuff, alternating, getting quieter."""
    n = int(dur * SR); x = np.zeros(n); per = 0.52
    tb = np.arange(int(0.18 * SR)) / SR
    for k in range(int(dur / per)):
        i = max(0, int((k * per + rng.uniform(-0.03, 0.03)) * SR))
        if i >= n:
            break
        thud = np.sin(2 * np.pi * rng.uniform(70, 95) * tb) * np.exp(-tb * 45)
        scuff = shaped_noise(len(tb), rng, 600, 4000, -0.3) * np.exp(-tb * 25) * 0.6
        g = (1 - k * per / dur * 0.85) if fade_out else 1.0
        s_ = (thud + scuff) * g * (0.9 if k % 2 else 1.0)
        x[i:i + len(s_)] += s_[: n - i]
    return x / (np.abs(x).max() + 1e-9)


def sfx_soil(dur, rng):
    """Earth falling onto the grave: dull shovel thuds with a gravel trickle."""
    n = int(dur * SR); x = shaped_noise(n, rng, 300, 3000, -0.4) * 0.08
    tb = np.arange(int(0.5 * SR)) / SR
    for k in range(int(dur / 0.7)):
        i = int((k * 0.7 + rng.uniform(0, 0.2)) * SR)
        if i >= n:
            break
        s_ = shaped_noise(len(tb), rng, 40, 400, -0.9) * np.exp(-tb * 10) + shaped_noise(len(tb), rng, 800, 5000, -0.2) * np.exp(-tb * 6) * 0.35
        x[i:i + len(s_)] += s_[: n - i]
    return x / (np.abs(x).max() + 1e-9)


def drama_bed(n, rng):
    """Non-tonal low drone: filtered rumble with slow swells and a little air on top."""
    st = np.zeros((n, 2))
    for c in range(2):
        r = np.random.default_rng(rng.integers(1 << 30))
        st[:, c] = shaped_noise(n, r, 25, 140, -1.0) * slow_env(n, r, 0.08, 0.5) + shaped_noise(n, r, 1500, 6000, -0.3) * slow_env(n, r, 0.1, 0.2) * 0.08
    return st / (np.abs(st).max() + 1e-9)


def sfx_plan(lines, starts, durs):
    """Where the cues go. Auto: riser + impact into Quran/hadith cards and 'heavy'/'firm' highlight lines,
    heartbeat under 'heavy' lines; per-line "sfx" overrides. Impacts are spaced at least SFX_MIN_GAP apart."""
    cues, last = [], -99.0
    for i, ln in enumerate(lines):
        want = ln.get("sfx")
        if want == "none":
            continue
        st = starts[i]
        card = ln.get("font") == "arabic"
        strong = ln.get("mood") in ("heavy", "firm") and "{" in ln.get("text", "")
        if want in ("hit", "rise") or (want is None and (card or strong) and st - last >= SFX_MIN_GAP and i > 0):
            cues.append(("rise", st - 1.6)); cues.append(("hit", st)); last = st
        if want == "heart" or (want is None and ln.get("mood") == "heavy" and not card):
            cues.append(("heart", st, durs[i]))
        if want in ("steps", "soil"):
            cues.append((want, st, durs[i]))
    return cues


def build_audio(clips, starts, shots, total, path, breaths=(), cues=()):
    n = int(total * SR) + SR
    voice = np.zeros(n)
    for c, st in zip(clips, starts):
        if c is not None:
            i = int(st * SR)
            voice[i:i + len(c)] += c[: max(0, n - i)]
    if len(breaths) and np.abs(voice).max() > 0:
        brng = np.random.default_rng(21); pk = np.abs(voice).max()
        for bt in breaths:
            b = breath(brng) * pk * db(BREATH_DB) * brng.uniform(0.7, 1.1); i = int(bt * SR)
            voice[i:i + len(b)] += b[: max(0, n - i)]
    if np.abs(voice).max() > 0:
        voice = voice_chain(voice)
        voice *= 0.8 / np.abs(voice).max()
    mix = np.repeat(voice[:, None], 2, 1)
    rng = np.random.default_rng(5)
    amb = np.zeros((n, 2))
    cache = {}
    xf = int(0.8 * SR)
    for k, sh in enumerate(shots):
        kind = sh["scene"].ambience
        if kind not in cache:
            cache[kind] = ambience(kind, n, rng)
        a, b = int(sh["start"] * SR), int(sh["end"] * SR)
        g = np.zeros(n)
        g[max(0, a - xf // 2):min(n, b + xf // 2)] = 1
        if k > 0:
            g[max(0, a - xf // 2):a + xf // 2] = np.linspace(0, 1, len(g[max(0, a - xf // 2):a + xf // 2]))
        if k < len(shots) - 1:
            seg = g[b - xf // 2:b + xf // 2]; g[b - xf // 2:b + xf // 2] = np.linspace(1, 0, len(seg))
        amb += cache[kind] * g[:, None]
    mix += amb * db(AMBIENCE_DB) * 0.8
    for sh in shots[1:]:
        w = whoosh(rng); i = int((sh["start"] - 0.3) * SR)
        if i > 0:
            mix[i:i + len(w)] += (w * db(WHOOSH_DB))[:, None][: n - i]
    if SFX_MODE != "off":                                 # sound design, ducked under the voice
        venv = np.abs(mix[:, 0]); k_ = int(0.25 * SR)
        venv = np.convolve(venv, np.ones(k_) / k_, mode="same"); venv = np.clip(venv / (venv.max() + 1e-9) * 3, 0, 1)
        duck = (1 - 0.55 * venv)[:, None]
        sfx = drama_bed(n, rng) * db(DRONE_DB)
        if SFX_MODE == "dramatic":
            for c in cues:
                if c[0] == "hit":
                    s_ = sfx_hit(rng) * db(HIT_DB)
                elif c[0] == "rise":
                    s_ = sfx_rise(rng) * db(RISE_DB)
                elif c[0] == "steps":
                    s_ = sfx_steps(c[2], rng) * db(STEPS_DB)
                elif c[0] == "soil":
                    s_ = sfx_soil(c[2], rng) * db(SOIL_DB)
                else:
                    s_ = sfx_heart(c[2], rng) * db(HEART_DB)
                i = int(max(0, c[1]) * SR)
                if i < n:
                    sfx[i:i + len(s_)] += s_[: n - i, None]
        mix += sfx * duck
    if BGM_FILE and os.path.exists(BGM_FILE):
        b = load_audio(BGM_FILE); b = np.tile(b, n // len(b) + 1)[:n]
        mix += b[:, None] * db(BGM_DB)
    end = int(total * SR)
    fade = np.ones(n); fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
    fade[end - int(0.6 * SR):end] = np.linspace(1, 0, int(0.6 * SR)); fade[end:] = 0
    mix = (mix * fade[:, None])[:end]
    raw = path + ".raw.wav"
    save_wav(raw, mix.reshape(-1) * 0.7, ch=2)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11", "-ar", str(SR), path], check=True)
    os.remove(raw)


# ============================== TEXT ==============================
def font(kind, size):
    return ImageFont.truetype(FONT_ARABIC if kind == "arabic" else FONT_URDU, size)


class Caption:
    """Pre-rendered subtitle that reveals word by word (right to left)."""

    def __init__(self, line, lang=None, scale=1.0, key="text"):
        lang = lang or TEXT_LANG
        primary = key == "text"
        self.lang, self.warnings = lang, []
        is_ar = (primary and line.get("font") == "arabic") or key == "text0"
        ltr = lang == "en" and not is_ar
        if ltr:
            f = ImageFont.truetype(FONT_EN, int(EN_SIZE * scale))
            try:
                f.set_variation_by_axes([EN_WEIGHT])
            except Exception:
                pass
            kw = dict(direction="ltr", language="en")
        else:
            f = font("arabic" if is_ar else "urdu", int((ARABIC_SIZE if is_ar else URDU_SIZE) * scale))
            kw = dict(direction="rtl", language="ar" if is_ar else "ur")
        sym = ImageFont.truetype(FONT_ARABIC, int(EN_SIZE * scale * 1.05))      # for ﷺ inside English lines

        emo_px = int(f.size * 1.05)
        self._emoji = {}

        def emoji_img(wd):
            if wd not in self._emoji:
                ef = ImageFont.truetype(FONT_EMOJI, 109)
                im = Image.new("RGBA", (int(ef.getlength(wd)) + 8, 136), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((4, 4), wd, font=ef, embedded_color=True)
                im = im.crop(im.getbbox() or (0, 0, 1, 1))
                self._emoji[wd] = im.resize((max(1, int(im.width * emo_px / max(1, im.height))), emo_px), Image.LANCZOS)
            return self._emoji[wd]

        def wlen(wd):
            if ltr and EMOJI_RE.fullmatch(wd):
                return emoji_img(wd).width
            if ltr and "ﷺ" in wd:                            # ﷺ may carry punctuation: "ﷺ." / "ﷺ,”"
                return sum(sym.getlength(p) if p == "ﷺ" else f.getlength(p, **kw) for p in re.split("(ﷺ)", wd) if p)
            return f.getlength(wd, **kw)

        def wrap(words, size_ok):
            rows, cur = [], []
            for wd in words:
                if cur and not size_ok(cur + [wd]):
                    rows.append(cur); cur = [wd]
                else:
                    cur.append(wd)
            rows.append(cur)
            return rows

        space = f.getlength(" ", **kw) if ltr else 0
        rowlen = (lambda r: sum(wlen(x) for x in r) + space * (len(r) - 1)) if ltr else (lambda r: f.getlength(" ".join(r), **kw))
        # {highlighted words} -> accent colour (same layer as gold)
        raw_words, hl, inside = line[key].split(), [], False
        words = []
        for wd in raw_words:
            start = wd.startswith("{")
            end = wd.endswith("}") or wd.rstrip(".,?!:;…”\"'").endswith("}")
            hl.append(inside or start)
            inside = (inside or start) and not end
            words.append(wd.replace("{", "").replace("}", ""))
        if key == "text0":
            hl = [True] * len(hl)                              # the Arabic wording is shown in gold
        self.hl_words = hl
        rows = wrap(words, lambda r: rowlen(r) <= TEXT_MAXW)
        size = int(ARABIC_SIZE * scale) if is_ar else None
        while is_ar and len(rows) > 2 and size > 44:          # long ayat: shrink instead of stacking 4+ rows
            size -= 6
            f = font("arabic", size)
            rows = wrap(words, lambda r: f.getlength(" ".join(r), **kw) <= TEXT_MAXW)
        self.h = 640
        # every row (and the label / sub block) is drawn on its OWN layer and revealed on its own,
        # so a revealed word can never uncover part of the row below it, and tall letters are never clipped
        self._layers = []

        def new_layer(kind):
            im = [Image.new("RGBA", (W, self.h), (0, 0, 0, 0)), Image.new("RGBA", (W, self.h), (0, 0, 0, 0)), Image.new("L", (W, self.h), 0)]
            self._layers.append(dict(kind=kind, imgs=im, words=[]))
            return ImageDraw.Draw(im[0]), ImageDraw.Draw(im[1]), ImageDraw.Draw(im[2])
        asc, desc = f.getmetrics()
        row_h = int((asc + desc) * (1.12 if ltr else 0.92))
        sub_rows, sub_f, sub_kw, sub_h = [], None, None, 0
        has_ur = lambda s_: bool(re.search(r"[\u0600-\u06FF]", s_ or ""))
        if primary and line.get("sub"):
            if not has_ur(line["sub"]):
                sub_f = ImageFont.truetype(FONT_EN_IT, int(EN_SUB_SIZE * max(scale, 0.8))); sub_kw = dict(direction="ltr", language="en")
            else:
                sub_f = font("urdu", int(SUB_SIZE * max(scale, 0.8))); sub_kw = dict(direction="rtl", language="ur")
            sub_rows = [" ".join(r) for r in wrap(line["sub"].split(), lambda r: sub_f.getlength(" ".join(r), **sub_kw) <= TEXT_MAXW)]
            sa, sd = sub_f.getmetrics()
            sub_h = int((sa + sd) * 1.15)
        lab = line.get("label") if primary else None
        lab_ur = has_ur(lab)
        lab_f = (font("urdu", int(LABEL_SIZE * 1.55)) if lab_ur else ImageFont.truetype(FONT_EN, LABEL_SIZE)) if lab else None
        if lab_f and not lab_ur:
            try:
                lab_f.set_variation_by_axes([700])
            except Exception:
                pass
        lab_h = int(LABEL_SIZE * (3.0 if lab_ur else 2.0)) if lab else 0
        total = lab_h + row_h * len(rows) + (sub_h * len(sub_rows) + 24 if sub_rows else 0)
        self.content_h = total
        for r in rows:
            if rowlen(r) > TEXT_MAXW + 2:
                self.warnings.append(f"word wider than the text area: {' '.join(r)[:40]}")
        if total > self.h - 30:
            self.warnings.append(f"text block {int(total)} px is taller than the caption canvas ({self.h} px) - will clip")
        if is_ar and size is not None and size <= 44 and len(rows) > 2:
            self.warnings.append("long ayah: still more than 2 rows at minimum size - consider splitting")
        y = self.h / 2 - total / 2
        self.label_box = None
        if lab:
            dW, dG, dS = new_layer("label")
            spaced = lab if lab_ur else " ".join(lab.upper())
            lkw = dict(direction="rtl", language="ur") if lab_ur else {}
            dW.text((W / 2, y + lab_h * 0.35), spaced, font=lab_f, fill=TH("label") + (255,), anchor="mm", stroke_width=3, stroke_fill=TH("label_stroke"), **lkw)
            dS.text((W / 2 + 2, y + lab_h * 0.35 + 3), spaced, font=lab_f, fill=200, anchor="mm", **lkw)
            self.label_box = (int(y - 10), int(y + lab_h))
            y += lab_h
        self.words = []
        order = 0
        stroke = dict(stroke_width=3, stroke_fill=TH("stroke0")) if key == "text0" else dict(stroke_width=2, stroke_fill=TH("stroke"))
        for r in rows:
            dW, dG, dS = new_layer("row")
            full = rowlen(r)
            right, left = W / 2 + full / 2, W / 2 - full / 2
            if ltr:
                x = left
                for wd in r:
                    L = wlen(wd)
                    if EMOJI_RE.fullmatch(wd):
                        em = emoji_img(wd)
                        ey = int(y + row_h * 0.50 - em.height / 2)
                        for im_ in self._layers[-1]["imgs"][:2]:
                            im_.alpha_composite(em, (int(x), max(0, ey)))
                    elif "ﷺ" in wd:
                        xx = x
                        for p in [p for p in re.split("(ﷺ)", wd) if p]:
                            for d_, fill in ((dW, TH("text") + (255,)), (dG, TH("gold") + (255,))):
                                if p == "ﷺ":
                                    d_.text((xx, y + row_h * 0.62), p, font=sym, fill=fill, anchor="ls")
                                else:
                                    d_.text((xx, y), p, font=f, fill=fill, anchor="la", **stroke, **kw)
                            if p == "ﷺ":
                                dS.text((xx + 3, y + row_h * 0.62 + 5), p, font=sym, fill=235, anchor="ls")
                            else:
                                dS.text((xx + 3, y + 5), p, font=f, fill=235, anchor="la", **kw)
                            xx += sym.getlength(p) if p == "ﷺ" else f.getlength(p, **kw)
                    else:
                        for d_, fill in ((dW, TH("text") + (255,)), (dG, TH("gold") + (255,))):
                            d_.text((x, y), wd, font=f, fill=fill, anchor="la", **stroke, **kw)
                        dS.text((x + 3, y + 5), wd, font=f, fill=235, anchor="la", **kw)
                    is_gold = any(re.sub(r"[^\w']", "", wd.lower()).startswith(g) for g in GOLD_WORDS_EN) or wd == "ﷺ" or self.hl_words[order]
                    self.words.append([x - 4, x + L + 14, 0, self.h, order, is_gold, len(wd), x, x + L])
                    self._layers[-1]["words"].append(order)
                    order += 1
                    x += L + space
            else:
                txt = " ".join(r)
                for d_, fill in ((dW, TH("text") + (255,)), (dG, TH("gold") + (255,))):
                    d_.text((right, y), txt, font=f, fill=fill, anchor="ra", **stroke, **kw)
                dS.text((right + 3, y + 5), txt, font=f, fill=235, anchor="ra", **kw)
                for k, wd in enumerate(r):
                    a_ = f.getlength(" ".join(r[:k]) + (" " if k else ""), **kw)
                    b_ = f.getlength(" ".join(r[:k + 1]), **kw)
                    is_gold = any(g in wd for g in GOLD_WORDS) or self.hl_words[order]
                    self.words.append([right - b_ - 14, right - a_ + 4, 0, self.h, order, is_gold, len(wd), right - b_, right - a_])
                    self._layers[-1]["words"].append(order)
                    order += 1
            y += row_h
        if sub_rows:
            dW, dG, dS = new_layer("sub")
            y0 = y
            y += 24
            for sr in sub_rows:
                dW.text((W / 2, y), sr, font=sub_f, fill=TH("sub") + (255,), anchor="ma", stroke_width=2, stroke_fill=TH("sub_stroke"), **sub_kw)
                dS.text((W / 2 + 2, y + 3), sr, font=sub_f, fill=200, anchor="ma", **sub_kw)
                y += sub_h
            self.sub_box = (int(y0), self.h)
        else:
            self.sub_box = None
        self.layers = []
        for L_ in self._layers:
            white, gold, shadow = L_["imgs"]
            base = Image.new("RGBA", (W, self.h), TH("halo") + (0,))
            base.putalpha(shadow.filter(ImageFilter.GaussianBlur(7)).point(lambda v, a=TH("halo_a"): int(v * a)))
            wa = np.asarray(Image.alpha_composite(base, white), np.float32)
            ga = np.asarray(Image.alpha_composite(base, gold), np.float32)
            gm = np.zeros(W, np.float32)                       # gold is chosen per column inside a row
            for k in L_["words"]:
                wd = self.words[k]
                if wd[5]:
                    gm[max(0, int(wd[7]) - 2):int(wd[8]) + 2] = 1
            gm = np.convolve(gm, np.ones(7) / 7, "same")[None, :, None]
            rgba = wa * (1 - gm) + ga * gm
            ys = np.where(rgba[..., 3].max(1) > 0)[0]          # crop the layer to its own pixels (speed)
            y0, y1 = (int(ys[0]), int(ys[-1]) + 1) if len(ys) else (0, 1)
            self.layers.append(dict(kind=L_["kind"], words=L_["words"], y0=y0, rgba=rgba[y0:y1]))
        del self._layers
        self.times = None

    def set_timing(self, speech_dur, cmap=None):
        """Word reveal times follow the speech (incl. dramatic pauses when a chunk map is given)."""
        lens = np.array([wd[6] + 2 for wd in self.words], float)
        frac = np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum()
        if not cmap:
            self.times = frac * max(0.4, speech_dur * 0.75)
            return
        total = sum(c[2] for c in cmap)
        times = []
        for p in frac:
            c, cum = p * total, 0
            for st, du, n in cmap:
                if c <= cum + n:
                    times.append(st + (c - cum) / max(n, 1) * du * 0.85); break
                cum += n
            else:
                times.append(cmap[-1][0])
        self.times = np.array(times)

    def render(self, lt, alpha):
        out = Image.new("RGBA", (W, self.h), (0, 0, 0, 0))
        k13 = np.ones(13) / 13
        for L_ in self.layers:
            if L_["kind"] == "row":
                col = np.zeros(W, np.float32)                  # reveal mask along x, for this row only
                for k in L_["words"]:
                    x0, x1 = self.words[k][0], self.words[k][1]
                    a = float(smooth(self.times[k], self.times[k] + 0.16, lt))
                    if a > 0:
                        sl = col[max(0, int(x0)):int(x1)]
                        np.maximum(sl, a, out=sl)
                m = np.convolve(col, k13, "same")[None, :]
            elif L_["kind"] == "sub":
                m = float(smooth(self.times[-1] + 0.3, self.times[-1] + 1.0, lt))
            else:
                m = float(smooth(0.0, 0.25, lt))
            if np.max(m) <= 0 or alpha <= 0:
                continue
            arr = L_["rgba"].copy()
            arr[..., 3] *= m * alpha
            out.alpha_composite(Image.fromarray(arr.astype(np.uint8), "RGBA"), (0, L_["y0"]))
        return out


# ============================== LOOK ==============================
def make_lut(theme="dark"):
    x = np.arange(256) / 255.0
    if theme == "light":                                   # airy: soft highlights, no crushed or lifted blacks, a touch warm
        s = x + 0.04 * np.sin(np.pi * (x - 0.5) * 2) * 0.5 * (1 - abs(2 * x - 1))
        r = s + 0.010 * (1 - x); g = s + 0.004 * (1 - x); b = s - 0.006 * x
        return [int(np.clip(v * 255, 0, 255)) for ch in (r, g, b) for v in ch]
    s = x + 0.10 * np.sin(np.pi * (x - 0.5) * 2) * 0.5 * (1 - abs(2 * x - 1))   # gentle S
    base = 0.035 + 0.95 * s                                                    # lifted blacks
    r = base + 0.025 * x ** 2
    g = base + 0.004
    b = base + 0.035 * (1 - x) ** 2 - 0.01 * x ** 2
    return [int(np.clip(v * 255, 0, 255)) for ch in (r, g, b) for v in ch]


def camera(img, kind, p):
    if kind == "static":
        return img
    e = p * p * (3 - 2 * p)
    z, dx, dy = 1.06, 0.0, 0.0
    if kind == "push":
        z = 1.0 + 0.09 * e
    elif kind == "pull":
        z = 1.09 - 0.09 * e
    elif kind == "rise":
        dy = 0.035 * (1 - 2 * e); z = 1.08
    elif kind == "sink":
        dy = -0.035 * (1 - 2 * e); z = 1.08
    elif kind == "drift_r":
        dx = -0.03 * (1 - 2 * e); z = 1.08
    elif kind == "drift_l":
        dx = 0.03 * (1 - 2 * e); z = 1.08
    cw, ch = W / z, H / z
    ox = (W - cw) / 2 + dx * W; oy = (H - ch) / 2 + dy * H
    ox = min(max(ox, 0), W - cw); oy = min(max(oy, 0), H - ch)
    return img.resize((W, H), Image.BILINEAR, box=(ox, oy, ox + cw, oy + ch))


class Bokeh:
    def __init__(self, rng, n):
        self.p = np.c_[rng.uniform(-100, W + 100, n), rng.uniform(0, H, n), rng.uniform(40, 120, n),
                       rng.uniform(-14, 14, n), rng.uniform(-10, 4, n), rng.uniform(0, 6.28, n)]

    k = 1.0

    def layer(self, t, color, n):
        im = Image.new("L", (W // 4, H // 4), 0); d = ImageDraw.Draw(im)
        for x, y, r, vx, vy, ph in self.p[:n]:
            x = (x + vx * t) / 4; y = (y + vy * t) / 4; r /= 4
            a = int((26 + 18 * math.sin(t * 0.6 + ph)) * self.k)
            d.ellipse([x - r, y - r, x + r, y + r], fill=a)
            d.ellipse([x - r * 0.82, y - r * 0.82, x + r * 0.82, y + r * 0.82], fill=int(a * 0.7))
        im = im.filter(ImageFilter.GaussianBlur(2.2)).resize((W, H), Image.BILINEAR)
        return Image.merge("RGB", [im.point(lambda v, c=c: v * c // 255) for c in color])


def leak_layer(p, rng_seed):
    rng = np.random.default_rng(rng_seed)
    im = Image.new("RGB", (W // 8, H // 8), 0); d = ImageDraw.Draw(im)
    cx = (W // 8) * (0.2 + 0.6 * p); cy = (H // 8) * rng.uniform(0.2, 0.6)
    for r, c in ((70, (120, 60, 20)), (45, (220, 130, 50)), (22, (255, 210, 150))):
        d.ellipse([cx - r, cy - r * 1.6, cx + r, cy + r * 1.6], fill=c)
    return im.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR)


# ============================== RENDER ==============================
def pause_after(ln):
    s = (say_text(ln) or ln.get("say_ur") or ln["text"]).replace("*", "").replace("|", "").strip()
    if s.endswith((",", "،")):
        return 0.10
    return 0.30


_CMAPS = {}


def missing_glyphs(text, font_path):
    from fontTools.ttLib import TTFont
    if font_path not in _CMAPS:
        _CMAPS[font_path] = set(TTFont(font_path).getBestCmap())
    cm = _CMAPS[font_path]
    skip = set(" \n\t{}*|") | {chr(c) for c in range(0x200B, 0x2010)}
    return sorted({ch for ch in text if ch not in skip and ord(ch) not in cm and ord(ch) >= 0x20})


def preflight(spec):
    """Errors stop the render; warnings go into the QA report."""
    errs, warns = [], []
    vl = spec.get("voice_lang", spec.get("lang", DEFAULT_LANG)); tl = spec.get("text_lang", spec.get("lang", DEFAULT_LANG))
    for i, ln in enumerate(spec["lines"]):
        n = i + 1
        if ln.get("speak", True) and VOICE_ENGINE not in ("file", "clips"):
            if vl == "en" and not ln.get("say") and (tl != "en" or ln.get("font") == "arabic"):
                errs.append(f"line {n}: English narration needs a 'say' field (the on-screen text is not English)")
            if vl == "ur" and VOICE_ENGINE == "kokoro" and not ln.get("say_hi"):
                errs.append(f"line {n}: Urdu narration with kokoro needs 'say_hi' (Devanagari)")
            if vl == "ur" and VOICE_ENGINE == "edge" and not ln.get("say_ur") and (tl != "ur" or ln.get("font") == "arabic"):
                errs.append(f"line {n}: Urdu narration with edge needs 'say_ur' (Urdu script)")
        if ln.get("scene") and ln["scene"] not in SCENES:
            errs.append(f"line {n}: unknown scene '{ln['scene']}'")
        checks = [("text", FONT_ARABIC if ln.get("font") == "arabic" else (FONT_EN if tl == "en" else FONT_URDU))]
        for fld in ("sub", "label", "text2"):
            if ln.get(fld):
                checks.append((fld, FONT_URDU if re.search(r"[\u0600-\u06FF]", ln[fld]) else FONT_EN))
        if ln.get("text0"):
            checks.append(("text0", FONT_ARABIC))
        for fld, fp in checks:
            txt = EMOJI_RE.sub("", ln.get(fld, "").replace("ﷺ", ""))
            miss = missing_glyphs(txt, fp)
            if miss:
                warns.append(f"line {n} {fld}: font {os.path.basename(fp)} lacks glyphs {''.join(miss)} (would show as boxes)")
    return errs, warns


def render_video(spec, verification=None):
    global LANG, TEXT_LANG, THEME, VOICE_ENGINE, CLIPS_DIR, CLIPS_TEMPO, CLIP_MOOD_PITCH, _VOICE_DEFAULTS
    if _VOICE_DEFAULTS is None:
        _VOICE_DEFAULTS = (VOICE_ENGINE, CLIPS_DIR, CLIPS_TEMPO, CLIP_MOOD_PITCH)
    VOICE_ENGINE, CLIPS_DIR, CLIPS_TEMPO, CLIP_MOOD_PITCH = _VOICE_DEFAULTS
    if spec.get("voice_engine"):
        VOICE_ENGINE = spec["voice_engine"]
    if spec.get("clips_dir"):
        CLIPS_DIR = os.path.join(HERE, spec["clips_dir"])
    CLIPS_TEMPO = float(spec.get("clips_tempo", CLIPS_TEMPO))
    CLIP_MOOD_PITCH = bool(spec.get("clip_mood_pitch", CLIP_MOOD_PITCH))
    first_scene = SCENES.get(next((l.get("scene") for l in spec["lines"] if l.get("scene")), ""), None)
    THEME = spec.get("theme") or getattr(first_scene, "theme", "dark")
    global THUMB_ON
    THUMB_ON = bool(spec.get("thumbnail", True))
    LANG = spec.get("voice_lang", spec.get("lang", DEFAULT_LANG))
    TEXT_LANG = spec.get("text_lang", spec.get("lang", DEFAULT_LANG))
    VOICE_USED.clear()
    name = spec["name"]; lines = spec["lines"]
    out_dir = os.path.join(OUT_ROOT, name); os.makedirs(out_dir, exist_ok=True)
    errs, pf_warns = preflight(spec)
    if errs:
        print(f"[{name}] NOT RENDERED - fix these first:"); [print("   -", e) for e in errs]
        return None
    tmp = tempfile.mkdtemp(prefix="reel_")
    print(f"[{name}] voice ({VOICE_ENGINE})...")
    clips, cmaps = make_voice(lines, tmp, name)

    # timeline: line starts, durations, speech starts
    rng = np.random.default_rng(len(name))
    t, starts, durs, vstarts = 0.0, [], [], []
    for i, (ln, c) in enumerate(zip(lines, clips)):
        lead = 0.45 if i == 0 else 0.06
        sd = len(c) / SR if c is not None else 0.9 + 0.07 * len(ln["text"])
        d = lead + sd + pause_after(ln) + rng.uniform(-0.02, 0.04)
        if "hold" in ln:
            d = max(ln["hold"], d + 0.5)
        d = max(1.1, d)
        starts.append(t); vstarts.append(t + lead); durs.append(d); t += d
    total = t + 0.6

    lang2 = spec.get("text2_lang") or ("ur" if TEXT_LANG == "en" else "en")
    caps, caps2, caps0 = [None] * len(lines), [None] * len(lines), [None] * len(lines)
    for i, ln in enumerate(lines):
        sc_ = SCENES[ln.get("scene") or list(SCENES)[i % len(SCENES)]]
        ty_ = int(H * sc_.text_y) if getattr(sc_, "text_y", None) else TEXT_Y
        z0, z1 = [int(H * v) for v in getattr(sc_, "text_zone", TEXT_ZONE)]
        for s_ in FIT_SCALES:
            c1 = Caption(ln, scale=s_)
            c2 = Caption(ln, lang=ln.get("text2_lang", lang2), scale=SECOND_SCALE * s_, key="text2") if ln.get("text2") else None
            c0 = Caption(ln, lang="ar", scale=ARABIC_TOP_SCALE * s_, key="text0") if ln.get("text0") else None
            pre = (c0.content_h + ARABIC_TOP_GAP) if c0 else 0
            block = pre + c1.content_h + (SECOND_GAP + c2.content_h if c2 else 0)
            top = ty_ - c1.content_h / 2 - pre
            if top < z0:
                top = z0
            if top + block > z1:
                top = z1 - block
            if top >= z0 - 1:
                break
        else:
            c1.warnings.append(f"text block ({int(block)} px) does not fit the scene's text zone ({z1 - z0} px) even at {FIT_SCALES[-1]:.0%}")
        if c0:
            c0.top_y = int(top)
            top += pre
        c1.top_y = int(top)
        c1.fit_scale = s_
        caps[i], caps2[i], caps0[i] = c1, c2, c0
    for cp, cp2, c, ln, cm in zip(caps, caps2, clips, lines, cmaps):
        sd_ = len(c) / SR if c is not None else 1.2 + 0.05 * len(ln["text"])
        cp.set_timing(sd_, cm)
        if cp2:
            cp2.set_timing(sd_)
    for cp0, c, ln in zip(caps0, clips, lines):
        if cp0:
            cp0.set_timing((len(c) / SR if c is not None else 2.0) * 0.6)
    breaths = [vstarts[i] - 0.34 for i in range(len(lines))
               if clips[i] is not None and (i == 0 or pause_after(lines[i - 1]) > 0.2) and vstarts[i] > 0.36]

    # shots: consecutive lines on the same scene share one continuous shot
    shots = []
    for i, ln in enumerate(lines):
        key = ln.get("scene") or list(SCENES)[i % len(SCENES)]
        if shots and shots[-1]["key"] == key:
            shots[-1]["end"] = starts[i] + durs[i]
        else:
            shots.append(dict(key=key, start=starts[i], end=starts[i] + durs[i], idx=len(shots)))
    shots[-1]["end"] = total
    print(f"[{name}] building {len(shots)} scenes...")
    for k, sh in enumerate(shots):
        sh["scene"] = SCENES[sh["key"]](W, H, seed=100 + 31 * k)
        sh["move"] = MOVES[k % len(MOVES)]
        sh["trans"] = TRANSITIONS[k % len(TRANSITIONS)]
        sh["xf"] = 0.45 if sh["trans"] in ("blur", "leak", "dip") else 0.35

    for sh in shots:
        if hasattr(sh["scene"], "set_timeline"):
            sh["scene"].set_timeline([(starts[i] - sh["start"] + 3.0, durs[i], lines[i]) for i in range(len(lines))
                                      if sh["start"] - 1e-6 <= starts[i] < sh["end"] - 1e-6])
        if getattr(sh["scene"], "camera", None) == "static":
            sh["move"] = "static"
    line_ty, line_scene = [], []
    for i in range(len(lines)):
        sh = next(s_ for s_ in shots if s_["start"] <= starts[i] + 1e-6 < s_["end"] + 1e-6)
        line_ty.append(int(H * sh["scene"].text_y) if getattr(sh["scene"], "text_y", None) else TEXT_Y)
        line_scene.append(sh["scene"])

    audio = os.path.join(tmp, "mix.wav")
    print(f"[{name}] mixing audio...")
    global SFX_MODE
    SFX_MODE = spec.get("sfx", "dramatic")
    build_audio(clips, vstarts, shots, total, audio, breaths if BREATHS else [], cues=sfx_plan(lines, starts, durs))

    lut = make_lut(THEME)
    grng = np.random.default_rng(1)
    grain = [grng.normal(0, 3.0, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) for _ in range(6)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = (1 - (0.10 if THEME == "light" else 0.34) * smooth(0.45, 1.30, np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))))[..., None]
    del yy, xx
    bok = Bokeh(np.random.default_rng(9), 12)
    band = Image.new("L", (W, 640), 0)
    ImageDraw.Draw(band).ellipse([-200, 210, W + 200, 430], fill=95)
    band = band.filter(ImageFilter.GaussianBlur(55))
    tag = None
    if CHANNEL_TAG:
        tag = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
        ImageDraw.Draw(tag).text((W / 2, 45), CHANNEL_TAG, font=ImageFont.truetype(FONT_ARABIC, 34), fill=TH("tag"), anchor="mm")

    def shot_frame(k, t):
        sh = shots[k]
        lt = t - sh["start"]
        p = min(1.0, max(0.0, (lt + sh["xf"] if k else lt) / (sh["end"] - sh["start"] + sh["xf"])))
        return camera(sh["scene"].frame(lt + 3.0), sh["move"], p)

    def bloom(img):
        small = img.resize((W // 6, H // 6), Image.BILINEAR)
        a = np.asarray(small, np.float32)
        lum = a.mean(-1, keepdims=True)
        a = a * smooth(200, 252, lum) * 0.55
        b = to_img(a).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
        return ImageChops.screen(img, b)

    out_tmp = os.path.join(out_dir, f".{name}.part.mp4")
    out = os.path.join(out_dir, f"{name}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", audio, *(["-af", f"adelay={int(THUMB_DUR * 1000)}:all=1"] if THUMB_ON else []), "-c:v", "libx264", "-profile:v", "high", "-preset", PRESET, "-crf", str(CRF), "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-g", str(FPS * 2), "-maxrate", "14M", "-bufsize", "28M", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", out_tmp]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(total * FPS)
    print(f"[{name}] rendering {nf} frames ({total:.1f}s)...")
    cover_frame = None
    bg_luma = [None] * len(lines)
    thumb = None
    if THUMB_ON:                                           # title card from a moment where the scene is fully built
        tt = min(total - 0.5, float(spec.get("thumb_t", total * 0.55)))
        kk = max(j for j in range(len(shots)) if shots[j]["start"] <= tt)
        bg = shot_frame(kk, tt).point(lut)
        bg = Image.fromarray(np.clip(np.asarray(bg, np.float32) * vig, 0, 255).astype(np.uint8))
        thumb = make_cover(spec, bg)
        for _ in range(int(round(THUMB_DUR * FPS))):
            ff.stdin.write(thumb.tobytes())
    for fi in range(nf):
        t = fi / FPS
        k = max(j for j in range(len(shots)) if shots[j]["start"] <= t)
        img = shot_frame(k, t)
        sh = shots[k]
        if k + 1 < len(shots) and t > sh["end"] - shots[k + 1]["xf"]:
            nx = shots[k + 1]; a = float(smooth(0, 1, (t - (sh["end"] - nx["xf"])) / nx["xf"]))
            img2 = shot_frame(k + 1, t)
            tr = nx["trans"]
            if tr == "dip":
                img = Image.blend(img, Image.new("RGB", (W, H), (250, 245, 235) if THEME == "light" else (0, 0, 0)), min(1, a * 2)) if a < 0.5 else Image.blend(Image.new("RGB", (W, H), (250, 245, 235) if THEME == "light" else (0, 0, 0)), img2, (a - 0.5) * 2)
            elif tr == "blur":
                r = 10 * math.sin(math.pi * a)
                if r > 0.5:
                    img = img.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(r / 2)).resize((W, H))
                    img2 = img2.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(r / 2)).resize((W, H))
                img = Image.blend(img, img2, a)
            else:
                img = Image.blend(img, img2, a)
                if tr == "leak":
                    img = ImageChops.screen(img, Image.blend(Image.new("RGB", (W, H)), leak_layer(a, k), math.sin(math.pi * a) * 0.9))
        if THEME != "light":                                # bloom would wash a bright scene out
            img = bloom(img)
        sc = sh["scene"]
        bok.k = 1.0 if sc.ambience in ("town", "night") else 0.6
        img = ImageChops.screen(img, bok.layer(t, sc.bokeh, sc.bokeh_n))
        img = img.point(lut)
        arr = np.asarray(img, np.float32) * vig + grain[fi % 6]
        fade = min(1.0, 1.0 if THUMB_ON else t / 0.3, (total - t) / 0.6)
        if fade < 1:
            if THEME == "light":                                # fade from / to warm cream instead of black
                arr = arr * max(0.0, fade) + np.array((250, 245, 235), np.float32) * (1 - max(0.0, fade))
            else:
                arr *= max(0.0, fade)
        frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        # subtitles
        i = max(j for j in range(len(lines)) if starts[j] <= t)
        if bg_luma[i] is None and t >= starts[i] + durs[i] / 2:
            b0 = max(0, (caps0[i] or caps[i]).top_y); b1 = min(H, b0 + int(caps[i].content_h + (SECOND_GAP + caps2[i].content_h if caps2[i] else 0)))
            ba_ = 0.75 * getattr(line_scene[i], "band", 1.0) * 95 / 255 * 0.8
            reg = arr[b0:b1, 90:W - 90] * (1 - ba_) + np.array(TH("band"), np.float32) * ba_
            bg_luma[i] = float(np.percentile(reg.mean(-1), 75)) if reg.size else 0.0
        lt = t - (vstarts[i] - 0.1)
        out_a = 1.0 if i == len(lines) - 1 else float(smooth(starts[i] + durs[i], starts[i] + durs[i] - 0.14, t))
        ta = max(0.0, fade) * out_a
        cy_ = [int(c_.top_y + c_.content_h / 2) for c_ in (caps[i - 1] if i else caps[i], caps[i])]
        ty = cy_[1] if i == 0 else int(cy_[0] + (cy_[1] - cy_[0]) * float(smooth(starts[i] - 0.15, starts[i] + 0.25, t)))
        bandA = 0.75 * getattr(line_scene[i], "band", 1.0) * max(0.0, fade) * float(smooth(0.3, 1.0, t))
        if bandA > 0:
            frame.paste(TH("band"), (0, ty - 320), band.point(lambda v, a=bandA: min(255, int(v * a))))
        if ta > 0 and lt > 0:
            cl = caps[i].render(lt, ta)
            rise = int(10 * (1 - float(smooth(0, 0.3, lt))))
            cyi = int(caps[i].top_y + caps[i].content_h / 2)
            frame.paste(cl, (0, cyi - caps[i].h // 2 + rise), cl)
            if caps0[i]:
                cl0 = caps0[i].render(lt + 0.05, ta)
                y0_ = int(caps0[i].top_y + caps0[i].content_h / 2)
                frame.paste(cl0, (0, y0_ - caps0[i].h // 2 + rise), cl0)
            if caps2[i]:
                cl2 = caps2[i].render(lt - 0.15, ta)
                y2 = int(caps[i].top_y + caps[i].content_h + SECOND_GAP + caps2[i].content_h / 2)
                frame.paste(cl2, (0, y2 - caps2[i].h // 2 + rise), cl2)
        if tag is not None:
            frame.paste(tag, (0, int(H * 0.115)), tag)
        if cover_frame is None and shots[-1]["start"] + 1.0 < t:
            cover_frame = img.copy()
        if thumb is not None and t < THUMB_XF:                 # dissolve from the title card into the video
            frame = Image.blend(thumb, frame, float(smooth(0, THUMB_XF, t)))
        ff.stdin.write(frame.tobytes())
        if fi % (FPS * 5) == 0:
            print(f"   {t:5.1f}s / {total:.1f}s")
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    os.replace(out_tmp, out)
    if thumb is not None:
        thumb.save(os.path.join(out_dir, f"{name}_cover.jpg"), quality=92)
    else:
        make_cover(spec, cover_frame or img, os.path.join(out_dir, f"{name}_cover.jpg"))
    write_captions(spec, os.path.join(out_dir, f"{name}_captions.txt"))
    meta = dict(
        name=name, title=spec.get("title"), topic=spec.get("topic"), style=spec.get("style"), hook_type=spec.get("hook_type"),
        theme=THEME, thumb=THUMB_DUR if THUMB_ON else 0.0, voice_lang=LANG, text_lang=TEXT_LANG, bilingual=any(caps2), voice_used=sorted(VOICE_USED),
        duration=total, fps=FPS, size=[W, H], scenes=[dict(key=s_["key"], start=round(s_["start"], 2), end=round(s_["end"], 2)) for s_ in shots],
        lines=[dict(n=i + 1, start=round(starts[i], 3), dur=round(durs[i], 3), speech_start=round(vstarts[i], 3),
                    speech_dur=round(len(clips[i]) / SR, 3) if clips[i] is not None else None,
                    reveal_end=round(vstarts[i] - 0.1 + float(caps[i].times[-1]) + 0.16, 3),
                    caption_warnings=caps[i].warnings + (caps2[i].warnings if caps2[i] else []),
                    bg_luma=round(bg_luma[i], 1) if bg_luma[i] is not None else None) for i in range(len(lines))],
        preflight_warnings=pf_warns, verification=(verification or {}).get("status"))
    with open(os.path.join(out_dir, f"{name}_render.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[{name}] done -> {out_dir}")
    if RUN_QA:
        import qa
        rep = qa.run_qa(out, meta, out_dir)
        print(f"[{name}] QA: {rep['status']}" + "".join(f"\n   - {x['check']}: {x['status']} {x['detail']}" for x in rep["checks"] if x["status"] != "PASS"))
        log_production(meta, rep)
    return out


def log_production(meta, qa_rep):
    """Append one record per render to output/production_log.jsonl (metrics filled later with log_metrics.py)."""
    rec = dict(date=__import__("datetime").datetime.now().isoformat(timespec="seconds"), name=meta["name"], title=meta["title"],
               topic=meta["topic"], style=meta["style"], hook_type=meta["hook_type"], voice_lang=meta["voice_lang"],
               text_lang=meta["text_lang"], bilingual=meta["bilingual"], scene_count=len(meta["scenes"]),
               scenes=[s_["key"] for s_ in meta["scenes"]], duration=round(meta["duration"], 2), voice=meta["voice_used"],
               verification=meta["verification"], qa=qa_rep["status"],
               qa_failures=[x["check"] for x in qa_rep["checks"] if x["status"] == "FAIL"], metrics=None)
    with open(os.path.join(OUT_ROOT, "production_log.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def make_cover(spec, img, path=None):
    """Thumbnail: the scene behind a big wrapped title ({word} = accent colour), optional Urdu line, channel tag.
    Title = spec "thumb_title" or "title". Returns the image; also saves it when path is given."""
    im = img.convert("RGB").copy()
    title = spec.get("thumb_title") or spec.get("title") or re.sub(r"[{}*|]", "", spec["lines"][0]["text"])
    title_ur = spec.get("thumb_title_ur", "")
    words = title.split()
    hl = [("{" in w_) for w_ in words]
    words = [w_.replace("{", "").replace("}", "") for w_ in words]
    if not any(hl) and len(words) > 1:                     # accent the longest word if none is marked
        hl[max(range(len(words)), key=lambda k: len(words[k]))] = True
    maxw = W - 150
    for size in (136, 124, 112, 100, 90, 80, 72):
        f = ImageFont.truetype(FONT_EN, size)
        try:
            f.set_variation_by_axes([700])
        except Exception:
            pass
        rows, cur = [], []
        for k, w_ in enumerate(words):
            trial = " ".join(words[j] for j in cur + [k])
            if cur and f.getlength(trial) > maxw:
                rows.append(cur); cur = [k]
            else:
                cur.append(k)
        rows.append(cur)
        if len(rows) <= 3 and all(f.getlength(" ".join(words[j] for j in r)) <= maxw for r in rows):
            break
    lh = int(size * 1.12)
    block = lh * len(rows) + (int(size * 0.75) if title_ur else 0)
    y0 = int(H * float(spec.get("thumb_y", 0.47)) - block / 2)   # spec "thumb_y": title centre (fraction of height)
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rounded_rectangle([-200, y0 - 160, W + 200, y0 + block + 160], radius=300, fill=175 if THEME == "light" else 160)
    im.paste(TH("cover_shade"), (0, 0), shade.filter(ImageFilter.GaussianBlur(80)))
    d = ImageDraw.Draw(im)
    for r_i, r in enumerate(rows):
        line_w = f.getlength(" ".join(words[j] for j in r))
        x = W / 2 - line_w / 2; y = y0 + r_i * lh
        for j in r:
            col = TH("gold") if hl[j] else TH("text")
            if THEME == "dark":
                d.text((x + 4, y + 6), words[j], font=f, fill=(0, 0, 0))
            d.text((x, y), words[j], font=f, fill=col, stroke_width=4, stroke_fill=TH("cover_stroke"))
            x += f.getlength(words[j] + " ")
    if title_ur:
        fu = font("urdu", int(size * 0.5))
        d.text((W / 2, y0 + lh * len(rows) + int(size * 0.25)), title_ur, font=fu, fill=TH("sub"), anchor="ma",
               direction="rtl", language="ur", stroke_width=2, stroke_fill=TH("cover_stroke"))
    if CHANNEL_TAG:
        d.text((W / 2, int(H * 0.115) + 45), CHANNEL_TAG, font=ImageFont.truetype(FONT_ARABIC, 34), fill=TH("tag"), anchor="mm")
    if path:
        im.save(path, quality=92)
    return im


def write_captions(spec, path):
    cap = spec.get("caption", spec["lines"][0]["text"])
    tags = spec.get("hashtags", [])
    title = spec.get("title", "")
    en = spec.get("title_en", "")
    if spec.get("text_lang", spec.get("lang", DEFAULT_LANG)) == "en":
        yt_title = f"{en or title} 🤍 #shorts"
    else:
        yt_title = f"{title} | {en} #shorts" if en else f"{title} #shorts"
    txt = f"""=== TikTok ===
{cap}

{' '.join(tags[:6])} #fyp #viral

=== Instagram Reels ===
{cap}
.
{' '.join(dict.fromkeys(tags + ['#reels', '#islamicreels', '#islamicquotes']))}

=== YouTube Shorts ===
Title: {yt_title[:100]}
Description:
{cap}
{' '.join(tags[:5])} #shorts

=== Facebook Reels ===
{cap}
{' '.join(tags[:5])} #reels
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)


def main():
    """python urdu_reels.py [videos.json] [--reviewed] [--skip-verify] [--no-qa] [--only NAME]"""
    global RUN_QA
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    RUN_QA = RUN_QA and "--no-qa" not in flags
    ensure_assets()
    spec = DEFAULT_VIDEOS
    if args:
        with open(args[0], encoding="utf-8") as fh:
            spec = json.load(fh)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    import verify
    for v in spec["videos"]:
        if only and v["name"] != only:
            continue
        rep = None
        if "--skip-verify" not in flags:
            rep = verify.verify_video(v, os.path.join(OUT_ROOT, v["name"]))
            bad = [x for x in rep["items"] if x["status"] in ("FAIL", "FLAG")]
            for x in bad:
                print(f"   [{v['name']}] line {x['line']} {x['ref']}: {x['status']} - {x['detail']}")
            if rep["status"] == "FAIL":
                print(f"[{v['name']}] NOT RENDERED - religious content failed verification (see {v['name']}_verification.md)")
                continue
            if rep["status"] == "FLAG" and not (v.get("reviewed") or "--reviewed" in flags):
                print(f"[{v['name']}] NOT RENDERED - flagged items need human review; add them to 'sources' or rerun with --reviewed")
                continue
        render_video(v, rep)


if __name__ == "__main__":
    main()
