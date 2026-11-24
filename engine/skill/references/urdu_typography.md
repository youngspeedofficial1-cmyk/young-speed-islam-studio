# Urdu, Arabic and English typography

## How shaping works here (do not add arabic-reshaper / python-bidi)
Pillow 12 with **libraqm** does full OpenType shaping (Nastaliq ligatures, joining, RTL order). Passing pre-reshaped text from `arabic-reshaper`/`python-bidi` on top of raqm *breaks* the text (double reshaping, reversed words). The engine warns at start-up if raqm is missing; then reinstall Pillow from the official wheels instead of adding reshapers.

## Modes (per video)
| `voice_lang` / `text_lang` | Fields per line |
|---|---|
| en / en | `text`, `say` |
| ur / ur | `text` (Urdu), `say_hi` (kokoro) or `say_ur` (edge) |
| en / ur | `text` (Urdu), `say` (English) |
| ur / en | `text` (English), `say_hi`/`say_ur` |
| bilingual | any of the above plus `text2` (second language, 62% size, under the main line); `text2_lang` sets its language (default: the other one) |
The pre-flight check refuses to render if a mode is missing its spoken field.

## Styling tools
- `{word}` or `{several words}`: gold highlight (works in Urdu and English).
- Words containing اللہ / اللَّه / Allah and the ﷺ sign are gold automatically.
- `"label"`: small heading above the line (English becomes spaced small caps in teal; Urdu stays Nastaliq).
- `"sub"`: translation or reference under the line (Lora Italic or Nastaliq, chosen by script).
- Arabic cards (`"font": "arabic"`) shrink from 78 px down to 44 px before wrapping to more than 2 rows.

## Checks
Pre-flight lists missing glyphs per font (they would show as boxes); Caption records lines wider than 860 px and blocks taller than the canvas; QA fails the video on either. Keep Urdu lines at 2-7 words and English at 3-10 words; split longer sentences into two lines.
