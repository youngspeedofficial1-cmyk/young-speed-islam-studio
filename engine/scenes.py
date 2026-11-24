"""
Vertical (9:16) animated scenes for urdu_reels.py.
Every scene: Scene(w, h, seed) -> .frame(t) returns a PIL RGB image of size (w, h).
Designed at 1080x1920; all sizes scale with u = w / 1080.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ------------------------------------------------------------------ helpers
def vgrad(w, h, stops):
    y = np.linspace(0, 1, h)
    ps = [s[0] for s in stops]
    cs = np.array([s[1] for s in stops], np.float32)
    col = np.stack([np.interp(y, ps, cs[:, c]) for c in range(3)], -1)
    return np.repeat(col[:, None, :], w, axis=1).astype(np.float32)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def blur_mask(size, draw_fn, radius):
    m = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(m))
    return np.asarray(m.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255.0


def add_glow(arr, mask, color, k=1.0):
    arr += mask[..., None] * np.array(color, np.float32) * k
    return arr


def radial(w, h, cx, cy, r):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r))


def blob_sprite(w, h, rng, lit, mid, shade, n=14, flat=0.80, soft=3, light=(-0.35, -0.80, 0.50)):
    """Cel-shaded puffy shape (clouds, tree canopies): union of domes lit from the upper left."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Hm = np.zeros((h, w), np.float32)
    base = h * flat
    for _ in range(n):
        u = rng.uniform(0.10, 0.90)
        r = h * rng.uniform(0.15, 0.30) * (1.2 - abs(u - 0.5))
        cx, cy = w * u, base - r * rng.uniform(0.25, 1.1)
        z = np.sqrt(np.clip(r * r - (xx - cx) ** 2 - (yy - cy) ** 2, 0, None))
        Hm = np.maximum(Hm, z)
    gy, gx = np.gradient(Hm)
    nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1)
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    dot = (-gx * nz) * L[0] + (-gy * nz) * L[1] + nz * L[2]
    dot = np.asarray(Image.fromarray(np.clip((dot + 1) * 127.5, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(soft)), np.float32) / 127.5 - 1
    s1, s2 = smooth(0.22, 0.42, dot), smooth(0.66, 0.84, dot)
    lit, mid, shade = (np.array(c, np.float32) for c in (lit, mid, shade))
    col = shade + (mid - shade) * s1[..., None] + (lit - mid) * s2[..., None]
    bot = smooth(base - h * 0.18, base, yy)[..., None] * 0.3
    col = col * (1 - bot) + shade * bot
    a = smooth(0.0, 2.5, Hm) * (smooth(base + 1, base - 5, yy) if flat < 0.99 else 1.0)
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8), "RGBA")
    im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(1.2)))
    return im


def cloud(w, h, rng, warm=0.0, **kw):
    lit = (255, 252 - 10 * warm, 246 - 30 * warm)
    mid = (226 + 10 * warm, 232, 242 - 20 * warm)
    shade = (150 + 20 * warm, 166, 198 - 10 * warm)
    return blob_sprite(w, h, rng, lit, mid, shade, **kw)


def ridge(w, rng, base, amp, octaves=4):
    x = np.arange(w, dtype=np.float32)
    y = np.full(w, base, np.float32)
    for o in range(octaves):
        f = (o + 1) ** 1.7 / w * rng.uniform(1.5, 3)
        y += amp / (o + 1) ** 1.3 * np.sin(2 * np.pi * f * x + rng.uniform(0, 6.28))
    return y


def fill_below(arr, ys, color, soft=1.5):
    h = arr.shape[0]
    yy = np.arange(h, dtype=np.float32)[:, None]
    a = np.clip((yy - ys[None, :]) / soft + 0.5, 0, 1)[..., None]
    arr[:] = arr * (1 - a) + np.array(color, np.float32) * a
    return arr


def wrap_x(x0, v, t, width, span):
    return (x0 + v * t + width) % (span + width) - width


class Rain:
    def __init__(self, w, h, rng, n=200, color=(210, 220, 235), alpha=(45, 105), slant=0.15, u=1.0):
        self.w, self.h, self.u = w, h, u
        self.x = rng.uniform(-60, w + 60, n); self.y = rng.uniform(0, h, n)
        self.v = rng.uniform(1500, 2200, n) * u; self.l = rng.uniform(26, 70, n) * u
        self.a = rng.uniform(*alpha, n); self.c = color; self.s = slant

    def draw(self, d, t):
        y = (self.y + self.v * t) % (self.h + 100) - 50
        x = self.x + self.s * (y - self.y)
        wd = max(1, int(2 * self.u))
        for xi, yi, li, ai in zip(x, y, self.l, self.a):
            d.line([(xi, yi), (xi - self.s * li, yi - li)], fill=self.c + (int(ai),), width=wd)


class Motes:
    def __init__(self, rng, n, box, color=(255, 238, 180), r=(1.5, 3.5), rise=8, sway=18):
        self.box = box
        x0, y0, x1, y1 = box
        self.x = rng.uniform(x0, x1, n); self.y = rng.uniform(y0, y1, n)
        self.ph = rng.uniform(0, 6.28, n); self.f = rng.uniform(0.3, 0.9, n)
        self.r = rng.uniform(*r, n); self.c = color; self.rise = rise; self.sway = sway

    def draw(self, d, t, glow=True):
        x0, y0, x1, y1 = self.box
        hh = y1 - y0
        for xi, yi, ph, f, r in zip(self.x, self.y, self.ph, self.f, self.r):
            x = xi + self.sway * math.sin(t * f + ph)
            y = y0 + ((yi - y0 - self.rise * t * f) % hh)
            a = int(210 * (0.3 + 0.7 * max(0.0, math.sin(t * f * 2.2 + ph)) ** 2))
            if glow:
                d.ellipse([x - r * 2.6, y - r * 2.6, x + r * 2.6, y + r * 2.6], fill=self.c + (a // 6,))
            d.ellipse([x - r, y - r, x + r, y + r], fill=self.c + (a,))


def person(d, x, y, s, t, col, walk=True, umbrella=None, away=False):
    """Simple silhouette standing on (x, y) feet line, height ~ 120*s."""
    step = math.sin(t * 5.2) if walk else 0.0
    bob = abs(math.sin(t * 5.2)) * 2 * s if walk else 0
    hy = y - 112 * s - bob
    d.line([(x, y - 48 * s - bob), (x - 9 * s * step, y)], fill=col, width=max(2, int(7 * s)))
    d.line([(x, y - 48 * s - bob), (x + 9 * s * step, y)], fill=col, width=max(2, int(7 * s)))
    d.polygon([(x - 15 * s, y - 46 * s - bob), (x + 15 * s, y - 46 * s - bob), (x + 11 * s, y - 98 * s - bob), (x - 11 * s, y - 98 * s - bob)], fill=col)
    d.ellipse([x - 10 * s, hy - 10 * s, x + 10 * s, hy + 10 * s], fill=col)
    if umbrella:
        d.line([(x + 6 * s, y - 80 * s - bob), (x + 6 * s, hy - 34 * s)], fill=col, width=max(1, int(3 * s)))
        d.chord([x - 50 * s, hy - 62 * s, x + 62 * s, hy - 6 * s], 180, 360, fill=umbrella)
        for k in range(1, 4):
            ex = x - 50 * s + k * 28 * s
            d.line([(x + 6 * s, hy - 60 * s), (ex, hy - 34 * s)], fill=tuple(max(0, c - 25) for c in umbrella), width=max(1, int(2 * s)))


# ------------------------------------------------------------------ scenes
class Scene:
    bokeh = (255, 240, 210)      # colour of out-of-focus foreground lights
    bokeh_n = 7
    ambience = "wind"
    tint = (1.0, 1.0, 1.0)

    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.u = w / 1080
        self.rng = np.random.default_rng(seed)
        self.build()

    def overlay(self):
        return Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))


