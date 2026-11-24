"""
Explainer-format scenes: one continuous shot, a persistent visual device, stick-figure
characters whose actions follow the script. Lines drive the scene through "beat" names.

The renderer calls scene.set_timeline([(local_start, dur, line), ...]) before rendering;
local time = scene time (the renderer passes shot time + 3.0).
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scenes import Scene, vgrad, smooth, to_img, radial, blur_mask, Motes, add_glow, ridge

INK = (242, 236, 224)
GOLD = (255, 198, 92)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ stick figures
L_TORSO, L_UA, L_FA, L_TH, L_SH, R_HEAD = 112, 60, 58, 74, 72, 25

POSES = {   # angles in degrees, 90 = up, 0 = facing right; hip = (dx, height above ground)
    "stand":    dict(hip=(0, 146), torso=90, head=0, ua=(262, 278), fa=(268, 272), th=(266, 274), sh=(270, 270)),
    "look_up":  dict(hip=(0, 146), torso=94, head=28, ua=(232, 308), fa=(214, 326), th=(264, 276), sh=(270, 270)),
    "sit_sad":  dict(hip=(-10, 22), torso=62, head=-55, ua=(-20, -25), fa=(-60, -64), th=(38, 34), sh=(-75, -80)),
    "sit_up":   dict(hip=(-10, 22), torso=84, head=24, ua=(-30, -36), fa=(-66, -70), th=(38, 34), sh=(-75, -80)),
    "sujood":   dict(hip=(-40, 74), torso=-10, head=-50, ua=(262, 266), fa=(2, 6), th=(268, 272), sh=(182, 184)),
    "kneel":    dict(hip=(0, 74), torso=92, head=-34, ua=(-30, -24), fa=(120, 110), th=(268, 270), sh=(182, 186)),
}


def pose_mix(a, b, t):
    pa, pb = POSES[a], POSES[b]
    out = {}
    for k in pa:
        va, vb = pa[k], pb[k]
        out[k] = tuple(lerp(x, y, t) for x, y in zip(va, vb)) if isinstance(va, tuple) else lerp(va, vb, t)
    return out


def _pt(x, y, ang, L):
    r = math.radians(ang)
    return x + math.cos(r) * L, y - math.sin(r) * L


def draw_stick(d, x, ground, pose, s=1.0, col=INK + (255,), flip=False):
    """Draw a stick figure. pose: dict as in POSES (already mixed). flip mirrors left/right."""
    fx = -1 if flip else 1
    A = lambda a: (180 - a) if flip else a
    hx, hy = x + fx * pose["hip"][0] * s, ground - pose["hip"][1] * s
    nx, ny = _pt(hx, hy, A(pose["torso"]), L_TORSO * s)
    w = max(3, int(13 * s))
    for i in (0, 1):
        kx, ky = _pt(hx, hy, A(pose["th"][i]), L_TH * s)
        fx_, fy_ = _pt(kx, ky, A(pose["sh"][i]), L_SH * s)
        d.line([(hx, hy), (kx, ky), (fx_, fy_)], fill=col, width=w, joint="curve")
    d.line([(hx, hy), (nx, ny)], fill=col, width=w + 2)
    for i in (0, 1):
        ex, ey = _pt(nx, ny + 8 * s, A(pose["ua"][i]), L_UA * s)
        wx, wy = _pt(ex, ey, A(pose["fa"][i]), L_FA * s)
        d.line([(nx, ny + 8 * s), (ex, ey), (wx, wy)], fill=col, width=w, joint="curve")
    cx, cy = _pt(nx, ny, A(pose["torso"] + pose["head"]), (R_HEAD + 8) * s)
    r = R_HEAD * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    for p in [(hx, hy), (nx, ny)]:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)


def draw_mare(d, x, ground, s, lift, col, t):
    """Mare facing right; `lift` 0..1 raises the right foreleg over the foal."""
    bx, by = x, ground - 150 * s
    d.ellipse([bx - 130 * s, by - 46 * s, bx + 120 * s, by + 46 * s], fill=col)                    # body
    d.polygon([(bx + 80 * s, by - 30 * s), (bx + 112 * s, by + 4 * s), (bx + 168 * s, by - 96 * s), (bx + 140 * s, by - 118 * s)], fill=col)  # neck
    hx, hy = bx + 170 * s, by - 106 * s
    d.polygon([(hx - 30 * s, hy - 18 * s), (hx + 6 * s, hy - 26 * s), (hx + 58 * s, hy + 26 * s), (hx + 44 * s, hy + 40 * s), (hx - 16 * s, hy + 14 * s)], fill=col)  # head bowed toward foal
    d.polygon([(hx - 20 * s, hy - 20 * s), (hx - 8 * s, hy - 44 * s), (hx - 2 * s, hy - 20 * s)], fill=col)   # ear
    sw = 6 * s * math.sin(t * 1.3)
    d.line([(bx - 128 * s, by - 20 * s), (bx - 170 * s + sw, by + 30 * s), (bx - 160 * s + sw, by + 80 * s)], fill=col, width=int(14 * s), joint="curve")  # tail
    lw = int(16 * s)
    for lx in (-96, -64):                                                                             # hind legs
        d.line([(bx + lx * s, by + 30 * s), (bx + (lx - 6) * s, by + 90 * s), (bx + lx * s, ground)], fill=col, width=lw, joint="curve")
    d.line([(bx + 70 * s, by + 30 * s), (bx + 72 * s, by + 90 * s), (bx + 70 * s, ground)], fill=col, width=lw, joint="curve")   # standing foreleg
    kx, ky = _pt(bx + 96 * s, by + 30 * s, lerp(270, 330, lift), 64 * s)                              # lifted foreleg
    ex, ey = _pt(kx, ky, lerp(270, 200, lift), 60 * s)
    d.line([(bx + 96 * s, by + 30 * s), (kx, ky), (ex, ey)], fill=col, width=lw, joint="curve")


def draw_foal(d, x, ground, s, col):
    """Small foal lying down (legs tucked), head up."""
    bx, by = x, ground - 34 * s
    d.ellipse([bx - 70 * s, by - 30 * s, bx + 60 * s, by + 30 * s], fill=col)
    d.polygon([(bx + 40 * s, by - 16 * s), (bx + 62 * s, by + 4 * s), (bx + 86 * s, by - 60 * s), (bx + 70 * s, by - 72 * s)], fill=col)
    d.ellipse([bx + 62 * s, by - 92 * s, bx + 112 * s, by - 58 * s], fill=col)
    d.polygon([(bx + 72 * s, by - 86 * s), (bx + 76 * s, by - 108 * s), (bx + 84 * s, by - 86 * s)], fill=col)
    d.line([(bx - 40 * s, by + 24 * s), (bx + 30 * s, by + 30 * s)], fill=col, width=int(10 * s))


# ------------------------------------------------------------------ the scene
class MercyGrid(Scene):
    """100-cell mercy grid. Beats: hook, light_one, mother, mare, others, light_99, reflect, ayah, cta."""
    ambience = "night_room"
    bokeh_n = 0
    camera = "static"
    text_y = 0.255
    text_zone = (0.165, 0.365)      # above the grid
    band = 0.0

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.ground = int(h * 0.80)
        self.night = vgrad(w, h, [(0, (8, 10, 26)), (0.55, (20, 24, 54)), (0.80, (36, 38, 76)), (0.801, (16, 16, 30)), (1, (8, 8, 16))])
        self.dawn = vgrad(w, h, [(0, (24, 26, 64)), (0.45, (90, 70, 120)), (0.78, (250, 160, 100)), (0.80, (255, 196, 130)), (0.801, (40, 30, 40)), (1, (14, 10, 18))])
        n = 160
        self.stars = np.c_[rng.uniform(0, w, n), rng.uniform(0, h * 0.75, n), rng.uniform(0, 6.28, n), rng.uniform(1.0, 2.4, n) * u, rng.uniform(0.6, 1.6, n)]
        self.moon = (w * 0.13, h * 0.135, 46 * u)
        # grid geometry: 20 x 5
        self.cols, self.rows = 20, 5
        self.cell, self.gap = 38 * u, 8 * u
        gw = self.cols * (self.cell + self.gap) - self.gap
        self.gx0, self.gy0 = (w - gw) / 2, h * 0.375
        first = (self.rows - 1, self.cols // 2 - 1)            # the "one part": centre of the bottom row
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        cells.sort(key=lambda rc: math.hypot(rc[0] - first[0], (rc[1] - first[1]) * 0.9))
        self.order = cells                                    # lighting order rippling out from the first cell
        self.rank = {rc: k for k, rc in enumerate(cells)}
        self.font = ImageFont.truetype(_font("Lora.ttf"), int(40 * u))
        self.font_small = ImageFont.truetype(_font("Lora-Italic.ttf"), int(30 * u))
        self.beats = {}

    def set_timeline(self, items):
        for st, du, ln in items:
            b = ln.get("beat")
            if b and b not in self.beats:
                self.beats[b] = (st, du)

    def bt(self, name, default=1e9):
        return self.beats.get(name, (default, 0))[0]

    def cell_box(self, r, c):
        x = self.gx0 + c * (self.cell + self.gap); y = self.gy0 + r * (self.cell + self.gap)
        return x, y, x + self.cell, y + self.cell

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        g = self.ground
        warm = ease((t - self.bt("light_99") - 0.6) / 2.4)
        arr = self.night * (1 - warm) + self.dawn * warm
        one_on = ease((t - self.bt("light_one") - 0.3) / 0.5)
        if one_on > 0:   # pool of light where the beam lands
            arr += (radial(w, h, w / 2, g, 260 * u) * 70 * one_on * (1 - 0.5 * warm))[..., None] * np.array([1, 0.8, 0.5], np.float32)
        im = to_img(arr)
        d = ImageDraw.Draw(im, "RGBA")
        for x, y, ph, r, f in self.stars:
            a = int(255 * (0.25 + 0.6 * (0.5 + 0.5 * math.sin(t * f + ph))) * (1 - 0.7 * warm))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 255, a))
        mx, my, mr = self.moon
        d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 244, 214, int(255 * (1 - warm))))
        bg = tuple(int(v) for v in arr[int(my), int(mx + mr)])
        d.ellipse([mx - mr + 20 * u, my - mr - 10 * u, mx + mr + 20 * u, my + mr - 10 * u], fill=bg + (255,))

        # ---- grid
        t_in = self.bt("hook", 0.0) + 0.25
        lit_one_t = self.bt("light_one") + 0.3
        pulse_t = self.bt("others")
        cas_t = self.bt("light_99") + 0.4
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        n_lit = 0
        for (r, c), k in self.rank.items():
            x0, y0, x1, y1 = self.cell_box(r, c)
            appear = ease((t - t_in - k * 0.010) / 0.18)
            if appear <= 0:
                continue
            if k == 0:
                lit = ease((t - lit_one_t) / 0.35)
            else:
                lit = ease((t - cas_t - (k - 1) * 0.020) / 0.25)
            if lit > 0.5:
                n_lit += 1
            pul = 0.0
            if k > 0 and t > pulse_t and lit < 0.01:
                pul = 0.5 + 0.5 * math.sin((t - pulse_t) * 5 - k * 0.15)
            dim_fill = (34 + 30 * pul, 40 + 30 * pul, 78 + 40 * pul)
            fill = tuple(int(lerp(dv, gv, lit)) for dv, gv in zip(dim_fill, GOLD))
            outline = tuple(int(lerp(a_, b_, lit)) for a_, b_ in zip((96, 108, 160), (255, 232, 170)))
            sc = 0.6 + 0.4 * appear + 0.12 * math.sin(math.pi * min(1, lit * 1.0)) * (lit < 1)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            hw = self.cell / 2 * sc
            d.rounded_rectangle([cx - hw, cy - hw, cx + hw, cy + hw], radius=int(8 * u), fill=fill + (int(255 * appear),), outline=outline + (int(255 * appear),), width=max(2, int(2 * u)))
            if lit > 0:
                dg.rounded_rectangle([cx - hw, cy - hw, cx + hw, cy + hw], radius=int(8 * u), fill=int(200 * lit))
        if one_on > 0:   # beam from the first cell down to the earth
            x0, y0, x1, y1 = self.cell_box(*self.order[0])
            bx = (x0 + x1) / 2
            beam_len = (g - y1) * ease((t - lit_one_t - 0.15) / 0.6)
            fade = 1 - 0.6 * warm
            yb = y1 + 62 * u
            beam_len = max(0.0, beam_len - 62 * u)
            dg.polygon([(bx - 5 * u, yb), (bx + 5 * u, yb), (bx + 40 * u, yb + beam_len), (bx - 40 * u, yb + beam_len)], fill=int(90 * fade))
            d.polygon([(bx - 3 * u, yb), (bx + 3 * u, yb), (bx + 16 * u, yb + beam_len), (bx - 16 * u, yb + beam_len)], fill=GOLD + (int(120 * fade),))
        gl = glow.filter(ImageFilter.GaussianBlur(14 * u))
        glow_rgb = Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in GOLD])
        from PIL import ImageChops
        im = ImageChops.screen(im, glow_rgb)
        d = ImageDraw.Draw(im, "RGBA")
        # counter under the grid
        if t > lit_one_t:
            gy1 = self.gy0 + self.rows * (self.cell + self.gap)
            n_show = max(1, n_lit)
            txt = f"{n_show} / 100"
            a = int(255 * ease((t - lit_one_t) / 0.4))
            d.text((w / 2, gy1 + 34 * u), txt, font=self.font, fill=(GOLD if n_show > 1 else (236, 230, 214)) + (a,), anchor="mm")

        # ---- characters
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(ch)
        cx = w / 2
        t_mother, t_mare, t_others = self.bt("mother"), self.bt("mare"), self.bt("others")
        t_99, t_ayah = self.bt("light_99"), self.bt("ayah")
        a_hero = 1 - ease((t - t_mother) / 0.35) + ease((t - t_others + 0.2) / 0.4)
        a_mother = ease((t - t_mother) / 0.35) * (1 - ease((t - t_mare) / 0.35))
        a_mare = ease((t - t_mare) / 0.35) * (1 - ease((t - t_others + 0.2) / 0.35))
        S = 1.25 * u
        if a_hero > 0.01:
            if t < t_99:
                p = pose_mix("sit_sad", "sit_up", ease((t - t_others - 0.3) / 0.8))
            elif t < t_ayah:
                k = ease((t - t_99 - 0.3) / 1.2)
                p = pose_mix("sit_up", "stand", min(1, k * 1.6)) if k < 0.6 else pose_mix("stand", "look_up", ease((k - 0.6) / 0.4))
            else:
                p = pose_mix("look_up", "sujood", ease((t - t_ayah) / 1.1))
            breath = 1 + 0.01 * math.sin(t * 1.8)
            draw_stick(dc, cx - 20 * u, g, p, S * breath, INK + (int(255 * min(1, a_hero)),))
        if a_mother > 0.01:
            rock = 3 * math.sin(t * 1.6)
            pm = dict(POSES["kneel"]); pm = {k_: v for k_, v in pm.items()}; pm["torso"] = 96 + rock
            col = INK + (int(255 * a_mother),)
            draw_stick(dc, cx - 50 * u, g, pm, S, col)
            pc = dict(POSES["stand"]); pc["ua"] = (34, 26); pc["fa"] = (70, 60); pc["head"] = 12; pc["torso"] = 96 - rock * 0.5
            draw_stick(dc, cx + 52 * u, g, pc, S * 0.6, col, flip=True)
        if a_mare > 0.01:
            col = (226, 206, 176, int(255 * a_mare))
            lift = ease((t - t_mare - 0.6) / 0.9) * (0.9 + 0.1 * math.sin(t * 2))
            draw_mare(dc, cx - 120 * u, g, 1.05 * u, lift, col, t)
            draw_foal(dc, cx + 70 * u, g, 0.95 * u, (240, 224, 196, int(255 * a_mare)))
        # warm rim glow on characters once the light is down
        if one_on > 0:
            rim = ch.getchannel("A").filter(ImageFilter.GaussianBlur(10 * u)).point(lambda v: int(v * 0.6 * one_on))
            gl2 = Image.new("RGBA", (w, h), GOLD + (0,)); gl2.putalpha(rim)
            im.paste(gl2, (0, 0), gl2)
        im.paste(ch, (0, 0), ch)
        # ground line
        d = ImageDraw.Draw(im, "RGBA")
        d.line([(0, g), (w, g)], fill=(255, 255, 255, 40), width=max(1, int(2 * u)))
        return im


class FourQuestions(Scene):
    """Day of Judgment: feet held in place until 4 questions are asked.
    Beats: hook, q1, q2, q3, q4, reflect, ayah, cta."""
    ambience = "heat"
    bokeh_n = 0
    camera = "static"
    text_y = 0.235
    text_zone = (0.165, 0.335)      # above the question cards
    band = 0.0
    ROWS = [("LIFE", "how did you spend it?"), ("KNOWLEDGE", "what did you do with it?"),
            ("WEALTH", "where did it come from, where did it go?"), ("BODY", "how did you use it?")]

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.ground = g = int(h * 0.80)
        a = vgrad(w, h, [(0, (40, 12, 18)), (0.40, (110, 34, 30)), (0.70, (196, 88, 48)), (0.80, (236, 140, 70)), (0.801, (34, 16, 16)), (1, (14, 8, 8))])
        self.sun = (w * 0.80, h * 0.075, 118 * u)
        a = a + (radial(w, h, self.sun[0], self.sun[1], 520 * u) * 80)[..., None] * np.array([1, 0.75, 0.45], np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        disc = np.clip(self.sun[2] - np.hypot(xx - self.sun[0], yy - self.sun[1]) + 1, 0, 1)
        a = a * (1 - disc[..., None]) + np.array([255, 236, 196], np.float32) * disc[..., None]
        bg = to_img(a); d = ImageDraw.Draw(bg, "RGBA")
        # endless crowd standing on the plain (behind the hero)
        for r in range(5):
            p = r / 4
            y = g - 70 * u + p * 64 * u
            s = (0.48 + 0.30 * p) * u
            x = -rng.uniform(0, 30)
            col = (int(70 - 30 * p), int(24 - 8 * p), int(26 - 8 * p), 255)
            while x < w + 30:
                pz = dict(POSES["stand"]); pz["head"] = rng.uniform(-30, 10)
                draw_stick(d, x, y, pz, s, col)
                x += rng.uniform(70, 120) * s / u
        self.bg = bg
        self.f_lab = ImageFont.truetype(_font("Lora.ttf"), int(36 * u))
        try:
            self.f_lab.set_variation_by_axes([700])
        except Exception:
            pass
        self.f_txt = ImageFont.truetype(_font("Lora-Italic.ttf"), int(31 * u))
        self.f_num = ImageFont.truetype(_font("Lora.ttf"), int(30 * u))
        self.px0, self.px1 = 90 * u, w - 90 * u
        self.py0, self.rh, self.rg = h * 0.345, 84 * u, 16 * u
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def icon(self, d, k, cx, cy, s, col, t):
        if k == 0:      # hourglass
            d.polygon([(cx - 16 * s, cy - 22 * s), (cx + 16 * s, cy - 22 * s), (cx, cy)], fill=col)
            d.polygon([(cx - 16 * s, cy + 22 * s), (cx + 16 * s, cy + 22 * s), (cx, cy)], outline=col, width=max(2, int(3 * s)))
            d.line([(cx - 20 * s, cy - 24 * s), (cx + 20 * s, cy - 24 * s)], fill=col, width=max(2, int(4 * s)))
            d.line([(cx - 20 * s, cy + 24 * s), (cx + 20 * s, cy + 24 * s)], fill=col, width=max(2, int(4 * s)))
        elif k == 1:    # open book
            d.polygon([(cx, cy - 12 * s), (cx - 26 * s, cy - 20 * s), (cx - 26 * s, cy + 16 * s), (cx, cy + 22 * s)], fill=col)
            d.polygon([(cx, cy - 12 * s), (cx + 26 * s, cy - 20 * s), (cx + 26 * s, cy + 16 * s), (cx, cy + 22 * s)], fill=col)
            d.line([(cx, cy - 12 * s), (cx, cy + 22 * s)], fill=(40, 20, 20, 255), width=max(1, int(2 * s)))
        elif k == 2:    # coin
            d.ellipse([cx - 22 * s, cy - 22 * s, cx + 22 * s, cy + 22 * s], fill=col)
            d.ellipse([cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s], outline=(120, 70, 20, 255), width=max(2, int(3 * s)))
        else:           # body
            draw_stick(d, cx, cy + 30 * s, POSES["stand"], 0.27 * s, col)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        g = self.ground
        im = self.bg.copy()
        d = ImageDraw.Draw(im, "RGBA")
        # heat shimmer on the sun glow
        sx, sy, sr = self.sun
        for k in range(3):
            rr = sr + (14 + 10 * k) * u + 6 * u * math.sin(t * 2 + k)
            d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], outline=(255, 220, 170, 40 - 10 * k), width=int(6 * u))
        t_hook = self.bt("hook", 0.0)
        qs = [self.bt(f"q{i + 1}") for i in range(4)]
        t_ref, t_ayah, t_cta = self.bt("reflect"), self.bt("ayah"), self.bt("cta")
        # --- question cards
        for k, (lab, txt) in enumerate(self.ROWS):
            ap = ease((t - qs[k]) / 0.35)
            if ap <= 0:
                continue
            y0 = self.py0 + k * (self.rh + self.rg)
            x_off = (1 - ap) * -60 * u
            active = qs[k] <= t < (qs[k + 1] if k < 3 else t_ref)
            focus = 1.0 if active else 0.55
            box = [self.px0 + x_off, y0, self.px1 + x_off, y0 + self.rh]
            d.rounded_rectangle(box, radius=int(18 * u), fill=(30, 10, 12, int(170 * ap)),
                                outline=(GOLD if active else (200, 150, 120)) + (int(255 * ap * focus),), width=max(2, int((3 if active else 2) * u)))
            cy = y0 + self.rh / 2
            d.text((box[0] + 32 * u, cy), str(k + 1), font=self.f_num, fill=(255, 220, 170, int(200 * ap)), anchor="lm")
            self.icon(d, k, box[0] + 100 * u, cy, 1.0 * u, GOLD + (int(255 * ap * (0.6 + 0.4 * focus)),), t)
            d.text((box[0] + 150 * u, cy - 15 * u), lab, font=self.f_lab, fill=GOLD + (int(255 * ap),), anchor="lm")
            d.text((box[0] + 150 * u, cy + 21 * u), txt, font=self.f_txt, fill=(245, 236, 224, int(235 * ap * focus + 20)), anchor="lm")
            if t > t_ref:   # empty answer boxes that pulse: unanswered
                pa = ease((t - t_ref - k * 0.15) / 0.3)
                pul = 0.6 + 0.4 * math.sin((t - t_ref) * 4 + k)
                bx = box[2] - 62 * u
                d.rounded_rectangle([bx, cy - 20 * u, bx + 40 * u, cy + 20 * u], radius=int(6 * u),
                                    outline=(255, 236, 200, int(255 * pa * pul)), width=max(2, int(3 * u)))
                d.text((bx + 20 * u, cy), "?", font=self.f_num, fill=(255, 236, 200, int(255 * pa * pul)), anchor="mm")
        # --- hero, feet held in place
        cx = w / 2
        lock = ease((t - t_hook - 1.2) / 0.6)
        for k in range(3):
            ph = ((t - t_hook) * 0.7 + k / 3) % 1.0
            if lock > 0:
                rr = (40 + 90 * ph) * u
                d.ellipse([cx - rr, g - rr * 0.22, cx + rr, g + rr * 0.22], outline=GOLD + (int(150 * (1 - ph) * lock),), width=max(2, int(3 * u)))
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(ch)
        if t < t_ayah:
            look = ease((t - t_hook - 0.5) / 0.8)
            p = pose_mix("stand", "look_up", 0.35 * look)
            p = dict(p); p["head"] = lerp(p["head"], -10, ease((t - t_ref) / 0.8))
        else:
            p = dict(POSES["stand"]); p["head"] = -45; p["ua"] = (250, 290); p["fa"] = (262, 278)
        # slight tremble while being questioned
        tr = 1.5 * u * math.sin(t * 23) * (1 if any(q <= t < q + 1.5 for q in qs) else 0)
        draw_stick(dc, cx + tr, g, p, 1.25 * u, INK + (255,))
        rim = ch.getchannel("A").filter(ImageFilter.GaussianBlur(10 * u)).point(lambda v: int(v * 0.5))
        gl = Image.new("RGBA", (w, h), (255, 170, 90, 0)); gl.putalpha(rim)
        im.paste(gl, (0, 0), gl); im.paste(ch, (0, 0), ch)
        d = ImageDraw.Draw(im, "RGBA")
        for fx in (-14, 14):                       # glowing anchors under each foot
            d.ellipse([cx + fx * u - 18 * u, g - 6 * u, cx + fx * u + 18 * u, g + 6 * u], fill=GOLD + (int(220 * lock),))
        d.line([(0, g), (w, g)], fill=(255, 220, 180, 50), width=max(1, int(2 * u)))
        return im


class ThreeAfterDeath(Scene):
    """Deeds counter that stops at death, then keeps rising from the three things that continue.
    Beats: life, death, except, e1, e2, e3, reflect, ayah, cta."""
    ambience = "night_room"
    bokeh_n = 0
    camera = "static"
    text_y = 0.235
    text_zone = (0.165, 0.335)
    band = 0.0
    ITEMS = [("1", "ONGOING CHARITY"), ("2", "BENEFICIAL KNOWLEDGE"), ("3", "A RIGHTEOUS CHILD")]

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.ground = int(h * 0.80)
        a = vgrad(w, h, [(0, (8, 10, 26)), (0.55, (20, 24, 52)), (0.80, (34, 34, 66)), (0.801, (14, 14, 26)), (1, (8, 8, 14))])
        self.bg = to_img(a + (radial(w, h, w / 2, self.ground, 420 * u) * 18)[..., None])
        n = 150
        self.stars = np.c_[rng.uniform(0, w, n), rng.uniform(0, h * 0.75, n), rng.uniform(0, 6.28, n), rng.uniform(1.0, 2.2, n) * u, rng.uniform(0.6, 1.6, n)]
        self.f_num = ImageFont.truetype(_font("Lora.ttf"), int(104 * u))
        self.f_cap = ImageFont.truetype(_font("Lora.ttf"), int(28 * u))
        self.f_item = ImageFont.truetype(_font("Lora.ttf"), int(26 * u))
        for f_ in (self.f_num, self.f_cap, self.f_item):
            try:
                f_.set_variation_by_axes([700])
            except Exception:
                pass
        self.pos = [(w * 0.18, h * 0.70), (w * 0.50, h * 0.555), (w * 0.82, h * 0.70)]
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def count(self, t):
        t_life, t_death = self.bt("life", 0.0), self.bt("death")
        e = [self.bt(k) for k in ("e1", "e2", "e3")]
        stop_t = t_death + 0.8
        n = 120 * max(0.0, min(t, stop_t) - t_life) ** 1.25
        for k, te in enumerate(e):
            if t > te + 0.6:
                n += (2.5 + 2.0 * k) * (t - te - 0.6) ** 1.1
        return int(n)

    def icon(self, d, k, cx, cy, s, col, t):
        if k == 0:      # a well: water that keeps giving
            d.rounded_rectangle([cx - 46 * s, cy - 10 * s, cx + 46 * s, cy + 40 * s], radius=int(8 * s), fill=col)
            d.line([(cx - 40 * s, cy - 10 * s), (cx - 40 * s, cy - 70 * s)], fill=col, width=int(7 * s))
            d.line([(cx + 40 * s, cy - 10 * s), (cx + 40 * s, cy - 70 * s)], fill=col, width=int(7 * s))
            d.polygon([(cx - 60 * s, cy - 66 * s), (cx + 60 * s, cy - 66 * s), (cx, cy - 104 * s)], fill=col)
            d.line([(cx, cy - 66 * s), (cx, cy - 30 * s)], fill=col, width=int(3 * s))
            d.rectangle([cx - 10 * s, cy - 32 * s, cx + 10 * s, cy - 16 * s], fill=col)
            for j in range(3):
                ph = ((t * 0.8 + j / 3) % 1.0)
                d.ellipse([cx - 4 * s, cy - 14 * s + ph * 26 * s - 4 * s, cx + 4 * s, cy - 14 * s + ph * 26 * s + 4 * s], fill=(150, 210, 255, int(255 * (1 - ph))))
        elif k == 1:    # open book
            d.polygon([(cx, cy - 26 * s), (cx - 70 * s, cy - 42 * s), (cx - 70 * s, cy + 30 * s), (cx, cy + 44 * s)], fill=col)
            d.polygon([(cx, cy - 26 * s), (cx + 70 * s, cy - 42 * s), (cx + 70 * s, cy + 30 * s), (cx, cy + 44 * s)], fill=col)
            for j in range(4):
                yy = cy - 18 * s + j * 14 * s
                d.line([(cx - 58 * s, yy - 6 * s), (cx - 10 * s, yy + 4 * s)], fill=(60, 40, 20, 200), width=max(1, int(3 * s)))
                d.line([(cx + 10 * s, yy + 4 * s), (cx + 58 * s, yy - 6 * s)], fill=(60, 40, 20, 200), width=max(1, int(3 * s)))
        else:           # a child making dua
            p = dict(POSES["kneel"]); p["head"] = 20; p["ua"] = (60, 120); p["fa"] = (95, 85)
            draw_stick(d, cx, cy + 96 * s, p, 0.62 * s, col, flip=True)

    def frame(self, t):
        from PIL import ImageChops
        w, h, u = self.w, self.h, self.u
        g = self.ground
        im = self.bg.copy(); d = ImageDraw.Draw(im, "RGBA")
        for x, y, ph, r, f in self.stars:
            a = int(255 * (0.25 + 0.55 * (0.5 + 0.5 * math.sin(t * f + ph))))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 255, a))
        t_life, t_death = self.bt("life", 0.0), self.bt("death")
        e = [self.bt(k) for k in ("e1", "e2", "e3")]
        t_ref, t_cta = self.bt("reflect"), self.bt("cta")
        dead = ease((t - t_death - 0.4) / 0.8)
        resumed = any(t > te + 0.6 for te in e)
        n = self.count(t)
        cy0 = h * 0.37
        d.text((w / 2, cy0), "D E E D S   R E C O R D E D", font=self.f_cap, fill=(200, 210, 230, 210), anchor="mm")
        col = GOLD if resumed else tuple(int(lerp(a_, b_, dead)) for a_, b_ in zip((246, 240, 228), (110, 112, 130)))
        d.text((w / 2, cy0 + 80 * u), f"{n:,}", font=self.f_num, fill=col + (255,), anchor="mm", stroke_width=2, stroke_fill=(10, 10, 20, 200))
        if dead > 0 and not resumed:
            d.text((w / 2, cy0 + 150 * u), "S T O P P E D", font=self.f_cap, fill=(230, 120, 110, int(230 * dead)), anchor="mm")
        if resumed:
            d.text((w / 2, cy0 + 150 * u), "S T I L L   R I S I N G", font=self.f_cap, fill=GOLD + (230,), anchor="mm")
        cx = w / 2
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(ch, "RGBA")
        if dead < 1:
            ph = (t - t_life) * 5.0
            p = dict(POSES["stand"])
            sw = 18 * math.sin(ph)
            p["th"] = (270 + sw, 270 - sw); p["sh"] = (268 + sw * 0.6, 268 - sw * 0.6)
            p["ua"] = (270 - sw * 1.2, 270 + sw * 1.2); p["fa"] = (272 - sw, 272 + sw); p["head"] = -6
            x = lerp(w * 0.18, cx, ease((t - t_life) / 3.5))
            draw_stick(dc, x, g, p, 1.2 * u, INK + (int(255 * (1 - dead)),))
        if dead > 0:
            a = int(255 * dead)
            dc.chord([cx - 170 * u, g - 64 * u, cx + 170 * u, g + 50 * u], 180, 360, fill=(70, 56, 46, a))
            for sx, hh in ((cx - 150 * u, 92), (cx + 150 * u, 68)):
                dc.rounded_rectangle([sx - 13 * u, g - hh * u, sx + 13 * u, g], radius=int(11 * u), fill=(120, 122, 132, a))
        im.paste(ch, (0, 0), ch)
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        top = (cx, g - 70 * u)
        for k, ((num, lab), (ix, iy), te) in enumerate(zip(self.ITEMS, self.pos, e)):
            ap = ease((t - te) / 0.45)
            if ap <= 0:
                continue
            focus = 1.0 if (te <= t < (e[k + 1] if k < 2 else t_ref)) or (t > t_cta) else 0.75
            pul = 1.0 if t < t_cta else 0.75 + 0.25 * math.sin((t - t_cta) * 5 + k * 2)
            col = GOLD + (int(255 * ap * focus * pul),)
            self.icon(dl, k, ix, iy, 1.0 * u, col, t)
            dg.ellipse([ix - 80 * u, iy - 110 * u, ix + 80 * u, iy + 60 * u], fill=int(110 * ap * focus))
            dl.text((ix, iy + 78 * u), lab, font=self.f_item, fill=(255, 236, 200, int(235 * ap)), anchor="mm")
            dl.ellipse([ix - 20 * u, iy - 150 * u, ix + 20 * u, iy - 110 * u], outline=GOLD + (int(220 * ap),), width=max(2, int(3 * u)))
            dl.text((ix, iy - 130 * u), num, font=self.f_item, fill=GOLD + (int(255 * ap),), anchor="mm")
            sx, sy = ix, iy - 20 * u
            mx, my = (sx + top[0]) / 2, min(sy, top[1]) - 120 * u
            th = ease((t - te - 0.2) / 0.6)
            if k != 1:
                pts = [((1 - s_) ** 2 * sx + 2 * (1 - s_) * s_ * mx + s_ ** 2 * top[0], (1 - s_) ** 2 * sy + 2 * (1 - s_) * s_ * my + s_ ** 2 * top[1]) for s_ in np.linspace(0, th, 30)]
                if th > 0.02:
                    dl.line(pts, fill=GOLD + (int(150 * ap),), width=max(2, int(3 * u)))
            elif th > 0.02:
                dl.line([(ix, iy + 46 * u), (ix, iy + 46 * u + (top[1] - iy - 46 * u) * th)], fill=GOLD + (int(150 * ap),), width=max(2, int(3 * u)))
            if th >= 1:
                for j in range(3):
                    q = ((t * 0.7 + j / 3 + k * 0.2) % 1.0)
                    if k != 1:
                        px = (1 - q) ** 2 * sx + 2 * (1 - q) * q * mx + q ** 2 * top[0]
                        py = (1 - q) ** 2 * sy + 2 * (1 - q) * q * my + q ** 2 * top[1]
                    else:
                        px, py = ix, iy + 46 * u + (top[1] - iy - 46 * u) * q
                    dl.ellipse([px - 6 * u, py - 6 * u, px + 6 * u, py + 6 * u], fill=(255, 240, 200, 230))
                    dg.ellipse([px - 16 * u, py - 16 * u, px + 16 * u, py + 16 * u], fill=160)
        if resumed:
            dg.ellipse([cx - 220 * u, g - 120 * u, cx + 220 * u, g + 40 * u], fill=int(70 * min(1, (t - e[0] - 0.6) / 1.5)))
        gl = glow.filter(ImageFilter.GaussianBlur(26 * u))
        im = ImageChops.screen(im, Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in GOLD]))
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im, "RGBA")
        d.line([(0, g), (w, g)], fill=(255, 255, 255, 40), width=max(1, int(2 * u)))
        return im


class SevenShade(Scene):
    """The Day with no shade but His: seven figures walk out of the heat into a cool shade.
    Beats: hook, seven, s1..s7, reflect, cta."""
    ambience = "heat"
    bokeh_n = 0
    camera = "static"
    text_y = 0.235
    text_zone = (0.165, 0.33)
    band = 0.0
    ICONS = ["scales", "prayer", "mosque", "pair", "palm", "coin", "tear"]

    def build(self):
        from scenes_topics import tiny_person
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.hz = hz = int(h * 0.62)
        self.ground = int(h * 0.80)
        a = vgrad(w, h, [(0, (30, 8, 12)), (0.30, (84, 22, 20)), (0.52, (176, 70, 38)), (0.62, (240, 140, 66)), (0.621, (196, 128, 74)), (0.80, (150, 88, 52)), (1, (64, 34, 22))])
        self.sun = (w * 0.83, h * 0.065, 150 * u)
        a = a + (radial(w, h, self.sun[0], self.sun[1], 640 * u) * 95)[..., None] * np.array([1, 0.72, 0.42], np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        disc = np.clip(self.sun[2] - np.hypot(xx - self.sun[0], yy - self.sun[1]) + 1, 0, 1)
        a = a * (1 - disc[..., None]) + np.array([255, 240, 205], np.float32) * disc[..., None]
        bg = to_img(a); d = ImageDraw.Draw(bg, "RGBA")
        for r in range(14):                                   # the vast crowd on the horizon
            p = r / 13
            y = hz + 4 * u + p * 70 * u
            s = (0.35 + 0.55 * p) * u
            x = -rng.uniform(0, 20)
            c = int(70 - 25 * p)
            while x < w + 20:
                tiny_person(d, x + rng.uniform(-2, 2), y, s, (c + 30, int(c * 0.55), int(c * 0.45), 255))
                x += rng.uniform(9, 15) * s / u
        self.bg = np.asarray(bg, np.float32)
        # the shade: a cool column falling onto an elliptical pool, abstract (nothing drawn above it)
        cx, gy = w / 2, self.ground
        self.pool = blur_mask((w, h), lambda dd: dd.ellipse([cx - 0.45 * w, gy - 0.06 * h, cx + 0.45 * w, gy + 0.05 * h], fill=255), 30 * u)
        self.column = blur_mask((w, h), lambda dd: dd.polygon([(cx - 0.36 * w, h * 0.40), (cx + 0.36 * w, h * 0.40), (cx + 0.47 * w, gy + 0.02 * h), (cx - 0.47 * w, gy + 0.02 * h)], fill=170), 70 * u)
        self.column *= np.clip((np.arange(h)[:, None] - h * 0.40) / (h * 0.25), 0, 1)
        rim = Image.new("L", (w, h), 0)
        ImageDraw.Draw(rim).ellipse([cx - 0.45 * w, gy - 0.06 * h, cx + 0.45 * w, gy + 0.05 * h], outline=255, width=max(2, int(3 * u)))
        self.rim = np.asarray(rim.filter(ImageFilter.GaussianBlur(5 * u)), np.float32) / 255
        self.slots = [(w / 2 + (k - 3) * 0.106 * w, gy + 0.018 * h * (1 - ((k - 3) / 3) ** 2)) for k in range(7)]
        self.hot = Motes(rng, 70, (0, h * 0.35, w, h), color=(255, 190, 120), r=(1.4 * u, 3.0 * u), rise=-14, sway=40 * u)
        self.cool = Motes(rng, 45, (w * 0.1, h * 0.55, w * 0.9, gy), color=(190, 236, 255), r=(1.2 * u, 2.6 * u), rise=8, sway=14 * u)
        self.f_n = ImageFont.truetype(_font("Lora.ttf"), int(26 * u))
        self.f_c = ImageFont.truetype(_font("Lora.ttf"), int(30 * u))
        for f_ in (self.f_n, self.f_c):
            try:
                f_.set_variation_by_axes([700])
            except Exception:
                pass
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def icon(self, d, kind, cx, cy, s, col, t):
        lw = max(2, int(4 * s))
        if kind == "scales":
            d.line([(cx, cy - 34 * s), (cx, cy + 26 * s)], fill=col, width=lw)
            d.line([(cx - 34 * s, cy - 24 * s), (cx + 34 * s, cy - 24 * s)], fill=col, width=lw)
            for sx in (-34, 34):
                d.line([(cx + sx * s, cy - 24 * s), (cx + (sx - 12) * s, cy), (cx + (sx + 12) * s, cy), (cx + sx * s, cy - 24 * s)], fill=col, width=max(1, int(2 * s)))
                d.chord([cx + (sx - 14) * s, cy - 8 * s, cx + (sx + 14) * s, cy + 10 * s], 0, 180, fill=col)
            d.rectangle([cx - 16 * s, cy + 24 * s, cx + 16 * s, cy + 30 * s], fill=col)
        elif kind == "prayer":                               # prayer mat
            d.polygon([(cx - 22 * s, cy - 30 * s), (cx + 22 * s, cy - 30 * s), (cx + 26 * s, cy + 30 * s), (cx - 26 * s, cy + 30 * s)], outline=col, width=lw)
            d.arc([cx - 14 * s, cy - 24 * s, cx + 14 * s, cy + 4 * s], 180, 360, fill=col, width=lw)
        elif kind == "mosque":
            d.chord([cx - 26 * s, cy - 30 * s, cx + 26 * s, cy + 22 * s], 180, 360, fill=col)
            d.rectangle([cx - 30 * s, cy - 4 * s, cx + 30 * s, cy + 28 * s], fill=col)
            d.rectangle([cx + 36 * s, cy - 36 * s, cx + 44 * s, cy + 28 * s], fill=col)
            d.line([(cx, cy - 30 * s), (cx, cy - 42 * s)], fill=col, width=max(1, int(3 * s)))
        elif kind == "pair":                                 # two linked rings: brotherhood for Allah's sake
            d.ellipse([cx - 34 * s, cy - 18 * s, cx + 2 * s, cy + 18 * s], outline=col, width=lw)
            d.ellipse([cx - 2 * s, cy - 18 * s, cx + 34 * s, cy + 18 * s], outline=col, width=lw)
        elif kind == "palm":                                 # a raised hand: refusing sin
            d.rounded_rectangle([cx - 18 * s, cy - 10 * s, cx + 18 * s, cy + 28 * s], radius=int(10 * s), fill=col)
            for j, fx in enumerate((-14, -5, 4, 13)):
                L = (30, 36, 34, 26)[j]
                d.rounded_rectangle([cx + fx * s - 4 * s, cy - L * s, cx + fx * s + 4 * s, cy - 4 * s], radius=int(4 * s), fill=col)
            d.rounded_rectangle([cx - 30 * s, cy - 2 * s, cx - 18 * s, cy + 14 * s], radius=int(5 * s), fill=col)
        elif kind == "coin":
            d.ellipse([cx - 24 * s, cy - 24 * s, cx + 24 * s, cy + 24 * s], fill=col)
            d.ellipse([cx - 15 * s, cy - 15 * s, cx + 15 * s, cy + 15 * s], outline=(110, 60, 20, 255), width=max(2, int(3 * s)))
            gl = 0.5 + 0.5 * math.sin(t * 3)
            d.line([(cx - 8 * s, cy - 30 * s), (cx + 8 * s, cy - 30 * s)], fill=(255, 255, 255, int(200 * gl)), width=max(1, int(2 * s)))
        else:                                                # tear
            d.polygon([(cx, cy - 30 * s), (cx - 16 * s, cy + 4 * s), (cx + 16 * s, cy + 4 * s)], fill=col)
            d.ellipse([cx - 16 * s, cy - 12 * s, cx + 16 * s, cy + 20 * s], fill=col)

    def pose_for(self, k, t):
        p = dict(POSES["stand"])
        if k == 1:                                           # youth standing in prayer, hands folded
            p["ua"] = (296, 244); p["fa"] = (20, 160); p["head"] = -18
        elif k == 3:
            p["ua"] = (300, 262); p["fa"] = (300, 272)
        elif k == 4:                                         # hand raised, turning away
            p["ua"] = (20, 262); p["fa"] = (80, 272); p["head"] = 14
        elif k == 5:                                         # one hand low, giving quietly
            p["ua"] = (262, 300); p["fa"] = (272, 330); p["head"] = -26
        elif k == 6:                                         # kneeling, hands raised, head bowed
            p = dict(POSES["kneel"]); p["head"] = -40; p["ua"] = (60, 120); p["fa"] = (95, 85)
        return p

    def frame(self, t):
        from PIL import ImageChops
        w, h, u = self.w, self.h, self.u
        g = self.ground
        t_hook = self.bt("hook", 0.0)
        ss = [self.bt(f"s{k + 1}") for k in range(7)]
        t_seven, t_ref, t_cta = self.bt("seven"), self.bt("reflect"), self.bt("cta")
        shade = ease((t - t_hook - 0.6) / 1.6)
        filled = sum(1 for s_ in ss if t > s_ + 0.9)
        arr = self.bg.copy()
        # heat shimmer around the horizon
        y0, y1 = self.hz - int(40 * u), self.hz + int(140 * u)
        band = arr[y0:y1]
        for r_ in range(0, band.shape[0], 3):
            sh = int(3 * u * math.sin(r_ * 0.09 + t * 7) * (r_ / band.shape[0]))
            band[r_:r_ + 3] = np.roll(band[r_:r_ + 3], sh, axis=1)
        arr[y0:y1] = band
        pulse = 0.5 + 0.5 * math.sin(t * 2.2)
        arr += (radial(w, h, self.sun[0], self.sun[1], (260 + 30 * pulse) * u) * 26 * pulse)[..., None] * np.array([1, 0.8, 0.5], np.float32)
        # the shade cools everything it touches
        cool = np.array([34, 74, 96], np.float32)
        k_ = (self.column * 0.75 + self.pool * 0.9) * shade * (0.85 + 0.15 * filled / 7)
        k_ = np.clip(k_, 0, 0.92)[..., None]
        arr = arr * (1 - k_) + cool * k_ + self.rim[..., None] * np.array([150, 230, 255], np.float32) * 0.55 * shade
        im = to_img(arr)
        d = ImageDraw.Draw(im, "RGBA")
        for k in range(3):
            rr = self.sun[2] + (16 + 14 * k + 8 * pulse) * u
            d.ellipse([self.sun[0] - rr, self.sun[1] - rr, self.sun[0] + rr, self.sun[1] + rr], outline=(255, 226, 170, 60 - 15 * k), width=int(6 * u))
        # counter: seven dots
        if t > t_seven:
            ap = ease((t - t_seven) / 0.5)
            cy = h * 0.355
            for k in range(7):
                x = w / 2 + (k - 3) * 54 * u
                on = 1.0 if t > ss[k] + 0.9 else 0.0
                d.ellipse([x - 15 * u, cy - 15 * u, x + 15 * u, cy + 15 * u], fill=(GOLD + (int(255 * ap),)) if on else (40, 14, 14, int(160 * ap)),
                          outline=(255, 226, 170, int(230 * ap)), width=max(2, int(2 * u)))
                d.text((x, cy), str(k + 1), font=self.f_n, fill=((60, 30, 10) if on else (255, 226, 170)) + (int(255 * ap),), anchor="mm")
            d.text((w / 2, cy + 46 * u), f"{filled} / 7  IN THE SHADE", font=self.f_c, fill=(255, 236, 200, int(230 * ap)), anchor="mm")
        # figures
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(ch, "RGBA")
        ic = Image.new("RGBA", (w, h), (0, 0, 0, 0)); di = ImageDraw.Draw(ic, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        for k, (sx, sy) in enumerate(self.slots):
            te = ss[k]
            if t < te:
                continue
            walk = ease((t - te) / 1.1)
            start_x = -60 * u if sx < w / 2 else w + 60 * u
            if k == 3:
                start_x = w / 2 - 0.55 * w
            x = lerp(start_x, sx, walk)
            S = (0.62 if k == 1 else 0.74) * u
            if walk < 1:
                p = dict(POSES["stand"]); sw = 18 * math.sin((t - te) * 9)
                p["th"] = (270 + sw, 270 - sw); p["ua"] = (270 - sw, 270 + sw)
                col = (40, 18, 14, 255)
            else:
                p = self.pose_for(k, t)
                c_ = ease((t - te - 1.1) / 0.6)
                col = tuple(int(lerp(a_, b_, c_)) for a_, b_ in zip((40, 18, 14), (236, 246, 250))) + (255,)
            if k == 3:                                       # two who love each other for Allah's sake
                for off in (-26, 26):
                    pp = dict(p)
                    if walk >= 1:
                        pp["ua"] = (300, 262) if off < 0 else (278, 240); pp["fa"] = (330, 272) if off < 0 else (270, 210)
                    draw_stick(dc, x + off * u, sy, pp, S, col, flip=off > 0 and walk >= 1)
            else:
                draw_stick(dc, x, sy, p, S, col)
            if k == 6 and walk >= 1:                         # tears falling
                for j in range(2):
                    q = ((t * 0.9 + j / 2) % 1.0)
                    dc.ellipse([x + 12 * u - 3 * u, sy - 150 * u + q * 50 * u - 4 * u, x + 12 * u + 3 * u, sy - 150 * u + q * 50 * u + 4 * u], fill=(200, 236, 255, int(230 * (1 - q))))
            if walk >= 1:
                ia = ease((t - te - 1.0) / 0.5)
                iy = sy - 300 * u
                self.icon(di, self.ICONS[k], x, iy, 0.9 * u, GOLD + (int(255 * ia),), t)
                dg.ellipse([x - 60 * u, iy - 60 * u, x + 60 * u, iy + 60 * u], fill=int(120 * ia))
                dg.ellipse([x - 70 * u, sy - 260 * u, x + 70 * u, sy + 20 * u], fill=int(70 * ia))
        # "you": a lone figure still standing in the heat
        vx, vy = w * 0.065, h * 0.875
        look = ease((t - t_ref) / 0.8)
        step = ease((t - t_cta) / 2.0)
        vp = dict(POSES["stand"]); vp["head"] = lerp(-20, 18, look)
        if step > 0:
            sw = 16 * math.sin((t - t_cta) * 7) * (1 - step)
            vp["th"] = (270 + sw, 270 - sw)
        draw_stick(dc, vx + step * 70 * u, vy, vp, 0.82 * u, (20, 8, 6, 255))
        gl = glow.filter(ImageFilter.GaussianBlur(24 * u))
        im = ImageChops.screen(im, Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in (180, 230, 255)]))
        rim = ch.getchannel("A").filter(ImageFilter.GaussianBlur(8 * u)).point(lambda v: int(v * 0.45))
        rl = Image.new("RGBA", (w, h), (170, 230, 255, 0)); rl.putalpha(rim)
        im.paste(rl, (0, 0), rl); im.paste(ch, (0, 0), ch); im.paste(ic, (0, 0), ic)
        ov = self.overlay(); do = ImageDraw.Draw(ov)
        self.hot.draw(do, t)
        if shade > 0:
            self.cool.draw(do, t)
        im.paste(ov, (0, 0), ov)
        return im


class ScaleOfWords(Scene):
    """Two words light on the tongue, heavy on the Scale (symbolic balance).
    Beats: hook, light, heavy, beloved, w1, w2, now, ayah, cta."""
    ambience = "night_room"
    bokeh_n = 0
    camera = "static"
    text_y = 0.24
    text_zone = (0.165, 0.395)
    band = 0.0
    WORDS = ["سُبْحَانَ اللَّهِ الْعَظِيمِ", "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ"]  # Bukhari 6406 order

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (8, 8, 10)), (0.5, (20, 18, 17)), (1, (7, 7, 8))])
        self.base = a + (radial(w, h, w / 2, h * 0.56, 560 * u) * 40)[..., None] * np.array([1, 0.8, 0.5], np.float32)
        self.piv = (w / 2, h * 0.505)
        self.beam_l = 0.36 * w
        self.chain = 0.15 * h
        self.f_ar = ImageFont.truetype(_font("Amiri-Regular.ttf"), int(44 * u))
        self.plaques = []
        for txt in self.WORDS:                               # pre-render the two glowing word plaques
            pw, ph = int(330 * u), int(92 * u)
            im = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([20, 20, 20 + pw, 20 + ph], radius=int(22 * u), fill=(46, 34, 18, 245), outline=GOLD + (255,), width=max(2, int(3 * u)))
            d.text((20 + pw / 2, 20 + ph / 2 + 4 * u), txt, font=self.f_ar, fill=(255, 226, 160, 255), anchor="mm", direction="rtl", language="ar")
            self.plaques.append(im)
        self.dust = Motes(rng, 60, (0, h * 0.2, w, h), color=(255, 214, 140), r=(1.0 * u, 2.4 * u), rise=8, sway=18 * u)
        self.feather_seed = rng.uniform(0, 6.28)
        self.rays = [blur_mask((w, h), lambda dd, x=x: dd.polygon([(x - 30 * u, -10), (x + 30 * u, -10), (x + 180 * u, h * 0.8), (x - 180 * u, h * 0.8)], fill=60), 46 * u)
                     for x in (w * 0.32, w * 0.5, w * 0.68)]
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def tilt(self, t):
        """Beam angle in degrees (positive = right pan down). Springs when the words land."""
        th = self.bt("heavy") + 0.55
        if t < th:
            return 1.5 * math.sin(t * 0.9)                    # idle sway, nearly balanced
        x = t - th
        return 15.0 * (1 - math.exp(-3.2 * x) * math.cos(9.0 * x))

    def frame(self, t):
        from PIL import ImageChops
        w, h, u = self.w, self.h, self.u
        t_light, t_heavy, t_bel = self.bt("light"), self.bt("heavy"), self.bt("beloved")
        tw = [self.bt("w1"), self.bt("w2")]
        t_ayah, t_cta = self.bt("ayah"), self.bt("cta")
        arr = self.base.copy()
        bel = ease((t - t_bel) / 1.2)
        for k, r in enumerate(self.rays):
            arr = add_glow(arr, r, (255, 220, 160), (0.10 + 0.25 * bel) * (0.85 + 0.15 * math.sin(t * 0.7 + k * 2)))
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        px, py = self.piv
        ang = math.radians(self.tilt(t))
        L = self.beam_l
        lx, ly = px - L * math.cos(ang), py - L * math.sin(ang)
        rx, ry = px + L * math.cos(ang), py + L * math.sin(ang)
        gold_d, gold_l = (150, 110, 50), (232, 186, 102)
        base_y = h * 0.80
        d.polygon([(px - 120 * u, base_y), (px + 120 * u, base_y), (px + 70 * u, base_y - 30 * u), (px - 70 * u, base_y - 30 * u)], fill=gold_d)
        d.rectangle([px - 14 * u, py, px + 14 * u, base_y - 30 * u], fill=gold_d)
        d.line([(px - 6 * u, py + 10 * u), (px - 6 * u, base_y - 34 * u)], fill=gold_l, width=max(2, int(4 * u)))
        for k in range(4):                                    # rings on the pillar
            yy = py + (k + 1) * (base_y - py) / 5
            d.rounded_rectangle([px - 24 * u, yy - 7 * u, px + 24 * u, yy + 7 * u], radius=int(6 * u), fill=gold_l)
        d.line([(lx, ly), (rx, ry)], fill=gold_d, width=int(16 * u))
        d.line([(lx, ly - 4 * u), (rx, ry - 4 * u)], fill=gold_l, width=int(5 * u))
        d.ellipse([px - 26 * u, py - 26 * u, px + 26 * u, py + 26 * u], fill=gold_l, outline=gold_d, width=int(4 * u))
        d.polygon([(px, py - 70 * u), (px - 12 * u, py - 24 * u), (px + 12 * u, py - 24 * u)], fill=gold_l)
        pans = []
        for ex, ey in ((lx, ly), (rx, ry)):
            d.ellipse([ex - 12 * u, ey - 12 * u, ex + 12 * u, ey + 12 * u], fill=gold_l)
            pyb = ey + self.chain
            for sx in (-110, 0, 110):
                d.line([(ex, ey), (ex + sx * u, pyb)], fill=(200, 160, 90), width=max(2, int(3 * u)))
            d.chord([ex - 140 * u, pyb - 30 * u, ex + 140 * u, pyb + 40 * u], 0, 180, fill=gold_d)
            d.line([(ex - 140 * u, pyb + 5 * u), (ex + 140 * u, pyb + 5 * u)], fill=gold_l, width=int(6 * u))
            pans.append((ex, pyb))
        # the two word plaques
        land_y = pans[1][1] - 6 * u
        for k, pl in enumerate(self.plaques):
            ap = ease((t - t_light) / 0.6)
            if ap <= 0:
                continue
            fx = w / 2 + (k - 0.5) * 360 * u
            fy = h * 0.43 + 10 * u * math.sin(t * 1.6 + k * 1.7)       # floating: weightless
            drop = ease((t - t_heavy - k * 0.18) / 0.55) ** 2
            tx_, ty_ = pans[1][0], land_y - k * 86 * u
            x = lerp(fx, tx_, drop); y = lerp(fy, ty_, drop)
            lit = max(ease((t - tw[k]) / 0.4) * (1 - 0.4 * ease((t - tw[k] - 2.6) / 0.6)) if t < t_cta else 0.0,
                      0.6 + 0.4 * math.sin((t - t_cta) * 4 + k) if t > t_cta else 0.0)
            img = pl.copy()
            if ap < 1:
                img.putalpha(img.getchannel("A").point(lambda v, a=ap: int(v * a)))
            im.paste(img, (int(x - img.width / 2), int(y - img.height + 20 * u)), img)
            dg.rounded_rectangle([x - 180 * u, y - img.height, x + 180 * u, y + 10 * u], radius=int(30 * u), fill=int(90 + 120 * lit))
        # landing impact: flash + dust ring
        imp = t - (t_heavy + 0.55)
        if 0 < imp < 1.2:
            k_ = 1 - imp / 1.2
            ex, ey = pans[1]
            rr = (60 + 320 * imp) * u
            d.ellipse([ex - rr, ey - rr * 0.25, ex + rr, ey + rr * 0.25], outline=(255, 226, 170, int(200 * k_)), width=max(2, int(5 * u * k_ + 1)))
            dg.ellipse([ex - 260 * u, ey - 200 * u, ex + 260 * u, ey + 80 * u], fill=int(230 * k_ ** 2))
        # a feather drifting down: light on the tongue
        if t_light < t < t_heavy + 1.0:
            fa = ease((t - t_light) / 0.6) * (1 - ease((t - t_heavy) / 0.8))
            q = (t - t_light)
            fx = w * 0.22 + 50 * u * math.sin(q * 1.4 + self.feather_seed)
            fy = h * 0.475 + q * 18 * u
            angf = 0.5 * math.sin(q * 1.4)
            dx, dy = math.cos(angf) * 60 * u, math.sin(angf) * 60 * u
            d.line([(fx - dx, fy - dy), (fx + dx, fy + dy)], fill=(245, 236, 220, int(220 * fa)), width=max(2, int(3 * u)))
            for j in range(-5, 6):
                bx, by = fx + dx * j / 6, fy + dy * j / 6
                d.line([(bx, by), (bx - dy * 0.35 + 6 * u, by + dx * 0.35)], fill=(245, 236, 220, int(150 * fa)), width=max(1, int(2 * u)))
                d.line([(bx, by), (bx + dy * 0.35 + 6 * u, by - dx * 0.35)], fill=(245, 236, 220, int(150 * fa)), width=max(1, int(2 * u)))
        gl = glow.filter(ImageFilter.GaussianBlur(28 * u))
        im = ImageChops.screen(im, Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in GOLD]))
        ov = self.overlay(); self.dust.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class LastThird(Scene):
    """The last third of the night (Bukhari 1145). Night timeline, a sleeping town whose lights go out,
    one person in dua, and three answered calls rising as lights. Nothing depicts Allah.
    Beats: hook, said, third, c1, c2, c3, card, reflect, ayah, cta."""
    ambience = "night"
    bokeh_n = 0
    camera = "static"
    text_y = 0.24
    text_zone = (0.165, 0.40)
    band = 0.0
    WORDS = ["answer", "give", "forgive"]

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        a = vgrad(w, h, [(0, (4, 6, 18)), (0.55, (14, 20, 48)), (0.80, (34, 36, 72)), (1, (8, 8, 16))])
        self.base = a
        n = 260
        self.sx = rng.uniform(0, w, n); self.sy = rng.uniform(0, h * 0.78, n) ** 1.0
        self.sr = rng.uniform(0.6, 2.2, n) * u; self.sp = rng.uniform(0, 6.28, n); self.sf = rng.uniform(0.6, 2.0, n)
        # town silhouette
        self.hor = h * 0.80
        town = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(town)
        self.windows = []
        x = -20 * u
        col = (9, 11, 24, 255)
        while x < w + 20 * u:
            bw = rng.uniform(70, 150) * u; bh = rng.uniform(80, 230) * u
            top = self.hor - bh
            d.rectangle([x, top, x + bw, h], fill=col)
            if rng.random() < 0.25:
                d.pieslice([x + bw * 0.2, top - bw * 0.3, x + bw * 0.8, top + bw * 0.3], 180, 360, fill=col)
            for wy in np.arange(top + 22 * u, self.hor - 20 * u, 40 * u):
                for wx in np.arange(x + 16 * u, x + bw - 26 * u, 34 * u):
                    if rng.random() < 0.45:
                        self.windows.append((wx, wy, rng.uniform(0.05, 0.95)))
            x += bw + rng.uniform(-10, 8) * u
        mx = w * 0.82                                              # a minaret
        d.rectangle([mx - 16 * u, self.hor - 360 * u, mx + 16 * u, h], fill=col)
        d.rectangle([mx - 28 * u, self.hor - 300 * u, mx + 28 * u, self.hor - 286 * u], fill=col)
        d.polygon([(mx - 18 * u, self.hor - 360 * u), (mx, self.hor - 420 * u), (mx + 18 * u, self.hor - 360 * u)], fill=col)
        self.town = town
        # foreground terrace
        self.ground = h * 0.90
        self.f_lab = ImageFont.truetype(_font("Lora.ttf"), int(30 * u))
        self.f_small = ImageFont.truetype(_font("Lora.ttf"), int(24 * u))
        self.dust = Motes(rng, 40, (0, h * 0.45, w, h), color=(255, 224, 160), r=(1.0 * u, 2.2 * u), rise=6, sway=14 * u)
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def night_pos(self, t):
        """0 = Maghrib, 1 = Fajr. Reaches the last third when that line starts, then creeps on."""
        t0, t3 = 3.0, self.bt("third")
        if t < t3:
            return 0.05 + 0.617 * ease((t - t0) / max(0.1, t3 - t0))
        return 0.667 + 0.13 * (1 - math.exp(-(t - t3) / 10))

    def frame(self, t):
        from PIL import ImageChops
        w, h, u = self.w, self.h, self.u
        t3 = self.bt("third"); tc = [self.bt("c1"), self.bt("c2"), self.bt("c3")]
        t_ref, t_ayah, t_cta = self.bt("reflect"), self.bt("ayah"), self.bt("cta")
        th = ease((t - t3) / 1.5)
        arr = self.base.copy()
        arr = arr + (radial(w, h, w / 2, h * 0.86, 520 * u) * (12 + 30 * ease((t - tc[0] + 0.5) / 1.5)))[..., None] * np.array([1, 0.78, 0.45], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        # stars brighten in the last third
        tw = 0.55 + 0.45 * np.sin(t * self.sf + self.sp)
        for x, y, r, k in zip(self.sx, self.sy, self.sr, tw):
            a_ = int(min(255, (90 + 120 * th) * k))
            rr = r * (1 + 0.5 * th)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(235, 236, 255, a_))
        # night timeline
        bx0, bx1, by = w * 0.12, w * 0.88, h * 0.445
        L = bx1 - bx0
        d.line([(bx0, by), (bx1, by)], fill=(150, 160, 200, 120), width=max(2, int(4 * u)))
        for k in (1, 2):
            xx = bx0 + L * k / 3
            d.line([(xx, by - 12 * u), (xx, by + 12 * u)], fill=(170, 180, 220, 150), width=max(2, int(3 * u)))
        if th > 0:
            d.line([(bx0 + L * 2 / 3, by), (bx1, by)], fill=GOLD + (int(255 * th),), width=int(8 * u))
            dg.line([(bx0 + L * 2 / 3, by), (bx1, by)], fill=int(200 * th), width=int(30 * u))
            d.text((bx0 + L * 5 / 6, by + 26 * u), "last third", font=self.f_small, fill=GOLD + (int(255 * th),), anchor="ma")
        d.text((bx0, by + 26 * u), "Maghrib", font=self.f_small, fill=(170, 180, 220, 170), anchor="la")
        d.text((bx1, by + 26 * u), "Fajr", font=self.f_small, fill=(170, 180, 220, 170), anchor="ra")
        p = self.night_pos(t); mx = bx0 + L * p; my = by - 46 * u
        R = 26 * u
        d.ellipse([mx - R, my - R, mx + R, my + R], fill=(250, 236, 200, 255))
        d.ellipse([mx - R + 12 * u, my - R - 6 * u, mx + R + 12 * u, my + R - 6 * u], fill=tuple(int(c) for c in arr[int(my), int(min(w - 1, mx + R + 30 * u))]) + (255,))
        dg.ellipse([mx - 60 * u, my - 60 * u, mx + 60 * u, my + 60 * u], fill=110)
        # town: windows go out as the night deepens
        im.paste(self.town, (0, 0), self.town)
        sleep = ease((t - 3.4) / max(0.5, (t3 - 3.4) * 1.05))
        for wx, wy, k in self.windows:
            if k > sleep:
                d.rectangle([wx, wy, wx + 12 * u, wy + 16 * u], fill=(255, 200, 120, 210))
                dg.rectangle([wx - 4 * u, wy - 4 * u, wx + 16 * u, wy + 20 * u], fill=60)
        # foreground terrace and the one person awake
        gy = self.ground
        d.rectangle([0, gy, w, h], fill=(6, 6, 12, 255))
        d.line([(0, gy), (w, gy)], fill=(40, 40, 64, 255), width=max(2, int(3 * u)))
        ap = ease((t - (t3 + 0.4)) / 1.0)
        cx = w / 2
        if ap > 0:
            d.polygon([(cx - 120 * u, gy + 4 * u), (cx + 150 * u, gy + 4 * u), (cx + 130 * u, gy + 26 * u), (cx - 140 * u, gy + 26 * u)], fill=(90, 40, 40, int(255 * ap)))
            pose = dict(POSES["kneel"], ua=(-60, -64), fa=(40, 46), head=-10)   # dua: palms raised in front
            pose["torso"] = 92 + 1.2 * math.sin(t * 1.3)
            fig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw_stick(ImageDraw.Draw(fig), cx - 40 * u, gy + 4 * u, pose, s=1.2 * u, col=(250, 226, 180, 255))
            if ap < 1:
                fig.putalpha(fig.getchannel("A").point(lambda v, a=ap: int(v * a)))
            im.paste(fig, (0, 0), fig)
            dg.ellipse([cx - 170 * u, gy - 300 * u, cx + 170 * u, gy + 20 * u], fill=int(80 * ap))
        hx, hy = cx + 50 * u, gy - 215 * u                         # around the raised hands
        # three calls rising as lights
        slots = [(w * 0.24, h * 0.55), (w * 0.50, h * 0.53), (w * 0.76, h * 0.55)]
        for k, (sx, sy) in enumerate(slots):
            q = (t - tc[k] - 0.2) / 1.3
            if q <= 0:
                continue
            e = ease(q)
            x = lerp(hx, sx, e); y = lerp(hy, sy, e) - 120 * u * math.sin(math.pi * min(1, q))
            for j in range(1, 9):                                 # trail
                qq = max(0.0, min(1.0, q - j * 0.03)); ee = ease(qq)
                tx_ = lerp(hx, sx, ee); ty_ = lerp(hy, sy, ee) - 120 * u * math.sin(math.pi * qq)
                rr = (10 - j) * u
                d.ellipse([tx_ - rr, ty_ - rr, tx_ + rr, ty_ + rr], fill=GOLD + (int(150 * (1 - j / 9) * (1 - min(1, q - 1) if q > 1 else 1)),))
            pulse = 1.0
            if t > t_ayah:
                pulse = 1 + 0.25 * math.sin((t - t_ayah) * 3 + k)
            if t > t_cta:
                pulse = 1 + 0.35 * math.sin((t - t_cta) * 4 + k * 1.3)
            R = 26 * u * pulse
            d.ellipse([x - R, y - R, x + R, y + R], fill=(255, 236, 190, 255))
            dg.ellipse([x - 3 * R, y - 3 * R, x + 3 * R, y + 3 * R], fill=int(min(255, 150 + 80 * (pulse - 1) * 3)))
            if q > 1:
                la = ease(q - 1) if q < 2 else 1.0
                d.text((sx, sy + 44 * u), self.WORDS[k], font=self.f_lab, fill=GOLD + (int(255 * la),), anchor="ma")
        gl = glow.filter(ImageFilter.GaussianBlur(26 * u))
        im = ImageChops.screen(im, Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in GOLD]))
        ov = self.overlay(); self.dust.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


class BirdsProvision(Scene):
    """Tirmidhi 2344: birds go out hungry in the morning and return full. Sky runs pre-dawn ->
    morning -> sunset -> dusk; birds leave the tree slim and come back round.
    Beats: hook, said, rely, provide, out, full, card, notice, ayah, cta."""
    ambience = "meadow"
    bokeh_n = 0
    camera = "static"
    text_y = 0.24
    text_zone = (0.165, 0.40)
    band = 1.3
    SKIES = [  # (top, mid, horizon)
        ((10, 14, 38), (40, 44, 90), (150, 96, 110)),     # pre-dawn
        ((70, 128, 196), (130, 178, 220), (236, 214, 176)),  # morning
        ((54, 40, 96), (196, 96, 86), (255, 176, 92)),    # sunset
        ((12, 12, 34), (34, 28, 66), (110, 60, 70)),      # dusk
    ]
    LAND = [(18, 20, 34), (34, 56, 46), (30, 20, 30), (10, 10, 18)]

    def build(self):
        w, h, rng, u = self.w, self.h, self.rng, self.u
        self.skies = [vgrad(w, h, [(0, a), (0.55, b), (0.80, c), (1, c)]) for a, b, c in self.SKIES]
        far = ridge(w, rng, h * 0.74, 40 * u); near = ridge(w, rng, h * 0.81, 30 * u)
        yy = np.arange(h, dtype=np.float32)[:, None]
        self.m_far = np.clip((yy - far[None, :]) / 1.5 + 0.5, 0, 1)
        self.m_near = np.clip((yy - near[None, :]) / 1.5 + 0.5, 0, 1)
        # tree silhouette mask
        tm = Image.new("L", (w, h), 0); d = ImageDraw.Draw(tm)
        tx = w * 0.64
        d.polygon([(tx - 34 * u, h * 0.84), (tx + 40 * u, h * 0.84), (tx + 16 * u, h * 0.56), (tx - 10 * u, h * 0.56)], fill=255)
        for (x0, y0, x1, y1, wd) in [(tx, h * 0.64, tx - 400 * u, h * 0.60, 16), (tx, h * 0.60, tx + 170 * u, h * 0.53, 16), (tx, h * 0.58, tx - 90 * u, h * 0.50, 14)]:
            d.line([(x0, y0), (x1, y1)], fill=255, width=int(wd * u))
        for _ in range(26):
            cx = tx + rng.uniform(-260, 230) * u; cy = h * rng.uniform(0.44, 0.53)
            r = rng.uniform(50, 95) * u
            d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=255)
        self.m_tree = np.asarray(tm.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
        self.perch = [(tx - 360 * u + k * 88 * u, h * 0.60 + ((40 + k * 88) / 400) * 0.04 * h) for k in range(4)] + [(tx + 130 * u, h * 0.545)]  # on the long branch + one on the right
        self.birds = [dict(ph=rng.uniform(0, 6.28), dx=rng.uniform(-60, 60) * u, dy=rng.uniform(-40, 40) * u, sp=rng.uniform(0.9, 1.15)) for _ in self.perch]
        self.motes = Motes(rng, 40, (0, h * 0.4, w, h), color=(255, 236, 190), r=(1.0 * u, 2.4 * u), rise=6, sway=20 * u)
        self.beats = {}

    set_timeline = MercyGrid.set_timeline
    bt = MercyGrid.bt

    def sky_p(self, t):
        """0 pre-dawn, 1 morning, 2 sunset, 3 dusk."""
        t_out, t_full, t_ayah = self.bt("out"), self.bt("full"), self.bt("ayah")
        if t < t_full:
            return min(1.0, ease((t - 3.0) / max(0.5, t_out - 3.0 + 0.6)))
        if t < t_ayah:
            return 1 + ease((t - t_full) / 1.4)
        return 2 + 0.8 * ease((t - t_ayah) / 2.5)

    def _mix(self, seq, p):
        i = min(int(p), len(seq) - 2); f = p - i
        return i, f

    def draw_bird(self, d, x, y, s, flap, full, col, face=-1):
        bw, bh = 34 * s, (13 + 9 * full) * s
        d.ellipse([x - bw, y - bh, x + bw, y + bh], fill=col)
        hx = x + face * bw * 0.95; hy = y - bh * 0.7
        d.ellipse([hx - 11 * s, hy - 11 * s, hx + 11 * s, hy + 11 * s], fill=col)
        d.polygon([(hx + face * 9 * s, hy - 3 * s), (hx + face * 22 * s, hy + 1 * s), (hx + face * 9 * s, hy + 5 * s)], fill=col)
        d.polygon([(x - face * bw * 0.8, y - 4 * s), (x - face * (bw + 26 * s), y - 14 * s), (x - face * (bw + 22 * s), y + 6 * s)], fill=col)
        wy = y - bh * 0.3 - flap * 46 * s
        d.polygon([(x - 18 * s, y - bh * 0.4), (x + 14 * s, y - bh * 0.4), (x - face * 30 * s, wy)], fill=col)

    def frame(self, t):
        from PIL import ImageChops
        w, h, u = self.w, self.h, self.u
        p = self.sky_p(t); i, f = self._mix(self.skies, p)
        arr = self.skies[i] * (1 - f) + self.skies[i + 1] * f
        # sun / moon arc
        sun_k = min(1.0, max(0.0, (p - 0.15) / 1.9))
        sx = lerp(w * 0.08, w * 0.94, sun_k); sy = h * 0.74 - math.sin(math.pi * sun_k) * h * 0.30
        if p < 2.6:
            sc = np.array([255, 236, 190], np.float32) if p < 1.5 else np.array([255, 170, 90], np.float32)
            arr = arr + (radial(w, h, sx, sy, 300 * u) * 90)[..., None] * (sc / 255)
        lc = np.array(self.LAND[i], np.float32) * (1 - f) + np.array(self.LAND[i + 1], np.float32) * f
        arr = arr * (1 - self.m_far[..., None]) + (lc * 1.35 + 6) * self.m_far[..., None]
        arr = arr * (1 - self.m_near[..., None]) + lc * self.m_near[..., None]
        arr = arr * (1 - self.m_tree) + lc * 0.8 * self.m_tree
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        if p < 2.6:
            R = 46 * u
            d.ellipse([sx - R, sy - R, sx + R, sy + R], fill=(255, 244, 214, 255) if p < 1.5 else (255, 200, 120, 255))
        if p > 2.3:                                           # stars at dusk
            a_ = int(200 * min(1, (p - 2.3) / 0.5))
            rs = np.random.default_rng(3)
            for x, y in zip(rs.uniform(0, w, 140), rs.uniform(0, h * 0.6, 140)):
                d.ellipse([x - 1.5 * u, y - 1.5 * u, x + 1.5 * u, y + 1.5 * u], fill=(240, 240, 255, int(a_ * (0.6 + 0.4 * math.sin(t * 2 + x)))))
        # birds
        t_out, t_full = self.bt("out"), self.bt("full")
        col = tuple(int(c * 0.45) for c in lc) + (255,)
        for k, ((px, py), b) in enumerate(zip(self.perch, self.birds)):
            s = 1.35 * u
            if t < t_out + 0.2 + k * 0.12:                    # sitting, slim
                x, y, flap, full = px, py - 18 * s, 0.1 * math.sin(t * 2 + b["ph"]), 0.0
                self.draw_bird(d, x, y, s, flap, full, col)
                continue
            if t < t_full:                                    # flying away, up and left
                q = (t - t_out - 0.2 - k * 0.12) * b["sp"]
                x = px - q * 420 * u + b["dx"] * min(1, q); y = py - 18 * s - q * 260 * u + 30 * u * math.sin(q * 3 + b["ph"]) + b["dy"] * min(1, q)
                flap = math.sin(t * 14 + b["ph"])
                if x > -80 * u and y > -80 * u:
                    self.draw_bird(d, x, y, s, flap, 0.0, col)
                continue
            q = 1 - (t - t_full - 0.3 - k * 0.15) * 0.42 * b["sp"]    # 1 = far away, 0 = landed
            full = 1.0
            if q <= 0:
                self.draw_bird(d, px, py - 22 * s, s, 0.1 * math.sin(t * 2 + b["ph"]), full, col)
                continue
            qe = q * q * (3 - 2 * q)
            x = px - qe * 900 * u + b["dx"] * qe; y = py - 22 * s - qe * 520 * u + b["dy"] * qe + 20 * u * math.sin(q * 6 + b["ph"]) * qe
            self.draw_bird(d, x, y, s, math.sin(t * 12 + b["ph"]) * min(1, q * 4), full, col)
        ov = self.overlay(); self.motes.draw(ImageDraw.Draw(ov), t)
        im.paste(ov, (0, 0), ov)
        return im


def _font(name):
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", name)


EXPLAINER_SCENES = {"mercy_grid": MercyGrid, "four_questions": FourQuestions, "three_after_death": ThreeAfterDeath, "seven_shade": SevenShade, "scale_of_words": ScaleOfWords, "last_third": LastThird, "birds_provision": BirdsProvision}
