#!/usr/bin/env python3
"""
verify.py - religious-content verification for urdu_reels videos (runs before rendering).

  python verify.py videos.json            # report only
  (urdu_reels.py calls verify_video() automatically and stops on FAIL / unreviewed FLAG)

What it checks
  QURAN  (automatic, against authoritative data):
    - every line whose "sub" (or "quran" field) carries a reference like (Az-Zumar 39:53) or "39:53-54"
    - Arabic cards ("font": "arabic"): text must be an exact word sequence of the Tanzil Simple text
    - English quotes in “curly quotes”: must appear verbatim (punctuation-insensitive) in Saheeh International
    - Urdu quotes in “…” / «…»: must appear verbatim in the Junagarhi Urdu translation (QuranEnc)
    Data: risan/quran-json (Tanzil + QuranEnc), downloaded once into data/quran/.
  HADITH (cannot be auto-verified offline -> human-review register):
    - any line citing Bukhari, Muslim, Tirmidhi, Abu Dawud, Nasa'i, Ibn Majah, Ahmad, Malik, Riyad as-Salihin, ...
      must have a matching entry in the video's "sources" list:
        {"ref": "Sahih al-Bukhari 6514", "url": "https://sunnah.com/bukhari:6514",
         "grade": "sahih (agreed upon)", "wording": "faithful rendering of the sunnah.com translation",
         "checked": "2026-11-06"}
      Missing entry -> FLAG (needs human review before rendering).
  INTERPRETATION: lines marked "claim": "interpretation" are listed for review as reflections, not quotes.

Status: PASS / FLAG (needs review) / FAIL (mismatch -> must be fixed).
"""
import json, os, re, sys, unicodedata, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, "data", "quran")
QFILES = {
    "ar": ("tanzil_simple.json", "https://raw.githubusercontent.com/risan/quran-json/main/data/tanzil/simple.json"),
    "en": ("english_saheeh.json", "https://raw.githubusercontent.com/risan/quran-json/main/data/quranenc/english_saheeh.json"),
    "ur": ("urdu_junagarhi.json", "https://raw.githubusercontent.com/risan/quran-json/main/data/quranenc/urdu_junagarhi.json"),
}
HADITH_RE = re.compile(r"(Bukhari|Muslim|Tirmidhi|Ab[iu] Dawud|Nasa'?i|Nasa’i|Ibn Majah|Ahmad|Muwatta|Malik|Riyad|Nawawi|Darimi|Hakim|Bayhaqi|بخاری|مسلم|ترمذی|ابو داؤد)", re.I)
REF_RE = re.compile(r"(\d{1,3})\s*:\s*(\d{1,3})(?:\s*[–\-]\s*(\d{1,3}))?")
SURAH_HINT = re.compile(r"\(([^()]*?\d{1,3}\s*:\s*\d{1,3}[^()]*)\)")

_DATA = {}


def load(kind):
    if kind in _DATA:
        return _DATA[kind]
    fn, url = QFILES[kind]
    p = os.path.join(QDIR, fn)
    if not os.path.exists(p):
        os.makedirs(QDIR, exist_ok=True)
        print(f"  downloading Quran data ({kind})")
        urllib.request.urlretrieve(url, p)
    with open(p, encoding="utf-8") as f:
        _DATA[kind] = json.load(f)
    return _DATA[kind]


def verse(kind, c, v):
    for x in load(kind)[str(c)]:
        if x["verse"] == v:
            return x["text"]
    raise KeyError(f"{c}:{v}")


def skel(t):
    """Arabic skeleton (no harakat) for locating words."""
    return "".join(ch for ch in unicodedata.normalize("NFKD", t) if not unicodedata.combining(ch) and ch not in "ٰـ")


def norm_en(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"\[\d+\]|\(\d+\)", "", t)
    t = t.replace("[", "").replace("]", "").replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9' ]", " ", t.lower()).split()


