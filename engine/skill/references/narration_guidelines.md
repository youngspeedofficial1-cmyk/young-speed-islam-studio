# Narration

## Engines (independent per language; do not change working settings without a test render)
| Narration | Engine (config in urdu_reels.py) | Text field read |
|---|---|---|
| English | `EN_ENGINE = "edge"`: **en-US-AndrewNeural, rate -16%** (user-approved). Falls back to Kokoro `am_michael` if Microsoft is unreachable; the cloud workspace is always unreachable, so renders made there use Kokoro | `say` |
| English (offline) | `EN_ENGINE = "kokoro"`, `EN_VOICE = "am_michael"`, `EN_SPEED = 1.06` | `say` |
| Urdu | `VOICE_ENGINE = "kokoro"`: `hm_omega`, `KOKORO_SPEED = 1.28`, reads Devanagari with Urdu pronunciation | `say_hi` |
| Urdu (online) | `VOICE_ENGINE = "edge"`: `ur-PK-AsadNeural` | `say_ur` |
| Own voice | `VOICE_ENGINE = "file"` (one recording, auto-split) or `"clips"` (one wav per line) | n/a |

The voice language comes from `voice_lang` (default `lang`); the text language from `text_lang` (default `lang`).

## Writing spoken lines
- Speak like a person, not a book: short clauses, 4-12 words per line, one breath per line.
- `|` = dramatic pause (0.20 s). **One per line**: the engine ignores extra ones, because every pause splits the line into another TTS take and too many sound like reading word by word.
- With Andrew (edge) each line is spoken in **one take** (`|` becomes a comma), which gives the most fluent result. With Kokoro a line is at most two takes, joined with a continuation comma.
- `*word*` marks the key word; by default it stays inside its phrase (`STRESS_SPLIT = False`). Set `STRESS_SPLIT = True` only for a deliberately dramatic one-word emphasis.
- English base speed is `EN_SPEED` (Kokoro) / `EN_EDGE_RATE` (Andrew, -16%); Urdu uses `KOKORO_SPEED`. They are independent (V2.0 wrongly applied the Urdu speed to English; fixed in V2.1).
- English pronunciation is phonemised **per phrase**, so connected speech ("for the" -> fɚðə) stays natural; only `PRON_EN` words are swapped in.
- Every line has a `mood`: `question`, `soft`, `heavy`, `hope`, `firm`, `neutral`. Arc: question, then soft/heavy, then hope, then firm, then soft ending.
- Say "The Prophet, peace be upon him, said:" while the screen shows "The Prophet ﷺ said:".
- Never TTS-recite Quranic Arabic. Narrate the translation and show the Arabic.
- Ayah and hadith references are shown, not spoken.

## Pronunciation
- English: words the voice gets wrong go into `PRON_EN` as phonemes (Allah, dua, sujood, Quran, hadith, qudsi, Rahman are already set). Andrew (edge) usually pronounces Islamic words well; still listen.
- Urdu via Devanagari: ز/ذ/ض/ظ = ज़, غ = ग़, خ = ख़, ف = फ़, ق = क़; دعا = दुआ, اللہ = अल्लाह, سپرد = सुपुर्द, معاملہ = मामला. Check with `kokoro.tokenizer.phonemize(text, "hi")`.

## Pacing targets
Check: silences of 90 ms or more inside a spoken line should equal the number of `|` marks.
English Kokoro at 1.06 gives about 3.4 words/s; Urdu at 1.28 about 5.7 syllables/s. Speech should fill 75-90% of the runtime and no gap should exceed about 0.5 s unless the screen is doing something (an explainer payoff).
