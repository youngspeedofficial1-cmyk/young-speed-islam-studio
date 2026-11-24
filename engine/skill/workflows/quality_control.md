# QA workflow
1. After render, read the QA status line printed by the engine.
2. Open `<name>_qa_sheet.jpg`: text readable on every frame? subject not hidden by text? no clipped Urdu?
3. Pull full-size frames at the busiest beats (`ffmpeg -ss T -frames:v 1`), especially Arabic/Urdu cards.
4. Any FAIL: fix and re-render only what changed (one video via `--only`).
5. Report the objective audio numbers (LUFS, true peak) and say the audio must be checked by ear.
