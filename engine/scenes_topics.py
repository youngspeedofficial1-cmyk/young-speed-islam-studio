"""
Topic scenes for akhirah reminders (grave, Day of Judgment, death, mercy, repentance).
Same contract as scenes.py: Scene(w, h, seed).frame(t) -> PIL RGB.
Optional class attribute text_y: subtitle centre as a fraction of height for that scene.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scenes import (Scene, vgrad, smooth, to_img, blur_mask, add_glow, radial, blob_sprite, cloud,
                    ridge, fill_below, wrap_x, Rain, Motes, person)


def branch(d, x, y, ang, length, width, depth, rng, col, tips=None):
    if depth == 0 or length < 4:
        if tips is not None:
            tips.append((x, y))
        return
    x2, y2 = x + math.cos(ang) * length, y - math.sin(ang) * length
    d.line([(x, y), (x2, y2)], fill=col, width=max(1, int(width)))
    n = 2 if rng.random() < 0.7 else 3
    for k in range(n):
        a = ang + rng.uniform(-0.65, 0.65) + (k - (n - 1) / 2) * 0.25
        branch(d, x2, y2, a, length * rng.uniform(0.62, 0.80), width * 0.68, depth - 1, rng, col, tips)


def fog_sprite(w, h, rng, n=12, alpha=90, blur=40):
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(h * 0.3, h * 0.7)
        rx, ry = rng.uniform(w * 0.08, w * 0.2), rng.uniform(h * 0.15, h * 0.3)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=alpha)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255


def tiny_person(d, x, y, s, col):
    d.ellipse([x - 3.2 * s, y - 17 * s, x + 3.2 * s, y - 10.6 * s], fill=col)
    d.rounded_rectangle([x - 4.2 * s, y - 11 * s, x + 4.2 * s, y], radius=max(1, int(2.5 * s)), fill=col)


# ------------------------------------------------------------------ GRAVE
class Graveyard(Scene):
    ambience = "wind_night"
    bokeh = (190, 200, 230)
    bokeh_n = 5

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        hz = int(h * 0.60)
        a = vgrad(w, h, [(0, (6, 10, 24)), (0.40, (24, 34, 58)), (0.60, (58, 66, 88)), (0.61, (30, 32, 38)), (1, (12, 12, 16))])
        self.moon = (w * 0.68, h * 0.22)
        a = add_glow(a, radial(w, h, *self.moon, 260 * u), (150, 160, 190), 0.55)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        disc = np.clip(70 * u - np.hypot(xx - self.moon[0], yy - self.moon[1]) + 0.5, 0, 1)
        a = a * (1 - disc[..., None]) + np.array([236, 236, 226], np.float32) * disc[..., None]
        a = fill_below(a, ridge(w, rng, hz - 30 * u, 22 * u), (26, 30, 44))
        a = fill_below(a, np.full(w, hz, np.float32), (34, 34, 40))
        bg = to_img(a); d = ImageDraw.Draw(bg)
        # graves: low earth mounds with plain head/foot stones, in receding rows
        rows = 5
        for r in range(rows):
            p = r / (rows - 1)
            y = hz + 30 * u + (h - hz) * (p ** 1.6) * 0.92
            s = (0.55 + 1.9 * p ** 1.3) * u
            n = int(6 - 3 * p)
            for k in range(n):
                x = (k + 0.5 + rng.uniform(-0.25, 0.25)) / n * w
                L, Wd = 150 * s, 40 * s
                col = tuple(int(c) for c in np.array([52, 44, 38]) * (0.6 + 0.4 * p))
                d.ellipse([x - L / 2, y - Wd / 2, x + L / 2, y + Wd / 2], fill=col)
                d.ellipse([x - L / 2 + 6 * s, y - Wd / 2, x + L / 2 - 6 * s, y + Wd / 4], fill=tuple(min(255, c + 14) for c in col))
                st = tuple(int(c * (0.7 + 0.5 * p)) for c in (88, 90, 96))
                for sx in (x - L / 2 + 8 * s, x + L / 2 - 8 * s):
                    hh = (34 if sx < x else 24) * s
                    d.rounded_rectangle([sx - 7 * s, y - hh, sx + 7 * s, y + 4 * s], radius=max(1, int(6 * s)), fill=st)
        # bare tree
        tips = []
        branch(d, w * 0.12, hz + 40 * u, math.radians(84), 260 * u, 26 * u, 8, rng, (8, 8, 12), tips)
        branch(d, w * 0.96, hz + 10 * u, math.radians(100), 180 * u, 18 * u, 7, rng, (10, 10, 14), tips)
        self.bg = bg
        self.fog = fog_sprite(w * 2, int(h * 0.30), rng, n=16, alpha=110, blur=50 * u)
        self.fog2 = fog_sprite(w * 2, int(h * 0.25), rng, n=12, alpha=80, blur=40 * u)
        self.hz = hz
        self.clouds = [(blob_sprite(int(560 * u), int(150 * u), rng, n=10, lit=(120, 126, 150), mid=(70, 76, 100), shade=(36, 40, 60)),
                        rng.uniform(-200, w), rng.uniform(0.12, 0.30) * h, rng.uniform(8, 14) * u) for _ in range(3)] if False else []
        self.wisps = []
        for _ in range(3):
            m = Image.new("L", (int(620 * u), int(110 * u)), 0); dm = ImageDraw.Draw(m)
            for _ in range(6):
                x = rng.uniform(50, 520) * u; y = rng.uniform(30, 70) * u
                dm.ellipse([x - 110 * u, y - 16 * u, x + 110 * u, y + 16 * u], fill=120)
            m = m.filter(ImageFilter.GaussianBlur(14 * u))
            spr = Image.new("RGBA", m.size, (40, 46, 70, 0)); spr.putalpha(m)
            self.wisps.append((spr, rng.uniform(-300, w), rng.uniform(0.12, 0.30) * h, rng.uniform(10, 18) * u))

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = np.asarray(self.bg, np.float32).copy()
        for fog, y0, sp, col in ((self.fog2, self.hz - int(120 * u), 10, (120, 130, 160)), (self.fog, self.hz + int(60 * u), 18, (150, 156, 176))):
            f = np.roll(fog, -int(t * sp * u) % w, axis=1)[:, :w]
            y1 = min(h, y0 + f.shape[0])
            arr[y0:y1] = arr[y0:y1] * (1 - f[:y1 - y0, :, None] * 0.6) + np.array(col, np.float32) * f[:y1 - y0, :, None] * 0.6
        im = to_img(arr)
        for spr, x0, y, v in self.wisps:
            im.paste(spr, (int(wrap_x(x0, v, t, spr.width, w)), int(y)), spr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        # a lone visitor making dua at a grave
        x, y, s = w * 0.70, self.hz + 0.25 * h, 1.9 * u
        person(d, x, y, s, 0, (6, 6, 10, 255), walk=False)
        for side in (-1, 1):   # hands raised in dua at chest height
            d.line([(x + side * 11 * s, y - 94 * s), (x + side * 20 * s, y - 80 * s), (x + side * 13 * s, y - 100 * s)], fill=(6, 6, 10, 255), width=int(5 * s), joint="curve")
            d.ellipse([x + side * 13 * s - 5 * s, y - 108 * s, x + side * 13 * s + 5 * s, y - 96 * s], fill=(6, 6, 10, 255))
        im.paste(ov, (0, 0), ov)
        return im


class GraveInside(Scene):
    ambience = "earth"
    bokeh = (200, 190, 170)
    bokeh_n = 3
    text_y = 0.50

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.surf = sy = int(h * 0.26)
        a = vgrad(w, h, [(0, (8, 12, 26)), (0.255, (36, 42, 64)), (0.26, (40, 30, 22)), (0.5, (30, 22, 16)), (1, (10, 8, 6))])
        # soil strata
        for k in range(9):
            y0 = sy + (h - sy) * (k + 1) / 10 + rng.uniform(-20, 20) * u
            ys = ridge(w, rng, y0, 10 * u, 3)
            tone = rng.uniform(-10, 10)
            yy = np.arange(h, dtype=np.float32)[:, None]
            band = np.exp(-((yy - ys[None, :]) / (14 * u)) ** 2)
            a += band[..., None] * np.array([tone + 8, tone + 5, tone + 2], np.float32)
        bg = to_img(a); d = ImageDraw.Draw(bg)
        for _ in range(260):
            x, y, r = rng.uniform(0, w), rng.uniform(sy + 20 * u, h), rng.uniform(2, 9) * u
            c = int(rng.uniform(40, 80)); d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=(c, c - 8, c - 16))
        for _ in range(9):  # roots
            x = rng.uniform(0, w); y = sy
            pts = [(x, y)]
            for _ in range(14):
                x += rng.uniform(-16, 16) * u; y += rng.uniform(10, 26) * u; pts.append((x, y))
            d.line(pts, fill=(58, 40, 26), width=max(2, int(rng.uniform(2, 6) * u)))
        # surface: grass line + grave mound + stones
        d.rectangle([0, sy - 4 * u, w, sy + 6 * u], fill=(24, 30, 22))
        mx = w * 0.5
        d.chord([mx - 220 * u, sy - 46 * u, mx + 220 * u, sy + 40 * u], 180, 360, fill=(58, 44, 32))
        for sx, hh in ((mx - 196 * u, 70), (mx + 196 * u, 52)):
            d.rounded_rectangle([sx - 12 * u, sy - hh * u, sx + 12 * u, sy], radius=int(10 * u), fill=(96, 98, 104))
        # the chamber (lahd) and the shrouded body
        cy = h * 0.74
        self.cy = cy
        d.rounded_rectangle([mx - 330 * u, cy - 110 * u, mx + 330 * u, cy + 70 * u], radius=int(20 * u), fill=(6, 5, 4))
        sh = (176, 170, 156)
        d.polygon([(mx - 200 * u, cy - 34 * u), (mx - 60 * u, cy - 44 * u), (mx + 120 * u, cy - 30 * u), (mx + 260 * u, cy - 6 * u),
                   (mx + 280 * u, cy + 16 * u), (mx + 260 * u, cy + 40 * u), (mx + 120 * u, cy + 50 * u), (mx - 60 * u, cy + 54 * u), (mx - 200 * u, cy + 48 * u)], fill=sh)
        d.ellipse([mx - 290 * u, cy - 34 * u, mx - 180 * u, cy + 50 * u], fill=(184, 178, 164))
        for tx in (mx - 210 * u, mx + 40 * u, mx + 240 * u):
            d.line([(tx, cy - 38 * u), (tx, cy + 50 * u)], fill=(128, 120, 106), width=int(5 * u))
        d.line([(mx - 170 * u, cy + 8 * u), (mx + 250 * u, cy + 14 * u)], fill=(150, 144, 130), width=int(3 * u))
        # unbaked bricks closing the niche
        for k in range(7):
            bx = mx - 330 * u + k * 94 * u
            d.polygon([(bx, cy - 110 * u), (bx + 90 * u, cy - 110 * u), (bx + 70 * u, cy - 150 * u), (bx + 4 * u, cy - 150 * u)], fill=(70, 52, 38))
        self.bg = bg
        self.dark = radial(w, h, mx, cy, 420 * u)
        self.glow = radial(w, h, mx, cy - 10 * u, 300 * u)
        self.walkers = [(mx + rng.uniform(-120, 120) * u, rng.choice([-1, 1]) * rng.uniform(26, 40) * u, rng.uniform(0.9, 1.15)) for _ in range(5)]
        self.dust = Motes(rng, 40, (mx - 340 * u, cy - 120 * u, mx + 340 * u, cy + 80 * u), color=(220, 210, 180), r=(0.8 * u, 1.8 * u), rise=3, sway=8)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        arr = np.asarray(self.bg, np.float32).copy()
        g = float(smooth(2.0, 6.0, lt))
        arr = add_glow(arr, self.glow, (255, 226, 160), 0.18 * g)
        arr *= (0.55 + 0.45 * self.dark)[..., None]
        im = to_img(arr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        # family walking away on the surface
        for x0, v, s in self.walkers:
            x = x0 + v * max(0.0, lt) * 2.2
            person(d, x, self.surf - 4 * u, 0.95 * u * s, t + x0, (4, 4, 8, 255), walk=True)
        self.dust.draw(d, t)
        im.paste(ov, (0, 0), ov)
        return im


# ------------------------------------------------------------------ JUDGMENT
class SunNear(Scene):
    ambience = "heat"
    text_y = 0.74
    band = 1.5
    bokeh = (255, 180, 90)
    bokeh_n = 4

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        hz = int(h * 0.64)
        a = vgrad(w, h, [(0, (255, 214, 120)), (0.30, (250, 150, 60)), (0.55, (196, 72, 36)), (0.64, (150, 50, 30)), (0.641, (226, 160, 96)), (1, (150, 92, 56))])
        self.sun = (w * 0.5, -h * 0.02)
        a = add_glow(a, radial(w, h, *self.sun, 900 * u), (255, 240, 200), 0.6)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dsun = np.hypot(xx - self.sun[0], yy - self.sun[1])
        disc = np.clip(560 * u - dsun + 1, 0, 1)
        a = a * (1 - disc[..., None]) + np.array([255, 250, 230], np.float32) * disc[..., None]
        bg = to_img(a); d = ImageDraw.Draw(bg)
        # vast crowd in perspective
        rows = 46
        for r in range(rows):
            p = (r / (rows - 1)) ** 1.8
            y = hz + 10 * u + (h - hz) * p * 1.0
            s = (0.45 + 4.4 * p) * u
            step = 15 * s
            x = -rng.uniform(0, step)
            col = int(40 + 50 * (1 - p))
            while x < w + step:
                if rng.random() < 0.85:
                    xx, yy = x + rng.uniform(-3, 3) * s, y + rng.uniform(-2, 2) * s
                    tiny_person(d, xx, yy, s, (col, int(col * 0.62), int(col * 0.48)))
                    if s > 1.2 * u:
                        d.arc([xx - 3.2 * s, yy - 17 * s, xx + 3.2 * s, yy - 10.6 * s], 200, 340, fill=(255, 210, 150), width=max(1, int(s * 0.8)))
                x += step * rng.uniform(0.8, 1.25)
        self.bg = bg
        self.hz = hz
        self.dust = Motes(rng, 70, (0, h * 0.3, w, h), color=(255, 200, 140), r=(1.2 * u, 2.6 * u), rise=-6, sway=50 * u)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = np.asarray(self.bg, np.float32)
        y0 = self.hz - int(60 * u)
        band = arr[y0:].copy()
        rows = np.arange(band.shape[0])
        shift = (3 * u * np.sin(rows * 0.07 + t * 6) * (rows / len(rows))).astype(int)
        for k in range(0, len(rows), 3):
            band[k:k + 3] = np.roll(band[k:k + 3], shift[k], axis=1)
        arr = arr.copy(); arr[y0:] = band
        pulse = 0.12 + 0.06 * math.sin(t * 2.4)
        arr[: int(h * 0.5)] += pulse * 40
        im = to_img(arr)
        ov = self.overlay(); self.dust.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class MountainsDust(Scene):
    ambience = "storm_wind"
    bokeh = (220, 200, 230)
    bokeh_n = 4

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.base = vgrad(w, h, [(0, (40, 30, 56)), (0.45, (120, 80, 100)), (0.62, (200, 140, 120)), (1, (60, 40, 50))])
        self.ridges = [(ridge(w, rng, h * 0.42, 190 * u, 2), (70, 58, 80), 0.6),
                       (ridge(w, rng, h * 0.56, 150 * u, 2), (44, 36, 54), 0.9),
                       (ridge(w, rng, h * 0.72, 110 * u, 2), (24, 20, 32), 1.2)]
        n = 2600
        self.pk = np.c_[rng.integers(0, 3, n), rng.uniform(0, w, n), rng.uniform(0, 4.0, n), rng.uniform(20, 60, n) * u,
                        rng.uniform(-30, 50, n) * u, rng.uniform(1.6, 4.6, n) * u]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = self.base.copy()
        cur = []
        for k, (rd, col, speed) in enumerate(self.ridges):
            ys = rd + speed * 9 * u * t
            arr = fill_below(arr, ys, col, soft=2.0)
            cur.append((ys, col))
        im = to_img(arr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        for k, x, ph, vy, vx, r in self.pk:
            age = (t + ph) % 4.0
            ys, col = cur[int(k)]
            xi = int(min(w - 1, max(0, x)))
            px = x + vx * age + 12 * u * math.sin(age * 2 + ph)
            py = ys[xi] - vy * age
            a = int(220 * (1 - age / 4.0) * min(1.0, age * 3))
            c = tuple(min(255, int(v * 1.9 + 40)) for v in col)
            rr = r * (1 + age * 0.8)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=c + (a,))
        ov = ov.filter(ImageFilter.GaussianBlur(1.2))
        im.paste(ov, (0, 0), ov)
        return im


class SkySplit(Scene):
    ambience = "storm"
    bokeh = (255, 230, 180)
    bokeh_n = 4

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (10, 8, 20)), (0.5, (34, 24, 44)), (0.78, (60, 40, 50)), (0.781, (14, 12, 18)), (1, (6, 6, 10))])
        self.base = a
        # the crack: a jagged path across the sky
        pts, x, y = [], -40.0, h * 0.20
        while x < w + 40:
            pts.append((x, y)); x += rng.uniform(40, 90) * u; y += rng.uniform(-50, 50) * u
            y = min(max(y, h * 0.08), h * 0.38)
        self.crack = pts
        self.branches = []
        for _ in range(9):
            i = rng.integers(1, len(pts) - 1); bx, by = pts[i]; bp = [(bx, by)]
            ang = rng.uniform(0.3, 2.8) * (1 if rng.random() < 0.5 else -1)
            for _ in range(rng.integers(3, 7)):
                bx += math.cos(ang) * rng.uniform(30, 70) * u; by += math.sin(ang) * rng.uniform(30, 70) * u
                ang += rng.uniform(-0.5, 0.5); bp.append((bx, by))
            self.branches.append(bp)
        self.figs = [(rng.uniform(0.1, 0.9) * w, rng.uniform(0.8, 1.2)) for _ in range(9)]
        n = 40
        self.fall = np.c_[rng.uniform(0, w, n), rng.uniform(0, 6, n), rng.uniform(500, 900, n) * u]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        open_ = 0.25 + 0.75 * float(smooth(-1.0, 6.0, lt))
        m = Image.new("L", (w // 2, h // 2), 0); d = ImageDraw.Draw(m)
        half = [(x / 2, y / 2) for x, y in self.crack]
        d.line(half, fill=255, width=max(2, int(10 * open_ * u)))
        for bp in self.branches:
            d.line([(x / 2, y / 2) for x, y in bp], fill=int(200 * open_), width=max(1, int(4 * open_ * u)))
        core = np.asarray(m.resize((w, h)), np.float32) / 255
        glow = np.asarray(m.filter(ImageFilter.GaussianBlur(30 * u)).resize((w, h)), np.float32) / 255
        flash = 0.0
        tf = t % 5.3
        if tf < 0.25:
            flash = math.sin(tf / 0.25 * math.pi) * 0.5
        arr = self.base + flash * 70
        arr = add_glow(arr, glow, (255, 210, 150), 2.2 * open_)
        arr = arr * (1 - core[..., None]) + np.array([255, 250, 235], np.float32) * core[..., None]
        im = to_img(arr)
        ov = self.overlay(); dd = ImageDraw.Draw(ov)
        for x, ph, v in self.fall:
            age = (t + ph) % 6
            y = h * 0.05 + v * age * 0.4
            if y > h * 0.76:
                continue
            dd.line([(x - 0.15 * v * 0.1, y - 60 * u), (x, y)], fill=(255, 236, 200, 160), width=max(2, int(2 * u)))
        gy = h * 0.78
        for x, s in self.figs:
            person(dd, x, gy + 4 * u, 0.9 * u * s, 0, (4, 4, 8, 255), walk=False)
        im.paste(ov, (0, 0), ov)
        return im


# ------------------------------------------------------------------ DEATH
class Hourglass(Scene):
    ambience = "clock"
    bokeh = (255, 214, 160)
    bokeh_n = 6
    text_y = 0.66

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (20, 14, 12)), (0.6, (34, 24, 18)), (0.62, (70, 46, 30)), (1, (36, 22, 14))])
        a = add_glow(a, radial(w, h, w * 0.5, h * 0.32, 520 * u), (255, 190, 120), 0.35)
        self.bg = to_img(a)
        self.cx, self.top, self.bot = w * 0.5, h * 0.08, h * 0.58
        self.rw = 230 * u
        self.motes = Motes(rng, 50, (0, 0, w, h * 0.6), color=(255, 220, 170), r=(1 * u, 2.4 * u), rise=4)

    def glass_x(self, y):
        """half-width of the glass at height y"""
        top, bot, rw = self.top + 40 * self.u, self.bot - 40 * self.u, self.rw
        mid = (top + bot) / 2
        p = abs(y - mid) / ((bot - top) / 2)
        return 10 * self.u + (rw - 10 * self.u) * (np.sin(np.clip(p, 0, 1) * np.pi / 2) ** 1.6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy(); d = ImageDraw.Draw(im)
        cx, top, bot = self.cx, self.top, self.bot
        gt, gb = top + 40 * u, bot - 40 * u
        mid = (gt + gb) / 2
        frac = min(0.97, 0.25 + (t % 60) / 60 * 0.7)          # fraction of sand already fallen
        ys = np.linspace(gt, gb, 200)
        xs = self.glass_x(ys)
        outline = [(cx - x, y) for x, y in zip(xs, ys)] + [(cx + x, y) for x, y in zip(xs[::-1], ys[::-1])]
        d.polygon(outline, fill=(60, 50, 46))
        sand = (230, 180, 100)
        # top sand: from neck upwards to a level that drops with time
        top_level = mid - (mid - gt - 20 * u) * (1 - frac)
        yt = np.linspace(top_level, mid, 60)
        d.polygon([(cx - x, y) for x, y in zip(self.glass_x(yt), yt)] + [(cx + x, y) for x, y in zip(self.glass_x(yt[::-1]), yt[::-1])], fill=sand)
        # bottom pile: a mound that grows
        ph = (gb - mid - 20 * u) * frac
        yb = np.linspace(gb - ph, gb, 60)
        hw = self.glass_x(yb) * np.clip((yb - (gb - ph)) / max(ph, 1) * 1.6, 0, 1)
        d.polygon([(cx - x, y) for x, y in zip(hw, yb)] + [(cx + x, y) for x, y in zip(hw[::-1], yb[::-1])], fill=(224, 170, 92))
        # falling stream with flicker
        jitter = 1.5 * u * math.sin(t * 40)
        d.line([(cx + jitter, mid), (cx, gb - ph)], fill=(240, 196, 120), width=max(2, int(4 * u)))
        # glass highlights
        hl = self.overlay(); dh = ImageDraw.Draw(hl)
        dh.line([(cx - x * 0.82 + 14 * u, y) for x, y in zip(xs[14:60], ys[14:60])], fill=(255, 255, 255, 110), width=max(2, int(5 * u)))
        dh.line([(cx - x * 0.82 + 14 * u, y) for x, y in zip(xs[140:186], ys[140:186])], fill=(255, 255, 255, 90), width=max(2, int(4 * u)))
        im.paste(hl, (0, 0), hl.filter(ImageFilter.GaussianBlur(2)))
        d = ImageDraw.Draw(im)
        # wooden frame
        wood, wood2 = (92, 56, 32), (64, 38, 22)
        for yy in (top, bot - 40 * u):
            d.rounded_rectangle([cx - self.rw - 50 * u, yy, cx + self.rw + 50 * u, yy + 40 * u], radius=int(12 * u), fill=wood)
            d.line([(cx - self.rw - 40 * u, yy + 10 * u), (cx + self.rw + 40 * u, yy + 10 * u)], fill=(130, 84, 50), width=int(3 * u))
        for px in (cx - self.rw - 30 * u, cx + self.rw + 30 * u):
            d.rectangle([px - 9 * u, top + 40 * u, px + 9 * u, bot - 40 * u], fill=wood2)
        d.ellipse([cx - self.rw - 80 * u, bot - 6 * u, cx + self.rw + 80 * u, bot + 36 * u], fill=(20, 12, 8))
        ov = self.overlay(); self.motes.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class Candle(Scene):
    ambience = "candle"
    bokeh = (255, 190, 110)
    bokeh_n = 6
    out_at = None          # local seconds (after shot start) when the flame goes out
    text_y = 0.66

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (8, 6, 6)), (0.56, (16, 12, 10)), (0.565, (40, 26, 18)), (1, (16, 10, 8))])
        self.base = a
        self.cx, self.fy = w * 0.5, h * 0.30
        self.glow_big = radial(w, h, self.cx, self.fy, 520 * u)
        self.glow_small = radial(w, h, self.cx, self.fy, 120 * u)
        self.smoke = []

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        on = 1.0 if self.out_at is None else 1.0 - float(smooth(self.out_at, self.out_at + 0.35, lt))
        fl = 1.0 + 0.10 * math.sin(t * 13) + 0.06 * math.sin(t * 29 + 1) + 0.05 * math.sin(t * 7.3)
        arr = self.base.copy()
        arr = add_glow(arr, self.glow_big, (255, 150, 60), 0.75 * on * fl)
        arr = add_glow(arr, self.glow_small, (255, 220, 160), 0.8 * on * fl)
        im = to_img(arr); d = ImageDraw.Draw(im)
        cx, fy = self.cx, self.fy
        # holder + candle (short, burnt down)
        d.ellipse([cx - 190 * u, h * 0.53, cx + 190 * u, h * 0.57], fill=(70, 50, 30))
        d.rectangle([cx - 30 * u, h * 0.47, cx + 30 * u, h * 0.545], fill=(80, 58, 34))
        d.ellipse([cx - 110 * u, h * 0.455, cx + 110 * u, h * 0.485], fill=(96, 70, 40))
        top = fy + 70 * u
        d.rectangle([cx - 62 * u, top, cx + 62 * u, h * 0.47], fill=(236, 226, 206))
        d.ellipse([cx - 62 * u, top - 14 * u, cx + 62 * u, top + 14 * u], fill=(246, 238, 220))
        for k, dx in enumerate((-40, 18, 52)):
            L = (40 + 30 * k) * u
            d.rounded_rectangle([cx + dx * u - 9 * u, top, cx + dx * u + 9 * u, top + L], radius=int(9 * u), fill=(244, 236, 218))
        d.line([(cx, top), (cx + 2 * u, top - 22 * u)], fill=(30, 20, 14), width=int(4 * u))
        ov = self.overlay(); do = ImageDraw.Draw(ov)
        if on > 0.02:
            sway = 6 * u * math.sin(t * 3.1) + 3 * u * math.sin(t * 11)
            hgt = 120 * u * fl * on
            for k, (col, sc) in enumerate((((255, 150, 40), 1.0), ((255, 210, 110), 0.72), ((255, 250, 220), 0.42))):
                fw, fh = 34 * u * sc, hgt * sc
                bx, by = cx, top - 18 * u
                pts = [(bx - fw, by - fh * 0.15), (bx - fw * 0.6, by - fh * 0.6), (bx + sway * 0.6, by - fh), (bx + fw * 0.6, by - fh * 0.6), (bx + fw, by - fh * 0.15), (bx, by + fw * 0.4)]
                do.polygon(pts, fill=col + (int(235 * on),))
            do.ellipse([cx - 9 * u, top - 34 * u, cx + 9 * u, top - 14 * u], fill=(60, 120, 255, int(150 * on)))
        if self.out_at is not None and lt > self.out_at:
            age = lt - self.out_at
            for k in range(16):
                a = age - k * 0.12
                if a <= 0:
                    continue
                y = top - 30 * u - a * 90 * u
                x = cx + 18 * u * math.sin(a * 2.2 + k) * (1 + a)
                r = (3 + a * 5) * u
                al = int(max(0, 110 - a * 34))
                do.ellipse([x - r, y - r, x + r, y + r], fill=(170, 170, 176, al))
        ov = ov.filter(ImageFilter.GaussianBlur(1.6 * u))
        im.paste(ov, (0, 0), ov)
        return im


class CandleOut(Candle):
    out_at = 2.0


class Autumn(Scene):
    ambience = "autumn"
    bokeh = (255, 200, 140)
    bokeh_n = 5

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        hz = int(h * 0.70)
        a = vgrad(w, h, [(0, (120, 128, 140)), (0.6, (186, 176, 166)), (0.70, (196, 180, 160)), (0.701, (120, 80, 50)), (1, (70, 42, 26))])
        a = fill_below(a, ridge(w, rng, hz - 40 * u, 20 * u), (150, 146, 150))
        a = fill_below(a, np.full(w, hz, np.float32), (128, 84, 52))
        bg = to_img(a); d = ImageDraw.Draw(bg)
        for _ in range(900):
            x, y = rng.uniform(0, w), hz + (h - hz) * rng.random() ** 0.8
            r = (3 + 9 * (y - hz) / (h - hz)) * u
            c = [(196, 96, 40), (220, 140, 50), (160, 60, 30), (230, 170, 70)][rng.integers(4)]
            d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=c)
        tips = []
        d.polygon([(w * 0.5 - 52 * u, hz + 30 * u), (w * 0.5 + 52 * u, hz + 30 * u), (w * 0.5 + 16 * u, hz - 260 * u), (w * 0.5 - 16 * u, hz - 260 * u)], fill=(40, 30, 26))
        branch(d, w * 0.5, hz - 250 * u, math.radians(90), 230 * u, 30 * u, 8, rng, (40, 30, 26), tips)
        self.tips = tips
        for x, y in tips[::2]:
            r = rng.uniform(8, 16) * u
            d.ellipse([x - r, y - r, x + r, y + r], fill=[(206, 110, 40), (230, 150, 60), (170, 70, 30)][rng.integers(3)])
        self.bg = bg
        n = 70
        self.leaves = np.c_[rng.uniform(-100, w + 100, n), rng.uniform(0, 10, n), rng.uniform(70, 140, n) * u,
                            rng.uniform(0, 6.28, n), rng.uniform(7, 14, n) * u, rng.integers(0, 4, n)]
        self.cols = [(206, 110, 40), (230, 150, 60), (170, 70, 30), (240, 190, 90)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy(); ov = self.overlay(); d = ImageDraw.Draw(ov)
        for x0, ph, v, rot, s, c in self.leaves:
            age = (t + ph) % 10
            y = -40 + v * age * 1.6
            if y > h + 40:
                continue
            x = x0 + 60 * u * math.sin(age * 0.9 + rot) + 30 * u * age
            ang = rot + age * 2.4
            dx, dy = math.cos(ang) * s, math.sin(ang) * s * 0.45
            d.polygon([(x - dx, y - dy), (x - dy * 0.6, y + dx * 0.4), (x + dx, y + dy), (x + dy * 0.6, y - dx * 0.4)], fill=self.cols[int(c)] + (235,))
        im.paste(ov, (0, 0), ov)
        return im


class Sunset(Scene):
    ambience = "sea"
    bokeh = (255, 200, 150)
    bokeh_n = 5
    text_y = 0.34

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.hz = hz = int(h * 0.70)
        self.sky = vgrad(w, hz, [(0, (40, 30, 70)), (0.45, (150, 70, 90)), (0.80, (246, 140, 70)), (1, (255, 200, 120))])
        self.sea = vgrad(w, h - hz, [(0, (200, 110, 80)), (0.2, (110, 60, 80)), (1, (20, 16, 36))])
        self.clouds = [(blob_sprite(int(rng.uniform(400, 700) * u), int(rng.uniform(80, 140) * u), rng, n=12, flat=0.85,
                              lit=(255, 190, 140), mid=(210, 120, 120), shade=(110, 60, 90)), rng.uniform(-300, w), rng.uniform(0.15, 0.55) * h, rng.uniform(6, 12) * u) for _ in range(5)]
        n = 400
        self.sp = np.c_[rng.normal(w * 0.5, 0.08 * w, n), hz + 6 + (h - hz) * rng.random(n) ** 1.8, rng.uniform(0, 6.28, n), rng.uniform(1, 3, n)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        sy = self.hz - 150 * u + min(1.0, max(0.0, lt / 14)) * 190 * u
        sky = self.sky.copy()
        sky = add_glow(sky, radial(w, self.hz, w * 0.5, sy, 420 * u), (255, 170, 90), 0.6)
        yy, xx = np.mgrid[0:self.hz, 0:w].astype(np.float32)
        disc = np.clip(110 * u - np.hypot(xx - w * 0.5, yy - sy) + 1, 0, 1)
        sky = sky * (1 - disc[..., None]) + np.array([255, 236, 190], np.float32) * disc[..., None]
        arr = np.concatenate([sky, self.sea.copy()], 0)
        xs = np.arange(w, dtype=np.float32)[None, :]
        ys = np.linspace(0, 1, h - self.hz, dtype=np.float32)[:, None]
        vis = float(np.clip((self.hz - sy + 110 * u) / (220 * u), 0, 1))
        arr[self.hz:] += (80 * vis * np.exp(-((xs - w * 0.5) / (90 * u)) ** 2) * (1 - ys) ** 1.2)[..., None] * np.array([1, 0.7, 0.4], np.float32)
        im = to_img(arr)
        for spr, x0, y, v in self.clouds:
            im.paste(spr, (int(wrap_x(x0, v, t, spr.width, w)), int(y)), spr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        for x, y, ph, f in self.sp:
            a = max(0.0, math.sin(t * f + ph)) ** 3 * vis
            if a > 0.05:
                ln = (4 + 20 * (y - self.hz) / (h - self.hz)) * u
                d.line([(x - ln, y), (x + ln, y)], fill=(255, 220, 170, int(220 * a)), width=max(2, int(2 * u)))
        im.paste(ov, (0, 0), ov)
        return im


# ------------------------------------------------------------------ MERCY / TAWBAH
class DesertRain(Scene):
    ambience = "rain"
    bokeh = (220, 230, 220)
    bokeh_n = 4

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.hz = hz = int(h * 0.50)
        sky = vgrad(w, hz, [(0, (60, 66, 80)), (0.7, (120, 124, 130)), (1, (170, 160, 140))])
        dry = vgrad(w, h - hz, [(0, (196, 160, 112)), (1, (150, 110, 70))])
        self.dry = np.concatenate([sky, dry], 0)
        wet = vgrad(w, h - hz, [(0, (120, 110, 84)), (1, (70, 58, 40))])
        self.wet = np.concatenate([sky, wet], 0)
        cr = Image.new("L", (w, h), 0); d = ImageDraw.Draw(cr)
        for _ in range(140):
            x, y = rng.uniform(0, w), hz + (h - hz) * rng.random() ** 0.7
            p = (y - hz) / (h - hz)
            pts = [(x, y)]
            for _ in range(rng.integers(3, 8)):
                x += rng.uniform(-60, 60) * u * (0.3 + p); y += rng.uniform(-14, 14) * u * (0.3 + p); pts.append((x, y))
            d.line(pts, fill=255, width=max(1, int((1 + 3 * p) * u)))
        self.cracks = np.asarray(cr, np.float32)[..., None] / 255
        self.clouds = [(blob_sprite(int(rng.uniform(600, 900) * u), int(rng.uniform(260, 360) * u), rng,
                              lit=(150, 154, 164), mid=(112, 118, 132), shade=(80, 84, 100), n=20, flat=0.75).filter(ImageFilter.GaussianBlur(5 * u)), rng.uniform(-500, w - 200), rng.uniform(-0.08, 0.20) * h, rng.uniform(5, 10) * u) for _ in range(7)]
        n = 700
        ys = hz + 20 * u + (h - hz) * rng.random(n) ** 0.7
        order = np.argsort(ys)
        self.sprouts = np.c_[rng.uniform(0, w, n), ys, rng.uniform(0, 1, n), rng.uniform(0, 6.28, n)][order]
        self.rain = Rain(w, h, rng, n=200, color=(210, 220, 230), alpha=(40, 100), slant=0.1, u=u)
        self.flowers = np.c_[rng.uniform(0, w, 60), hz + 40 * u + (h - hz) * rng.random(60), rng.uniform(0, 1, 60)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        wet = float(smooth(0.0, 3.0, lt))
        grow = float(smooth(1.0, 9.0, lt))
        arr = self.dry * (1 - wet) + self.wet * wet
        arr = arr * (1 - self.cracks * 0.55 * (1 - 0.6 * grow))
        im = to_img(arr)
        for spr, x0, y, v in self.clouds:
            im.paste(spr, (int(x0 + v * t), int(y)), spr)
        d = ImageDraw.Draw(im)
        hz = self.hz
        for x, y, th, ph in self.sprouts:
            g = float(np.clip((grow - th * 0.6) / 0.4, 0, 1))
            if g <= 0:
                continue
            p = (y - hz) / (h - hz)
            L = (10 + 60 * p) * u * g
            sw = 4 * u * math.sin(t * 1.4 + ph)
            c = (int(70 + 60 * (1 - p)), int(140 + 50 * (1 - p)), 60)
            d.line([(x, y), (x + sw, y - L)], fill=c, width=max(2, int((2 + 3 * p) * u)))
            d.line([(x + 2, y), (x + sw - 10 * u * g, y - L * 0.7)], fill=c, width=max(2, int((2 + 2 * p) * u)))
        for x, y, th in self.flowers:
            g = float(np.clip((grow - 0.6 - th * 0.3) / 0.2, 0, 1))
            if g > 0:
                r = 5 * u * g * (0.5 + (y - hz) / (h - hz))
                d.ellipse([x - r, y - r - 30 * u * g, x + r, y + r - 30 * u * g], fill=(255, 240, 200))
        ov = self.overlay(); self.rain.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class MotherChild(Scene):
    ambience = "meadow"
    bokeh = (255, 220, 160)
    bokeh_n = 8
    text_y = 0.20
    band = 1.5

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        hz = int(h * 0.62)
        a = vgrad(w, h, [(0, (90, 110, 170)), (0.30, (230, 170, 140)), (0.58, (255, 210, 150)), (0.62, (240, 190, 130)), (0.621, (150, 120, 70)), (1, (60, 50, 30))])
        a = add_glow(a, radial(w, h, w * 0.5, h * 0.34, 380 * u), (255, 240, 200), 0.8)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        disc = np.clip(80 * u - np.hypot(xx - w * 0.5, yy - h * 0.34) + 1, 0, 1)
        a = a * (1 - disc[..., None]) + np.array([255, 250, 230], np.float32) * disc[..., None]
        a = fill_below(a, ridge(w, rng, hz - 20 * u, 14 * u), (170, 140, 110))
        self.bg = to_img(a)
        self.clouds = [(blob_sprite(int(rng.uniform(380, 620) * u), int(rng.uniform(90, 140) * u), rng, n=11, flat=0.85,
                              lit=(255, 230, 200), mid=(240, 180, 160), shade=(170, 120, 140)), rng.uniform(-300, w), rng.uniform(0.06, 0.26) * h, rng.uniform(6, 10) * u) for _ in range(4)]
        S = 1.0 * u
        spr = Image.new("RGBA", (int(700 * S), int(760 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(spr)
        col = (30, 20, 18, 255)
        P = lambda pts: [(x * S, y * S) for x, y in pts]
        d.ellipse(P([(150, 640), (640, 750)]), fill=col)                                   # folded legs / skirt on the ground
        d.polygon(P([(250, 690), (232, 520), (240, 420), (282, 352), (360, 330), (430, 372), (470, 470), (520, 600), (560, 700)]), fill=col)  # torso
        d.polygon(P([(300, 196), (372, 182), (430, 226), (446, 286), (428, 330), (372, 352), (262, 372), (228, 330), (250, 252)]), fill=col)  # head + hijab, bowed
        d.polygon(P([(430, 262), (452, 296), (434, 304)]), fill=col)                     # face profile
        d.ellipse(P([(380, 470), (612, 566)]), fill=col)                                    # baby bundle across the lap
        d.ellipse(P([(560, 430), (640, 506)]), fill=col)                                    # baby's head
        d.line(P([(360, 372), (430, 470), (560, 520)]), fill=col, width=int(40 * S), joint="curve")   # cradling arm
        d.line(P([(320, 380), (380, 520), (520, 560)]), fill=col, width=int(36 * S), joint="curve")
        rim = spr.getchannel("A").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(6 * S))
        rimimg = Image.new("RGBA", spr.size, (255, 200, 140, 0)); rimimg.putalpha(rim.point(lambda v: int(v * 0.55)))
        out = Image.new("RGBA", spr.size, (0, 0, 0, 0)); out.alpha_composite(rimimg); out.alpha_composite(spr)
        self.fig = out
        self.motes = Motes(rng, 50, (0, h * 0.2, w, h), color=(255, 236, 190), r=(1.4 * u, 3 * u), rise=6)
        self.grass = np.c_[rng.uniform(0, w, 500), h * 0.64 + h * 0.36 * rng.random(500) ** 0.6, rng.uniform(0, 6.28, 500)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy()
        for spr, x0, y, v in self.clouds:
            im.paste(spr, (int(wrap_x(x0, v, t, spr.width, w)), int(y)), spr)
        d = ImageDraw.Draw(im)
        for x, y, ph in self.grass:
            p = (y - h * 0.64) / (h * 0.36)
            L = (10 + 50 * p) * u
            sw = 6 * u * math.sin(t * 1.3 + x * 0.01 + ph)
            d.line([(x, y), (x + sw, y - L)], fill=(int(70 + 40 * (1 - p)), int(60 + 30 * (1 - p)), 30), width=max(2, int(3 * u)))
        ang = 2.2 * math.sin(t * 1.4)
        fig = self.fig.rotate(ang, resample=Image.BICUBIC, center=(self.fig.width * 0.5, self.fig.height))
        im.paste(fig, (int(w * 0.46 - fig.width / 2), int(h * 0.985 - fig.height)), fig)
        ov = self.overlay(); self.motes.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class NightPrayer(Scene):
    ambience = "night_room"
    bokeh = (180, 200, 255)
    bokeh_n = 4
    text_y = 0.56

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        fy = int(h * 0.66)
        a = vgrad(w, h, [(0, (14, 16, 30)), (0.66, (20, 22, 38)), (0.661, (28, 26, 36)), (1, (12, 12, 18))])
        bg = to_img(a); d = ImageDraw.Draw(bg)
        self.win = (int(w * 0.30), int(h * 0.08), int(w * 0.70), int(h * 0.40))
        x0, y0, x1, y1 = self.win
        sky = vgrad(x1 - x0, y1 - y0, [(0, (10, 16, 46)), (1, (40, 50, 96))])
        sk = to_img(sky); ds = ImageDraw.Draw(sk)
        for _ in range(80):
            x, y = rng.uniform(0, x1 - x0), rng.uniform(0, y1 - y0)
            b = int(rng.uniform(120, 255)); r = rng.uniform(0.8, 2.0) * u
            ds.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b))
        mx, my, mr = (x1 - x0) * 0.68, (y1 - y0) * 0.30, 46 * u
        ds.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 244, 214))
        ds.ellipse([mx - mr + 20 * u, my - mr - 12 * u, mx + mr + 20 * u, my + mr - 12 * u], fill=(16, 22, 56))
        bg.paste(sk, (x0, y0))
        fr = (8, 8, 14)
        d.rectangle([x0, y0, x1, y1], outline=fr, width=int(16 * u))
        d.line([((x0 + x1) // 2, y0), ((x0 + x1) // 2, y1)], fill=fr, width=int(10 * u))
        d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=fr, width=int(10 * u))
        arr = np.asarray(bg, np.float32)
        self.beam = blur_mask((w, h), lambda dd: dd.polygon([(x0, y0), (x1, y0), (x1 + 120 * u, h), (x0 - 120 * u, h)], fill=60), 40 * u)
        patch = blur_mask((w, h), lambda dd: dd.polygon([(x0 - 40 * u, fy + 40 * u), (x1 + 40 * u, fy + 40 * u), (x1 + 120 * u, h), (x0 - 120 * u, h)], fill=110), 12 * u)
        arr = add_glow(arr, patch, (150, 170, 230), 0.5)
        bg = to_img(arr); d = ImageDraw.Draw(bg)
        mat = [(w * 0.40, fy + 70 * u), (w * 0.60, fy + 70 * u), (w * 0.70, h * 0.97), (w * 0.30, h * 0.97)]
        d.polygon(mat, fill=(70, 40, 60))
        d.line(mat + [mat[0]], fill=(150, 130, 90), width=int(5 * u))
        self.bg = bg
        self.fy = fy
        self.motes = Motes(rng, 40, (x0 - 100 * u, y0, x1 + 100 * u, h), color=(200, 214, 255), r=(1 * u, 2.2 * u), rise=3)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = np.asarray(self.bg, np.float32).copy()
        arr = add_glow(arr, self.beam, (170, 190, 255), 0.5 + 0.08 * math.sin(t * 0.6))
        im = to_img(arr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        col = (6, 6, 12, 255)
        cx, base = w * 0.5, h * 0.90
        br = 1 + 0.012 * math.sin(t * 1.6)
        s = 1.2 * u
        d.ellipse([cx - 120 * s, base - 70 * s, cx + 120 * s, base + 10 * s], fill=col)                     # kneeling legs
        d.polygon([(cx - 80 * s, base - 40 * s), (cx + 80 * s, base - 40 * s), (cx + 56 * s, base - 230 * s * br), (cx - 56 * s, base - 230 * s * br)], fill=col)
        d.ellipse([cx - 40 * s, base - 320 * s * br, cx + 40 * s, base - 236 * s * br], fill=col)          # head (back view)
        for side in (-1, 1):                                                                           # hands raised in dua, at face height
            sx, sy = cx + side * 52 * s, base - 214 * s * br
            ex, ey = cx + side * 74 * s, base - 252 * s * br
            d.line([(sx, sy), (cx + side * 84 * s, base - 196 * s * br), (ex, ey)], fill=col, width=int(24 * s), joint="curve")
            d.ellipse([ex - 18 * s, ey - 30 * s, ex + 18 * s, ey + 6 * s], fill=col)
        self.motes.draw(d, t)
        im.paste(ov, (0, 0), ov)
        return im


class StormClear(Scene):
    ambience = "storm_to_birds"
    text_y = 0.73
    band = 1.5
    bokeh = (255, 240, 210)
    bokeh_n = 5

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        hz = int(h * 0.68)
        a = vgrad(w, h, [(0, (70, 140, 210)), (0.55, (190, 220, 236)), (0.68, (220, 230, 220)), (0.681, (100, 150, 80)), (1, (40, 80, 40))])
        a = fill_below(a, ridge(w, rng, hz - 50 * u, 40 * u), (90, 130, 110))
        a = fill_below(a, ridge(w, rng, hz + 20 * u, 30 * u), (70, 120, 60))
        self.clear = a
        dark = a * 0.35 + np.array([20, 22, 30], np.float32)
        self.dark = dark
        self.sun = (w * 0.5, h * 0.24)
        self.rays = []
        for k in range(11):
            ang = math.radians(20 + k * 14 + rng.uniform(-4, 4))
            m = blur_mask((w, h), lambda dd, a=ang: dd.polygon([self.sun, (self.sun[0] + math.cos(a - 0.04) * 2400 * u, self.sun[1] + math.sin(a - 0.04) * 2400 * u),
                                                                (self.sun[0] + math.cos(a + 0.04) * 2400 * u, self.sun[1] + math.sin(a + 0.04) * 2400 * u)], fill=90), 22 * u)
            self.rays.append(m)
        self.sunglow = radial(w, h, *self.sun, 300 * u)
        self.left = [(blob_sprite(int(rng.uniform(700, 1000) * u), int(rng.uniform(320, 460) * u), rng, n=18, lit=(120, 124, 136), mid=(70, 74, 90), shade=(34, 36, 48)), rng.uniform(-0.6, 0.1) * w, rng.uniform(-0.06, 0.40) * h) for _ in range(5)]
        self.right = [(blob_sprite(int(rng.uniform(700, 1000) * u), int(rng.uniform(320, 460) * u), rng, n=18, lit=(120, 124, 136), mid=(70, 74, 90), shade=(34, 36, 48)), rng.uniform(0.3, 0.8) * w, rng.uniform(-0.06, 0.40) * h) for _ in range(5)]
        self.rain = Rain(w, h, rng, n=160, color=(200, 210, 230), alpha=(30, 80), slant=0.12, u=u)
        self.birds = np.c_[rng.uniform(-200, w, 5), rng.uniform(0.25, 0.45, 5) * h, rng.uniform(50, 80, 5) * u]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        lt = t - 3.0
        p = float(smooth(0.5, 8.0, lt))
        arr = self.dark * (1 - p) + self.clear * p
        arr = add_glow(arr, self.sunglow, (255, 240, 200), 0.9 * p)
        for k, m in enumerate(self.rays):
            arr = add_glow(arr, m, (255, 244, 210), 0.45 * p * (0.8 + 0.2 * math.sin(t * 0.7 + k)))
        im = to_img(arr)
        for spr, x0, y in self.left:
            im.paste(spr, (int(x0 - p * 700 * u - 6 * u * t), int(y)), spr)
        for spr, x0, y in self.right:
            im.paste(spr, (int(x0 + p * 700 * u + 6 * u * t), int(y)), spr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        if p < 0.7:
            self.rain.alpha_scale = 1 - p / 0.7
            self.rain.draw(d, t)
        if p > 0.6:
            for bx, by, v in self.birds:
                x = (bx + v * t) % (w + 200) - 100
                f = 8 * u * math.sin(t * 7 + bx)
                d.line([(x - 14 * u, by - f), (x, by), (x + 14 * u, by - f)], fill=(40, 50, 60, int(255 * (p - 0.6) / 0.4)), width=max(2, int(2 * u)))
        im.paste(ov, (0, 0), ov)
        return im


class PremiumGold(Scene):
    """Premium Islamic Cinematic / Quran-focused: charcoal, gold geometry, spotlight, gold dust."""
    ambience = "night_room"
    bokeh = (255, 214, 140)
    bokeh_n = 6
    camera = "static"
    text_y = 0.50

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (9, 9, 10)), (0.5, (19, 18, 17)), (1, (7, 7, 8))])
        self.base = add_glow(a, radial(w, h, w / 2, h * 0.47, 560 * u), (92, 72, 44), 0.55)
        # 8-point star lattice (two overlapping squares per cell), drawn once large for rotation
        S = int(1.6 * max(w, h))
        pat = Image.new("L", (S, S), 0); d = ImageDraw.Draw(pat)
        step = 220 * u
        for gy in np.arange(-step, S + step, step):
            for gx in np.arange(-step, S + step, step):
                for k in range(2):
                    pts = [(gx + math.cos(math.radians(45 * k + 90 * j)) * step * 0.42, gy + math.sin(math.radians(45 * k + 90 * j)) * step * 0.42) for j in range(4)]
                    d.polygon(pts, outline=255, width=max(1, int(2 * u)))
                d.ellipse([gx - step * 0.12, gy - step * 0.12, gx + step * 0.12, gy + step * 0.12], outline=180, width=max(1, int(1.5 * u)))
                tip = step * 0.42
                d.line([(gx + tip, gy), (gx + step - tip, gy)], fill=200, width=max(1, int(2 * u)))
                d.line([(gx, gy + tip), (gx, gy + step - tip)], fill=200, width=max(1, int(2 * u)))
                cx2, cy2, r2 = gx + step / 2, gy + step / 2, step * 0.16
                d.polygon([(cx2 + math.cos(math.radians(45 * j)) * (r2 if j % 2 else r2 * 0.45), cy2 + math.sin(math.radians(45 * j)) * (r2 if j % 2 else r2 * 0.45)) for j in range(8)], outline=150)
        self.pat = pat
        c = radial(w, h, w / 2, h * 0.47, 430 * u)
        self.fade = np.clip(1.0 - 0.85 * c, 0, 1) * (0.45 + 0.55 * radial(w, h, w / 2, h * 0.5, 1100 * u))
        self.dust = Motes(rng, 70, (0, 0, w, h), color=(255, 214, 140), r=(1.0 * u, 2.6 * u), rise=10, sway=20 * u)
        self.rays = [blur_mask((w, h), lambda dd, x=x: dd.polygon([(x - 40 * u, -10), (x + 40 * u, -10), (x + 220 * u, h), (x - 220 * u, h)], fill=50), 50 * u)
                     for x in (w * 0.35, w * 0.65)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        ang = (t * 1.2) % 360
        rot = self.pat.rotate(ang, resample=Image.BILINEAR)
        S = rot.width
        z = 1.0 + 0.04 * math.sin(t * 0.25)
        cw, ch = w / z, h / z
        crop = rot.crop((int((S - cw) / 2), int((S - ch) / 2), int((S + cw) / 2), int((S + ch) / 2))).resize((w, h), Image.BILINEAR)
        m = np.asarray(crop, np.float32) / 255 * self.fade
        arr = self.base + m[..., None] * np.array([222, 178, 100], np.float32) * 0.42
        for k, r in enumerate(self.rays):
            arr = add_glow(arr, r, (255, 220, 160), 0.18 + 0.06 * math.sin(t * 0.6 + k * 2))
        im = to_img(arr)
        ov = self.overlay(); self.dust.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


TOPIC_SCENES = {
    "graveyard": Graveyard, "grave_inside": GraveInside, "sun_near": SunNear, "mountains_dust": MountainsDust,
    "sky_split": SkySplit, "hourglass": Hourglass, "candle": Candle, "candle_out": CandleOut, "autumn": Autumn,
    "sunset": Sunset, "desert_rain": DesertRain, "mother_child": MotherChild, "night_prayer": NightPrayer,
    "storm_clear": StormClear, "premium_gold": PremiumGold,
}
