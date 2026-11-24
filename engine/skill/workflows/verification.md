# Verification workflow
1. For each ayah: put `(Surah c:v)` in `sub` or `"quran": "c:v"`; show Arabic only as a card copied by `verify.py --fix`; quote translations verbatim in “…” / «…».
2. For each hadith: open the exact sunnah.com page; copy the meaning faithfully; record `sources` (ref, url, grade, wording, checked). Reject weak/fabricated narrations; flag graded-disputed ones to the user.
3. Run `python verify.py file.json` and read `output/<name>/<name>_verification.md`.
4. FAIL: fix the text (never "fix" the source). FLAG: complete the register or get the user's review (`"reviewed": true` or `--reviewed`).
5. Put the source links in the final reply under "Sources:".
