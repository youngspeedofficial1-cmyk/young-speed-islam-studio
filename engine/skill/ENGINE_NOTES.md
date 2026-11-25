# Engine notes: what V2 changed, what is missing, recommendations

## Implemented in V2 (tested)
- `urdu_reels.py`: voice/text language split; bilingual `text2`; Urdu `{highlight}` and labels; caption overflow warnings; pre-flight (missing spoken fields, unknown scenes, missing glyphs via fontTools); verification gate; render metadata `<name>_render.json`; QA hook; production log; Andrew (edge) English engine with automatic Kokoro fallback; `--only`, `--reviewed`, `--skip-verify`, `--no-qa` flags.
- `verify.py` (new): Quran Arabic/English/Urdu verification, hadith register, `--fix`.
- `qa.py` (new): output inspection + contact sheet.
- `log_metrics.py` (new): adds real performance numbers to the production log.
- `scenes_topics.py`: `premium_gold` scene.
- Caption auto-fit into per-scene `text_zone`; background-contrast probe per line; label/sub outlines; bigger Urdu labels.

## Missing (identified, not guessed)
- **Historical style**: no architecture/map/timeline scenes yet (Kaaba-era Makkah, Madinah, caravans, maps). Needs new procedural scenes; be careful with depictions of sacred places.
- **Word-level timing from TTS**: reveals are estimated from chunk durations and character counts. edge-tts emits WordBoundary events; using them would give exact word sync for the Andrew voice.
- **Urdu edge voice with moods/pauses**: `|` and `*` only apply to Kokoro; the edge Urdu path reads the line as one chunk.
- **Background music**: `BGM_FILE` exists but no ducking under the voice; add sidechain-style ducking if music is used.
- **Render speed**: about 0.25 s/frame on 2 CPUs. Biggest costs: bloom + LUT + grain on every full frame, per-frame scene rebuilds of large numpy arrays (`sun_near` shimmer, `storm_clear` rays). Options: cache static layers as uint8, render subtitles onto a smaller ROI, use multiprocessing per shot with the concat demuxer.
- **Automatic style selection** is a creative decision made by the assistant from the skill, not code.

## Arabic row above a line + emojis (Nov 2026)
- `"text0"`: Arabic wording shown in gold above the English (`ARABIC_TOP_SCALE`, `ARABIC_TOP_GAP`). It must be an exact,
  contiguous excerpt of its source, or `verify.py` FAILs:
  - hadith: `"text0_ref": "<ref>"` and the sources entry carries the full Arabic in `"arabic"` (copy it from a dataset such as
    github.com/AhmedBaset/hadith-json, never type it by hand);
  - Quran: `"text0_quran": "c:v"` (checked against Tanzil).
- Emojis: put them as separate words in the English `text` (e.g. `"... today. 🤍"`); they are drawn from
  `fonts/NotoColorEmoji.ttf`. Keep them out of quoted hadith/ayah lines and out of the Urdu `text2`. Always give `say` so emojis are not spoken.

## Light theme (default for new videos, Nov 2026)
- `THEMES["light"]` in `urdu_reels.py`: dark ink text (40,36,48), deep-gold highlights (168,104,14), cream halo and band behind
  the words, teal labels. The theme comes from the first scene's `theme` attribute, or the script's `"theme": "light"|"dark"`.
- Light renders: no bloom, vignette 0.10 (dark 0.34), an airy LUT, fades and dip transitions to cream (250,245,235).
- `qa.py` is theme-aware: on light videos the contrast check warns when the background behind text is darker than luma 150,
  and fades must reach cream (luma >= 235) instead of black.
- Light scenes live in `scenes_light.py` (`LightStage` base: `theme = "light"`, ink-coloured stick figures):
  `soft_light` (cream to peach, faint 8-point-star lattice, pastel bokeh, petals) and `light_sky` (pale sky, clouds, sun rays, sage hills).
- Palette for new light scenes: cream (250,245,235), sand (240,226,204), peach (246,214,190), sky (206,226,240), sage (200,220,196),
  blush (244,214,214); ink (52,46,58); accent gold (176,120,40). Keep backgrounds above luma ~170 where text sits.

## Title card / thumbnail at the start (Nov 2026)
- Every video now opens with a 0.30 s title card (`THUMB_DUR`) that dissolves into the video over 0.25 s (`THUMB_XF`).
  TikTok and Instagram use the first frame as the default cover, so no manual cover pick is needed. The same image is saved as `<name>_cover.jpg`.
- Script fields: `"thumb_title"` (2-6 words; `{word}` = accent colour; default = `"title"`), `"thumb_title_ur"` (optional Urdu line),
  `"thumb_t"` (seconds into the video for the background, default 55 % of the length), `"thumbnail": false` to switch it off.
- The audio is padded with 0.30 s of real silence (`adelay`), not a start-time offset, so platforms that ignore stream offsets stay in sync.
- `qa.py` reads `thumb` from the render metadata and shifts duration, fade and ending checks by it.