def norm_ur(t):
    t = re.sub(r"\[\d+\]|\(\d+\)", "", t)
    t = t.replace("\u0647", "\u06c1").replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")   # Arabic vs Urdu heh/yeh/kaf
    t = re.sub(r"[ً-ْٰ]", "", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return t.split()


def contains(hay, needle):
    n = len(needle)
    return n > 0 and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def refs_in(text):
    out = []
    text = (text or "").translate(DIGITS)
    for m in SURAH_HINT.finditer(text):
        for r in REF_RE.finditer(m.group(1)):
            c, a, b = int(r.group(1)), int(r.group(2)), int(r.group(3) or r.group(2))
            if 1 <= c <= 114:
                out.append((c, list(range(a, b + 1))))
    return out


def quotes(text):
    return re.findall(r"[“«\"](.+?)[”»\"]", text or "")


def check_quran(lines, reg=()):
    items = []
    for i, ln in enumerate(lines):
        refs = refs_in(ln.get("sub", "")) + refs_in(ln.get("text2", ""))
        if "quran" in ln:
            refs += [(int(c), list(range(int(a), int(b or a) + 1))) for c, a, b in REF_RE.findall(ln["quran"])]
        if not refs:
            if ln.get("font") == "arabic":
                hr = ln.get("hadith_ref", "")
                if ln.get("arabic_source") == "hadith" and any(hr and hr in r.get("ref", "") and r.get("url") for r in reg):
                    items.append(dict(line=i + 1, ref=hr, kind="hadith arabic", status="PASS",
                                      detail="non-Quranic Arabic (wording of a registered hadith) - check spelling by eye"))
                else:
                    items.append(dict(line=i + 1, ref="?", kind="arabic", status="FLAG",
                                      detail='Arabic card without a reference - add "quran": "surah:ayah", or "arabic_source": "hadith" + "hadith_ref" from the sources register'))
            continue
        c, vs = refs[0]
        ref = f"{c}:{vs[0]}" + (f"-{vs[-1]}" if len(vs) > 1 else "")
        try:
            ar = " ".join(verse("ar", c, v) for v in vs)
            en = norm_en(" ".join(verse("en", c, v) for v in vs))
            ur = norm_ur(" ".join(verse("ur", c, v) for v in vs))
        except KeyError as e:
            items.append(dict(line=i + 1, ref=ref, status="FAIL", detail=f"reference {e} does not exist"))
            continue
        # Arabic card
        if ln.get("font") == "arabic":
            words = ar.split()
            mine = ln["text"].split()
            exact = " ".join(mine) in ar
            canon = unicodedata.normalize("NFD", " ".join(mine)) in unicodedata.normalize("NFD", ar)
            located = contains([skel(w) for w in words], [skel(w) for w in mine])
            st = "PASS" if (exact or canon) else "FAIL"
            det = "Arabic matches Tanzil exactly" if exact else (
                "Arabic identical to Tanzil after Unicode normalisation (mark order only); run --fix for byte-exact text" if canon else
                "Arabic words found but characters differ - replace with the exact Tanzil text (use verify.py --fix)" if located
                else "Arabic NOT found in this ayah")
            items.append(dict(line=i + 1, ref=ref, kind="arabic", status=st, detail=det))
        # quoted translations: this line + preceding consecutive quoted lines that this ref closes
        qlines = [i]
        j = i - 1
        while j >= 0 and quotes(lines[j]["text"]) and not refs_in(lines[j].get("sub", "")):
            qlines.insert(0, j); j -= 1
        for k in qlines:
            for field in ("text", "sub", "text2"):
                for q in quotes(lines[k].get(field, "")):
                    if REF_RE.search(q) and len(q) < 12:
                        continue
                    is_ur = bool(re.search(r"[؀-ۿ]", q))
                    if is_ur and lines[k].get("font") == "arabic" and field == "text":
                        continue
                    ok = contains(ur, norm_ur(q)) if is_ur else contains(en, norm_en(q))
                    items.append(dict(line=k + 1, ref=ref, kind="urdu translation" if is_ur else "english translation",
                                      status="PASS" if ok else "FAIL",
                                      detail=("matches " + ("Junagarhi (QuranEnc)" if is_ur else "Saheeh International")) if ok
                                      else f"quote not found verbatim in {'Junagarhi' if is_ur else 'Saheeh International'}: “{q[:70]}”"))
    return items


def check_hadith(spec):
    items = []
    reg = spec.get("sources", [])
    for i, ln in enumerate(spec["lines"]):
        for field in ("sub", "text", "text2"):
            s = ln.get(field, "")
            if not HADITH_RE.search(s):
                continue
            m = re.search(r"\(([^()]+)\)", s)
            ref = (m.group(1) if m else s).strip()
            num = re.findall(r"\d+[a-z]?", ref)
            hit = next((r for r in reg if num and all(n in r.get("ref", "") for n in num[:1]) and
                        re.sub(r"[^a-z]", "", ref.lower())[:5] in re.sub(r"[^a-z]", "", r.get("ref", "").lower())), None)
            if hit and hit.get("url") and hit.get("grade"):
                items.append(dict(line=i + 1, ref=ref, kind="hadith", status="PASS",
                                  detail=f"registered: {hit['grade']}; {hit.get('wording', '')}; {hit['url']}"))
            else:
                items.append(dict(line=i + 1, ref=ref, kind="hadith", status="FLAG",
                                  detail="not in the video's 'sources' register (needs url + grade + wording check)"))
            break
    return items


def check_claims(spec):
    return [dict(line=i + 1, ref="-", kind="interpretation", status="NOTE",
                 detail=f"reflection/interpretation, not a quote: {ln['text'][:70]}")
            for i, ln in enumerate(spec["lines"]) if ln.get("claim") == "interpretation"]


def fix_arabic(spec):
    """Replace near-miss Arabic cards with the exact Tanzil word sequence."""
    changed = 0
    for ln in spec["lines"]:
        if ln.get("font") != "arabic":
            continue
        refs = refs_in(ln.get("sub", "")) or [(int(c), list(range(int(x), int(y or x) + 1))) for c, x, y in REF_RE.findall(ln.get("quran", ""))]
        if not refs:
            continue
        c, vs = refs[0]
        words = " ".join(verse("ar", c, v) for v in vs).split()
        mine = [skel(w) for w in ln["text"].split()]
        sk = [skel(w) for w in words]
        for k in range(len(sk) - len(mine) + 1):
            if sk[k:k + len(mine)] == mine:
                exact = " ".join(words[k:k + len(mine)])
                if exact != ln["text"]:
                    ln["text"] = exact; changed += 1
                break
    return changed


def ar_words(t):
    """Arabic words with harakat, in canonical mark order; punctuation, quote marks and invisible marks removed."""
    t = unicodedata.normalize("NFD", t).replace("\u0640", "")
    t = re.sub(r"[\u200b-\u200f\u061f\u060c\u061b\u06d4\u066b\u066c.,:;!?\"'«»“”()\[\]‏‎]", " ", t)
    return t.split()


def check_text0(spec):
    """The optional Arabic row above a line ("text0") must be a contiguous, exact excerpt of the hadith's
    Arabic in the sources register (field "arabic", matched by "text0_ref") or of a Quran verse ("text0_quran")."""
    items = []
    reg = spec.get("sources", [])
    for i, ln in enumerate(spec["lines"]):
        a = ln.get("text0")
        if not a:
            continue
        need = ar_words(a)
        if ln.get("text0_quran"):
            c, v = map(int, ln["text0_quran"].split(":"))
            hay, ref = ar_words(verse("ar", c, v)), f"Quran {c}:{v}"
        else:
            src = [r for r in reg if r.get("arabic") and ln.get("text0_ref") and ln["text0_ref"] in r.get("ref", "")]
            if not src:
                items.append(dict(line=i + 1, ref=ln.get("text0_ref", "?"), kind="arabic (top)", status="FAIL",
                                  detail="no 'arabic' text in the sources register for this text0_ref"))
                continue
            hay, ref = ar_words(src[0]["arabic"]), src[0]["ref"]
        if contains(hay, need):
            items.append(dict(line=i + 1, ref=ref, kind="arabic (top)", status="PASS", detail="exact excerpt of the source Arabic"))
        elif contains([skel(w) for w in hay], [skel(w) for w in need]):
            items.append(dict(line=i + 1, ref=ref, kind="arabic (top)", status="FAIL", detail="letters match but harakat differ from the source - copy it exactly"))
        else:
            items.append(dict(line=i + 1, ref=ref, kind="arabic (top)", status="FAIL", detail="not found in the source Arabic"))
    return items


def verify_video(spec, out_dir=None):
    items = check_quran(spec["lines"], spec.get("sources", [])) + check_hadith(spec) + check_text0(spec) + check_claims(spec)
    fails = [x for x in items if x["status"] == "FAIL"]
    flags = [x for x in items if x["status"] == "FLAG"]
    status = "FAIL" if fails else ("FLAG" if flags else "PASS")
    rep = dict(video=spec["name"], status=status, checked=datetime.date.today().isoformat(), items=items,
               reviewed=bool(spec.get("reviewed")))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{spec['name']}_verification.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        md = [f"# Verification report - {spec['name']}", "", f"**Status: {status}**  (checked {rep['checked']})", "",
              "| Line | Reference | Kind | Status | Detail |", "|---|---|---|---|---|"]
        md += [f"| {x['line']} | {x['ref']} | {x.get('kind', 'quran')} | {x['status']} | {x['detail']} |" for x in items]
        if not items:
            md.append("| - | - | - | - | no religious references found |")
        md += ["", "Sources: Quran Arabic = Tanzil Simple; English = Saheeh International; Urdu = Muhammad Junagarhi "
               "(QuranEnc), via github.com/risan/quran-json. Hadith entries come from the video's 'sources' register."]
        with open(os.path.join(out_dir, f"{spec['name']}_verification.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
    return rep


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if "--fix" in sys.argv:
        n = sum(fix_arabic(v) for v in spec["videos"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        print(f"fixed {n} Arabic card(s) to exact Tanzil text")
    worst = "PASS"
    for v in spec["videos"]:
        rep = verify_video(v, os.path.join(HERE, "output", v["name"]))
        print(f"{v['name']:28s} {rep['status']}")
        for x in rep["items"]:
            if x["status"] != "PASS":
                print(f"   line {x['line']:>2} {x['ref']:<28} {x['status']}: {x['detail']}")
        worst = "FAIL" if "FAIL" in (worst, rep["status"]) else ("FLAG" if "FLAG" in (worst, rep["status"]) else "PASS")
    sys.exit({"PASS": 0, "FLAG": 2, "FAIL": 1}[worst])


if __name__ == "__main__":
    main()