class Sea(Scene):
    ambience = "sea"
    band = 1.6
    bokeh = (255, 246, 220)

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.hz = hz = int(h * 0.64)
        sky = vgrad(w, hz, [(0, (30, 92, 172)), (0.45, (78, 146, 214)), (0.85, (176, 214, 238)), (1, (222, 236, 244))])
        self.sun = (w * 0.64, h * 0.40)
        sky += (radial(w, hz, *self.sun, 380 * u) * 45)[..., None] * np.array([1, 0.95, 0.8], np.float32)
        sea = vgrad(w, h - hz, [(0, (132, 192, 220)), (0.10, (70, 156, 206)), (1, (12, 74, 136))])
        xx = np.arange(w, dtype=np.float32)[None, :]
        yy = np.linspace(0, 1, h - hz, dtype=np.float32)[:, None]
        sea += (60 * np.exp(-((xx - self.sun[0]) / (0.11 * w)) ** 2) * (1 - yy) ** 1.4)[..., None]
        bg = to_img(np.concatenate([sky, sea], 0))
        for _ in range(7):
            spr = cloud(int(rng.uniform(220, 380) * u), int(80 * u), rng, n=10, flat=0.9)
            bg.paste(spr, (int(rng.uniform(-100, w - 100)), hz - int(72 * u)), spr)
        d = ImageDraw.Draw(bg)
        sx, sy = int(w * 0.16), hz + int(5 * u)
        d.rectangle([sx, sy - 7 * u, sx + 110 * u, sy + 1], fill=(84, 78, 86))
        d.rectangle([sx + 76 * u, sy - 18 * u, sx + 96 * u, sy - 7 * u], fill=(224, 226, 232))
        self.bg = bg
        # towering cumulus over the sun
        self.clouds = [
            (cloud(int(1100 * u), int(760 * u), rng, n=22, warm=0.2), w * 0.64 - 600 * u, h * 0.05, 5 * u),
            (cloud(int(640 * u), int(380 * u), rng, n=16), -260 * u, h * 0.28, 9 * u),
            (cloud(int(560 * u), int(300 * u), rng, n=14), w * 0.62, h * 0.02, 7 * u),
            (cloud(int(620 * u), int(320 * u), rng, n=14), w * 0.55, h * 0.36, 11 * u),
        ]
        self.rays = []
        for k in range(7):
            ang = math.radians(60 + k * 10 + rng.uniform(-3, 3))
            m = blur_mask((w, h), lambda dd, a=ang: dd.polygon(
                [self.sun, (self.sun[0] + math.cos(a - 0.03) * 2200 * u, self.sun[1] + math.sin(a - 0.03) * 2200 * u),
                 (self.sun[0] + math.cos(a + 0.03) * 2200 * u, self.sun[1] + math.sin(a + 0.03) * 2200 * u)], fill=60), 26 * u)
            m[hz:] *= 0.25
            self.rays.append((m, rng.uniform(0, 6.28)))
        n = 520
        self.sp = np.c_[np.where(rng.random(n) < 0.5, rng.normal(self.sun[0], 0.07 * w, n), rng.uniform(0, w, n)),
                        hz + 8 + (h - hz - 8) * rng.random(n) ** 1.7, rng.uniform(0, 6.28, n), rng.uniform(1.0, 3.0, n)]
        self.boat_x0 = w * 0.30
        self.gulls = np.c_[rng.uniform(-100, w, 3), rng.uniform(h * 0.22, h * 0.45, 3), rng.uniform(25, 45, 3) * u, rng.uniform(0, 6, 3)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy()
        for spr, x0, y, v in self.clouds:
            im.paste(spr, (int(x0 + v * t), int(y)), spr)
        arr = np.asarray(im, np.float32).copy()
        for m, ph in self.rays:
            arr += m[..., None] * np.array([255, 244, 214], np.float32) * (0.12 + 0.08 * math.sin(t * 0.5 + ph))
        im = to_img(arr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        for x, y, ph, f in self.sp:
            a = max(0.0, math.sin(t * f + ph)) ** 3
            if a > 0.05:
                ln = (4 + 22 * (y - self.hz) / (h - self.hz)) * u
                d.line([(x - ln, y), (x + ln, y)], fill=(255, 255, 255, int(225 * a)), width=max(2, int(2 * u)))
        s = 1.35 * u
        bx, by = self.boat_x0 + 15 * u * t, h * 0.76
        for k in range(12):
            wx = bx - 26 * s - k * 18 * s
            d.line([(wx, by + 12 * s + k * 0.8), (wx - 14 * s, by + 12 * s + k * 0.8)], fill=(240, 250, 255, max(0, 180 - k * 15)), width=2)
        d.ellipse([bx - 72 * s, by + 4 * s, bx + 76 * s, by + 18 * s], fill=(8, 46, 86, 90))
        d.polygon([(bx - 68 * s, by - 6 * s), (bx + 72 * s, by - 6 * s), (bx + 60 * s, by + 11 * s), (bx - 60 * s, by + 11 * s)], fill=(28, 36, 58))
        d.line([(bx - 64 * s, by - 2 * s), (bx + 68 * s, by - 2 * s)], fill=(170, 40, 40), width=int(3 * s))
        d.rectangle([bx - 38 * s, by - 24 * s, bx + 32 * s, by - 6 * s], fill=(240, 238, 230))
        d.rectangle([bx - 32 * s, by - 19 * s, bx + 26 * s, by - 14 * s], fill=(90, 110, 140))
        d.rectangle([bx - 5 * s, by - 46 * s, bx + 10 * s, by - 24 * s], fill=(30, 30, 34))
        d.rectangle([bx - 5 * s, by - 40 * s, bx + 10 * s, by - 35 * s], fill=(180, 40, 40))
        d.line([(bx + 46 * s, by - 6 * s), (bx + 46 * s, by - 44 * s)], fill=(40, 40, 50), width=2)
        for k in range(10):
            age = (t * 0.5 + k / 10) % 1.0
            r = (7 + age * 30) * s * 0.8
            cx, cy = bx + 2 * s - age * 110 * s, by - 52 * s - age * 60 * s - 10 * math.sin(age * 3)
            g = int(70 + age * 120)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(g, g, g + 6, int(190 * (1 - age) ** 1.4)))
        for gx, gy, v, ph in self.gulls:
            x = (gx + v * t) % (w + 200) - 100
            y = gy + 10 * math.sin(t * 0.7 + ph)
            f = 9 * u * math.sin(t * 6 + ph)
            d.line([(x - 18 * u, y - f), (x - 6 * u, y - 2 * u), (x, y + 2 * u), (x + 6 * u, y - 2 * u), (x + 18 * u, y - f)], fill=(50, 56, 70, 230), width=max(2, int(3 * u)), joint="curve")
        im.paste(ov, (0, 0), ov)
        return im


class RainPond(Scene):
    ambience = "rain"
    bokeh = (220, 236, 226)

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (150, 168, 160)), (0.25, (104, 120, 108)), (0.6, (70, 86, 76)), (1, (38, 52, 46))])
        trees = blur_mask((w, h), lambda d: [d.ellipse([x - r, -r * 0.6, x + r, r * 1.1], fill=200)
                                             for x, r in zip(rng.uniform(-100, w + 100, 9), rng.uniform(140, 260, 9) * u)], 28 * u)
        a = a * (1 - 0.55 * trees[..., None]) + trees[..., None] * np.array([28, 52, 34], np.float32) * 0.55
        refl = blur_mask((w, h), lambda d: [d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=int(rng.uniform(50, 120)))
                                            for x, y, rx, ry in zip(rng.uniform(0, w, 10), rng.uniform(h * 0.15, h * 0.7, 10),
                                                                    rng.uniform(140, 320, 10) * u, rng.uniform(30, 90, 10) * u)], 46 * u)
        a += refl[..., None] * np.array([80, 88, 84], np.float32)
        bg = to_img(a); d = ImageDraw.Draw(bg)
        pads = [(0.10, 0.82, 190), (0.30, 0.96, 150), (0.92, 0.74, 200), (0.78, 0.93, 130), (0.95, 0.35, 120),
                (0.04, 0.45, 110), (0.62, 0.86, 90), (0.18, 0.62, 80)]
        for px, py, r in pads:
            x, y, r = px * w, py * h, r * u
            box = [x - r, y - r * 0.45, x + r, y + r * 0.45]
            st = rng.uniform(0, 360)
            d.ellipse([box[0] + 6, box[1] + 10, box[2] + 6, box[3] + 10], fill=(28, 42, 34))
            d.pieslice(box, st + 20, st + 360, fill=(36, 76, 42))
            d.pieslice([box[0] + 8 * u, box[1] + 4 * u, box[2] - 8 * u, box[3] - 4 * u], st + 30, st + 350, fill=(64, 116, 58))
            d.pieslice([box[0] + r * 0.35, box[1] + r * 0.15, box[2] - r * 0.35, box[3] - r * 0.15], st + 30, st + 350, fill=(86, 138, 72))
        # a lotus bud on the biggest pad
        x, y = 0.90 * w, 0.72 * h
        for k, c in enumerate([(236, 170, 190), (248, 200, 214), (255, 228, 236)]):
            rr = (34 - k * 9) * u
            d.ellipse([x - rr * 0.7, y - rr * 1.6, x + rr * 0.7, y], fill=c)
        self.bg = bg
        n = 340
        self.rip = np.c_[rng.uniform(0, 12, n), rng.uniform(0, w, n), rng.uniform(0.12 * h, h, n)]
        self.rain = Rain(w, h, rng, n=170, color=(228, 236, 230), alpha=(36, 90), slant=0.08, u=u)
        self.petals = np.c_[rng.uniform(0, w, 9), rng.uniform(0.2 * h, 0.9 * h, 9), rng.uniform(0, 6.28, 9)]

    def frame(self, t):
        u = self.u
        im = self.bg.copy(); ov = self.overlay(); d = ImageDraw.Draw(ov)
        tt = t % 12
        for t0, x, y in self.rip:
            age = (tt - t0) % 12
            if age > 2.0:
                continue
            s = (0.6 + 0.9 * y / self.h) * u
            fade = 1 - age / 2.0
            for k, frac in ((0, 1.0), (1, 0.6), (2, 0.3)):
                r = age * 70 * s * frac
                if r < 2:
                    continue
                d.ellipse([x - r, y - r * 0.34, x + r, y + r * 0.34], outline=(228, 238, 232, int(150 * fade * (1 - 0.35 * k))), width=max(2, int(2 * u)))
            if age < 0.12:
                d.ellipse([x - 3 * u, y - 7 * u, x + 3 * u, y], fill=(240, 245, 240, 200))
        for px, py, ph in self.petals:
            x = px + 14 * u * t + 10 * u * math.sin(t * 0.6 + ph)
            y = py + 6 * u * math.sin(t * 0.4 + ph)
            x = x % (self.w + 40) - 20
            r = 11 * u
            d.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], fill=(250, 214, 224, 235))
            d.ellipse([x - r * 0.4, y - r * 0.25, x + r * 0.5, y + r * 0.2], fill=(255, 236, 242, 200))
        self.rain.draw(d, t)
        im.paste(ov, (0, 0), ov)
        return im


