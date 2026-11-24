"""
Light-theme scenes (Nov 2026). Soft, pleasant palettes: cream, warm sand, pale sky, sage, blush.
Scenes here set `theme = "light"`, so captions render in dark ink with deep-gold highlights.
Same contract as the other scene modules.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scenes import Scene, vgrad, to_img, radial, Motes, ridge
from scenes_batch2 import Stage, walk_pose, ease, lerp  # noqa: F401  (Stage: timeline + figure helpers)

# palette (RGB)
CREAM, SAND, PEACH = (250, 245, 235), (240, 226, 204), (246, 214, 190)
SKY, SKY_HI, SAGE = (206, 226, 240), (236, 244, 250), (200, 220, 196)
BLUSH, INK_L, GOLD_D = (244, 214, 214), (52, 46, 58), (176, 120, 40)
PASTELS = [(255, 214, 170), (200, 226, 246), (214, 236, 210), (246, 206, 214), (236, 222, 250)]


def star8(d, cx, cy, r, col, width=1):
    """Outline of an 8-point star (two squares), the classic Islamic lattice motif."""
    for rot in (0, math.pi / 4):
        pts = [(cx + r * math.cos(rot + k * math.pi / 2), cy + r * math.sin(rot + k * math.pi / 2)) for k in range(4)]
        d.polygon(pts, outline=col, width=width)


class LightStage(Stage):
    theme = "light"
    band = 1.0            # cream glow behind the text block
    ink = INK_L           # stick-figure colour on light backgrounds

    def fig(self, im, x, ground, pose, s, col=None, alpha=1.0, flip=False):
        super().fig(im, x, ground, pose, s, col=col or self.ink, alpha=alpha, flip=flip)


class SoftLight(LightStage):
    """Generic premium light background: cream to peach, a sunlit glow, a faint 8-point-star lattice,
    pastel bokeh and drifting petals. Good behind quotes, ayah cards and any explainer without its own device."""
    ambience = "night_room"
    text_y = 0.36
    text_zone = (0.20, 0.62)

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (252, 248, 240)), (0.45, CREAM), (0.8, PEACH), (1, (236, 200, 176))])
        self.base = self.base + (radial(w, h, w * 0.72, h * 0.18, 720 * u) * 18)[..., None] * np.array([1, 0.9, 0.7], np.float32)
        pat = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(pat)
        step = 150 * u
        for j, y in enumerate(np.arange(-step, h + step, step)):
            for x in np.arange(-step + (step / 2 if j % 2 else 0), w + step, step):
                star8(d, x, y, 46 * u, (196, 160, 100, 46), width=max(1, int(2 * u)))
                d.ellipse([x - 5 * u, y - 5 * u, x + 5 * u, y + 5 * u], outline=(196, 160, 100, 40), width=max(1, int(2 * u)))
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        fade = np.clip(0.35 + 0.65 * yy, 0, 1)                      # lattice stronger toward the bottom
        a = np.asarray(pat.getchannel("A"), np.float32) * fade
        pat.putalpha(Image.fromarray(a.astype(np.uint8)))
        self.pat = pat
        self.bok = []
        for _ in range(16):                                         # pre-rendered soft pastel discs
            r = rng.uniform(40, 120) * u; col = PASTELS[int(rng.integers(len(PASTELS)))]
            sz = int(r * 2.6); spr = Image.new("RGBA", (sz, sz), col + (0,))
            m = Image.new("L", (sz, sz), 0); ImageDraw.Draw(m).ellipse([sz * 0.2, sz * 0.2, sz * 0.8, sz * 0.8], fill=110)
            spr.putalpha(m.filter(ImageFilter.GaussianBlur(r * 0.35)))
            self.bok.append((rng.uniform(0, w), rng.uniform(0, h), spr, rng.uniform(0, 6.28), rng.uniform(0.2, 0.6)))
        self.base_img = to_img(self.base)
        self.petals = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(10, 18) * u, rng.uniform(0, 6.28), rng.uniform(20, 50) * u) for _ in range(18)]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        im = self.base_img.copy()
        for x, y, spr, ph, sp in self.bok:                          # soft pastel bokeh, drifting and breathing
            xx = x + 30 * u * math.sin(t * 0.15 * sp + ph); yy_ = y + 20 * u * math.cos(t * 0.12 + ph)
            k = 0.7 + 0.3 * math.sin(t * 0.6 + ph)
            s_ = spr.copy(); s_.putalpha(spr.getchannel("A").point(lambda v, k=k: int(v * k)))
            im.paste(s_, (int(xx - spr.width / 2), int(yy_ - spr.height / 2)), s_)
        im.paste(self.pat, (0, int(8 * u * math.sin(t * 0.2))), self.pat)
        d = ImageDraw.Draw(im, "RGBA")
        for x, y, s, ph, sp in self.petals:                         # petals drifting down and across
            py = (y + sp * t) % (h + 60 * u) - 30 * u
            px = x + 40 * u * math.sin(t * 0.5 + ph)
            ang = t * 0.8 + ph
            dx, dy = math.cos(ang) * s, math.sin(ang) * s * 0.5
            d.ellipse([px - abs(dx) - 4 * u, py - abs(dy) - 3 * u, px + abs(dx) + 4 * u, py + abs(dy) + 3 * u], fill=(240, 180, 180, 150))
        return im


class LightSky(LightStage):
    """Pale morning sky with drifting clouds, gentle sun rays and sage hills. Nature narration, hope, dua."""
    ambience = "meadow"
    text_y = 0.30
    text_zone = (0.17, 0.52)

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (186, 214, 236)), (0.45, SKY), (0.72, SKY_HI), (1, (232, 240, 228))])
        self.base = self.base + (radial(w, h, w * 0.78, h * 0.20, 600 * u) * 40)[..., None] * np.array([1, 0.92, 0.75], np.float32)
        far = ridge(w, rng, h * 0.76, 34 * u); near = ridge(w, rng, h * 0.84, 26 * u)
        yy = np.arange(h, dtype=np.float32)[:, None]
        self.m_far = np.clip((yy - far[None, :]) / 1.5 + 0.5, 0, 1)[..., None]
        self.m_near = np.clip((yy - near[None, :]) / 1.5 + 0.5, 0, 1)[..., None]
        self.clouds = []
        for _ in range(7):
            cl = Image.new("L", (int(560 * u), int(300 * u)), 0); d = ImageDraw.Draw(cl)
            for _k in range(7):
                cx, cy, r = rng.uniform(140, 420) * u, rng.uniform(130, 170) * u, rng.uniform(40, 80) * u
                d.ellipse([cx - r * 1.4, cy - r, cx + r * 1.4, cy + r], fill=255)
            self.clouds.append((cl.filter(ImageFilter.GaussianBlur(14 * u)), rng.uniform(-0.2, 1.0), rng.uniform(0.06, 0.5), rng.uniform(4, 12)))
        m = Image.new("L", (w, h), 0); dm = ImageDraw.Draw(m)
        sx, sy = w * 0.78, h * 0.20
        for k in range(5):                                          # soft rays falling from the sun, down-left
            ang = math.radians(200 + k * 11)
            dm.polygon([(sx, sy), (sx + math.cos(ang - 0.04) * 2600, sy - math.sin(ang - 0.04) * 2600),
                        (sx + math.cos(ang + 0.04) * 2600, sy - math.sin(ang + 0.04) * 2600)], fill=30)
        self.rays = np.asarray(m.filter(ImageFilter.GaussianBlur(30 * u)), np.float32)[..., None] / 255
        self.birds = [(rng.uniform(0, 1), rng.uniform(0.40, 0.60), rng.uniform(0.02, 0.04), rng.uniform(0, 6.28)) for _ in range(5)]
        self.motes = Motes(rng, 30, (0, h * 0.4, w, h), color=(255, 246, 220), r=(1.0 * u, 2.2 * u), rise=6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        arr = self.base.copy()
        ra = self.rays * (0.8 + 0.2 * math.sin(t * 0.4))
        arr = arr * (1 - ra) + 255 * ra
        arr = arr * (1 - self.m_far) + np.array((176, 202, 186), np.float32) * self.m_far
        arr = arr * (1 - self.m_near) + np.array((150, 182, 150), np.float32) * self.m_near
        im = to_img(arr)
        for cl, x0, y0, sp in self.clouds:
            x = ((x0 * w + sp * u * t * 6) % (w + cl.width)) - cl.width
            im.paste((255, 255, 255), (int(x), int(y0 * h * 0.6)), cl.point(lambda v: int(v * 0.85)))
        d = ImageDraw.Draw(im, "RGBA")
        sx, sy = w * 0.78, h * 0.20
        d.ellipse([sx - 54 * u, sy - 54 * u, sx + 54 * u, sy + 54 * u], fill=(255, 250, 230, 255))
        for bx, by, sp, ph in self.birds:
            x = ((bx + sp * t) % 1.2 - 0.1) * w; y = by * h + 10 * u * math.sin(t + ph)
            f = 10 * u * math.sin(t * 8 + ph)
            d.line([(x - 18 * u, y - f), (x, y), (x + 18 * u, y - f)], fill=(90, 100, 120, 200), width=max(2, int(3 * u)))
        ov = self.overlay(); self.motes.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


LIGHT_SCENES = {"soft_light": SoftLight, "light_sky": LightSky}


class SeedDaily(LightStage):
    """Bukhari 6465: two pots. Left: one huge bucket at once, the plant shoots up then wilts.
    Right: a few drops every 'day', the plant grows into a small flowering tree. A day counter runs.
    Beats: hook, regular, few, ability, burst, grow, daily, ayah, cta."""
    ambience = "meadow"
    text_y = 0.26
    text_zone = (0.165, 0.40)

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (214, 232, 244)), (0.5, (240, 244, 240)), (0.84, (250, 242, 226)), (1, (236, 222, 200))])
        self.gy = h * 0.86
        self.px = (w * 0.27, w * 0.73)
        self.f_lab = self.font("Lora.ttf", 32); self.f_day = self.font("Lora.ttf", 40)
        self.leaf_ph = [rng.uniform(0, 6.28) for _ in range(40)]
        self.flowers = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 6.28)) for _ in range(14)]
        self.motes = Motes(rng, 26, (0, h * 0.42, w, h), color=(255, 250, 230), r=(1.0 * u, 2.2 * u), rise=5)

    # ---- drawing helpers
    def pot(self, d, x, gy):
        u = self.u * 1.3
        d.polygon([(x - 90 * u, gy - 120 * u), (x + 90 * u, gy - 120 * u), (x + 68 * u, gy), (x - 68 * u, gy)], fill=(206, 128, 92, 255))
        d.polygon([(x - 90 * u, gy - 120 * u), (x - 30 * u, gy - 120 * u), (x - 40 * u, gy), (x - 68 * u, gy)], fill=(222, 146, 110, 255))
        d.rectangle([x - 100 * u, gy - 138 * u, x + 100 * u, gy - 112 * u], fill=(190, 112, 80, 255))
        d.ellipse([x - 86 * u, gy - 146 * u, x + 86 * u, gy - 126 * u], fill=(110, 80, 60, 255))
        return gy - 136 * u

    def plant(self, d, x, base_y, height, bend, wilt, t, crown=0.0):
        """Stem with leaf pairs; `bend` in radians (wilting droop), `wilt` 0..1 colour shift to brown."""
        u = self.u
        g0, b0 = np.array((86, 160, 90)), np.array((150, 120, 70))
        col = tuple(int(v) for v in g0 * (1 - wilt) + b0 * wilt) + (255,)
        n = 12
        pts = []
        for k in range(n + 1):
            f = k / n
            ang = math.pi / 2 - bend * f ** 1.6 + 0.04 * math.sin(t * 1.3 + f * 2)
            if not pts:
                pts.append((x, base_y))
            else:
                px, py = pts[-1]
                seg = height / n
                pts.append((px + math.cos(ang) * seg, py - math.sin(ang) * seg))
        d.line(pts, fill=col, width=max(3, int((6 + 6 * crown) * u)), joint="curve")
        nleaf = int(min(9, height / (48 * u)))
        for k in range(1, nleaf + 1):
            i = max(1, int(k / (nleaf + 1) * n))
            lx, ly = pts[i]
            L = (34 + 22 * min(1, height / (400 * u))) * u
            Wd = L * 0.38
            for side in ((-1, 1) if k % 2 else (1, -1)):
                a = 0.55 + 0.08 * math.sin(t * 1.5 + self.leaf_ph[k % 40]) - wilt * 1.6     # wilting leaves hang down
                tx_, ty_ = lx + side * L * math.cos(a), ly - L * math.sin(a)
                mx_, my_ = (lx + tx_) / 2, (ly + ty_) / 2
                nx, ny = -(ty_ - ly) / L * Wd, (tx_ - lx) / L * Wd
                d.polygon([(lx, ly), (mx_ + nx, my_ + ny), (tx_, ty_), (mx_ - nx, my_ - ny)], fill=col)
                d.line([(lx, ly), (tx_, ty_)], fill=tuple(min(255, c + 30) for c in col[:3]) + (200,), width=max(1, int(2 * u)))
        if crown > 0:                                        # leafy crown + flowers at the top
            tx, ty = pts[-1]
            R = 150 * u * crown
            for k in range(9):
                a = k / 9 * math.tau
                cx = tx + math.cos(a) * R * 0.6; cy = ty - R * 0.25 + math.sin(a) * R * 0.45
                d.ellipse([cx - R * 0.5, cy - R * 0.4, cx + R * 0.5, cy + R * 0.4], fill=(100 + k * 3, 172, 104, 255))
            for fx, fy, ph in self.flowers:
                if crown < 0.6:
                    break
                cx = tx + fx * R * 0.9; cy = ty - R * 0.25 + fy * R * 0.55
                r = 10 * u * (0.8 + 0.2 * math.sin(t * 2 + ph))
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 160, 180, 255))
                d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=(255, 226, 140, 255))
        return pts[-1]

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        t_reg, t_burst, t_grow, t_ayah, t_cta = self.bt("regular"), self.bt("burst"), self.bt("grow"), self.bt("ayah"), self.bt("cta")
        im = to_img(self.base); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        sx_, sy_ = w * 0.50, h * 0.50                          # soft sun behind the scene
        dg.ellipse([sx_ - 160 * u, sy_ - 160 * u, sx_ + 160 * u, sy_ + 160 * u], fill=120)
        d.ellipse([sx_ - 70 * u, sy_ - 70 * u, sx_ + 70 * u, sy_ + 70 * u], fill=(255, 244, 214, 255))
        for k in range(2):                                     # distant soft hills (smooth sine ridges)
            pts = [(xx, gy - (70 - k * 30) * u - (26 - k * 8) * u * math.sin(xx / (w * (0.35 + 0.1 * k)) * math.tau + k * 1.7)) for xx in range(0, w + 20, 20)]
            d.polygon(pts + [(w, gy), (0, gy)], fill=(204 - k * 14, 224 - k * 8, 198 - k * 10, 255))
        d.rectangle([0, gy, w, h], fill=(222, 204, 172, 255))
        d.line([(0, gy), (w, gy)], fill=(196, 176, 140, 255), width=max(2, int(3 * u)))
        # day counter: one 'day' every 0.55 s once the regular watering starts
        day_len = 0.55
        days = int(max(0, (t - t_reg) / day_len)) + 1 if t > t_reg else 0
        if days:
            k = ease((t - t_reg) / 0.5)
            d.text((w * 0.50, h * 0.425), f"Day {days}", font=self.f_day, fill=(60, 120, 90, int(255 * k)), anchor="mm")
        # ---- left: all at once
        lx, rx = self.px
        ltop = self.pot(d, lx, gy)
        pour = (t - t_burst) / 1.1
        lh = 70 * u + (300 * u * ease((t - t_burst - 0.3) / 0.6) if t > t_burst else 0)
        wilt = ease((t - t_burst - 1.6) / 1.8)
        bend = 2.0 * wilt
        if 0 < pour < 1.2:                                   # a huge bucket tipping over the pot
            a = min(1, pour * 3) * (1 - max(0, pour - 1) * 5)
            bx, by = lx + 40 * u, h * 0.50
            d.polygon([(bx - 70 * u, by - 60 * u), (bx + 70 * u, by - 90 * u), (bx + 90 * u, by + 30 * u), (bx - 50 * u, by + 60 * u)], fill=(120, 150, 180, int(255 * a)))
            d.rectangle([lx - 46 * u, by + 30 * u, lx + 30 * u, ltop], fill=(110, 170, 230, int(200 * a)))
            for j in range(14):                                # splashes and overflow
                sx = lx + (j - 7) * 18 * u; sy = ltop - 10 * u - abs(math.sin(t * 9 + j)) * 30 * u
                d.ellipse([sx - 6 * u, sy - 6 * u, sx + 6 * u, sy + 6 * u], fill=(140, 190, 240, int(220 * a)))
        if t > t_burst + 0.6:                                   # puddle
            pk = min(1, (t - t_burst - 0.6) / 0.6) * (1 - ease((t - t_burst - 3.0) / 2.0))
            d.ellipse([lx - 170 * u, gy - 8 * u, lx + 170 * u, gy + 22 * u], fill=(140, 190, 230, int(160 * pk)))
        self.plant(d, lx, ltop, lh, bend, wilt, t)
        if t > t_burst:
            k = ease((t - t_burst) / 0.6)
            d.text((lx, gy + 30 * u), "all at once", font=self.f_lab, fill=(150, 90, 70, int(255 * k)), anchor="ma")
        # ---- right: a little, every day
        rtop = self.pot(d, rx, gy)
        g = 0.0 if not days else min(1.0, (t - t_reg) / max(1.0, (t_ayah - t_reg)))
        rh = 70 * u + 560 * u * g
        crown = ease((g - 0.55) / 0.45)
        if days:
            q = ((t - t_reg) % day_len) / day_len              # each day: tilt the small can, two drops
            cx, cy = rx + 150 * u, rtop - rh - 110 * u if rtop - rh - 110 * u > h * 0.48 else h * 0.48
            tilt = math.sin(math.pi * min(1, q * 1.6)) * 0.5
            can = (120, 176, 160, 255)
            d.rounded_rectangle([cx - 46 * u, cy - 34 * u, cx + 46 * u, cy + 34 * u], radius=int(14 * u), fill=can)
            d.arc([cx - 30 * u, cy - 70 * u, cx + 40 * u, cy - 10 * u], 180, 360, fill=can, width=int(9 * u))
            ex, ey = cx - 46 * u - 70 * u * math.cos(tilt), cy + 6 * u + 40 * u * math.sin(tilt)
            d.line([(cx - 40 * u, cy + 10 * u), (ex, ey)], fill=can, width=int(11 * u))
            d.ellipse([ex - 12 * u, ey - 12 * u, ex + 12 * u, ey + 12 * u], fill=(100, 156, 140, 255))
            for j in range(2):
                dq = (q - 0.2 - j * 0.18) / 0.5
                if 0 < dq < 1:
                    sx = ex; sy = lerp(ey + 14 * u, rtop - 8 * u, dq)
                    d.ellipse([sx - 6 * u, sy - 9 * u, sx + 6 * u, sy + 9 * u], fill=(110, 170, 230, 255))
        top = self.plant(d, rx, rtop, rh, 0.0, 0.0, t, crown=crown)
        if t > t_reg:
            k = ease((t - t_reg) / 0.6)
            d.text((rx, gy + 30 * u), "a little, every day", font=self.f_lab, fill=(60, 120, 90, int(255 * k)), anchor="ma")
        if t > t_ayah:                                         # soft golden glow around the grown tree
            k = ease((t - t_ayah) / 1.0) * (1 + (0.2 * math.sin((t - t_cta) * 4) if t > t_cta else 0))
            dg.ellipse([top[0] - 230 * u, top[1] - 230 * u, top[0] + 230 * u, top[1] + 160 * u], fill=int(85 * min(1, k)))
        im = self.finish(im, glow, col=(255, 226, 150), dust=self.motes, t=t)
        return im


LIGHT_SCENES["seed_daily"] = SeedDaily


# ------------------------------------------------------------------ the burial story (cut-away view)
from scenes_explainer import POSES as _POSES, pose_mix as _pose_mix  # noqa: E402


class GraveStory(LightStage):
    """The burial story as one continuous shot with a vertical camera.
    Above ground (big sky, the funeral) -> the camera sinks through the earth into the grave when he is alone
    -> rises back to a golden sky for the closing verse. Text always sits over light sky or light sand.
    Beats: carry, lower, soil, three, back, remain, steps, hear (camera down), angels, q1-q3, a1-a3, crier,
    door, breeze, widen, seats, both, other, dk, hell, narrow, hammer, calm, ayah (camera up).
    The angels are never drawn: their coming is shown only as light filling the grave."""
    ambience = "earth"
    text_y = 0.25
    text_zone = (0.165, 0.395)
    band = 1.0

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.DROP = 0.62 * h                                   # how far the camera travels down
        WH = int(h + self.DROP + 4)
        self.Gw = 0.80 * h                                     # ground line in world coordinates
        Gw = self.Gw
        sky = vgrad(w, int(Gw), [(0, (190, 214, 236)), (0.6, (222, 234, 242)), (1, (246, 238, 222))])
        soil = vgrad(w, WH - int(Gw), [(0, (228, 210, 178)), (0.30, (210, 182, 144)), (0.62, (166, 130, 96)), (1, (110, 84, 64))])
        world = np.concatenate([sky, soil], 0)
        self.world_sky = world
        gold = vgrad(w, int(Gw), [(0, (238, 212, 166)), (0.6, (250, 230, 194)), (1, (252, 240, 214))])
        grey = vgrad(w, int(Gw), [(0, (184, 188, 196)), (0.6, (210, 210, 212)), (1, (228, 222, 214))])
        self.sky_gold = np.concatenate([gold, soil], 0); self.sky_grey = np.concatenate([grey, soil], 0)
        over = Image.new("RGBA", (w, WH), (0, 0, 0, 0)); d = ImageDraw.Draw(over)
        for k in range(12):                                    # strata and stones in the earth
            y = Gw + (k + 1) * (WH - Gw) / 13 + rng.uniform(-12, 12) * u
            d.line([(x, y + 7 * u * math.sin(x / (100 * u) + k)) for x in range(0, w + 30, 30)], fill=(120, 92, 68, 50), width=max(1, int(3 * u)))
        for _ in range(140):
            x, y, r = rng.uniform(0, w), rng.uniform(Gw + 40 * u, WH), rng.uniform(4, 13) * u
            d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=(150, 124, 100, 110))
        # graveyard on the surface
        d.polygon([(x, Gw - 70 * u - 30 * u * math.sin(x / (w * 0.45) * math.tau + 0.6)) for x in range(0, w + 20, 20)] + [(w, Gw), (0, Gw)], fill=(206, 224, 200, 255))
        for x in [w * f for f in (0.05, 0.16, 0.27, 0.73, 0.84, 0.95)]:
            x += rng.uniform(-14, 14) * u; hh = rng.uniform(80, 120) * u; ww = rng.uniform(34, 46) * u
            d.rounded_rectangle([x - ww, Gw - hh, x + ww, Gw + 6 * u], radius=int(ww * 0.9), fill=(220, 218, 212, 255), outline=(168, 164, 156, 255), width=max(2, int(3 * u)))
        for tx in (w * 0.10, w * 0.90):
            d.line([(tx, Gw), (tx, Gw - 230 * u)], fill=(124, 104, 86, 255), width=int(16 * u))
            for _k in range(7):
                cx, cy = tx + rng.uniform(-90, 90) * u, Gw - 280 * u + rng.uniform(-60, 50) * u
                d.ellipse([cx - 80 * u, cy - 56 * u, cx + 80 * u, cy + 56 * u], fill=(150, 186, 140, 255))
        d.line([(0, Gw), (w, Gw)], fill=(176, 150, 116, 255), width=max(2, int(4 * u)))
        self.over = over
        self.cx = w / 2
        self.sw = w * 0.12
        self.f_lab = self.font("Lora.ttf", 34); self.f_q = self.font("Lora.ttf", 44)
        self.dust = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0.5, 1.5)) for _ in range(60)]
        self.leaves = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6.28)) for _ in range(26)]
        self.crowd = [(rng.uniform(-0.03, 0.03) * w, rng.uniform(0.92, 1.04)) for _ in range(7)]

    def e(self, t, name, dur=0.8, delay=0.0):
        return ease((t - self.bt(name) - delay) / dur)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        bt, cx = self.bt, self.cx
        down = self.e(t, "hear", 3.0) * (1 - self.e(t, "ayah", 3.0))
        oy = self.DROP * down
        G = self.Gw - oy                                       # ground line on screen
        bad = self.e(t, "other", 1.0) * (1 - self.e(t, "calm", 1.4))
        gold = self.e(t, "ayah", 2.0)
        y0 = int(oy)
        sl_ = slice(y0, y0 + h)
        world = self.world_sky[sl_]
        if bad > 0 or gold > 0:                               # blend only the visible slice
            world = world * (1 - bad * 0.6 - gold * 0.7) + self.sky_grey[sl_] * (bad * 0.6) + self.sky_gold[sl_] * (gold * 0.7)
        im = to_img(world); ov_ = self.over.crop((0, y0, w, y0 + h)); im.paste(ov_, (0, 0), ov_)
        d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        # chamber geometry (world offsets from the ground line)
        wide = self.e(t, "widen", 1.6) * (1 - self.e(t, "other", 0.8)) + self.e(t, "calm", 1.4) * self.e(t, "widen", 0.1)
        narrow = self.e(t, "narrow", 1.2) * (1 - self.e(t, "calm", 1.0))
        ct = G + lerp(0.38 * h, 0.30 * h, wide) + 50 * u * narrow
        cb = G + lerp(0.62 * h, 0.78 * h, wide) - 40 * u * narrow
        cw = lerp(0.34 * w, 0.47 * w, wide) * (1 - 0.45 * narrow)
        shake = 0.0
        th_ = bt("hammer") + 0.5
        if th_ < t < th_ + 0.8:
            shake = (1 - (t - th_) / 0.8) * 16 * u
        if bad > 0.5 and bt("narrow") < t < bt("narrow") + 1.6:
            shake = max(shake, 6 * u * (1 - (t - bt("narrow")) / 1.6))
        light = self.e(t, "angels", 0.9) * (1 - 0.6 * self.e(t, "a1", 2.0))
        warm = self.e(t, "crier", 1.2) * (1 - bad)
        base_in = np.array((84, 64, 50), np.float32)
        inside = base_in * (1 - warm) + np.array((206, 230, 196), np.float32) * warm
        inside = inside * (1 - bad) + np.array((70, 34, 28), np.float32) * bad
        inside = inside * (1 - light * 0.75) + np.array((255, 248, 226), np.float32) * light * 0.75
        filled = self.e(t, "soil", 2.4)
        # shaft
        d.rectangle([cx - self.sw, G, cx + self.sw, ct], fill=(70, 52, 40, 255))
        if filled > 0:
            d.rectangle([cx - self.sw, lerp(ct, G, filled), cx + self.sw, ct], fill=(176, 146, 112, 255))
        d.line([(cx - self.sw, G), (cx - self.sw, ct)], fill=(140, 112, 84, 255), width=max(1, int(2 * u)))
        d.line([(cx + self.sw, G), (cx + self.sw, ct)], fill=(140, 112, 84, 255), width=max(1, int(2 * u)))
        # chamber
        d.rounded_rectangle([cx - cw, ct, cx + cw, cb], radius=int(22 * u), fill=tuple(int(v) for v in inside) + (255,), outline=(96, 72, 54, 255), width=max(3, int(5 * u)))
        if light > 0.02:
            dg.rounded_rectangle([cx - cw - 30 * u, ct - 30 * u, cx + cw + 30 * u, cb + 30 * u], radius=int(30 * u), fill=int(210 * light))
            for k in range(5):
                x0 = cx - cw * 0.8 + k * cw * 0.4
                d.polygon([(x0 - 16 * u, ct), (x0 + 16 * u, ct), (x0 + 70 * u, cb), (x0 - 70 * u, cb)], fill=(255, 255, 255, int(70 * light)))
        floor_y = cb - 18 * u
        # Paradise: bed, door on the right wall, breeze
        door = self.e(t, "door", 1.2) * (1 - bad)
        if door > 0:
            d.rounded_rectangle([cx - 230 * u, floor_y - 18 * u, cx + 230 * u, floor_y + 8 * u], radius=int(12 * u), fill=(120, 186, 136, int(255 * door)))
            aw, ah = 130 * u, (cb - ct) * 0.62
            ax, ay = cx + cw - aw - 40 * u, ct + (cb - ct) * 0.14
            d.rounded_rectangle([ax - aw, ay, ax + aw, ay + ah], radius=int(aw), fill=(150, 214, 150, int(255 * door)), outline=(226, 190, 110, int(255 * door)), width=max(3, int(6 * u)))
            d.ellipse([ax - 40 * u, ay + 30 * u, ax + 40 * u, ay + 110 * u], fill=(255, 250, 220, int(255 * door)))
            for k in range(5):
                tx_ = ax - aw * 0.6 + k * aw * 0.3; ty_ = ay + ah * 0.86
                d.line([(tx_, ty_), (tx_, ty_ - 60 * u)], fill=(104, 150, 96, int(255 * door)), width=max(2, int(5 * u)))
                d.ellipse([tx_ - 30 * u, ty_ - 104 * u, tx_ + 30 * u, ty_ - 48 * u], fill=(110, 182, 112, int(255 * door)))
                d.ellipse([tx_ - 7 * u, ty_ - 84 * u, tx_ + 7 * u, ty_ - 70 * u], fill=(250, 170, 190, int(255 * door)))
            dg.rounded_rectangle([ax - aw * 1.5, ay - 40 * u, ax + aw * 1.5, ay + ah + 40 * u], radius=int(aw), fill=int(170 * door))
            br = self.e(t, "breeze", 1.0) * (1 - bad)
            if br > 0:
                for lx, ly, ph in self.leaves:
                    q = (lx + t * 0.13) % 1
                    x = ax - aw - q * cw * 1.4; y = ay + ah * (0.15 + 0.7 * ly) + 16 * u * math.sin(t * 2 + ph)
                    d.ellipse([x - 7 * u, y - 4 * u, x + 7 * u, y + 4 * u], fill=(120, 196, 120, int(220 * br * (1 - q))))
        # the seat in the Fire (left wall): shown, then replaced; and the Fire door for the disbeliever
        seat = self.e(t, "seats", 0.7) * (1 - self.e(t, "both", 1.0, 2.2)) * (1 - bad)
        hell = self.e(t, "hell", 1.0) * bad
        k = max(seat, hell)
        if k > 0:
            aw, ah = 120 * u, (cb - ct) * 0.62
            fx, fy = cx - cw + aw + 40 * u, ct + (cb - ct) * 0.14
            fl = 0.85 + 0.15 * math.sin(t * 11) * math.sin(t * 7)
            d.rounded_rectangle([fx - aw, fy, fx + aw, fy + ah], radius=int(aw), fill=(226, 92, 48, int(255 * k * fl)), outline=(110, 36, 28, int(255 * k)), width=max(3, int(6 * u)))
            for j in range(7):
                hx = fx - aw * 0.7 + j * aw * 0.23; hy = fy + ah * (0.35 + 0.3 * math.sin(t * 5 + j))
                d.polygon([(hx - 14 * u, fy + ah - 4 * u), (hx, hy), (hx + 14 * u, fy + ah - 4 * u)], fill=(255, 196, 90, int(230 * k)))
            if hell > 0:
                for j in range(12):
                    q = (t * 0.45 + j / 12) % 1
                    x = fx + aw + q * cw * 1.0; y = fy + ah * 0.5 + 34 * u * math.sin(t * 3 + j)
                    d.ellipse([x - 7 * u, y - 7 * u, x + 7 * u, y + 7 * u], fill=(240, 120, 60, int(170 * k * (1 - q))))
        # ---- the deceased
        sit = self.e(t, "angels", 1.0, 0.5)
        carry = ease((t - bt("carry")) / max(0.6, bt("lower") - bt("carry")))
        lowr = self.e(t, "lower", 2.2, 0.3)
        shroud = (252, 250, 244, 255)
        if t < bt("lower") + 0.3:                              # on the bier, carried in from the left
            bx = lerp(-0.30 * w, cx, carry); by = G - 250 * u
            for k_ in range(4):
                px = bx - 150 * u + k_ * 100 * u
                p = walk_pose(t * 4.2 + k_ * 0.9, 0.8 if carry < 1 else 0.0)
                p["ua"] = (96, 100); p["fa"] = (92, 96)
                self.fig(im, px, G, p, 0.95, col=(84, 78, 92))
            d.rectangle([bx - 190 * u, by + 26 * u, bx + 190 * u, by + 40 * u], fill=(146, 112, 82, 255))
            d.rounded_rectangle([bx - 160 * u, by - 26 * u, bx + 160 * u, by + 28 * u], radius=int(26 * u), fill=shroud, outline=(196, 190, 180, 255), width=2)
        elif sit <= 0:
            by = lerp(G - 30 * u, floor_y - 30 * u, lowr)
            d.rounded_rectangle([cx - 150 * u, by - 26 * u, cx + 150 * u, by + 26 * u], radius=int(26 * u), fill=shroud, outline=(196, 190, 180, 255), width=2)
        else:
            col = (64, 58, 72) if bad < 0.5 else (214, 204, 200)
            p = _pose_mix("sit_up", "sit_sad", bad)
            ox = cx - 30 * u + (math.sin(t * 40) * shake * 0.5 if shake else 0)
            self.fig(im, ox, floor_y, p, 1.05, col=col, alpha=min(1.0, sit * 1.3))
        # ---- the crowd: walks in, stands at the grave, family goes back, the last ones leave
        back = self.e(t, "back", 3.2)
        steps = self.e(t, "steps", 3.8)
        for k_, (dx, sc_) in enumerate(self.crowd):
            fam = k_ < 4
            side = -1 if k_ % 2 == 0 else 1
            stand_x = cx + side * (0.22 + 0.07 * (k_ // 2)) * w + dx
            x = lerp(-0.6 * w - k_ * 70 * u, stand_x, carry)
            leave = back if fam else steps
            x += leave * 1.4 * w
            if x > w + 100 * u:
                continue
            moving = carry < 1 or 0 < leave < 1
            p = walk_pose(t * 4.2 + k_ * 0.7, 0.85 if moving else 0.0)
            if not moving:
                p["head"] = -14
            self.fig(im, x, G, p, 0.82 * sc_, col=(96, 90, 104))
        # ---- the three that follow
        three = self.e(t, "three", 0.7)
        if three > 0 and t < bt("remain") + 3.2:
            chips = [("family", cx - 0.30 * w), ("wealth", cx), ("deeds", cx + 0.30 * w)]
            for lab, x in chips:
                y = G - 470 * u
                a = three
                if lab != "deeds":
                    x += back * 1.2 * w; a *= (1 - back)
                else:
                    rem = self.e(t, "remain", 2.2)
                    x = lerp(x, cx + 90 * u, rem); y = lerp(y, floor_y - 40 * u, rem)
                if a <= 0.02:
                    continue
                S_ = 1.5 * u
                if lab == "wealth":
                    for c in range(3):
                        d.ellipse([x - 30 * S_, y - 12 * S_ - c * 14 * S_, x + 30 * S_, y + 12 * S_ - c * 14 * S_], fill=(238, 190, 80, int(255 * a)), outline=(170, 120, 40, int(255 * a)), width=2)
                elif lab == "family":
                    for c in range(3):
                        hx = x - 34 * S_ + c * 34 * S_
                        d.ellipse([hx - 11 * S_, y - 42 * S_, hx + 11 * S_, y - 20 * S_], fill=(104, 98, 116, int(255 * a)))
                        d.rounded_rectangle([hx - 14 * S_, y - 16 * S_, hx + 14 * S_, y + 20 * S_], radius=int(9 * S_), fill=(104, 98, 116, int(255 * a)))
                else:
                    d.polygon([(x - 38 * S_, y - 20 * S_), (x, y - 11 * S_), (x + 38 * S_, y - 20 * S_), (x + 38 * S_, y + 20 * S_), (x, y + 29 * S_), (x - 38 * S_, y + 20 * S_)], fill=(255, 236, 176, int(255 * a)), outline=(196, 150, 60, int(255 * a)), width=2)
                    dg.ellipse([x - 90 * u, y - 80 * u, x + 90 * u, y + 80 * u], fill=int(210 * a))
                if t < bt("remain") + 0.8:
                    d.text((x, y + 50 * u), lab, font=self.f_lab, fill=(70, 60, 70, int(255 * a)), anchor="ma")
        if t > bt("remain") + 2.2:                             # his deeds stay with him as a small light
            k_ = (1 - bad) * (0.85 + 0.15 * math.sin(t * 2))
            x, y = cx + 90 * u, floor_y - 40 * u
            d.ellipse([x - 14 * u, y - 14 * u, x + 14 * u, y + 14 * u], fill=(255, 236, 176, int(255 * k_)))
            dg.ellipse([x - 70 * u, y - 70 * u, x + 70 * u, y + 70 * u], fill=int(190 * k_))
        # ---- questions (three rings) and answers
        for j in range(3):
            tq = bt(f"q{j + 1}")
            if t < tq:
                continue
            x = cx - 150 * u + j * 150 * u; y = ct + (cb - ct) * 0.17
            r = 30 * u
            ans = self.e(t, f"a{j + 1}", 0.5) * (1 - bad)
            dk = ease((t - bt("dk") - j * 0.5) / 0.4) * bad
            a = ease((t - tq) / 0.4) * (1 - self.e(t, "door", 0.8)) if bad < 0.5 else 1.0
            if bad > 0.5 and t < bt("dk"):
                a = ease((t - bt("other") - 1.5) / 0.6)
            if a <= 0.02:
                continue
            if ans > 0.5:
                col, sym, sc = (232, 182, 70), "✓", (255, 255, 255)
            elif dk > 0.5:
                col, sym, sc = (150, 60, 50), "×", (255, 255, 255)
            else:
                col, sym, sc = (255, 255, 255), "?", (255, 255, 255)
            filled_ = ans > 0.5 or dk > 0.5
            d.ellipse([x - r, y - r, x + r, y + r], outline=col + (int(255 * a),), width=max(3, int(5 * u)), fill=(col + (int(235 * a),)) if filled_ else (40, 32, 28, int(120 * a)))
            if sym == "?":
                d.text((x, y + 2 * u), sym, font=self.f_q, fill=sc + (int(255 * a),), anchor="mm")
            elif sym == "✓":                                    # drawn, not a font glyph (Lora has no tick)
                d.line([(x - 13 * u, y + 1 * u), (x - 4 * u, y + 11 * u), (x + 14 * u, y - 10 * u)], fill=sc + (int(255 * a),), width=max(3, int(6 * u)), joint="curve")
            else:
                for s_ in (1, -1):
                    d.line([(x - 11 * u, y - 11 * u * s_), (x + 11 * u, y + 11 * u * s_)], fill=sc + (int(255 * a),), width=max(3, int(6 * u)))
        if th_ < t < th_ + 0.5:                                # the moment of the blow: a flash, never shown
            k_ = 1 - (t - th_) / 0.5
            d.rounded_rectangle([cx - cw, ct, cx + cw, cb], radius=int(22 * u), fill=(255, 250, 240, int(235 * k_)))
        sl, nl = bt("soil") < t < bt("soil") + 2.6, bad > 0.5 and bt("narrow") < t < bt("narrow") + 2.0
        if sl or nl:                                          # earth falling
            for dx, dy, sp in self.dust:
                q = (dy + t * sp) % 1
                x = cx + dx * (self.sw if sl else cw)
                y = (G + q * (ct - G)) if sl else (ct + q * (cb - ct))
                d.ellipse([x - 4 * u, y - 4 * u, x + 4 * u, y + 4 * u], fill=(120, 92, 70, 220))
        im = self.finish(im, glow, col=(255, 238, 196), t=t)
        if shake:
            ox_, oy_ = int(math.sin(t * 61) * shake), int(math.cos(t * 47) * shake * 0.6)
            s_ = Image.new("RGB", im.size, (228, 210, 178)); s_.paste(im, (ox_, oy_)); im = s_
        return im


LIGHT_SCENES["grave_story"] = GraveStory


# ------------------------------------------------------------------ the three men in the cave (Bukhari 2272)
class CaveStory(LightStage):
    """Mountain cut-away. Rain outside, three men walk in, a boulder rolls down and seals the cave.
    Each man prays by a sincere deed: a memory bubble shows it, and the rock slides open a third.
    Beats: walk, enter, rock, dark, pray1, mem1, shift1, pray2, mem2, shift2, pray3, mem3, out, ayah."""
    ambience = "storm_to_birds"
    text_y = 0.25
    text_zone = (0.165, 0.395)
    band = 1.0

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.sky = vgrad(w, h, [(0, (188, 204, 222)), (0.45, (220, 226, 232)), (1, (226, 222, 214))])
        self.sky_sun = vgrad(w, h, [(0, (200, 224, 244)), (0.45, (240, 244, 240)), (1, (250, 240, 220))])
        self.gy = h * 0.88                                     # outside ground (right side)
        m = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
        def ridge_y(x):                                       # a peak at 0.42w, sloping down to the cave mouth at 0.80w
            f = x / w
            peak = h * 0.405 + (abs(f - 0.42) ** 1.35) * h * 0.30
            return peak + 10 * u * math.sin(x / (60 * u))
        top = [(x, ridge_y(x)) for x in range(0, int(w * 0.80) + 1, 16)]
        d.polygon([(0, h), (0, ridge_y(0))] + top + [(w * 0.80, h)], fill=(226, 206, 174, 255))
        d.line(top, fill=(204, 180, 146, 255), width=max(2, int(4 * u)))
        for k in range(10):                                    # rock strata
            y = h * 0.47 + k * 46 * u
            d.line([(x, y + 6 * u * math.sin(x / (80 * u) + k)) for x in range(0, int(w * 0.80), 24) if y > ridge_y(x) + 10 * u], fill=(200, 176, 142, 130), width=max(1, int(3 * u)))
        self.mtn = m
        self.cave = (w * 0.06, h * 0.62, w * 0.80, h * 0.87)    # interior; mouth opens on the right
        self.mouth_x = w * 0.80
        self.R = 0.115 * w                                     # boulder radius
        self.f_lab = self.font("Lora.ttf", 30)
        self.rain = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.6, 1.0)) for _ in range(120)]
        self.sheep = [(rng.uniform(-1, 1), rng.uniform(-1, 1), int(rng.integers(3))) for _ in range(18)]

    def e(self, t, name, dur=0.8, delay=0.0):
        return ease((t - self.bt(name) - delay) / dur)

    def bubble(self, im, cx, cy, r, a, kind, q, t):
        """A memory vignette in a cream circle. q = 0..1 progress through the memory."""
        u = self.u
        lay = Image.new("RGBA", (int(2 * r), int(2 * r)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
        d.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=(252, 246, 232, 255))
        g = 2 * r * 0.78                                       # ground inside the bubble
        ink = (70, 62, 74)
        if kind == 1:                                          # waiting with the bowl of milk till dawn
            sky = tuple(int(lerp(a_, b_, q)) for a_, b_ in zip((60, 70, 110), (250, 214, 160)))
            d.rectangle([0, 0, 2 * r, g], fill=sky + (255,))
            d.ellipse([r * 1.5 - 30 * u, g - 30 * u - q * 80 * u, r * 1.5 + 30 * u, g + 30 * u - q * 80 * u], fill=(255, 236, 180, int(255 * q)))
            for px in (r * 0.45, r * 0.85):                    # two elderly parents asleep
                d.rounded_rectangle([px - 50 * u, g - 26 * u, px + 50 * u, g], radius=int(12 * u), fill=(210, 200, 190, 255))
                d.ellipse([px - 64 * u, g - 30 * u, px - 34 * u, g - 4 * u], fill=ink + (255,))
            st = _POSES["stand"].copy(); st["ua"] = (300, 280); st["fa"] = (10, 10)
            draw_stick_ = __import__("scenes_explainer").draw_stick
            draw_stick_(d, r * 1.25, g, st, s=0.42 * u, col=ink + (255,))
            d.ellipse([r * 1.25 + 26 * u, g - 118 * u, r * 1.25 + 50 * u, g - 106 * u], fill=(255, 255, 250, 255), outline=ink + (255,), width=2)
        elif kind == 2:                                        # he leaves, and leaves the gold
            d.rectangle([0, 0, 2 * r, g], fill=(236, 224, 208, 255))
            d.rectangle([r * 0.25, g - 150 * u, r * 0.65, g], fill=(170, 130, 96, 255))
            for c in range(6):
                d.ellipse([r * 0.8 + c * 14 * u, g - 10 * u - (c % 2) * 8 * u, r * 0.8 + c * 14 * u + 22 * u, g - (c % 2) * 8 * u], fill=(240, 196, 80, 255), outline=(170, 120, 40, 255))
            x = lerp(r * 1.1, r * 1.85, q)
            __import__("scenes_explainer").draw_stick(d, x, g, walk_pose(t * 5, 0.9), s=0.42 * u, col=ink + (255,))
        else:                                                  # the wage grew into herds
            d.rectangle([0, 0, 2 * r, g], fill=(214, 234, 206, 255))
            n = int(1 + q * (len(self.sheep) - 1))
            for k, (sx, sy, sp) in enumerate(self.sheep[:n]):
                x = r + sx * r * 0.62; y = g - 10 * u + sy * 26 * u
                col = [(250, 248, 240), (150, 110, 80), (210, 170, 110)][sp]
                d.ellipse([x - 22 * u, y - 14 * u, x + 22 * u, y + 10 * u], fill=col + (255,), outline=(120, 100, 80, 255))
                d.ellipse([x + 16 * u, y - 18 * u, x + 30 * u, y - 4 * u], fill=col + (255,), outline=(120, 100, 80, 255))
            d.ellipse([r - 16 * u, g - 60 * u, r + 16 * u, g - 28 * u], fill=(240, 196, 80, int(255 * (1 - q))))
        d.rectangle([0, g, 2 * r, 2 * r], fill=(214, 196, 160, 255))
        mask = Image.new("L", lay.size, 0); ImageDraw.Draw(mask).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=int(255 * a))
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mask))
        ImageDraw.Draw(lay).ellipse([0, 0, 2 * r - 1, 2 * r - 1], outline=(226, 190, 110, int(255 * a)), width=max(3, int(6 * u)))
        im.paste(lay, (int(cx - r), int(cy - r)), lay)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        bt = self.bt
        sun = self.e(t, "out", 2.0)
        gold = self.e(t, "ayah", 2.0)
        arr = self.sky * (1 - sun) + self.sky_sun * sun
        if gold > 0:
            arr = arr * (1 - 0.4 * gold) + np.array((252, 232, 190), np.float32) * 0.4 * gold
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        d.rectangle([0, gy, w, h], fill=(196, 210, 180, 255))
        if sun > 0:
            d.ellipse([w * 0.86 - 50 * u, h * 0.47 - 50 * u, w * 0.86 + 50 * u, h * 0.47 + 50 * u], fill=(255, 246, 210, int(255 * sun)))
            dg.ellipse([w * 0.86 - 140 * u, h * 0.47 - 140 * u, w * 0.86 + 140 * u, h * 0.47 + 140 * u], fill=int(150 * sun))
        im.paste(self.mtn, (0, 0), self.mtn); d = ImageDraw.Draw(im, "RGBA")
        x0, y0, x1, y1 = self.cave
        open_ = self.e(t, "shift1", 1.0) / 3 + self.e(t, "shift2", 1.0) / 3 + self.e(t, "out", 1.4) / 3
        sealed = self.e(t, "rock", 0.9)
        dark = sealed * (1 - 0.75 * open_)
        inside = np.array((176, 150, 120)) * (1 - dark) + np.array((56, 44, 38)) * dark
        d.rounded_rectangle([x0, y0, x1 + 60 * u, y1], radius=int(70 * u), fill=tuple(int(v) for v in inside) + (255,))
        d.rectangle([x1 - 10 * u, y0 + 40 * u, x1 + 4 * u, y1], fill=tuple(int(v) for v in inside) + (255,))
        # light through the gap
        if sealed > 0 and open_ > 0:
            bw_ = (y1 - y0) * 0.9 * open_
            d.polygon([(x1, y1 - 20 * u - bw_), (x1, y1 - 20 * u), (x0 + (x1 - x0) * 0.25, y1), (x0 + (x1 - x0) * 0.15, y1 - bw_ * 0.4)], fill=(255, 244, 210, int(120 * min(1, open_ * 1.5))))
            dg.polygon([(x1, y1 - 20 * u - bw_), (x1, y1 - 20 * u), (x0 + (x1 - x0) * 0.3, y1), (x0 + (x1 - x0) * 0.2, y1 - bw_ * 0.4)], fill=int(170 * open_))
        # the boulder: rolls down the slope, seals the mouth, then slides out in thirds
        R = self.R
        fall = self.e(t, "rock", 0.9)
        bx = lerp(w * 0.62, self.mouth_x + R * 0.5, fall) + open_ * R * 2.6
        by = lerp(h * 0.36, y1 - R, fall ** 1.6)
        ang = (bx / R) * 0.8
        if t > bt("rock") - 0.1:
            d.ellipse([bx - R, by - R, bx + R, by + R], fill=(150, 136, 122, 255), outline=(110, 98, 88, 255), width=max(3, int(5 * u)))
            for k in range(4):
                a_ = ang + k * 1.6
                d.arc([bx - R * 0.6, by - R * 0.6, bx + R * 0.6, by + R * 0.6], math.degrees(a_), math.degrees(a_) + 40, fill=(126, 114, 102, 255), width=max(2, int(4 * u)))
        # rain outside (stops when they come out)
        rain = 1 - sun
        if rain > 0.02:
            for rx, ry, sp in self.rain:
                y = (ry + t * 900 * u * sp) % h; x = rx - (y / h) * 40 * u
                if x > w * 0.80 or y < h * 0.40:
                    d.line([(x, y), (x - 6 * u, y + 28 * u)], fill=(150, 170, 200, int(150 * rain)), width=max(1, int(2 * u)))
        # the three men: walk in from the right, sit; the praying one kneels with raised hands
        walk = ease((t - bt("walk")) / max(0.6, bt("rock") - bt("walk") - 0.4))
        outw = self.e(t, "out", 3.0, 0.8)
        seats = [x0 + (x1 - x0) * f for f in (0.30, 0.50, 0.70)]
        praying = [self.e(t, f"pray{k + 1}", 0.6) * (1 - self.e(t, f"shift{k + 1}" if k < 2 else "out", 0.6, 0.8)) for k in range(3)]
        col = (250, 240, 222) if dark > 0.5 else (70, 62, 74)
        for k in range(3):
            if walk < 1:
                x = lerp(w * 1.08 + k * 100 * u, seats[k], walk); g = gy if x > self.mouth_x else y1 - 6 * u
                self.fig(im, x, g, walk_pose(t * 5 + k, 0.9), 0.62, col=(70, 62, 74), flip=True)
                continue
            if outw > 0:
                x = lerp(seats[k], w * 0.86 + k * 60 * u, outw); g = gy if x > self.mouth_x else y1 - 6 * u
                self.fig(im, x, g, walk_pose(t * 5 + k, 0.9), 0.62, col=(70, 62, 74))
                continue
            pr = praying[k]
            p = _pose_mix("sit_up", "kneel", pr)
            if pr > 0.3:
                p["ua"] = (-60, -64); p["fa"] = (40, 46); p["head"] = 10
            self.fig(im, seats[k], y1 - 6 * u, p, 0.62, col=col)
            if pr > 0.3:
                dg.ellipse([seats[k] - 90 * u, y1 - 230 * u, seats[k] + 90 * u, y1], fill=int(110 * pr))
        # memory bubbles
        for k in range(3):
            tm = bt(f"mem{k + 1}"); te_ = bt(f"shift{k + 1}") if k < 2 else bt("out")
            if tm < t < te_ + 0.8:
                a = ease((t - tm) / 0.6) * (1 - ease((t - te_) / 0.7))
                q = min(1.0, (t - tm) / max(1.0, te_ - tm))
                self.bubble(im, x0 + (x1 - x0) * 0.46, y0 - 0.035 * h, 0.21 * w, a, k + 1, q, t)
                d = ImageDraw.Draw(im, "RGBA")
        return self.finish(im, glow, col=(255, 236, 190), t=t)


LIGHT_SCENES["cave_story"] = CaveStory


# ------------------------------------------------------------------ the last man to enter Paradise (Muslim 187)
class LastManStory(LightStage):
    """A long horizontal world; the camera follows one man from the distant glow of the Fire (left),
    past three trees raised one after another (each more beautiful), to the gate of Paradise (right).
    Nothing depicts Allah: His words are only spoken in the captions.
    Beats: walk, beyond, turn, tree1, near1, tree2, near2, tree3, near3, voices, admit, world, laugh, power, ayah."""
    ambience = "meadow"
    text_y = 0.25
    text_zone = (0.165, 0.40)
    band = 1.0

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.WW = int(w * 4.2)
        self.gy = h * 0.82
        sky = vgrad(self.WW, h, [(0, (196, 218, 238)), (0.55, (236, 240, 240)), (0.82, (246, 236, 216)), (1, (226, 214, 190))])
        xx = np.linspace(0, 1, self.WW, dtype=np.float32)[None, :, None]
        warm = np.clip(1 - xx * 4, 0, 1) ** 1.5                     # orange haze far left (the Fire, distant)
        sky = sky * (1 - 0.55 * warm) + np.array((250, 150, 90), np.float32) * 0.55 * warm
        goldx = np.clip((xx - 0.78) / 0.22, 0, 1)
        sky = sky * (1 - 0.35 * goldx) + np.array((255, 236, 180), np.float32) * 0.35 * goldx
        self.world = sky
        lay = Image.new("RGBA", (self.WW, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for k in range(2):                                     # rolling hills
            pts = [(x, self.gy - (90 - k * 40) * u - (34 - k * 10) * u * math.sin(x / (w * (0.5 + 0.2 * k)) * math.tau + k)) for x in range(0, self.WW + 40, 40)]
            d.polygon(pts + [(self.WW, self.gy), (0, self.gy)], fill=(206 - k * 12, 222 - k * 8, 196 - k * 10, 255))
        d.rectangle([0, self.gy, self.WW, h], fill=(222, 206, 172, 255))
        d.line([(0, self.gy), (self.WW, self.gy)], fill=(190, 168, 130, 255), width=max(2, int(4 * u)))
        for x in range(0, int(self.WW * 0.22), int(26 * u)):        # scorched ground near the Fire
            d.line([(x, self.gy + 6 * u), (x + 14 * u, self.gy + 20 * u)], fill=(150, 100, 70, 180), width=max(1, int(3 * u)))
        self.lay = lay
        self.trees = [(w * 1.35, 1.15, 0), (w * 2.25, 1.45, 1), (w * 3.15, 1.75, 2)]   # x, size, beauty level
        for k in range(260):                                  # flowers along the way, denser toward Paradise
            fx = rng.uniform(w * 0.9, self.WW)
            if rng.random() > (fx / self.WW) ** 1.5:
                continue
            fy = self.gy - rng.uniform(4, 40) * u
            c = [(250, 170, 190), (255, 214, 110), (250, 250, 240), (200, 170, 240)][int(rng.integers(4))]
            d.line([(fx, fy + 10 * u), (fx, fy)], fill=(120, 170, 110, 255), width=max(1, int(3 * u)))
            d.ellipse([fx - 7 * u, fy - 7 * u, fx + 7 * u, fy + 7 * u], fill=c + (255,))
        self.gate_x = w * 3.70
        self.f_lab = self.font("Lora.ttf", 32)
        self.leaves = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6.28)) for _ in range(30)]

    def e(self, t, name, dur=0.8, delay=0.0):
        return ease((t - self.bt(name) - delay) / dur)

    def man_x(self, t):
        """World x of the man along the path."""
        bt, w = self.bt, self.w
        keys = [(bt("walk"), w * 0.35), (bt("beyond"), w * 0.95), (bt("tree1") + 0.5, w * 0.95), (bt("near1") + 1.6, self.trees[0][0] - 60 * self.u),
                (bt("tree2") + 0.5, self.trees[0][0] - 60 * self.u), (bt("near2") + 1.6, self.trees[1][0] - 70 * self.u),
                (bt("tree3") + 0.5, self.trees[1][0] - 70 * self.u), (bt("near3") + 1.6, self.trees[2][0] - 80 * self.u),
                (bt("admit") + 0.2, self.trees[2][0] - 80 * self.u), (bt("ayah") + 2.5, self.gate_x)]
        keys = [k for k in keys if k[0] < 1e8]
        if t <= keys[0][0]:
            return keys[0][1], False
        for (ta, xa), (tb_, xb) in zip(keys, keys[1:]):
            if t < tb_:
                f = (t - ta) / max(1e-3, tb_ - ta)
                return lerp(xa, xb, ease(f)), abs(xb - xa) > 1 and 0.02 < f < 0.98
        return keys[-1][1], False

    def tree(self, d, dg, x, g, size, level, grow, t):
        u = self.u
        if grow <= 0:
            return
        s = size * grow
        trunk_h = 260 * u * s
        d.line([(x, g), (x, g - trunk_h)], fill=(130, 100, 76, 255), width=max(3, int(22 * u * s)))
        cols = [(150, 190, 140), (120, 186, 120), (110, 196, 126)][level]
        R = 150 * u * s
        for k in range(9):
            a = k / 9 * math.tau
            cx = x + math.cos(a) * R * 0.75; cy = g - trunk_h - R * 0.2 + math.sin(a) * R * 0.5
            d.ellipse([cx - R * 0.6, cy - R * 0.45, cx + R * 0.6, cy + R * 0.45], fill=cols + (255,))
        d.ellipse([x - R * 0.8, g - trunk_h - R * 0.75, x + R * 0.8, g - trunk_h + R * 0.35], fill=tuple(min(255, c + 16) for c in cols) + (255,))
        if level >= 1:                                         # fruit
            for k in range(10 + 8 * level):
                a = k * 2.4; rr = R * (0.3 + 0.55 * ((k * 37) % 10) / 10)
                fx = x + math.cos(a) * rr; fy = g - trunk_h - R * 0.2 + math.sin(a) * rr * 0.6
                c = (240, 120, 110) if level == 1 else ((255, 206, 90) if k % 2 else (250, 150, 180))
                d.ellipse([fx - 9 * u * s, fy - 9 * u * s, fx + 9 * u * s, fy + 9 * u * s], fill=c + (255,))
        if level == 2:
            dg.ellipse([x - R * 1.3, g - trunk_h - R * 1.1, x + R * 1.3, g - trunk_h + R * 0.7], fill=int(70 * grow))
        d.ellipse([x - 80 * u * s, g - 6 * u, x + 80 * u * s, g + 14 * u], fill=(150, 200, 230, 255))   # water at its foot

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        bt = self.bt
        mx, moving = self.man_x(t)
        cam = min(max(0, mx - w * 0.38), self.WW - w)
        c0 = int(cam)
        im = to_img(self.world[:, c0:c0 + w]); lay = self.lay.crop((c0, 0, c0 + w, h)); im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        g = self.gy
        # the distant Fire: only an orange glow and embers at the far left of the world
        fx = -cam
        if fx > -w * 0.6:
            for k in range(14):
                q = (t * 0.3 + k / 14) % 1
                ex = fx + (k * 47 % 400) * u; ey = g - q * 420 * u
                d.ellipse([ex - 6 * u, ey - 6 * u, ex + 6 * u, ey + 6 * u], fill=(250, 140, 70, int(200 * (1 - q))))
        # trees, raised one after another
        for k, (tx, size, lvl) in enumerate(self.trees):
            grow = self.e(t, f"tree{k + 1}", 1.6)
            self.tree(d, dg, tx - cam, g, size, lvl, grow, t)
        # the gate of Paradise: a tall arch of light
        gx = self.gate_x - cam
        if gx < w + 400 * u:
            gk = 0.6 + 0.4 * self.e(t, "voices", 1.2)
            op = self.e(t, "ayah", 2.0)
            aw, ah = 190 * u, 620 * u
            d.rounded_rectangle([gx - aw - 30 * u, g - ah - 30 * u, gx + aw + 30 * u, g], radius=int(aw + 30 * u), fill=(232, 204, 140, 255))
            d.rounded_rectangle([gx - aw, g - ah, gx + aw, g], radius=int(aw), fill=(255, 246, 216, int(255 * gk)))
            dg.rounded_rectangle([gx - aw * 1.6, g - ah * 1.1, gx + aw * 1.6, g + 40 * u], radius=int(aw * 1.4), fill=int(70 + 70 * gk * (0.5 + 0.5 * op)))
            if self.e(t, "voices", 1.0) > 0:                   # light motes drifting from the gate
                for lx, ly, ph in self.leaves:
                    q = (lx + t * 0.1) % 1
                    x = gx - q * 500 * u; y = g - ah * (0.2 + 0.7 * ly) + 20 * u * math.sin(t + ph)
                    d.ellipse([x - 4 * u, y - 4 * u, x + 4 * u, y + 4 * u], fill=(255, 236, 180, int(220 * (1 - q))))
        # the man
        sx = mx - cam
        stumble = 0.0
        if bt("walk") < t < bt("beyond"):
            ph = ((t - bt("walk")) / 1.6) % 1
            stumble = math.sin(math.pi * min(1, max(0, (ph - 0.55) / 0.3))) if ph > 0.55 else 0.0
            if 0.62 < ph < 0.72:                               # scorched once: an orange flash behind him
                dg.ellipse([sx - 260 * u, g - 380 * u, sx + 60 * u, g], fill=150)
        turn = self.e(t, "turn", 0.4) * (1 - self.e(t, "tree1", 0.4))
        in_shade = [(bt(f"near{k + 1}") + 1.6 < t < (bt(f"tree{k + 2}") if k < 2 else bt("admit"))) for k in range(3)]
        flip = turn > 0.5
        if any(in_shade) and t < bt("admit"):
            p = dict(_POSES["sit_up"]); p["head"] = 18
            self.fig(im, sx, g, p, 0.9, col=(70, 62, 74))
        elif stumble > 0:
            self.fig(im, sx, g, _pose_mix("stand", "kneel", stumble), 0.9, col=(70, 62, 74))
        else:
            p = walk_pose(t * 5, 0.9 if moving else 0.0)
            if not moving and t > bt("tree1"):
                p = dict(_POSES["look_up"])
            self.fig(im, sx, g, p, 0.9, col=(70, 62, 74), flip=flip)
        # "the world and its like": two soft globes that appear above the scene
        wk = self.e(t, "world", 0.8) * (1 - self.e(t, "power", 1.0, 1.0))
        if wk > 0:
            for j in range(2):
                cx_ = w * (0.34 + 0.32 * j); cy_ = h * 0.53
                k_ = ease((t - bt("world") - j * 0.7) / 0.6) * wk
                r = 120 * u
                d.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=(150, 200, 230, int(230 * k_)), outline=(226, 190, 110, int(255 * k_)), width=max(2, int(4 * u)))
                d.chord([cx_ - r * 0.7, cy_ - r * 0.5, cx_ + r * 0.2, cy_ + r * 0.6], 0, 360, fill=(140, 190, 130, int(230 * k_)))
            d.text((w * 0.50, h * 0.53 + 150 * u), "the world, and the like of it", font=self.f_lab, fill=(80, 70, 80, int(255 * wk)), anchor="ma")
        return self.finish(im, glow, col=(255, 236, 190), t=t)


LIGHT_SCENES["last_man_story"] = LastManStory


# ------------------------------------------------------------------ two blessings (Bukhari 6412)
from scenes_explainer import L_TORSO as _LT, L_UA as _LUA, L_FA as _LFA, _pt, POSES  # noqa: E402

_POSE_BENCH = {"hip": (0, 92), "torso": 92, "head": -26, "ua": (292, 300), "fa": (52, 60), "th": (6, 2), "sh": (272, 268)}
_POSE_OLD = {"hip": (0, 132), "torso": 66, "head": 8, "ua": (292, 262), "fa": (282, 270), "th": (262, 286), "sh": (266, 278)}
_POSE_DUA = {"hip": (0, 74), "torso": 92, "head": 16, "ua": (300, 296), "fa": (62, 70), "th": (268, 270), "sh": (182, 186)}


def _mix(pa, pb, k):
    return {key: (tuple(lerp(x, y, k) for x, y in zip(pa[key], pb[key])) if isinstance(pa[key], tuple) else lerp(pa[key], pb[key], k)) for key in pa}


class TwoBlessings(LightStage):
    """Bukhari 6412: two glowing blessings above a young man - a beating heart (health) and an hourglass
    (free time). He walks strong, then sinks into a bench scrolling his phone while a screen-time counter
    races and the sand pours; then he grows old and bent with a cane as the light turns to dusk; then
    he is young again on a prayer mat, and the blessings glow gold.
    Beats: hook, said, words, health, free, old, act, cta."""
    ambience = "meadow"
    text_y = 0.25
    text_zone = (0.165, 0.40)

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (222, 236, 246)), (0.5, (246, 244, 236)), (0.84, (250, 240, 222)), (1, (232, 216, 192))])
        self.dusk = vgrad(w, h, [(0, (232, 196, 190)), (0.5, (246, 214, 186)), (0.84, (236, 206, 176)), (1, (214, 186, 160))])
        self.gy = h * 0.865
        self.icx, self.icy = (w * 0.27, w * 0.73), h * 0.515
        self.f_lab = self.font("Lora.ttf", 40); self.f_cnt = self.font("Lora.ttf", 40)
        self.sand = [(rng.uniform(-1, 1), rng.uniform(0, 1)) for _ in range(40)]
        self.motes = Motes(rng, 26, (0, h * 0.42, w, h), color=(255, 248, 226), r=(1.0 * u, 2.2 * u), rise=5)
        self.rise = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0.6, 1.2)) for _ in range(22)]

    def hand(self, x, g, pose, s, idx=1):
        hx, hy = x + pose["hip"][0] * s, g - pose["hip"][1] * s
        nx, ny = _pt(hx, hy, pose["torso"], _LT * s)
        ex, ey = _pt(nx, ny + 8 * s, pose["ua"][idx], _LUA * s)
        return _pt(ex, ey, pose["fa"][idx], _LFA * s)

    def heart(self, d, dg, cx, cy, r, col, glow):
        pts = []
        for k in range(60):
            a = k / 60 * math.tau
            x = 16 * math.sin(a) ** 3
            y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            pts.append((cx + x * r / 16, cy - y * r / 16))
        d.polygon(pts, fill=col)
        if glow > 0:
            dg.ellipse([cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9], fill=int(glow))

    def hourglass(self, d, dg, cx, cy, r, level, flow, t, col, glow):
        """level: sand left in the top bulb (1 full .. 0 empty); flow: stream speed 0..2."""
        u = self.u; hw, hh = r * 0.62, r
        frame = (120, 92, 60, 255)
        d.rectangle([cx - hw - 12 * u, cy - hh - 12 * u, cx + hw + 12 * u, cy - hh], fill=frame)
        d.rectangle([cx - hw - 12 * u, cy + hh, cx + hw + 12 * u, cy + hh + 12 * u], fill=frame)
        glass = (236, 244, 250, 200)
        d.polygon([(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + 6 * u, cy), (cx - 6 * u, cy)], fill=glass)
        d.polygon([(cx - 6 * u, cy), (cx + 6 * u, cy), (cx + hw, cy + hh), (cx - hw, cy + hh)], fill=glass)
        if level > 0.01:                               # sand in the top bulb: a smaller triangle near the neck
            k = math.sqrt(level); ty = cy - hh * k
            d.polygon([(cx - hw * k, ty), (cx + hw * k, ty), (cx + 4 * u, cy - 3 * u), (cx - 4 * u, cy - 3 * u)], fill=col)
        fill_b = 1 - level                             # pile in the bottom bulb
        if fill_b > 0.01:
            k = math.sqrt(fill_b); top = cy + hh - hh * k * 0.95
            d.polygon([(cx - hw, cy + hh), (cx + hw, cy + hh), (cx + hw * (1 - k) * 0.4 + 4 * u, top), (cx - hw * (1 - k) * 0.4 - 4 * u, top)], fill=col)
        if level > 0.01 and flow > 0:                  # falling stream with grains
            d.line([(cx, cy - 2 * u), (cx, cy + hh * 0.9)], fill=col, width=max(2, int(3 * u * min(2, flow))))
            for gx, gp in self.sand[:int(10 * min(2, flow))]:
                q = (gp + t * 1.6 * flow) % 1
                d.ellipse([cx + gx * 3 * u - 2 * u, cy + q * hh * 0.9 - 2 * u, cx + gx * 3 * u + 2 * u, cy + q * hh * 0.9 + 2 * u], fill=col)
        d.polygon([(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + 6 * u, cy), (cx + hw, cy + hh), (cx - hw, cy + hh), (cx - 6 * u, cy)],
                  outline=(150, 130, 110, 255), width=max(2, int(3 * u)))
        if glow > 0:
            dg.ellipse([cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5], fill=int(glow))

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        T = {k: self.bt(k) for k in ("said", "words", "health", "free", "old", "act", "cta")}
        dusk = 0.7 * ease((t - T["old"]) / 1.2) * (1 - ease((t - T["act"]) / 0.9))
        arr = self.base * (1 - dusk) + self.dusk * dusk if dusk > 0 else self.base
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        for k in range(2):                                  # soft rolling hills
            pts = [(xx, gy - (90 - k * 36) * u - (24 - k * 8) * u * math.sin(xx / (w * (0.4 + 0.12 * k)) * math.tau + k * 2.1)) for xx in range(0, w + 20, 20)]
            c = (206 - k * 14, 224 - k * 8, 200 - k * 10)
            c = tuple(int(lerp(a, b, dusk)) for a, b in zip(c, (214 - k * 10, 190 - k * 8, 176 - k * 8)))
            d.polygon(pts + [(w, gy), (0, gy)], fill=c + (255,))
        d.rectangle([0, gy, w, h], fill=(226, 208, 178, 255))
        d.line([(0, gy), (w, gy)], fill=(198, 176, 140, 255), width=max(2, int(3 * u)))
        # ---- the two blessings
        appear = ease((t - 2.95) / 0.5)
        pop = 1 + 0.18 * math.sin(math.pi * min(1.0, max(0.0, (t - 3.2) / 0.5)))
        hx, ix = self.icx; iy = self.icy - 16 * u * (1 - appear)
        beat = 1 + 0.10 * max(0, math.sin(t * (7.5 if t > T["health"] and t < T["free"] else 4.2))) ** 6
        if T["free"] < t < T["act"]:
            beat = 1 + 0.04 * max(0, math.sin(t * 3.0)) ** 6
        heart_col = (214, 74, 86)
        fade_h = ease((t - T["old"]) / 1.0) * (1 - ease((t - T["act"]) / 0.8))
        heart_col = tuple(int(lerp(a, b, fade_h)) for a, b in zip(heart_col, (196, 160, 160)))
        g_gold = ease((t - T["words"]) / 0.8) * (1 - ease((t - T["health"]) / 1.2)) + ease((t - T["act"]) / 1.0)
        hglow = 60 + 70 * g_gold + (60 if T["health"] < t < T["free"] else 0)
        self.heart(d, dg, hx, iy, 108 * u * beat * appear * pop, heart_col + (int(255 * appear),), hglow * appear)
        # sand: full until "free", then pours fast; nearly empty in "old"; act refills a little with gold
        if t < T["free"]:
            level, flow = 1.0, (0.4 if t > T["words"] else 0.0)
        elif t < T["old"]:
            level, flow = 1.0 - 0.6 * ease((t - T["free"]) / 4.5), 2.0
        elif t < T["act"]:
            level, flow = 0.4 - 0.32 * ease((t - T["old"]) / 3.0), 0.8
        else:
            level, flow = 0.08, 0.3
        sand = (214, 168, 92) if t < T["act"] else tuple(int(lerp(a, b, ease((t - T["act"]) / 1.0))) for a, b in zip((214, 168, 92), (232, 180, 60)))
        iglow = 60 + 70 * g_gold + (60 if T["free"] < t < T["old"] else 0)
        self.hourglass(d, dg, ix, iy, 124 * u * max(0.05, appear) * pop, level, flow, t, sand + (int(255 * appear),), iglow * appear)
        if t > T["words"]:
            k = max(0.0, min(1.0, ease(min(1.0, (t - T["words"]) / 0.6))))
            d.text((hx, iy + 140 * u), "health", font=self.f_lab, fill=(150, 60, 70, int(255 * k)), anchor="ma")
            d.text((ix, iy + 150 * u), "free time", font=self.f_lab, fill=(130, 96, 40, int(255 * k)), anchor="ma")
        # ---- the man
        cx = w * 0.50; s = 1.6
        if t < T["health"]:
            pose = POSES["stand"]; x = cx; alpha = 0.0
        elif t < T["free"]:                                    # walks in strongly from the left
            q = ease((t - T["health"]) / 2.2)
            x = lerp(w * 0.10, cx, q); alpha = ease((t - T["health"]) / 0.5)
            pose = walk_pose((t - T["health"]) * 7.0, 1.0 - 0.8 * ease((t - T["health"] - 2.0) / 0.6))
        elif t < T["old"]:                                     # sinks onto a bench with his phone
            x = cx; alpha = 1; q = ease((t - T["free"]) / 0.7)
            pose = _mix(POSES["stand"], _POSE_BENCH, q)
        elif t < T["act"]:                                     # grows old and bent
            x = cx; alpha = 1; q = ease((t - T["old"]) / 1.4)
            pose = _mix(_POSE_BENCH, _POSE_OLD, q)
        else:                                                  # young again, on a prayer mat: sujood then sitting dua
            x = cx; alpha = 1
            ta = t - T["act"]
            if ta < 0.8:
                pose = _mix(_POSE_OLD, POSES["stand"], ease(ta / 0.8))
            else:
                pose = _mix(POSES["stand"], _POSE_DUA, ease((ta - 0.8) / 0.9))
        if T["free"] <= t < T["act"]:                          # bench
            bk = ease((t - T["free"]) / 0.5) * (1 - ease((t - T["old"] - 0.6) / 0.6))
            if bk > 0:
                bc = (150, 112, 78, int(255 * bk))
                d.rounded_rectangle([x - 130 * u, gy - 96 * s * u, x + 150 * u, gy - 80 * s * u], radius=int(6 * u), fill=bc)
                for lx_ in (x - 110 * u, x + 130 * u):
                    d.rectangle([lx_ - 7 * u, gy - 82 * s * u, lx_ + 7 * u, gy], fill=bc)
        if t > T["act"]:                                       # prayer mat
            mk = ease((t - T["act"]) / 0.6)
            d.rounded_rectangle([x - 190 * u, gy - 10 * u, x + 170 * u, gy + 14 * u], radius=int(8 * u), fill=(90, 140, 120, int(255 * mk)))
            d.line([(x - 170 * u, gy + 2 * u), (x + 150 * u, gy + 2 * u)], fill=(232, 200, 120, int(220 * mk)), width=max(2, int(3 * u)))
        self.fig(im, x, gy, pose, s, alpha=max(0.0, min(1.0, alpha)))
        d = ImageDraw.Draw(im, "RGBA")
        if T["free"] < t < T["old"] + 0.8:                     # phone: glow on the face, screen-time counter racing
            pk = ease((t - T["free"] - 0.4) / 0.5) * (1 - ease((t - T["old"] - 0.2) / 0.6))
            px, py = self.hand(x, gy, pose, s * u)
            d.rounded_rectangle([px - 13 * u, py - 30 * u, px + 13 * u, py + 10 * u], radius=int(5 * u), fill=(40, 44, 60, int(255 * pk)))
            d.rounded_rectangle([px - 9 * u, py - 26 * u, px + 9 * u, py + 6 * u], radius=int(3 * u), fill=(160, 210, 255, int(255 * pk)))
            dg.ellipse([px - 90 * u, py - 120 * u, px + 90 * u, py + 40 * u], fill=int(110 * pk))
            mins = 92 + int(max(0, t - T["free"] - 0.4) * 43)
            txt = f"screen time  {mins // 60}h {mins % 60:02d}m"
            d.rounded_rectangle([hx - 205 * u, h * 0.648, hx + 205 * u, h * 0.648 + 62 * u], radius=int(26 * u), fill=(255, 255, 255, int(200 * pk)))
            d.text((hx, h * 0.648 + 31 * u), txt, font=self.f_cnt, fill=(60, 70, 100, int(255 * pk)), anchor="mm")
        if T["old"] < t < T["act"]:                            # cane
            ck = ease((t - T["old"] - 0.6) / 0.6)
            px, py = self.hand(x, gy, pose, s * u, idx=0)
            d.line([(px, py), (px + 22 * u, gy)], fill=(120, 86, 56, int(255 * ck)), width=max(3, int(7 * u)))
            d.arc([px - 14 * u, py - 18 * u, px + 14 * u, py + 10 * u], 180, 360, fill=(120, 86, 56, int(255 * ck)), width=max(3, int(7 * u)))
        if t > T["act"] + 0.8:                                 # golden motes rising toward the blessings
            for rx, rp, sp in self.rise:
                q = (rp + (t - T["act"]) * 0.22 * sp) % 1
                mx = x + rx * 160 * u + 30 * u * math.sin(q * 6 + rp * 9)
                my = lerp(gy - 120 * u, iy + 60 * u, q)
                a = math.sin(q * math.pi)
                d.ellipse([mx - 4 * u, my - 4 * u, mx + 4 * u, my + 4 * u], fill=(236, 186, 80, int(230 * a)))
                dg.ellipse([mx - 14 * u, my - 14 * u, mx + 14 * u, my + 14 * u], fill=int(70 * a))
        return self.finish(im, glow, col=(255, 222, 160), blur=24, dust=self.motes, t=t)


LIGHT_SCENES["two_blessings"] = TwoBlessings
