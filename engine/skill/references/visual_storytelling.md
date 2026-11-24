# Visual storytelling

Every scene must earn its place: it **shows** what the line **says**, or it holds the mood the line needs.

## Planning a video (before writing JSON)
1. **One idea**, the sentence a viewer would repeat to a friend.
2. **Hook (0-3 s)**: a number ("100 parts", "4 questions"), a direct question ("Do you think your sins are too many?") or a striking image with a short claim. Never open with "In this video…".
3. **Device**: for explainers, one on-screen object that tracks progress (grid, checklist, counter, bar). It stays on screen for the whole video.
4. **Character**: one recurring figure whose pose changes with the story (sad, then looking up, then sujood).
5. **Turn**: the line where the meaning flips ("So where are the other 99?").
6. **Payoff**: the visual and verbal resolution (99 cells light up; dawn).
7. **Close**: a verified ayah or hadith card, or a comment prompt the viewer can answer in one word or number.

## Shot rules
- Change the scene (or a device state) at least every 3-5 s; consecutive lines on the same scene become one continuous shot.
- Never put two bright scenes in a row behind white text; scenes with bright skies set `text_y`/`band` (see scene_design.md).
- One transition style per cut, chosen by the engine (fade / leak / blur / dip). Do not ask for more.
- Pauses (`|`) need something moving on screen: rain, a walking figure, a lighting cell.
- Ending: the last line gets `hold` >= 2.6 s so the viewer can read the reference.

## Metaphors already available
time running out (`hourglass`), life ending (`candle_out`, `sunset`), revival and mercy (`desert_rain`, `storm_clear`), loneliness and the grave (`grave_inside`, `graveyard`), Judgment (`sun_near`, `sky_split`, `mountains_dust`), worship at night (`night_prayer`), care (`mother_child`), the earth's beauty (nature set), Quran majesty (`premium_gold`).
