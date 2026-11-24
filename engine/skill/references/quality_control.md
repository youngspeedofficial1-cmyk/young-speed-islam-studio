# Quality control

`qa.py` runs after every render (switch off with `--no-qa`) and inspects the **exported MP4**:

| Check | Pass condition |
|---|---|
| resolution, frame rate, codecs | 1080x1920, 30 fps, H.264 High yuv420p, AAC 48 kHz |
| duration, frame count | matches the render plan within 0.25 s; no missing frames |
| loudness, true peak, clipping | -14 LUFS +-1, <= -1.0 dBTP, 0 clipped samples |
| black frames, frozen picture | none outside the fades; no freeze >= 3 s (WARN) |
| fade in / out, speech start, ending | starts dark, speech within 1.2 s, >= 0.35 s after the last word |
| sync | each spoken line fits its subtitle window; all words revealed before the line leaves |
| typography | no missing glyphs, no overflow, no clipped caption blocks, every block inside the scene's text zone |
| text contrast (WARN) | background behind white text (75th percentile luma, measured at each line's midpoint) <= 165 |

QA cannot judge taste or every collision: in the V2 tests it passed while a bilingual block covered the explainer grid. That is why the contact-sheet look is mandatory, and why text zones and contrast probing were added afterwards.

Outputs: `<name>_qa.md/json` and `<name>_qa_sheet.jpg` (12 frames). **Always look at the contact sheet** and at 2-3 full-size frames at the busiest moments before delivering. Claude cannot hear audio: say so, and give the objective numbers (LUFS, gaps, pitch spread) instead.
