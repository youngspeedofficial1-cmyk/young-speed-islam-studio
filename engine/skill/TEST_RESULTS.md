# V2 test results (2026-11-09, cloud workspace, real renderer)

| Test | Mode | Style / scenes | Verification | QA |
|---|---|---|---|---|
| test_en_quran | EN voice + EN text | quran_focused: rain, sea, premium_gold | PASS (39:53 Arabic + Saheeh quotes) | PASS (after the sea band fix; the contrast check first caught a bright sky) |
| test_ur_quran | UR voice + UR text | premium_cinematic: rain, premium_gold, storm_clear, mosque | PASS (39:53 Arabic + 2 Junagarhi Urdu quotes) | PASS |
| test_bilingual_explainer | EN voice + EN text + UR text2 | explainer: mercy_grid | PASS (Bukhari 6000, Muslim 2752 in register) | PASS (after the text-zone auto-fit; the first render overlapped the grid) |

Negative tests: tampered English quote → FAIL; wrong ayah number → FAIL; tampered Urdu quote → FAIL; hadith without register → FLAG.
Pre-flight: English narration over Urdu text without `say` → refused; missing glyphs → listed.
Regression: all 9 existing project videos verify PASS and pass pre-flight.
Voice note: the cloud workspace cannot reach Microsoft, so the English tests used the Kokoro fallback; the Andrew voice runs on the user's computer.

## V2.1 narration fix (2026-11-10)
User report: the bilingual test's reader paused at every word. Causes: per-word phonemisation (every word in stressed dictionary form), lines split into 3-4 TTS takes by several `|`/`*` marks, and English using the Urdu base speed (Andrew at about +1% instead of -16%).
After the fix, on test_bilingual_explainer: 2 takes per line (was 3-4); silences >= 90 ms inside spoken lines = 5, exactly one per marked pause (was 6); QA PASS.
