# Brand identity: Young Speed Islam

**Handle:** `@YOUNGSPEEDISLAM`, drawn faintly near the top (`CHANNEL_TAG`, y = 0.115 H) on every video.
**Promise:** calm, beautiful, *verified* reminders. Quality and authenticity come before quantity and virality.

## Constants across all six styles
| Element | Rule |
|---|---|
| Format | 1080x1920, 30 fps, one master for TikTok, Reels, Shorts and FB Reels |
| Palette | Gold (255,198,92) / soft gold (255,222,150) for Allah, ﷺ and `{highlights}`; warm white (255,255,250) body text; teal (120,210,180) small-caps labels |
| Latin type | Lora 600 (main), Lora Italic (translations, references) |
| Urdu type | Noto Nastaliq Urdu (headlines, subtitles, Urdu translations) |
| Arabic type | Amiri (Quranic text; also ﷺ inside English lines) |
| Look | Cinematic grade (lifted blacks, warm highlights, cool shadows), soft vignette, fine grain, gentle bloom |
| Sound | No music by default; scene ambience at -21 dB, soft whooshes on scene changes; voice in front; -14 LUFS |
| Ending | Quran or hadith card with the Arabic, a verified translation and the reference, OR a comment prompt; always a fade-out |
| Respect | No depiction of prophets, angels or Allah; no faces; human figures are silhouettes or stick figures; never mock or sensationalise |

## The six styles (pick automatically; the user can override with `"style"`)
| Style | Use when | Engine building blocks |
|---|---|---|
| `premium_cinematic` | strong single message, short emotional reminder | `premium_gold`, `mosque`, `night_prayer`, `candle`, gold highlights |
| `nature_narration` | gentle reflection, tawakkul, dua, gratitude | `sea`, `rain`, `forest`, `meadow`, `room`, `sunset`, `storm_clear`, `desert_rain` |
| `explainer` | a teachable structure: a number, a list, a comparison, "X kinds of…" | `mercy_grid`, `four_questions` (new devices are added in `scenes_explainer.py`) |
| `animated_story` | a hadith or ayah with action (walk away, flee, return, kneel) | stick figures (`draw_stick`, `POSES`), `grave_inside`, `graveyard`, `mother_child`, explainer scenes |
| `quran_focused` | one or two ayat carry the whole video | `premium_gold` + Arabic card (`font: arabic`) + translation `sub`, `label: "Allah says"` |
| `historical` | seerah, sahaba, places | **NOT YET IN THE ENGINE.** Needs architecture, map and timeline scenes; see ENGINE_NOTES.md. Until then, use nature or premium scenes and avoid unsupported historical claims |
