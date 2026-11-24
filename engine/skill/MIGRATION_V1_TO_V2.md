# Migration V1 → V2

Nothing that worked in V1 was removed; all old JSON files still render.

| V1 | V2 |
|---|---|
| `lang` sets voice and text | still works; new `voice_lang` / `text_lang` split them (4 modes) |
| one subtitle language | `text2` + `text2_lang` for bilingual subtitles |
| `{highlight}` and `label` English only | work in Urdu too (Nastaliq labels) |
| manual Quran checks in chat | `verify.py` runs before every render; FAIL blocks, FLAG needs review |
| hadith checked in chat only | `"sources"` register per video (url, grade, wording, date) |
| no output inspection | `qa.py` on every export + 12-frame contact sheet |
| no history | `output/production_log.jsonl` + `log_metrics.py` for real performance data |
| English voice Kokoro | English default **Andrew (edge) -16%**, Kokoro fallback; Urdu voice settings unchanged |
| 23 scenes | + `premium_gold` (Premium Islamic Cinematic / Quran-focused) |

V2.1 (narration fix): Andrew speaks each line in one take; Kokoro splits at most once per line; stress stays inline; English phonemes per phrase; English no longer uses the Urdu base speed. Old scripts with several `|` per line still work: extra pauses are ignored.

To migrate an old script: run `python verify.py old.json --fix`, add `"sources"` for each hadith (or `"quran"` refs for Urdu-only references), then render. Existing scripts in this project already have registers.
