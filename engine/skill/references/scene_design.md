# Scene design

## Catalogue (`"scene"` values)
| Key | File | Ambience | Text y | Notes |
|---|---|---|---|---|
| sea, rain, town, forest, room, meadow, mosque | scenes.py | matching | 0.585 | nature set; camera moves |
| graveyard, grave_inside | scenes_topics.py | wind / earth | -, 0.50 | grave: figures walk away, shroud in the lahd |
| sun_near, mountains_dust, sky_split | scenes_topics.py | heat / storm | 0.74, -, - | Judgment |
| hourglass, candle, candle_out, autumn, sunset | scenes_topics.py | clock / candle / sea | 0.66, 0.66, 0.66, -, 0.34 | death and time; candle_out goes out 2 s into the shot |
| desert_rain, storm_clear, mother_child, night_prayer | scenes_topics.py | rain / storm-to-birds / meadow / night | -, 0.73, 0.20, 0.56 | mercy and tawbah; time-based reveals start at shot start |
| premium_gold | scenes_topics.py | night room | 0.50 | charcoal and gold lattice; static camera; Quran-focused |
| mercy_grid | scenes_explainer.py | night room | 0.255 | beats: hook, light_one, mother, mare, others, light_99, ayah, cta |
| four_questions | scenes_explainer.py | heat | 0.235 | beats: hook, q1-q4, reflect, ayah, cta |
| three_after_death | scenes_explainer.py | night room | 0.235 | deeds counter; beats: life, death, except, e1-e3, reflect, ayah, cta |
| seven_shade | scenes_explainer.py | heat | 0.235 | 7 figures walk into a cool shade on a burning plain; beats: hook, seven, s1-s7, reflect, cta |

## Scene contract (adding a new scene)
```python
class MyScene(Scene):              # from scenes import Scene, helpers
    ambience = "rain"              # key in urdu_reels.ambience()
    bokeh, bokeh_n = (255,230,200), 5
    text_y = 0.30                  # optional: subtitle centre (fraction of H), keep clear of the subject
    band = 1.5                     # optional: stronger dark band behind text on bright scenes
    text_zone = (0.165, 0.365)     # optional: subtitles must stay inside this band (fractions of H); default (0.165, 0.78)
    camera = "static"              # optional: disables camera moves (explainers)
    def build(self): ...           # draw static layers ONCE (performance)
    def frame(self, t): ...        # return PIL RGB (W x H); t starts at 3.0 at the shot start
    def set_timeline(self, items): # optional: [(local_start, dur, line)] for "beat" driven scenes
```
Register the class in the module's dict (`TOPIC_SCENES` / `EXPLAINER_SCENES`). Test with a still at the busiest beat before any full render.

Captions are **auto-fitted**: if label + text + sub + `text2` do not fit the scene's `text_zone`, the block shrinks (100%, 90%, 80%, 72%) and moves; if it still does not fit, QA fails with "does not fit the scene's text zone". Explainer devices must declare their `text_zone`.

## Safe zones (TikTok / Reels / Shorts)
Top 0-0.11 H: platform tabs (channel tag sits at 0.115). Bottom 0.80-1.0 H: captions and buttons; keep text and key subjects above 0.78 H. Right 120 px: icon column; text max width is 860 px.

## Light scenes (preferred for new videos)
| key | look | use |
|---|---|---|
| `soft_light` | cream to peach, faint Islamic star lattice, pastel bokeh, drifting petals | quotes, ayah and hadith cards, any explainer without its own device |
| `light_sky` | pale morning sky, drifting clouds, sun rays, sage hills, birds | hope, dua, nature narration |
New explainer devices should subclass `LightStage` (scenes_light.py) and use the light palette in ENGINE_NOTES.
| `grave_story` | cut-away: sky + graveyard above, grave chamber below; vertical camera | the burial story (2.5 min) |
| `cave_story` | mountain cut-away with a cave; rain, boulder seals and opens in thirds; memory bubbles | the three men in the cave (Bukhari 2272) |
| `last_man_story` | long horizontal world, camera follows a man from the Fire's glow past three trees to the gate | the last man to enter Paradise (Muslim 187) |
