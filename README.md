# Young Speed Islam Studio

Video engine and voice relays for @YOUNGSPEEDISLAM.

- `engine/` - the urdu_reels video engine (scenes, verification, QA, scripts `videos_*.json`).
- Urdu voice (chosen): **OmniVoice clone of the creator's voice**, reference `voices/me_c6.wav` + `.txt`.
  Push `scripts_ov/<name>.json` -> workflow "OmniVoice Urdu relay" writes `audio/<name>/NN.wav`
  (best of N takes, scored by Whisper). Then `sh tools/fetch_clips.sh <name>` and render with
  `"voice_engine": "clips", "clip_mood_pitch": false` in the video spec.
  Licence: OmniVoice weights are CC-BY-NC (non-commercial).
- `scripts_f5/` + "SPRING_F5 Urdu relay": Apache-2.0 alternative (for a monetized channel).
- `scripts/` + "Urdu voice relay": Microsoft edge-tts voices (Asad/Uzma, en-US-Andrew).
- Finished test scripts live in `*/done/` so they are not regenerated.
