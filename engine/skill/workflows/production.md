# Production workflow: UNDERSTAND → RESEARCH → VERIFY → PLAN → WRITE → DESIGN → NARRATE → ANIMATE → RENDER → INSPECT → DELIVER

1. **Understand**: topic, audience (young Muslims, Urdu/English), the one emotional objective (hope, fear of Allah, gratitude, urgency to repent). Pick the style (brand_identity.md) and language mode.
2. **Research**: find 1-3 core texts (ayah or sahih/hasan hadith) that *carry* the message. Use WebSearch + WebFetch on sunnah.com / quran.com; Quran text comes from the engine's dataset.
3. **Verify**: record every hadith in `"sources"` (url, grade, wording, date). Note grading disagreements for the user. Plan quotes only from verified wording.
4. **Plan**: fill `templates/scene_plan.md`: hook, device, character, turn, payoff, close; scene per line; durations (25-45 s).
5. **Write**: JSON from a template. 8-13 lines. `text` (screen), `say`/`say_hi` (spoken, with `|` and `*`), `mood`, `scene`, `label`, `{highlights}`, `sub` with reference, `hold` on the last 1-2 lines. Mark reflections `"claim": "interpretation"`.
6. **Design**: if the idea needs a new device or scene, add it (scene_design.md contract) and render 3-6 stills at the beats before the full render.
7. **Gate**: `python verify.py file.json --fix` must end in PASS (or FLAG reviewed with the user).
8. **Render**: `python urdu_reels.py file.json` (`--only NAME` for one video). About 4-7 min per 30-40 s video in the cloud; runs in the background.
9. **Inspect**: read `<name>_qa.md` and look at `<name>_qa_sheet.jpg`; fix any FAIL; pull full-size frames at key beats.
10. **Deliver**: mp4, cover, captions; the verification summary with source links; what to check by ear. Update `urdu_reels.zip` if the code changed.