class NightTown(Scene):
    ambience = "town"
    bokeh = (255, 190, 120)
    bokeh_n = 10

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.street = st = int(h * 0.72)
        a = vgrad(w, h, [(0, (5, 10, 28)), (0.45, (22, 34, 70)), (0.70, (44, 56, 92)), (0.72, (30, 36, 56)), (1, (8, 10, 18))])
        bg = to_img(a); d = ImageDraw.Draw(bg)
        for x, y in zip(rng.uniform(0, w, 90), rng.uniform(0, h * 0.30, 90)):
            b = int(rng.uniform(90, 210)); d.point((x, y), fill=(b, b, b + 20))
        win = Image.new("L", (w, h), 0); dw = ImageDraw.Draw(win)

        def row(top_lo, top_hi, base, colbase, win_p, scale):
            x = -30
            while x < w:
                bw = int(rng.uniform(150, 260) * u * scale); bh = int(rng.uniform(top_lo, top_hi) * h)
                top = base - bh
                col = tuple(int(c) for c in np.array(colbase) + rng.integers(-4, 6, 3))
                d.rectangle([x, top, x + bw, base], fill=col)
                r = rng.integers(0, 3)
                dark = tuple(max(0, c - 7) for c in col)
                if r == 0:
                    d.polygon([(x - 12 * u, top), (x + bw // 2, top - 60 * u * scale), (x + bw + 12 * u, top)], fill=dark)
                elif r == 1:
                    d.polygon([(x - 8 * u, top), (x + bw + 8 * u, top - 36 * u * scale), (x + bw + 8 * u, top)], fill=dark)
                else:
                    d.rectangle([x - 6 * u, top - 10 * u, x + bw + 6 * u, top], fill=dark)
                    d.rectangle([x + bw * 0.6, top - 40 * u, x + bw * 0.7, top - 10 * u], fill=dark)
                ww, wh, gx, gy = 30 * u * scale, 38 * u * scale, 52 * u * scale, 66 * u * scale
                for wy in np.arange(top + 30 * u, base - 70 * u, gy):
                    for wx in np.arange(x + 20 * u, x + bw - ww - 10 * u, gx):
                        if rng.random() < win_p:
                            tint = (255, int(rng.uniform(176, 216)), int(rng.uniform(96, 140)))
                            d.rectangle([wx, wy, wx + ww, wy + wh], fill=tint)
                            d.line([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], fill=col, width=2)
                            dw.rectangle([wx, wy, wx + ww, wy + wh], fill=int(255 * scale))
                        else:
                            d.rectangle([wx, wy, wx + ww, wy + wh], fill=tuple(max(0, c - 10) for c in col))
                x += bw + int(rng.uniform(4, 24) * u)

        row(0.20, 0.30, st - int(30 * u), (30, 38, 66), 0.30, 0.7)
        row(0.22, 0.40, st, (20, 24, 40), 0.42, 1.0)
        # utility poles and sagging power lines (very anime)
        poles = [w * 0.10, w * 0.86]
        for px in poles:
            d.rectangle([px - 7 * u, h * 0.20, px + 7 * u, st], fill=(12, 14, 24))
            d.rectangle([px - 50 * u, h * 0.23, px + 50 * u, h * 0.23 + 8 * u], fill=(12, 14, 24))
            d.rectangle([px - 38 * u, h * 0.27, px + 38 * u, h * 0.27 + 7 * u], fill=(12, 14, 24))
        for k, (yo, off) in enumerate([(0.23, -46), (0.23, 46), (0.27, -34), (0.27, 34), (0.23, 0)]):
            x0, x1 = poles[0] + off * u, poles[1] + off * u
            y0 = h * yo
            pts = [(x0 + (x1 - x0) * s / 30, y0 + 70 * u * 4 * (s / 30) * (1 - s / 30) + k * 6 * u) for s in range(31)]
            d.line(pts, fill=(10, 12, 22), width=max(2, int(2 * u)))
            d.line([(-10, y0 + 40 * u + k * 10 * u), (x0, y0 + k * 3 * u)], fill=(10, 12, 22), width=max(2, int(2 * u)))
            d.line([(x1, y0 + k * 3 * u), (w + 10, y0 + 50 * u + k * 8 * u)], fill=(10, 12, 22), width=max(2, int(2 * u)))
        self.lx = lx = int(w * 0.66)
        d.rectangle([lx - 5 * u, st - 330 * u, lx + 5 * u, st], fill=(14, 16, 26))
        d.polygon([(lx - 26 * u, st - 332 * u), (lx + 26 * u, st - 332 * u), (lx + 14 * u, st - 366 * u), (lx - 14 * u, st - 366 * u)], fill=(20, 22, 32))
        d.rectangle([lx - 17 * u, st - 332 * u, lx + 17 * u, st - 320 * u], fill=(255, 228, 160))
        arr = np.asarray(bg, np.float32)
        arr = add_glow(arr, np.asarray(win.filter(ImageFilter.GaussianBlur(18 * u)), np.float32) / 255, (255, 168, 80), 0.95)
        arr = add_glow(arr, radial(w, h, lx, st - 326 * u, 150 * u), (255, 196, 120), 0.75)
        cone = blur_mask((w, h), lambda dd: dd.polygon([(lx - 16 * u, st - 320 * u), (lx + 16 * u, st - 320 * u), (lx + 170 * u, st), (lx - 170 * u, st)], fill=70), 24 * u)
        arr = add_glow(arr, cone, (255, 210, 140), 0.6)
        upper = arr[st - (h - st):st][::-1]
        refl = np.asarray(to_img(upper).resize((w // 4, (h - st) // 4)).filter(ImageFilter.GaussianBlur(3)).resize((w, h - st)), np.float32)
        streaks = np.repeat(np.clip(np.random.default_rng(3).normal(1, 0.28, (1, w)), 0.4, 1.7), h - st, 0)[..., None]
        arr[st:] = arr[st:] * 0.55 + refl[: h - st] * 0.42 * streaks
        self.bg = to_img(arr)
        self.rain = Rain(w, h, rng, n=230, color=(176, 194, 232), alpha=(40, 95), slant=0.12, u=u)
        self.fog = blur_mask((w * 2, int(220 * u)), lambda dd: [dd.ellipse([x, 40 * u + y, x + 460 * u, 170 * u + y], fill=90)
                                                              for x, y in zip(rng.uniform(0, w * 2, 12), rng.uniform(-20, 30, 12) * u)], 34 * u)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = np.asarray(self.bg, np.float32).copy()
        fog = np.roll(self.fog, -int(t * 16 * u) % w, axis=1)[:, :w]
        y0 = self.street - int(150 * u)
        arr[y0:y0 + fog.shape[0]] += fog[..., None] * np.array([60, 70, 96], np.float32) * 0.5
        im = to_img(arr); ov = self.overlay(); d = ImageDraw.Draw(ov)
        px = w * 0.18 + 26 * u * t
        s = 1.25 * u
        d.ellipse([px - 26 * s, self.street + 18 * s, px + 26 * s, self.street + 26 * s], fill=(0, 0, 0, 80))
        person(d, px, self.street + 20 * s, s, t, (10, 11, 18, 255), umbrella=(64, 30, 40, 255))
        self.rain.draw(d, t)
        im.paste(ov, (0, 0), ov)
        return im


class Forest(Scene):
    ambience = "forest"
    bokeh = (255, 244, 200)
    bokeh_n = 9

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        vy = h * 0.56
        a = vgrad(w, h, [(0, (196, 224, 160)), (0.35, (168, 206, 132)), (0.56, (120, 160, 92)), (0.75, (78, 118, 66)), (1, (36, 64, 40))])
        a = add_glow(a, radial(w, h, w * 0.52, vy - 80 * u, 380 * u), (255, 250, 220), 0.55)
        bg = to_img(a); d = ImageDraw.Draw(bg)
        far = Image.new("RGBA", (w, h), (0, 0, 0, 0)); df = ImageDraw.Draw(far)
        for x, y, r in zip(rng.uniform(-50, w + 50, 50), rng.uniform(h * 0.12, h * 0.52, 50), rng.uniform(70, 150, 50) * u):
            g = int(rng.uniform(128, 168))
            df.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=(g - 34, g + 18, g - 54, 255))
        far = far.filter(ImageFilter.GaussianBlur(6 * u)); bg.paste(far, (0, 0), far)
        d.polygon([(w * 0.18, h), (w * 0.86, h), (w * 0.555, vy), (w * 0.505, vy)], fill=(178, 160, 112))
        d.polygon([(w * 0.34, h), (w * 0.66, h), (w * 0.54, vy + 20 * u), (w * 0.52, vy + 20 * u)], fill=(206, 190, 140))
        trunks = sorted(list(rng.uniform(-0.05, 0.38, 5)) + list(rng.uniform(0.66, 1.05, 5)), key=lambda v: abs(v - 0.5), reverse=False)
        for xf in trunks:
            x = xf * w
            depth = 1 - min(1, abs(xf - 0.52) / 0.5)
            tw = (18 + 40 * (1 - depth)) * u
            base = vy + (0.10 + 0.28 * (1 - depth)) * h
            col = tuple(int(c) for c in np.array([60, 50, 38]) + depth * np.array([50, 56, 30]))
            d.polygon([(x - tw / 2, base), (x + tw / 2, base), (x + tw * 0.34, -10), (x - tw * 0.34, -10)], fill=col)
            d.line([(x + tw * 0.18, base), (x + tw * 0.12, -10)], fill=tuple(min(255, c + 30) for c in col), width=max(2, int(3 * u)))
        grass = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dg = ImageDraw.Draw(grass)
        for x, y, r in zip(rng.uniform(-30, w + 30, 90), rng.uniform(h * 0.66, h * 1.05, 90), rng.uniform(46, 110, 90) * u):
            if w * 0.30 < x < w * 0.72 and y < h * 0.95:
                continue
            dg.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(52, 96, 50, 255))
            dg.ellipse([x - r * 0.8, y - r * 0.6, x + r * 0.6, y + r * 0.1], fill=(92, 142, 70, 255))
        bg.paste(grass, (0, 0), grass)
        self.bg = bg
        self.canopy = []
        for cx, cy, sz in ((-0.10, -0.05, 1.0), (0.30, -0.10, 1.1), (0.75, -0.08, 1.0), (1.08, -0.02, 1.0),
                           (-0.12, 0.14, 0.8), (1.10, 0.18, 0.85), (0.50, -0.14, 0.9)):
            spr = blob_sprite(int(760 * u * sz), int(560 * u * sz), rng, lit=(132, 186, 92), mid=(76, 130, 66), shade=(34, 68, 40), n=20, flat=1.0)
            self.canopy.append((spr, cx * w - spr.width / 2, cy * h, rng.uniform(0, 6.28)))
        self.shafts = []
        for i in range(5):
            x = w * (0.30 + 0.12 * i) + rng.uniform(-30, 30) * u; wd = rng.uniform(34, 80) * u
            m = blur_mask((w, h), lambda dd, x=x, wd=wd: dd.polygon([(x, -10), (x + wd, -10), (x - 380 * u + wd * 2, h), (x - 440 * u, h)], fill=105), 24 * u)
            self.shafts.append((m, rng.uniform(0, 6.28)))
        self.motes = Motes(rng, 80, (0, 0, w, h * 0.9), r=(1.5 * u, 3.6 * u))
        self.vy = vy

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = np.asarray(self.bg, np.float32).copy()
        for m, ph in self.shafts:
            arr += m[..., None] * np.array([255, 240, 190], np.float32) * (0.40 + 0.25 * math.sin(t * 0.7 + ph))
        im = to_img(arr)
        ov = self.overlay(); d = ImageDraw.Draw(ov)
        p = min(1.0, (t % 40) / 40)
        py = h * 0.86 - p * (h * 0.86 - self.vy - 60 * u)
        s = (1.0 - 0.7 * p) * 0.9 * u
        person(d, w * 0.535 - 10 * u * p, py, s, t * 0.8, (40, 46, 40, 235))
        im.paste(ov, (0, 0), ov)
        for spr, x0, y0, ph in self.canopy:
            im.paste(spr, (int(x0 + 7 * u * math.sin(t * 0.8 + ph)), int(y0 + 3 * u * math.sin(t * 1.1 + ph))), spr)
        ov = self.overlay(); self.motes.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


def _persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
        B += [X, Y]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


class Room(Scene):
    ambience = "room"
    bokeh = (255, 232, 190)

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        fy = int(h * 0.66)
        a = vgrad(w, h, [(0, (86, 66, 58)), (0.64, (58, 44, 40)), (0.66, (104, 76, 58)), (1, (74, 52, 42))])
        bg = to_img(a); d = ImageDraw.Draw(bg)
        for k, y in enumerate(np.arange(fy, h, 28 * u)):
            d.line([(0, y), (w, y)], fill=(84, 60, 46), width=max(2, int(2 * u)))
        self.win = (int(w * 0.18), int(h * 0.10), int(w * 0.82), int(h * 0.50))
        x0, y0, x1, y1 = self.win
        sw = (x1 - x0) * 3
        sky = to_img(vgrad(sw, y1 - y0, [(0, (84, 156, 224)), (1, (214, 236, 246))]))
        for _ in range(7):
            spr = cloud(int(rng.uniform(220, 360) * u), int(140 * u), rng, n=11)
            sky.paste(spr, (int(rng.uniform(0, sw - 200)), int(rng.uniform(0, (y1 - y0) * 0.55))), spr)
        ds = ImageDraw.Draw(sky)
        for x, r in zip(rng.uniform(0, sw, 40), rng.uniform(40, 80, 40) * u):
            ds.ellipse([x - r, (y1 - y0) - r * 0.8, x + r, (y1 - y0) + r], fill=(62, 112, 72))
        # a distant minaret through the window
        hh = y1 - y0
        for k in range(2):
            mx = sw * (0.22 + 0.5 * k)
            c = (164, 184, 204)
            ds.ellipse([mx - 70 * u, hh * 0.80, mx + 70 * u, hh * 0.80 + 120 * u], fill=c)
            ds.rectangle([mx - 90 * u, hh * 0.86, mx + 90 * u, hh], fill=c)
            for ox in (-110, 110):
                ds.rectangle([mx + ox * u - 7 * u, hh * 0.62, mx + ox * u + 7 * u, hh], fill=c)
                ds.rectangle([mx + ox * u - 11 * u, hh * 0.70, mx + ox * u + 11 * u, hh * 0.70 + 6 * u], fill=c)
                ds.polygon([(mx + ox * u - 8 * u, hh * 0.62), (mx + ox * u + 8 * u, hh * 0.62), (mx + ox * u, hh * 0.57)], fill=c)
        self.sky = sky
        # bookshelf (right, partly off-frame)
        bx0, bx1 = int(w * 0.86), int(w * 1.05)
        d.rectangle([bx0, int(h * 0.20), bx1, fy + 40 * u], fill=(46, 30, 24))
        pal = [(140, 60, 50), (60, 90, 120), (170, 140, 90), (80, 110, 70), (120, 90, 120), (190, 170, 140)]
        for sy in np.arange(h * 0.23, fy, 96 * u):
            bx = bx0 + 12 * u
            while bx < bx1:
                bw = rng.uniform(12, 26) * u; bh = rng.uniform(56, 80) * u
                d.rectangle([bx, sy + 82 * u - bh, bx + bw, sy + 82 * u], fill=pal[rng.integers(len(pal))])
                bx += bw + 2
            d.rectangle([bx0, sy + 82 * u, bx1, sy + 92 * u], fill=(68, 46, 34))
        # prayer mat in perspective
        mw, mh = 300, 520
        mat = Image.new("RGB", (mw, mh), (96, 22, 34)); dm = ImageDraw.Draw(mat)
        dm.rectangle([10, 10, mw - 11, mh - 11], outline=(214, 172, 92), width=8)
        dm.rectangle([30, 30, mw - 31, mh - 31], outline=(70, 20, 30), width=6)
        dm.rectangle([46, 140, mw - 47, mh - 46], fill=(116, 30, 42))
        dm.polygon([(46, 140), (mw // 2, 60), (mw - 47, 140)], fill=(116, 30, 42))
        dm.line([(46, 140), (mw // 2, 60), (mw - 47, 140)], fill=(214, 172, 92), width=5)
        for yy in range(170, mh - 60, 46):
            dm.polygon([(mw // 2, yy), (mw // 2 + 26, yy + 20), (mw // 2, yy + 40), (mw // 2 - 26, yy + 20)], outline=(214, 172, 92))
        for xx in range(20, mw - 10, 22):
            dm.line([(xx, mh - 8), (xx, mh)], fill=(230, 210, 170), width=3)
        quad = [(w * 0.40, fy + 70 * u), (w * 0.66, fy + 70 * u), (w * 0.80, h * 0.97), (w * 0.22, h * 0.97)]
        coeffs = _persp_coeffs(quad, [(0, 0), (mw, 0), (mw, mh), (0, mh)])
        warped = mat.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
        mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).polygon(quad, fill=255)
        bg.paste(warped, (0, 0), mask)
        # rehal with open Quran at the head of the mat
        rx, ry = w * 0.53, fy + 30 * u
        u = u * 1.6
        d.line([(rx - 60 * u, ry + 40 * u), (rx + 50 * u, ry - 30 * u)], fill=(96, 62, 38), width=int(10 * u))
        d.line([(rx + 60 * u, ry + 40 * u), (rx - 50 * u, ry - 30 * u)], fill=(110, 72, 44), width=int(10 * u))
        d.polygon([(rx - 70 * u, ry - 36 * u), (rx, ry - 20 * u), (rx, ry + 6 * u), (rx - 66 * u, ry - 8 * u)], fill=(246, 238, 220))
        d.polygon([(rx + 70 * u, ry - 36 * u), (rx, ry - 20 * u), (rx, ry + 6 * u), (rx + 66 * u, ry - 8 * u)], fill=(236, 226, 206))
        for k in range(4):
            d.line([(rx - 60 * u, ry - 28 * u + k * 7 * u), (rx - 10 * u, ry - 16 * u + k * 7 * u)], fill=(150, 130, 110), width=1)
            d.line([(rx + 60 * u, ry - 28 * u + k * 7 * u), (rx + 10 * u, ry - 16 * u + k * 7 * u)], fill=(150, 130, 110), width=1)
        u = self.u
        self.patch = blur_mask((w, h), lambda dd: dd.polygon([(x0 + 60 * u, fy + 30 * u), (x1 + 40 * u, fy + 30 * u), (x1 + 260 * u, h), (x0 - 40 * u, h)], fill=120), 14 * u)
        self.beam = blur_mask((w, h), lambda dd: dd.polygon([(x0, y0), (x1, y0), (x1 + 260 * u, h), (x0 - 40 * u, h)], fill=46), 40 * u)
        self.bg = bg
        self.motes = Motes(rng, 70, (x0 - 40 * u, y0, x1 + 200 * u, h), color=(255, 236, 190), r=(1.2 * u, 2.8 * u), rise=4)
        self.fy = fy

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        x0, y0, x1, y1 = self.win
        im = self.bg.copy()
        off = int(t * 12 * u) % (self.sky.width - (x1 - x0))
        im.paste(self.sky.crop((off, 0, off + (x1 - x0), y1 - y0)), (x0, y0))
        d = ImageDraw.Draw(im)
        fr = (44, 30, 24)
        d.rectangle([x0, y0, x1, y1], outline=fr, width=int(18 * u))
        d.line([((x0 + x1) // 2, y0), ((x0 + x1) // 2, y1)], fill=fr, width=int(12 * u))
        d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=fr, width=int(12 * u))
        d.rectangle([x0 - 26 * u, y1, x1 + 26 * u, y1 + 18 * u], fill=(70, 48, 36))
        # potted plant on the sill
        px, py = x1 - 90 * u, y1
        d.polygon([(px - 30 * u, py - 54 * u), (px + 30 * u, py - 54 * u), (px + 22 * u, py), (px - 22 * u, py)], fill=(170, 90, 60))
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * 0.32 + 0.06 * math.sin(t * 1.3 + k)
            ex, ey = px + math.cos(ang) * 80 * u, py - 54 * u + math.sin(ang) * 80 * u
            d.line([(px, py - 54 * u), (ex, ey)], fill=(60, 110, 60), width=int(4 * u))
            d.ellipse([ex - 16 * u, ey - 9 * u, ex + 16 * u, ey + 9 * u], fill=(84, 146, 72))
        arr = np.asarray(im, np.float32)
        arr = add_glow(arr, self.patch, (255, 214, 150), 0.62)
        arr = add_glow(arr, self.beam, (255, 226, 170), 0.55 + 0.1 * math.sin(t * 0.5))
        im = to_img(arr)
        ov = self.overlay(); do = ImageDraw.Draw(ov)
        for side, cx in ((-1, x0 - 10 * u), (1, x1 + 10 * u)):
            sway = 12 * u * math.sin(t * 0.8 + (0 if side < 0 else 1.7))
            inner = cx - side * 40 * u
            outer = cx + side * 90 * u
            pts = [(outer, y0 - 30 * u)] + [(inner + sway * (k / 12) ** 2 + 6 * u * math.sin(k * 1.3 + t), y0 - 30 * u + k * (y1 - y0 + 90 * u) / 12) for k in range(13)]
            pts += [(outer + sway * 0.5, y1 + 60 * u)]
            do.polygon(pts, fill=(232, 220, 196, 240))
            for k in range(3):
                fx = (inner + outer) / 2 + (k - 1) * 30 * u
                do.line([(fx, y0 - 20 * u), (fx + sway, y1 + 50 * u)], fill=(196, 180, 156, 150), width=int(4 * u))
        self.motes.draw(do, t)
        im.paste(ov, (0, 0), ov)
        return im


class Meadow(Scene):
    ambience = "meadow"
    bokeh = (255, 250, 230)

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.hz = hz = int(h * 0.58)
        a = vgrad(w, h, [(0, (46, 120, 204)), (0.50, (160, 206, 236)), (0.58, (196, 224, 236)), (0.585, (120, 174, 88)), (1, (52, 118, 44))])
        a = fill_below(a, ridge(w, rng, hz - 70 * u, 50 * u), (140, 166, 198))
        a = fill_below(a, ridge(w, rng, hz - 16 * u, 14 * u, 6), (80, 130, 84))
        hill = hz + 30 * u - 90 * u * np.exp(-((np.arange(w) - w * 0.74) / (w * 0.30)) ** 2)
        a = fill_below(a, hill.astype(np.float32), (122, 178, 88))
        yy = np.linspace(0, 1, h)[:, None, None]
        a = np.where(yy > (hz + 30 * u) / h, a * (0.86 + 0.24 * (1 - yy)), a)
        bg = to_img(a); d = ImageDraw.Draw(bg)
        self.tx, self.ty = tx, ty = w * 0.74, hz - 60 * u
        d.polygon([(tx - 20 * u, ty), (tx + 20 * u, ty), (tx + 9 * u, ty - 230 * u), (tx - 9 * u, ty - 230 * u)], fill=(70, 52, 40))
        d.line([(tx, ty - 160 * u), (tx - 70 * u, ty - 250 * u)], fill=(70, 52, 40), width=int(10 * u))
        d.line([(tx, ty - 190 * u), (tx + 80 * u, ty - 270 * u)], fill=(70, 52, 40), width=int(9 * u))
        d.ellipse([tx - 120 * u, ty - 10 * u, tx + 140 * u, ty + 14 * u], fill=(84, 130, 66))
        self.bg = bg
        self.crown = blob_sprite(int(520 * u), int(380 * u), rng, lit=(150, 200, 96), mid=(92, 150, 70), shade=(44, 86, 50), n=20, flat=0.92)
        self.clouds = [(cloud(int(rng.uniform(460, 780) * u), int(rng.uniform(220, 340) * u), rng), rng.uniform(-300, w), rng.uniform(0, 0.32) * h, rng.uniform(8, 16) * u) for _ in range(4)]
        n = 1100
        ys = hz + 30 * u + (h - hz - 30 * u) * rng.random(n) ** 0.65
        order = np.argsort(ys)
        self.bl = np.c_[rng.uniform(-10, w + 10, n), ys, rng.uniform(0, 6.28, n), rng.uniform(0.7, 1.35, n)][order]
        self.flowers = np.c_[rng.uniform(0, w, 110), hz + 50 * u + (h - hz) * rng.random(110)]
        self.birds = np.c_[rng.uniform(-200, w, 4), rng.uniform(0.12, 0.36, 4) * h, rng.uniform(40, 70, 4) * u]
        self.seeds = Motes(rng, 30, (0, h * 0.3, w, h), color=(255, 255, 245), r=(1.5 * u, 2.8 * u), rise=10, sway=40 * u)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy()
        for spr, x0, y, v in self.clouds:
            im.paste(spr, (int(wrap_x(x0, v, t, spr.width, w)), int(y)), spr)
        sw = 5 * u * math.sin(t * 0.9)
        im.paste(self.crown, (int(self.tx - self.crown.width / 2 + sw), int(self.ty - 230 * u - self.crown.height * 0.72)), self.crown)
        d = ImageDraw.Draw(im)
        for x, y in self.flowers:
            r = 3 * u * (0.5 + (y - self.hz) / (h - self.hz))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(250, 248, 228))
        gx = (t * 320 * u) % (w * 2.4) - w * 0.7
        for x, y, ph, s in self.bl:
            p = (y - self.hz) / (h - self.hz)
            L = (12 + 70 * p ** 1.2) * s * u
            gust = math.exp(-((x - gx) / (220 * u)) ** 2)
            sway = (5 + 16 * p) * u * (math.sin(t * 1.6 + x * 0.008 + ph * 0.3) * 0.6 + 1.6 * gust)
            g = int(104 + 76 * (1 - p) + 22 * math.sin(ph))
            d.line([(x, y), (x + sway * 0.5, y - L * 0.55), (x + sway, y - L)], fill=(int(g * 0.55), g, int(g * 0.34)), width=max(2, int((2 + 3 * p) * u)), joint="curve")
        for bx, by, v in self.birds:
            x = (bx + v * t) % (w + 200) - 100
            f = 7 * u * math.sin(t * 7 + bx)
            d.line([(x - 12 * u, by - f), (x, by), (x + 12 * u, by - f)], fill=(40, 50, 60), width=max(2, int(2 * u)))
        ov = self.overlay(); self.seeds.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class Mosque(Scene):
    ambience = "night"
    bokeh = (255, 200, 130)
    bokeh_n = 8

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (4, 6, 22)), (0.45, (18, 22, 60)), (0.68, (70, 50, 104)), (0.78, (110, 70, 110)), (1, (30, 22, 44))])
        band = blur_mask((w, h), lambda d: d.polygon([(-100, h * 0.55), (w * 0.4, -50), (w * 0.75, -50), (w * 0.15, h * 0.62)], fill=80), 70 * u)
        a = add_glow(a, band, (130, 130, 180), 0.35)
        dust = blur_mask((w, h), lambda d: [d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=255) for x, y in
                                            zip(rng.uniform(0, w, 900), rng.uniform(0, h * 0.6, 900)) if band[int(min(y, h - 1)), int(min(x, w - 1))] > 0.2], 2)
        a = add_glow(a, dust, (200, 200, 240), 0.5)
        self.mx, self.my, self.mr = w * 0.76, h * 0.14, 52 * u
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d1 = np.hypot(xx - self.mx, yy - self.my); d2 = np.hypot(xx - self.mx - 21 * u, yy - self.my + 13 * u)
        moon = np.clip(self.mr - d1 + 0.5, 0, 1) * np.clip(d2 - (self.mr - 4 * u) + 0.5, 0, 1)
        a = add_glow(a, np.exp(-(d1 / (150 * u)) ** 2) * 0.55, (200, 190, 160), 0.6)
        a = a * (1 - moon[..., None]) + np.array([252, 244, 210], np.float32) * moon[..., None]
        a = fill_below(a, ridge(w, rng, h * 0.74, 34 * u), (34, 28, 62))
        a = fill_below(a, ridge(w, rng, h * 0.84, 20 * u), (18, 15, 36))
        bg = to_img(a); d = ImageDraw.Draw(bg)
        sil = (11, 10, 24)
        s = 1.35 * u
        cx, base = w * 0.52, h * 0.82
        d.rectangle([cx - 160 * s, base - 92 * s, cx + 160 * s, h], fill=sil)
        d.rectangle([cx - 84 * s, base - 136 * s, cx + 84 * s, base - 88 * s], fill=sil)
        d.ellipse([cx - 96 * s, base - 226 * s, cx + 96 * s, base - 60 * s], fill=sil)
        d.line([(cx, base - 228 * s), (cx, base - 258 * s)], fill=sil, width=int(4 * s))
        d.ellipse([cx - 9 * s, base - 278 * s, cx + 9 * s, base - 260 * s], outline=(232, 202, 122), width=max(2, int(3 * s)))
        for sx in (cx - 222 * s, cx + 222 * s):
            d.rectangle([sx - 14 * s, base - 310 * s, sx + 14 * s, h], fill=sil)
            d.rectangle([sx - 22 * s, base - 238 * s, sx + 22 * s, base - 229 * s], fill=sil)
            d.polygon([(sx - 16 * s, base - 310 * s), (sx + 16 * s, base - 310 * s), (sx, base - 356 * s)], fill=sil)
            d.rectangle([sx - 64 * s, base - 40 * s, sx + 64 * s, h], fill=sil)
        for sx in (cx - 124 * s, cx + 124 * s):
            d.ellipse([sx - 36 * s, base - 134 * s, sx + 36 * s, base - 72 * s], fill=sil)
        wm = Image.new("L", (w, h), 0); dw = ImageDraw.Draw(wm)
        for k in range(-3, 4):
            x = cx + k * 40 * s
            for dd, col in ((d, (255, 198, 112)), (dw, 255)):
                dd.rectangle([x - 9 * s, base - 52 * s, x + 9 * s, base - 20 * s], fill=col)
                dd.ellipse([x - 9 * s, base - 61 * s, x + 9 * s, base - 43 * s], fill=col)
        # foreground hill with a seated figure looking at the mosque
        fg = ridge(w, rng, h * 0.93, 18 * u)
        arr = np.asarray(bg, np.float32).copy()
        arr = add_glow(arr, np.asarray(wm.filter(ImageFilter.GaussianBlur(16 * u)), np.float32) / 255, (255, 170, 80), 0.85)
        arr = fill_below(arr, fg - 40 * u * np.exp(-((np.arange(w) - w * 0.16) / (w * 0.18)) ** 2), (6, 6, 14))
        bg = to_img(arr); d = ImageDraw.Draw(bg)
        fx, fy = w * 0.16, float(fg[int(w * 0.16)] - 40 * u) + 4 * u
        k = 1.25 * u
        d.ellipse([fx - 11 * k, fy - 78 * k, fx + 11 * k, fy - 56 * k], fill=(6, 6, 14))
        d.polygon([(fx - 20 * k, fy), (fx + 30 * k, fy), (fx + 18 * k, fy - 26 * k), (fx + 12 * k, fy - 58 * k), (fx - 12 * k, fy - 58 * k), (fx - 22 * k, fy - 26 * k)], fill=(6, 6, 14))
        self.bg = bg
        n = 300
        st = np.c_[rng.uniform(0, w, n), h * 0.66 * rng.random(n) ** 1.3, rng.uniform(0, 6.28, n), rng.uniform(0.8, 2.6, n) * u, rng.uniform(0.6, 1.8, n)]
        keep = np.hypot(st[:, 0] - self.mx, st[:, 1] - self.my) > self.mr + 10 * u
        self.stars = st[keep]
        self.flies = Motes(rng, 18, (0, h * 0.80, w, h), color=(255, 226, 140), r=(1.8 * u, 3.2 * u), rise=6, sway=30 * u)
        self.wisps = []
        for _ in range(3):
            m = Image.new("L", (int(620 * u), int(110 * u)), 0); dm = ImageDraw.Draw(m)
            for _ in range(6):
                x = rng.uniform(50, 520) * u; y = rng.uniform(30, 70) * u
                dm.ellipse([x - 110 * u, y - 16 * u, x + 110 * u, y + 16 * u], fill=110)
            m = m.filter(ImageFilter.GaussianBlur(14 * u))
            spr = Image.new("RGBA", m.size, (70, 60, 110, 0)); spr.putalpha(m)
            self.wisps.append((spr, rng.uniform(-300, w), rng.uniform(0.06, 0.40) * h, rng.uniform(10, 20) * u))

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.bg.copy(); ov = self.overlay(); d = ImageDraw.Draw(ov)
        for x, y, ph, r, f in self.stars:
            a = int(255 * (0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * f + ph)) ** 2))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 255, a))
            if r > 1.9 * u:
                d.line([(x - r * 3, y), (x + r * 3, y)], fill=(235, 235, 255, a // 3))
                d.line([(x, y - r * 3), (x, y + r * 3)], fill=(235, 235, 255, a // 3))
        ts = (t % 8.0) - 3.0
        if 0 <= ts < 0.8:
            p = ts / 0.8
            sx, sy = w * 0.12 + p * 460 * u, h * 0.06 + p * 170 * u
            d.line([(sx, sy), (sx - 140 * u * (1 - p * 0.5), sy - 52 * u * (1 - p * 0.5))], fill=(255, 255, 255, int(230 * (1 - p))), width=max(2, int(3 * u)))
        self.flies.draw(d, t)
        im.paste(ov, (0, 0), ov)
        for spr, x0, y, v in self.wisps:
            im.paste(spr, (int(wrap_x(x0, v, t, spr.width, w)), int(y)), spr)
        return im


SCENES = {"sea": Sea, "rain": RainPond, "town": NightTown, "forest": Forest,
          "room": Room, "meadow": Meadow, "mosque": Mosque}
