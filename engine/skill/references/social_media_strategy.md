# Social-media strategy (Reels, Shorts, TikTok, FB)

- **First 2-3 s**: a curiosity hook (number, question, bold claim from a verified text) plus immediate motion. No logo intro.
- **Every 3-5 s** something visibly changes (scene, device state, character pose).
- **Highlighted keywords** (`{...}`) carry the meaning for viewers watching muted.
- **Length**: 25-45 s is the sweet spot. Explainers can run to about 55 s if every beat pays off.
- **Ending**: one action: comment one word or number ("Comment 1, 2, 3 or 4"), or share with someone who needs it. Never fake urgency, never "Allah will punish you if you scroll".
- **Captions**: `<name>_captions.txt` has TikTok, Instagram, YouTube (title <= 100 chars incl. `#shorts`) and Facebook versions; covers in `<name>_cover.jpg`.
- **Credit**: when the core insight comes from a scholar's reflection, say so on screen ("Reflection: Sheikh …") after checking the attribution.
- **Learn from data**: after posting, log real numbers with `python log_metrics.py <name> --views … --likes … --comments … --shares … --saves … --avg-watch …`. Compare hook types and styles in `output/production_log.jsonl` before planning the next batch. Never invent numbers.
