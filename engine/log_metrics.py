#!/usr/bin/env python3
"""Add real social-media numbers to output/production_log.jsonl (latest record of that video).
   python log_metrics.py NAME --platform tiktok --views 12000 --likes 900 --comments 120 --shares 40 --saves 75 --avg-watch 14.2"""
import argparse, json, os, datetime
p = argparse.ArgumentParser()
p.add_argument("name"); p.add_argument("--platform", default="tiktok")
for k in ("views", "likes", "comments", "shares", "saves"):
    p.add_argument(f"--{k}", type=int)
p.add_argument("--avg-watch", type=float, help="average watch time in seconds")
a = p.parse_args()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "production_log.jsonl")
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
idx = max((i for i, r in enumerate(rows) if r["name"] == a.name), default=None)
if idx is None:
    raise SystemExit(f"no production record for {a.name}")
m = rows[idx].get("metrics") or {}
m[a.platform] = {k: v for k, v in dict(views=a.views, likes=a.likes, comments=a.comments, shares=a.shares, saves=a.saves,
                                        avg_watch_s=a.avg_watch, logged=datetime.date.today().isoformat()).items() if v is not None}
rows[idx]["metrics"] = m
with open(path, "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
print(f"logged {a.platform} metrics for {a.name}")