## Cinematic sound design (Nov 2026) - no instruments, no melody
- Generated in code (no samples, no copyright): `drama_bed` (non-tonal low rumble with slow swells), `sfx_rise` (noise riser),
  `sfx_hit` (low boom sweeping 90->32 Hz + transient + tail), `sfx_heart` (soft lub-dub). Mixed under the voice with ducking (-55 % while speaking).
- Levels: `DRONE_DB -27`, `HIT_DB -13`, `RISE_DB -21`, `HEART_DB -20`; impacts at least `SFX_MIN_GAP` = 4 s apart.
- Auto cues (`sfx_plan`): riser + impact into every Arabic card and every highlighted `heavy`/`firm` line; heartbeat under `heavy` lines.
- Script: `"sfx": "dramatic"` (default) | `"calm"` (drone only) | `"off"`; per line `"sfx": "hit" | "rise" | "heart" | "none"`.
- Kept instrument-free on purpose (the channel's own content follows scholars who avoid music). Optional `BGM_FILE` is for vocals-only nasheeds the user supplies.

## Long story videos (2-3 min) - lessons from "The Night They Bury You" (Nov 2026)
- `grave_story` (scenes_light.py): one continuous cut-away shot with a vertical camera (`DROP`): above ground for the
  funeral, sinks into the grave on the `hear` beat, rises to a golden sky on `ayah`. The upper soil is light sand so the
  light-theme text stays readable while the camera is underground. Keep this pattern for any story that moves between places.
- New sound cues: `"sfx": "steps"` (footsteps walking away, fading) and `"sfx": "soil"` (earth falling) - `STEPS_DB`, `SOIL_DB`.
- Never draw symbols with a font that may lack them (Lora has no ✓): draw ticks/crosses as lines. `qa.py` only checks caption glyphs.
- A 39-line, 144 s video takes ~25 min here (TTS ~5 min + ~6 frames/s). Blend large backgrounds only on the visible slice.
- QA warns above 90 s ("length for Reels/Shorts"); that is expected for long-form.
- Running two long renders in parallel can kill one silently while mixing audio (memory): render long videos one at a time.
- Lines with a long quote + Arabic row + Urdu can overflow the text zone (QA FAIL "text fits"): move the speaker tag ("They said:") to `say` only and trim the Arabic row to the core phrase.

## Urdu cloned voice via GitHub relay (Nov 2026, user-approved)
- Repo: youngspeedofficial1-cmyk/young-speed-islam-studio (private). The engine also lives in `engine/`.
- Chosen voice: OmniVoice clone of the creator's own voice, reference `voices/me_c6.wav` with exact text in `me_c6.txt`
  ("نبی کریم صلی اللہ علیہ وآلہ وسلم کا ارشاد گرامی ہے، نماز جنت کی کنجی ہے۔"). Plain spellings of اللہ / صلی اللہ علیہ وسلم are fine.
- Flow: push `scripts_ov/<name>.json` ({"videos":[{"name","ref":"voices/me_c6.wav","takes":2,"lines":[{"say_ur"}]}]}) ->
  workflow writes `audio/<name>/NN.wav` (~80 s per take on the free runner; best take by Whisper CER) -> pull ->
  copy to `clips/<name>/line_NN.wav` (NN from 01) -> spec `"voice_engine":"clips","clips_dir":"clips","clip_mood_pitch":false`.
- The reference transcript must be exact: a wrong ref_text caused mispronunciations and rushed speech.
- Move finished scripts to `scripts_ov/done/` so the relay does not regenerate them; the workflow checks out `main`.
- Licence: OmniVoice weights CC-BY-NC (non-commercial). For a monetized channel use the SPRING_F5 relay (Apache-2.0) or ElevenLabs.
- Emoji regex now covers ⏳⌛ (U+231A-231B, U+23E9-23FA).
- Cover title position: spec "thumb_y" (title centre as a fraction of height, default 0.47); pick "thumb_t" on a frame whose subject sits below the title.

## Character voices, ambience beds and clue lines (Nov 2026)
- Per line `"bg": [{"clip": "clips/bg/<voice>_NN.wav", "at": s, "pan": -1..1, "gain": dB}]` places a character's line in
  the scene (light room reverb, panned, not ducked). Make them with the "OmniVoice background voices" workflow:
  push `scripts_bg/<file>.json` with one video per voice and `"instruct"` (e.g. "male, elderly, low pitch", "male, child,
  high pitch"), `"num_step": 16` (~4 min for 12 lines). Copy `audio/<voice>/NN.wav` to `clips/bg/<voice>_NN.wav`.
- Per line `"amb": ["birds" | "street" | "murmur" | "wind"]` adds a synthesized real-life bed (ducked under narration).
  `"murmur"` mixes the spec's `"murmur_clips"` into distant crowd chatter.
- Clue lines: `"speak": false` + `"hold"` = the line's total length; time the `bg` voices inside it, and leave the narrator
  silent so the characters are heard. Clues must come from the hadith text itself.
- `"hold"` is a MINIMUM line length (max(hold, natural + 0.5)), not an extra pause.
