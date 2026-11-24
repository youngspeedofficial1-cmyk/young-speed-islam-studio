# Islamic verification (mandatory, automated + human)

Religious accuracy always outranks virality. `urdu_reels.py` runs `verify.py` before every render:
**FAIL stops the render, FLAG stops it unless reviewed, PASS continues.**

## Quran (automatic)
- Data: Tanzil Simple (Arabic), Saheeh International (English), Muhammad Junagarhi (Urdu), all via QuranEnc / `github.com/risan/quran-json`, downloaded into `data/quran/`.
- Put the reference in `sub` like `(Az-Zumar 39:53)` / `(الزمر 39:53)`, or add `"quran": "39:53"` to the line.
- Arabic cards (`"font": "arabic"`) must be an exact word sequence of the ayah. Use `python verify.py file.json --fix` to copy the exact Tanzil characters (mark-order differences are fixed automatically).
- Quotes inside “…” (English) or «…» (Urdu) must appear **verbatim** in the selected translation. Paraphrases must NOT be in quote marks.
- Never alter Quranic wording, never merge ayat without a range reference (`99:7-8`).

## Hadith (human-verified, machine-enforced)
For every hadith cited in a `sub`, the video needs an entry in `"sources"`:
```json
{"ref": "Sahih Muslim 2752", "url": "https://sunnah.com/muslim:2752c",
 "grade": "sahih (Sahih Muslim)", "wording": "faithful rendering of the sunnah.com translation", "checked": "2026-11-06"}
```
Workflow: search sunnah.com (or hadithunlocked / hadeethenc), open the exact page, read the English, record the collection, number and **grade**, and note any grading disagreement (e.g. Tirmidhi 2417: hasan sahih per at-Tirmidhi, sahih per al-Albani, da'if per Zubair Ali Zai). Only sahih or hasan hadith; if graders disagree, say so to the user. On screen, quote marks are only for wording that follows the translation; otherwise write "The Prophet ﷺ said that…".

## Explanations and reflections
- Mark your own reflective lines with `"claim": "interpretation"`; they are listed for review and never shown as quotes.
- Do not state rulings, unseen details (the grave, the Day of Judgment) or historical facts beyond what the cited text says.
- Where scholars differ, either avoid the point or name the difference.

## Already verified in this project (re-use)
Bukhari 6514, 1369, 6000, 5999; Muslim 2864, 2759, 2752c; Abu Dawud 4753 (sahih, al-Albani); Tirmidhi 2307, 3537, 3540 (hasan); Tirmidhi 2417 (graders differ, see above). Quran: 2:222, 3:185, 4:78, 7:156, 14:27, 30:50, 39:53, 40:44, 62:8, 80:34-37, 99:7-8, 101:4-5, 102:8.
