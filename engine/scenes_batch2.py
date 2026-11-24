"""
Batch-2 explainer devices (Nov 2026): one continuous shot per video, beats from the script.
Same contract as scenes_explainer: set_timeline(), bt(name), frame(t) with t = shot time + 3.0.
Respect rules: stick figures only, nothing depicts Allah, angels or prophets; light is symbolic.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scenes import Scene, vgrad, to_img, radial, blur_mask, Motes, add_glow, ridge, Rain
from scenes_explainer import (POSES, pose_mix, draw_stick, ease, lerp, GOLD, INK, _font)

ARABIC = "Amiri-Regular.ttf"
LATIN = "Lora.ttf"


def walk_pose(ph, amt=1.0):
    s = math.sin(ph) * amt
    p = dict(POSES["stand"])
    p["th"] = (270 + 24 * s, 270 - 24 * s)
    p["sh"] = (p["th"][0] - 12 * max(0, -s), p["th"][1] - 12 * max(0, s))
    p["ua"] = (270 - 26 * s, 270 + 26 * s)
    p["fa"] = (p["ua"][0] + 14, p["ua"][1] + 14)
    p["hip"] = (0, 146 - 4 * abs(s))
    return p


class Stage(Scene):
    bokeh_n = 0
    camera = "static"
    text_y = 0.24
    text_zone = (0.165, 0.40)
    band = 0.0
    ambience = "night_room"

    def set_timeline(self, items):
        self.beats = getattr(self, "beats", {})
        for st, du, ln in items:
            b = ln.get("beat")
            if b and b not in self.beats:
                self.beats[b] = (st, du)

    def bt(self, name, default=1e9):
        return getattr(self, "beats", {}).get(name, (default, 0))[0]

    def font(self, name, size):
        return ImageFont.truetype(_font(name), int(size * self.u))

    def finish(self, im, glow, col=GOLD, blur=26, dust=None, t=0.0):
        gl = glow.filter(ImageFilter.GaussianBlur(blur * self.u))
        im = ImageChops.screen(im, Image.merge("RGB", [gl.point(lambda v, c=c: v * c // 255) for c in col]))
        if dust is not None:
            ov = self.overlay(); dust.draw(ImageDraw.Draw(ov), t)
            im.paste(ov, (0, 0), ov)
        return im

    def fig(self, im, x, ground, pose, s, col=(250, 232, 196), alpha=1.0, flip=False):
        if alpha <= 0:
            return
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw_stick(ImageDraw.Draw(layer), x, ground, pose, s=s * self.u, col=col + (255,), flip=flip)
        if alpha < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v, a=alpha: int(v * a)))
        im.paste(layer, (0, 0), layer)

    def floor(self, d, y, col=(14, 12, 16), line=(60, 52, 44)):
        d.rectangle([0, y, self.w, self.h], fill=col + (255,))
        d.line([(0, y), (self.w, y)], fill=line + (255,), width=max(2, int(3 * self.u)))


# ---------------------------------------------------------------- 1. anger
class AngerCalm(Stage):
    """Bukhari 6114. Beats: hook, wrestle, strong, calm, ayah, cta."""
    def build(self):
        w, h, u = self.w, self.h, self.u
        self.base = vgrad(w, h, [(0, (10, 8, 10)), (0.6, (26, 18, 18)), (1, (8, 7, 8))])
        self.gy = h * 0.84
        self.f_lab = self.font(LATIN, 34)
        self.dust = Motes(self.rng, 40, (0, h * 0.42, w, h), color=(255, 200, 160), r=(1.0 * u, 2.2 * u), rise=10)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        t_wr, t_st, t_calm = self.bt("wrestle"), self.bt("strong"), self.bt("calm")
        heat = ease((t - t_st) / 0.8) * (1 - ease((t - t_calm - 0.4) / 2.2))
        cool = ease((t - t_calm - 0.4) / 2.2)
        arr = self.base + (radial(w, h, w / 2, h * 0.68, 520 * u) * (30 + 60 * heat))[..., None] * np.array([1, 0.35, 0.2], np.float32)
        arr = arr + (radial(w, h, w / 2, h * 0.68, 520 * u) * 45 * cool)[..., None] * np.array([0.5, 0.75, 1.0], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        self.floor(d, self.gy)
        gy = self.gy
        # part 1: one man throws another (physical strength) - fades out when "strong" begins
        a1 = 1 - ease((t - t_st) / 0.6)
        if a1 > 0:
            k = ease((t - t_wr - 0.3) / 0.9)
            pa = dict(POSES["stand"]); pa["ua"] = (lerp(262, 340, k), lerp(278, 350, k)); pa["fa"] = (lerp(268, 350, k), lerp(272, 0, k)); pa["torso"] = lerp(90, 76, k)
            self.fig(im, w * 0.40, gy, pa, 1.15, col=(205, 196, 186), alpha=a1 * ease((t - 3.0) / 0.6))
            pb = pose_mix("stand", "sit_sad", k)
            self.fig(im, w * 0.58 + 60 * u * k, gy, pb, 1.15, col=(150, 140, 136), alpha=a1 * ease((t - 3.0) / 0.6), flip=True)
        # part 2: the one who controls himself
        a2 = ease((t - t_st) / 0.7)
        if a2 > 0:
            cx = w / 2
            tight = heat
            p = dict(POSES["stand"]); p["ua"] = (262 - 30 * tight, 278 + 30 * tight); p["fa"] = (268 + 30 * tight, 272 - 30 * tight)
            p["head"] = -12 * tight + 10 * cool
            if cool > 0:                                      # settles, breathes
                p["torso"] = 90 + 1.5 * math.sin(t * 1.2)
            if heat > 0.02:                                   # flickering flames around him
                for j in range(14):
                    ang = j / 14 * math.tau + t * 0.6
                    r0 = 150 * u; fl = (60 + 50 * math.sin(t * 9 + j * 1.7)) * u * heat
                    bx = cx + math.cos(ang) * r0 * 0.75; by = gy - 200 * u - math.sin(ang) * r0 * 1.35
                    tx = cx + math.cos(ang) * (r0 + fl) * 0.75; ty = gy - 200 * u - math.sin(ang) * (r0 + fl) * 1.35
                    if ty > gy - 6 * u or by > gy - 6 * u:
                        continue
                    nx, ny = -math.sin(ang) * 22 * u, -math.cos(ang) * 22 * u
                    d.polygon([(bx + nx, by + ny), (tx, ty), (bx - nx, by - ny)], fill=(255, 90 + int(60 * math.sin(j)), 40, int(170 * heat)))
                dg.ellipse([cx - 220 * u, gy - 470 * u, cx + 220 * u, gy + 20 * u], fill=int(170 * heat))
            if cool > 0:
                rr = (160 + 10 * math.sin(t * 1.4)) * u
                d.ellipse([cx - rr * 0.8, gy - 200 * u - rr * 1.3, cx + rr * 0.8, gy - 200 * u + rr * 1.3], outline=(190, 220, 255, int(120 * cool)), width=max(2, int(3 * u)))
            self.fig(im, cx, gy, p, 1.3, col=(250, int(lerp(200, 238, cool)), int(lerp(170, 236, cool))), alpha=a2)
            # anger gauge on the right
            gx, g0, g1 = w * 0.86, h * 0.50, h * 0.78
            d.rounded_rectangle([gx - 16 * u, g0, gx + 16 * u, g1], radius=int(16 * u), outline=(200, 190, 180, int(200 * a2)), width=max(2, int(3 * u)))
            lvl = 0.15 + 0.8 * heat
            col = (int(lerp(150, 255, heat)), int(lerp(200, 80, heat)), int(lerp(255, 50, heat)), int(230 * a2))
            d.rounded_rectangle([gx - 10 * u, g1 - (g1 - g0) * lvl, gx + 10 * u, g1 - 6 * u], radius=int(10 * u), fill=col)
            d.text((gx, g1 + 18 * u), "anger", font=self.f_lab, fill=(220, 210, 200, int(220 * a2)), anchor="ma")
        col = tuple(int(lerp(a, b, cool)) for a, b in zip((255, 110, 60), (170, 210, 255)))
        return self.finish(im, glow, col=col, dust=self.dust, t=t)


# ---------------------------------------------------------------- 2. charity
class CharityJar(Stage):
    """Muslim 2588. Beats: hook, give, same, forgive, humble, ayah, cta."""
    def build(self):
        w, h, u = self.w, self.h, self.u
        self.base = vgrad(w, h, [(0, (9, 9, 12)), (0.6, (22, 19, 16)), (1, (8, 8, 9))])
        self.gy = h * 0.84
        self.jx, self.jy0, self.jy1, self.jw = w * 0.24, h * 0.60, h * 0.84, 150 * u
        self.f_lab = self.font(LATIN, 34)
        rng = self.rng
        self.coins = [(rng.uniform(-0.8, 0.8), rng.uniform(0, 1), rng.uniform(0, 6.28)) for _ in range(60)]
        self.fly = [(rng.uniform(-30, 30) * u, rng.uniform(0.0, 0.9), rng.uniform(-40, 40) * u) for _ in range(9)]
        self.dust = Motes(rng, 40, (0, h * 0.42, w, h), color=(255, 220, 150), r=(1.0 * u, 2.2 * u), rise=6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tg, ts, tf, th_ = self.bt("give"), self.bt("same"), self.bt("forgive"), self.bt("humble")
        arr = self.base + (radial(w, h, w * 0.45, h * 0.70, 560 * u) * 40)[..., None] * np.array([1, 0.8, 0.5], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        self.floor(d, gy)
        # jar: level dips while giving, then is restored
        jx, jy0, jy1, jw = self.jx, self.jy0, self.jy1, self.jw
        dip = 0.10 * ease((t - tg - 0.3) / 1.2) * (1 - ease((t - ts) / 0.9))
        lvl = 0.72 - dip
        top = jy1 - (jy1 - jy0) * lvl
        d.rectangle([jx - jw + 8 * u, top, jx + jw - 8 * u, jy1 - 6 * u], fill=(170, 120, 40, 255))
        for cxr, cyr, ph in self.coins:
            cy = top + (jy1 - top) * cyr
            cx = jx + cxr * (jw - 30 * u)
            d.ellipse([cx - 22 * u, cy - 9 * u, cx + 22 * u, cy + 9 * u], fill=(240, 190, 80, 255), outline=(150, 100, 30, 255))
        d.rounded_rectangle([jx - jw, jy0, jx + jw, jy1], radius=int(28 * u), outline=(220, 228, 236, 200), width=max(3, int(5 * u)))
        d.rectangle([jx - jw * 0.7, jy0 - 26 * u, jx + jw * 0.7, jy0 + 4 * u], outline=(220, 228, 236, 200), width=max(3, int(5 * u)))
        d.text((jx, jy1 + 22 * u), "wealth", font=self.f_lab, fill=(230, 220, 200, 220), anchor="ma")
        if t > ts:                                            # "does not decrease": the level line glows
            k = ease((t - ts) / 0.8)
            d.line([(jx - jw - 30 * u, top), (jx + jw + 30 * u, top)], fill=GOLD + (int(255 * k),), width=max(2, int(4 * u)))
            dg.rounded_rectangle([jx - jw, top - 40 * u, jx + jw, jy1], radius=int(28 * u), fill=int(140 * k * (0.8 + 0.2 * math.sin(t * 3))))
        # giver and receiver
        giver_x, recv_x = w * 0.52, w * 0.80
        a = ease((t - 3.0) / 0.6)
        lift = 120 * u * ease((t - th_ - 1.2) / 1.4)
        bow = ease((t - th_) / 0.6) * (1 - ease((t - th_ - 1.1) / 0.6))
        ped_top = gy - lift
        if lift > 0:
            d.rectangle([giver_x - 110 * u, ped_top, giver_x + 110 * u, gy], fill=(150, 112, 50, 255))
            d.line([(giver_x - 110 * u, ped_top), (giver_x + 110 * u, ped_top)], fill=GOLD + (255,), width=max(2, int(4 * u)))
            dg.rectangle([giver_x - 120 * u, ped_top - 20 * u, giver_x + 120 * u, gy], fill=110)
        gp = dict(POSES["stand"])
        if t > tg and t < ts + 1.0:
            gp["ua"] = (330, 278); gp["fa"] = (350, 272)
        gp = {k_: (tuple(lerp(x, y, bow) for x, y in zip(v, POSES["kneel"][k_])) if isinstance(v, tuple) else lerp(v, POSES["kneel"][k_], bow)) for k_, v in gp.items()}
        if bow > 0:
            gp["torso"] = lerp(gp["torso"], 30, bow); gp["head"] = lerp(gp["head"], -30, bow)
        self.fig(im, giver_x, ped_top, gp, 1.15, alpha=a)
        rp = dict(POSES["stand"])
        self.fig(im, recv_x, gy, rp, 1.0, col=(200, 196, 190), alpha=a, flip=True)
        # coins flying from giver to receiver
        for dx, delay, dy in self.fly:
            q = (t - tg - 0.4 - delay) / 0.9
            if 0 < q < 1:
                x = lerp(giver_x + 70 * u, recv_x - 60 * u, q) + dx * 0.2
                y = lerp(ped_top - 190 * u, gy - 190 * u, q) - math.sin(math.pi * q) * 120 * u + dy * 0.2
                d.ellipse([x - 16 * u, y - 16 * u, x + 16 * u, y + 16 * u], fill=(245, 196, 90, 255))
                dg.ellipse([x - 30 * u, y - 30 * u, x + 30 * u, y + 30 * u], fill=160)
        # forgiving: honour as a gold ring of light around the giver
        fk = ease((t - tf - 0.3) / 0.8)
        if fk > 0:
            cy = ped_top - 330 * u
            rr = 46 * u * (1 + 0.05 * math.sin(t * 3))
            for j in range(8):
                an = j / 8 * math.tau + t * 0.4
                d.line([(giver_x + math.cos(an) * rr * 0.5, cy + math.sin(an) * rr * 0.5), (giver_x + math.cos(an) * rr * 1.3, cy + math.sin(an) * rr * 1.3)], fill=GOLD + (int(230 * fk),), width=max(2, int(4 * u)))
            d.ellipse([giver_x - 12 * u, cy - 12 * u, giver_x + 12 * u, cy + 12 * u], fill=(255, 236, 190, int(255 * fk)))
            dg.ellipse([giver_x - 2 * rr, cy - rr, giver_x + 2 * rr, cy + rr], fill=int(200 * fk))
            d.text((giver_x, cy - 70 * u), "honour", font=self.f_lab, fill=GOLD + (int(255 * fk),), anchor="ms")
        if lift > 0:
            k = min(1, lift / (120 * u))
            d.text((giver_x, gy + 26 * u), "raised", font=self.f_lab, fill=GOLD + (int(255 * k),), anchor="ma")
        return self.finish(im, glow, dust=self.dust, t=t)


# ---------------------------------------------------------------- 3. the believer's affair
class BelieverTwo(Stage):
    """Muslim 2999. Left: ease -> gratitude; right: hardship -> patience; both feed one 'khayr'.
    Beats: hook, ease, grateful, distress, patient, both, ayah, cta."""
    def build(self):
        w, h, u = self.w, self.h, self.u
        self.warm = vgrad(w, h, [(0, (60, 52, 70)), (0.55, (210, 150, 96)), (0.8, (250, 206, 140)), (1, (40, 30, 26))])
        self.cold = vgrad(w, h, [(0, (12, 16, 26)), (0.55, (40, 52, 70)), (0.8, (70, 82, 96)), (1, (12, 14, 18))])
        self.dark = vgrad(w, h, [(0, (10, 10, 14)), (0.6, (22, 22, 26)), (1, (9, 9, 11))])
        self.gy = h * 0.84
        self.rain = Rain(w // 2, h, self.rng, n=90, u=u)
        self.f_ar = self.font(ARABIC, 64); self.f_lab = self.font(LATIN, 34)
        self.dust = Motes(self.rng, 30, (0, h * 0.45, w, h), color=(255, 226, 170), r=(1.0 * u, 2.2 * u), rise=6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        te, tg, td, tp, tb = self.bt("ease"), self.bt("grateful"), self.bt("distress"), self.bt("patient"), self.bt("both")
        ke, kd = ease((t - te) / 1.0), ease((t - td) / 1.0)
        arr = self.dark.copy()
        L = arr[:, : w // 2]; R = arr[:, w // 2:]
        L[:] = L * (1 - ke) + self.warm[:, : w // 2] * ke
        R[:] = R * (1 - kd) + self.cold[:, w // 2:] * kd
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        self.floor(d, gy)
        d.line([(w / 2, h * 0.46), (w / 2, gy)], fill=(255, 255, 255, 40), width=max(2, int(2 * u)))
        if ke > 0:                                            # sun on the left
            d.ellipse([w * 0.12 - 50 * u, h * 0.52 - 50 * u, w * 0.12 + 50 * u, h * 0.52 + 50 * u], fill=(255, 236, 180, int(255 * ke)))
            dg.ellipse([w * 0.12 - 120 * u, h * 0.52 - 120 * u, w * 0.12 + 120 * u, h * 0.52 + 120 * u], fill=int(150 * ke))
        if kd > 0:                                            # cloud and rain on the right
            ov = Image.new("RGBA", (w // 2, h), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            self.rain.draw(od, t)
            ov.putalpha(ov.getchannel("A").point(lambda v, a=kd: int(v * a)))
            ov = ov.crop((0, int(h * 0.5), w // 2, int(gy)))
            im.paste(ov, (w // 2, int(h * 0.5)), ov); d = ImageDraw.Draw(im, "RGBA")
            for k in range(5):
                cx = w * 0.62 + k * 70 * u; cy = h * 0.50 + 10 * u * math.sin(k)
                d.ellipse([cx - 70 * u, cy - 40 * u, cx + 70 * u, cy + 40 * u], fill=(70, 76, 90, int(235 * kd)))
        # left figure: ease -> sujood of gratitude
        lx, rx = w * 0.27, w * 0.73
        sj = ease((t - tg - 0.2) / 0.9) * (1 - ease((t - tg - 2.6) / 0.8))
        p = pose_mix("look_up", "sujood", sj) if t > tg else pose_mix("stand", "look_up", ke * 0.6)
        self.fig(im, lx, gy, p, 1.05, alpha=ease((t - 3.0) / 0.6))
        # right figure: sad -> patient (sits upright, calm)
        pt = ease((t - tp - 0.2) / 1.0)
        p = pose_mix("sit_sad", "sit_up", pt) if t > td else pose_mix("stand", "stand", 0)
        self.fig(im, rx, gy, p, 1.05, col=(220, 226, 236), alpha=ease((t - 3.0) / 0.6), flip=True)
        # each response sends a light to the shared 'khayr'
        kx, ky = w / 2, h * 0.53
        got = 0
        for x0, t0 in ((lx, tg + 1.0), (rx, tp + 1.2)):
            q = (t - t0) / 1.2
            if q <= 0:
                continue
            got += 1
            if q < 1:
                e = ease(q); x = lerp(x0, kx, e); y = lerp(gy - 180 * u, ky, e) - math.sin(math.pi * q) * 60 * u
                d.ellipse([x - 16 * u, y - 16 * u, x + 16 * u, y + 16 * u], fill=(255, 236, 190, 255))
                dg.ellipse([x - 40 * u, y - 40 * u, x + 40 * u, y + 40 * u], fill=200)
        if got:
            k = ease((t - (tg + 2.2)) / 0.6) if got == 1 else 1.0
            pulse = 1 + (0.15 * math.sin((t - tb) * 4) if t > tb else 0)
            R = (54 + 14 * (got - 1)) * u * pulse
            d.ellipse([kx - R, ky - R, kx + R, ky + R], fill=(40, 30, 16, int(230 * k)), outline=GOLD + (int(255 * k),), width=max(3, int(5 * u)))
            d.text((kx, ky + 4 * u), "خَيْر", font=self.f_ar, fill=GOLD + (int(255 * k),), anchor="mm", direction="rtl", language="ar")
            d.text((kx, ky + R + 16 * u), "good", font=self.f_lab, fill=GOLD + (int(255 * k),), anchor="ma")
            dg.ellipse([kx - 2.2 * R, ky - 2.2 * R, kx + 2.2 * R, ky + 2.2 * R], fill=int((140 + 50 * (got - 1)) * k))
        if ke > 0:
            d.text((lx, gy + 26 * u), "ease, then gratitude" if t > tg else "ease", font=self.f_lab, fill=(250, 226, 180, int(230 * ke)), anchor="ma")
        if kd > 0:
            d.text((rx, gy + 26 * u), "hardship, then patience" if t > tp else "hardship", font=self.f_lab, fill=(200, 214, 236, int(230 * kd)), anchor="ma")
        return self.finish(im, glow, dust=self.dust, t=t)


# ---------------------------------------------------------------- 4. mother
class MotherRank(Stage):
    """Bukhari 5971: four equal pillars lit in order: mother, mother, mother, father.
    Beats: hook, ask, m1, m2, m3, father, ayah, cta."""
    def build(self):
        w, h, u = self.w, self.h, self.u
        self.base = vgrad(w, h, [(0, (8, 8, 14)), (0.6, (24, 20, 26)), (1, (8, 8, 10))])
        self.gy = h * 0.84
        self.f_lab = self.font(LATIN, 34); self.f_num = self.font(LATIN, 44)
        self.xs = [w * (0.17 + 0.22 * k) for k in range(4)]
        self.dust = Motes(self.rng, 50, (0, h * 0.42, w, h), color=(255, 220, 190), r=(1.0 * u, 2.4 * u), rise=10)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tm = [self.bt("m1"), self.bt("m2"), self.bt("m3"), self.bt("father")]
        arr = self.base + (radial(w, h, w / 2, h * 0.84, 600 * u) * 30)[..., None] * np.array([1, 0.8, 0.7], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        self.floor(d, gy)
        top = h * 0.48
        labels = ["mother", "mother", "mother", "father"]
        for k, (x, t0) in enumerate(zip(self.xs, tm)):
            k_ = ease((t - t0) / 0.7)
            pw = 70 * u
            d.rounded_rectangle([x - pw, top, x + pw, gy], radius=int(18 * u), outline=(120, 110, 100, 120), width=max(2, int(3 * u)))
            if k_ > 0:
                col = (255, 214, 150) if k < 3 else (220, 210, 190)
                fy = gy - (gy - top) * k_
                d.rounded_rectangle([x - pw, fy, x + pw, gy], radius=int(18 * u), fill=col + (int(70 + 120 * k_),))
                dg.rounded_rectangle([x - pw, fy, x + pw, gy], radius=int(18 * u), fill=int((190 if k < 3 else 120) * k_))
                d.text((x, top - 66 * u), str(k + 1), font=self.f_num, fill=GOLD + (int(255 * k_),), anchor="ms")
                d.text((x, gy + 24 * u), labels[k], font=self.f_lab, fill=(col if k < 3 else (230, 220, 200)) + (int(255 * k_),), anchor="ma")
        # a small mother-and-child silhouette walks in at the start, then stands to the side
        a = ease((t - 3.0) / 0.8) * (1 - ease((t - tm[0] + 0.6) / 0.8))
        if a > 0:
            cx = w / 2
            p = dict(POSES["stand"]); p["ua"] = (300, 278); p["fa"] = (320, 272)
            self.fig(im, cx - 30 * u, gy, p, 1.3, alpha=a)
            c = dict(POSES["stand"]); c["ua"] = (120, 278); c["fa"] = (130, 272)
            self.fig(im, cx + 80 * u, gy, c, 0.62, alpha=a)
            dg.ellipse([cx - 200 * u, gy - 420 * u, cx + 200 * u, gy + 10 * u], fill=int(90 * a))
        return self.finish(im, glow, col=(255, 206, 150), dust=self.dust, t=t)


# ---------------------------------------------------------------- 5. river at the door
class RiverFive(Stage):
    """Bukhari 528. Beats: hook, river, dirt, five, clean, prayers, ayah, cta."""
    NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    ambience = "sea"

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (12, 20, 40)), (0.55, (40, 66, 96)), (0.68, (120, 150, 160)), (1, (14, 22, 30))])
        self.ry0, self.ry1 = h * 0.74, h * 0.86
        self.gy = h * 0.74
        self.f_lab = self.font(LATIN, 32)
        self.spots = [(rng.uniform(-1, 1), rng.uniform(0.05, 0.95), rng.uniform(5, 10)) for _ in range(26)]
        self.waves = [(rng.uniform(0, w), rng.uniform(self.ry0 + 10 * u, self.ry1 - 10 * u), rng.uniform(40, 110) * u, rng.uniform(60, 140)) for _ in range(40)]
        self.dust = Motes(rng, 30, (0, h * 0.42, w, h * 0.74), color=(220, 240, 255), r=(1.0 * u, 2.0 * u), rise=5)

    def dips(self, t):
        """Number of completed dips and current dip depth (0..1)."""
        t5 = self.bt("five")
        if t < t5:
            return 0, 0.0
        q = (t - t5 - 0.2) / 0.62
        n = int(max(0, min(5, math.floor(q + 1e-6))))
        if q >= 5:
            return 5, 0.0
        f = q - math.floor(q) if q > 0 else 0
        return n, math.sin(math.pi * f) if q > 0 else 0.0

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tr, tdirt, tc, tp = self.bt("river"), self.bt("dirt"), self.bt("clean"), self.bt("prayers")
        im = to_img(self.base); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        # house with a door on the left bank
        hx0, hx1, hy0 = w * 0.02, w * 0.34, h * 0.585
        d.rectangle([hx0, hy0, hx1, self.gy], fill=(28, 26, 34, 255))
        d.polygon([(hx0 - 20 * u, hy0), ((hx0 + hx1) / 2, hy0 - 110 * u), (hx1 + 20 * u, hy0)], fill=(22, 20, 28, 255))
        d.rectangle([w * 0.13, h * 0.64, w * 0.24, self.gy], fill=(255, 200, 120, 230))
        dg.rectangle([w * 0.13, h * 0.64, w * 0.24, self.gy], fill=120)
        d.rectangle([hx1, self.gy, w, self.gy + 4 * u], fill=(30, 40, 46, 255))
        # river
        rk = ease((t - tr) / 1.0)
        d.rectangle([0, self.ry0, w, self.ry1], fill=(30, 70, 110, 255))
        for x, y, L, sp in self.waves:
            xx = (x + sp * t * u) % (w + 200 * u) - 100 * u
            d.line([(xx, y), (xx + L, y)], fill=(170, 210, 240, int(60 + 120 * rk)), width=max(2, int(3 * u)))
        d.rectangle([0, self.ry1, w, h], fill=(12, 16, 20, 255))
        # the man: stands on the bank, dips into the river five times
        n, dip = self.dips(t)
        fx = w * 0.62
        ground = self.gy + 110 * u * dip
        p = pose_mix("stand", "kneel", dip)
        a = ease((t - 3.0) / 0.6)
        clean = ease((t - tc) / 0.8)
        self.fig(im, fx, ground, p, 1.15, alpha=a)
        # dirt marks fade with each dip
        show = ease((t - tdirt) / 0.6) * (1 - n / 5) if t < tc + 1 else 0
        if show > 0:
            for sx, sy, r in self.spots:
                x = fx + sx * 24 * u; y = ground - 40 * u - sy * 230 * u
                d.ellipse([x - r * u, y - r * u, x + r * u, y + r * u], fill=(70, 52, 40, int(230 * show)))
        if dip > 0.2:                                         # splash
            for j in range(10):
                ang = math.pi * (0.1 + 0.8 * j / 9)
                rr = 80 * u * dip
                x = fx + math.cos(ang) * rr * 1.6; y = self.ry0 - math.sin(ang) * rr
                d.ellipse([x - 6 * u, y - 6 * u, x + 6 * u, y + 6 * u], fill=(210, 236, 255, int(220 * dip)))
        if clean > 0:
            dg.ellipse([fx - 170 * u, self.gy - 420 * u, fx + 170 * u, self.gy + 20 * u], fill=int(150 * clean))
        # counter: five marks, named as the five prayers on the "prayers" beat
        names = ease((t - tp) / 0.8)
        for k in range(5):
            x = w * (0.14 + 0.18 * k); y = h * 0.455
            on = k < n
            r = 22 * u
            d.ellipse([x - r, y - r, x + r, y + r], outline=(220, 236, 255, 180), width=max(2, int(3 * u)),
                      fill=(GOLD + (255,)) if on else None)
            if on:
                dg.ellipse([x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r], fill=170)
            if names > 0:
                d.text((x, y + 36 * u), self.NAMES[k], font=self.f_lab, fill=GOLD + (int(255 * names),), anchor="ma")
        return self.finish(im, glow, col=(255, 220, 160), dust=self.dust, t=t)


# ---------------------------------------------------------------- 6. words
class WordsRecord(Stage):
    """Bukhari 6018 + Qaf 50:18. Good words rise as gold; harmful ones dissolve unsaid; all speech is recorded.
    Beats: hook, good, silent, record, ayah, cta."""
    GOOD = ["salam", "thank you", "SubhanAllah", "kind word", "truth", "dua"]

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (9, 10, 14)), (0.6, (22, 22, 30)), (1, (8, 8, 10))])
        self.gy = h * 0.84
        self.f_w = self.font(LATIN, 34); self.f_lab = self.font(LATIN, 34)
        self.shards = [(rng.uniform(0, 6.28), rng.uniform(0.6, 1.0)) for _ in range(8)]
        self.dust = Motes(rng, 40, (0, h * 0.42, w, h), color=(255, 226, 170), r=(1.0 * u, 2.2 * u), rise=6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tg, ts, tr = self.bt("good"), self.bt("silent"), self.bt("record")
        arr = self.base + (radial(w, h, w * 0.3, h * 0.70, 480 * u) * 34)[..., None] * np.array([1, 0.85, 0.6], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        self.floor(d, gy)
        fx = w * 0.26
        self.fig(im, fx, gy, POSES["stand"], 1.25, alpha=ease((t - 3.0) / 0.6))
        mx, my = fx + 34 * u, gy - 316 * u                    # mouth
        # the record: an open book on a stand at the right
        bk = ease((t - tr) / 0.8)
        bx, by = w * 0.74, h * 0.66
        if bk > 0:
            d.polygon([(bx - 150 * u, by), (bx, by + 26 * u), (bx, by - 120 * u), (bx - 150 * u, by - 140 * u)], fill=(236, 226, 204, int(255 * bk)))
            d.polygon([(bx + 150 * u, by), (bx, by + 26 * u), (bx, by - 120 * u), (bx + 150 * u, by - 140 * u)], fill=(226, 214, 190, int(255 * bk)))
            for k in range(5):
                yy = by - 110 * u + k * 22 * u
                d.line([(bx - 130 * u, yy - 18 * u), (bx - 20 * u, yy + 4 * u)], fill=(120, 100, 70, int(160 * bk)), width=max(1, int(3 * u)))
                d.line([(bx + 20 * u, yy + 4 * u), (bx + 130 * u, yy - 18 * u)], fill=(120, 100, 70, int(160 * bk)), width=max(1, int(3 * u)))
            d.line([(bx, by + 26 * u), (bx, gy)], fill=(120, 96, 60, int(255 * bk)), width=int(10 * u))
            dg.polygon([(bx - 170 * u, by + 10 * u), (bx + 170 * u, by + 10 * u), (bx + 170 * u, by - 160 * u), (bx - 170 * u, by - 160 * u)], fill=int(110 * bk))
        # good words float up and right (toward the book once it appears)
        for k, word in enumerate(self.GOOD):
            t0 = tg + 0.3 + k * 0.55
            if t < t0:
                continue
            q = t - t0
            if bk > 0 and t > tr:
                e = ease((t - max(t0, tr)) / 1.6)
            else:
                e = 0
            ee = ease(q / 1.2)
            x0 = lerp(mx + 30 * u, mx + 110 * u + (k % 2) * 250 * u, ee) + 8 * u * math.sin(t * 1.3 + k)
            y0 = lerp(my, my - 80 * u - k * 62 * u, ee) + 6 * u * math.sin(t * 1.7 + k)
            x = lerp(min(x0, w * 0.86), bx, e); y = lerp(y0, by - 70 * u, e)
            a = min(1, q / 0.4) * (1 - e)
            if a <= 0.02:
                continue
            d.text((x, y), word, font=self.f_w, fill=GOLD + (int(255 * a),), anchor="lm")
            tw = self.f_w.getlength(word)
            dg.rounded_rectangle([x - 10 * u, y - 26 * u, x + tw + 10 * u, y + 26 * u], radius=int(20 * u), fill=int(110 * a))
        # harmful words: sharp shards that form at the mouth and break apart before leaving
        if ts < t < ts + 3.2:
            q = t - ts
            form = ease(q / 0.6); brk = ease((q - 1.0) / 1.0)
            for ang, sz in self.shards:
                r = (40 + 160 * brk) * u
                x = mx + 70 * u + math.cos(ang) * r; y = my + math.sin(ang) * r * 0.6
                s = 22 * u * sz * (1 - brk * 0.6)
                d.polygon([(x - s, y), (x, y - s * 1.6), (x + s, y), (x, y + s * 0.6)], fill=(150, 150, 160, int(220 * form * (1 - brk))))
            d.text((mx + 70 * u, my - 90 * u), "or stay silent", font=self.f_lab, fill=(220, 220, 230, int(230 * form * (1 - ease((q - 2.4) / 0.6)))), anchor="ms")
        return self.finish(im, glow, dust=self.dust, t=t)


# ---------------------------------------------------------------- 7. traveler
class TravelerRoad(Stage):
    """Bukhari 6416. A traveler walks a long road toward the horizon; the world scrolls past.
    Beats: hook, stranger, traveler, evening, morning, ayah, cta."""
    ambience = "wind"
    band = 0.6

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.eve = vgrad(w, h, [(0, (30, 26, 60)), (0.45, (200, 110, 90)), (0.62, (255, 190, 120)), (1, (20, 16, 20))])
        self.morn = vgrad(w, h, [(0, (60, 110, 170)), (0.45, (150, 190, 220)), (0.62, (240, 226, 196)), (1, (24, 26, 22))])
        self.hor = h * 0.62
        self.far = ridge(w, rng, self.hor - 20 * u, 24 * u)
        yy = np.arange(h, dtype=np.float32)[:, None]
        self.m_far = np.clip((yy - self.far[None, :]) / 1.5 + 0.5, 0, 1)[..., None]
        self.trees = [(rng.choice([-1, 1]), rng.uniform(0, 1)) for _ in range(6)]
        self.f_lab = self.font(LATIN, 34)
        self.dust = Motes(rng, 40, (0, h * 0.5, w, h), color=(255, 226, 180), r=(1.0 * u, 2.4 * u), rise=4, sway=30 * u)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tm = self.bt("morning")
        k = ease((t - tm) / 2.0)
        arr = self.eve * (1 - k) + self.morn * k
        sy = lerp(self.hor - 30 * u, self.hor - 260 * u, k)
        arr = arr + (radial(w, h, w / 2, sy, 260 * u) * 80)[..., None] * np.array([1, 0.85, 0.6], np.float32)
        land = np.array([34, 26, 30], np.float32) * (1 - k) + np.array([40, 56, 40], np.float32) * k
        arr = arr * (1 - self.m_far) + (land * 1.4) * self.m_far
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        d.ellipse([w / 2 - 44 * u, sy - 44 * u, w / 2 + 44 * u, sy + 44 * u], fill=(255, 238, 200, 255))
        # ground and road in perspective
        hor = self.hor
        d.rectangle([0, hor, w, h], fill=tuple(int(c) for c in land) + (255,))
        d.polygon([(w / 2 - 8 * u, hor), (w / 2 + 8 * u, hor), (w * 0.86, h), (w * 0.14, h)], fill=(70, 62, 60, 255))
        speed = 0.35
        for j in range(14):                                   # centre dashes moving toward the viewer
            z = ((j / 14) + t * speed) % 1.0
            y = hor + (h - hor) * z ** 2.2; y2 = hor + (h - hor) * min(1, (z + 0.025)) ** 2.2
            d.line([(w / 2, y), (w / 2, y2)], fill=(230, 220, 190, 200), width=max(1, int(10 * u * z)))
        for side, ph in self.trees:                           # roadside trees passing by
            z = (ph + t * speed * 0.8) % 1.0
            if z > 0.78:
                continue
            y = hor + (h - hor) * z ** 2.2
            x = w / 2 + side * (20 * u + (w * 0.45) * z ** 2.2 * 1.25)
            s = 0.15 + 2.6 * z ** 2.2
            col = tuple(int(c * 0.6) for c in land) + (255,)
            d.line([(x, y), (x, y - 160 * u * s)], fill=col, width=max(2, int(12 * u * s)))
            d.ellipse([x - 70 * u * s, y - 250 * u * s, x + 70 * u * s, y - 130 * u * s], fill=col)
        # the traveler, walking away from us toward the horizon (seen from behind)
        ts = self.bt("stranger")
        a = ease((t - 3.0) / 0.6)
        tx, ty = w / 2 + 70 * u, h * 0.90
        p = walk_pose(t * 5.0)
        self.fig(im, tx, ty, p, 1.15, col=(250, 232, 200), alpha=a)
        # bag
        d.rounded_rectangle([tx - 26 * u, ty - 300 * u, tx + 18 * u, ty - 230 * u], radius=int(12 * u), fill=(150, 110, 70, int(255 * a)))
        dg.ellipse([tx - 180 * u, ty - 420 * u, tx + 180 * u, ty + 10 * u], fill=int(60 * a))
        if t > ts:
            kk = ease((t - ts) / 0.8)
            d.text((tx, ty + 18 * u), "passing through", font=self.f_lab, fill=(250, 236, 210, int(220 * kk)), anchor="ma")
        return self.finish(im, glow, col=(255, 220, 170), dust=self.dust, t=t)


# ---------------------------------------------------------------- 8. three darknesses
class ThreeDarks(Stage):
    """Al-Anbya 21:87-88. Night, the sea, and the belly of the fish (Ibn Kathir from Ibn Mas'ud).
    A small light (the du'a) rises through all three to the surface and the dawn.
    Beats: hook, night, sea, fish, dua, answered, ayah, cta."""
    ambience = "sea"
    band = 1.3

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (4, 6, 14)), (0.44, (10, 16, 34)), (0.46, (8, 22, 40)), (0.75, (3, 8, 16)), (1, (1, 2, 5))])
        self.dawn = vgrad(w, h, [(0, (40, 50, 96)), (0.30, (220, 150, 120)), (0.44, (255, 200, 150)), (0.46, (40, 80, 110)), (0.75, (10, 26, 44)), (1, (3, 6, 12))])
        self.sea_y = h * 0.45
        self.stars = [(rng.uniform(0, w), rng.uniform(0, h * 0.42), rng.uniform(0.6, 2.0) * u, rng.uniform(0, 6.28)) for _ in range(150)]
        self.bub = Motes(rng, 50, (0, h * 0.46, w, h), color=(170, 210, 240), r=(1.5 * u, 3.5 * u), rise=30, sway=10 * u)
        self.f_lab = self.font(LATIN, 34)
        self.fx, self.fy = w * 0.5, h * 0.74

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tn, ts, tf, td, ta = self.bt("night"), self.bt("sea"), self.bt("fish"), self.bt("dua"), self.bt("answered")
        dawn = ease((t - ta - 0.8) / 2.5)
        arr = self.base * (1 - dawn) + self.dawn * dawn
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        for x, y, r, ph in self.stars:
            a = int(200 * (1 - dawn) * (0.6 + 0.4 * math.sin(t * 1.5 + ph)))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 236, 255, a))
        d.ellipse([w * 0.80 - 30 * u, h * 0.12 - 30 * u, w * 0.80 + 30 * u, h * 0.12 + 30 * u], fill=(240, 236, 220, int(200 * (1 - dawn))))
        # waves at the surface
        for k in range(6):
            yy = self.sea_y + k * 8 * u
            pts = [(x, yy + 6 * u * math.sin(x / (60 * u) + t * 1.2 + k)) for x in range(0, w + 20, 20)]
            d.line(pts, fill=(120, 170, 210, 80 - k * 10), width=max(1, int(2 * u)))
        # labels for the three darknesses
        for lab, (x, y), t0 in (("darkness of the night", (w * 0.5, h * 0.42), tn), ("darkness of the sea", (w * 0.5, h * 0.55), ts), ("darkness inside the fish", (w * 0.5, h * 0.88), tf)):
            k = ease((t - t0) / 0.7) * (1 - ease((t - td) / 0.8))
            if k > 0:
                d.text((x, y), lab, font=self.f_lab, fill=(190, 206, 230, int(230 * k)), anchor="ms")
        # the great fish: a dark silhouette gliding slowly
        fk = ease((t - tf + 0.6) / 1.4)
        fx = self.fx + 30 * u * math.sin(t * 0.3); fy = self.fy + 10 * u * math.sin(t * 0.5)
        if fk > 0:
            col = (20, 36, 56, int(255 * fk))   # a little lighter than the deep water so the shape reads
            d.ellipse([fx - 330 * u, fy - 110 * u, fx + 270 * u, fy + 110 * u], fill=col)
            d.polygon([(fx + 240 * u, fy), (fx + 420 * u, fy - 120 * u), (fx + 390 * u, fy), (fx + 420 * u, fy + 120 * u)], fill=col)
            d.polygon([(fx - 40 * u, fy - 100 * u), (fx + 40 * u, fy - 200 * u), (fx + 80 * u, fy - 96 * u)], fill=col)
            d.ellipse([fx - 300 * u, fy - 110 * u, fx + 270 * u, fy + 110 * u], outline=(90, 140, 180, int(170 * fk)), width=max(2, int(3 * u)))
        # the du'a: a small light inside, rising after it is answered
        lk = ease((t - td) / 0.8)
        if lk > 0:
            q = ease((t - ta) / 3.0)
            x = lerp(fx - 40 * u, w / 2, q); y = lerp(fy, h * 0.38, q)
            r = (10 + 6 * math.sin(t * 4)) * u * (1 + q)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 200, int(255 * lk)))
            dg.ellipse([x - 5 * r, y - 5 * r, x + 5 * r, y + 5 * r], fill=int(230 * lk))
            if q > 0:
                for j in range(1, 12):
                    qq = max(0, q - j * 0.025); xx = lerp(fx - 40 * u, w / 2, qq); yy = lerp(fy, h * 0.38, qq)
                    rr = (8 - j * 0.5) * u
                    d.ellipse([xx - rr, yy - rr, xx + rr, yy + rr], fill=(255, 236, 190, int(160 * (1 - j / 12))))
        ov = self.overlay(); self.bub.draw(ImageDraw.Draw(ov), t, glow=False)
        im.paste(ov, (0, 0), ov)
        return self.finish(im, glow, col=(255, 222, 170))


# ---------------------------------------------------------------- 9. nearer
class NearerPath(Stage):
    """Bukhari 7405 (hadith qudsi). A man takes small steps on a dark path; light along the path answers
    each step with more. The light is symbolic of mercy, not a depiction.
    Beats: hook, expect, remember, span, cubit, walk, ayah, cta."""
    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (6, 8, 16)), (0.6, (16, 18, 30)), (1, (6, 6, 10))])
        self.f_lab = self.font(LATIN, 34)
        n = 40
        self.path = [(lerp(w * 0.16, w * 0.80, (k / (n - 1)) ** 0.9), lerp(h * 0.86, h * 0.52, (k / (n - 1)) ** 1.1)) for k in range(n)]
        self.stars = [(rng.uniform(0, w), rng.uniform(0, h * 0.5), rng.uniform(0.6, 1.8) * u, rng.uniform(0, 6.28)) for _ in range(120)]
        self.dust = Motes(rng, 40, (0, h * 0.42, w, h), color=(255, 226, 170), r=(1.0 * u, 2.4 * u), rise=6)

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tsp, tcu, twk, tre = self.bt("span"), self.bt("cubit"), self.bt("walk"), self.bt("remember")
        im = to_img(self.base); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        for x, y, r, ph in self.stars:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 226, 255, int(160 * (0.6 + 0.4 * math.sin(t + ph)))))
        n = len(self.path)
        # how far the man has come (his steps are small) and how much light has come toward him
        man = 0.02 + 0.03 * ease((t - tsp) / 0.8) + 0.04 * ease((t - tcu) / 0.8) + 0.06 * ease((t - twk) / 2.0)
        light = 0.0 + 0.10 * ease((t - tre) / 1.0) + 0.16 * ease((t - tsp - 0.6) / 0.6) + 0.22 * ease((t - tcu - 0.6) / 0.6) + 0.52 * ease((t - twk - 0.4) / 0.9)
        light = min(light, 1 - man)
        for k, (x, y) in enumerate(self.path):
            f = k / (n - 1)
            s = lerp(26, 10, f) * u
            lit = f >= 1 - light or f <= man
            col = (255, 220, 150, 255) if lit else (60, 60, 80, 200)
            d.ellipse([x - s, y - s * 0.4, x + s, y + s * 0.4], fill=col)
            if lit and f >= 1 - light:
                dg.ellipse([x - 2.4 * s, y - s, x + 2.4 * s, y + s], fill=150)
        ex, ey = self.path[-1]
        dg.ellipse([ex - 300 * u, ey - 50 * u, ex + 300 * u, ey + 50 * u], fill=int(90 + 80 * ease((t - twk) / 1.0)))   # soft horizon glow, not an orb
        # leading edge of the light, moving toward the man
        if light > 0.01:
            i = int((1 - light) * (n - 1)); x, y = self.path[max(0, min(n - 1, i))]
            dg.ellipse([x - 80 * u, y - 60 * u, x + 80 * u, y + 60 * u], fill=230)
        # the man
        i = man * (n - 1); i0 = int(i); fr = i - i0
        x0, y0 = self.path[i0]; x1, y1 = self.path[min(n - 1, i0 + 1)]
        mx, my = lerp(x0, x1, fr), lerp(y0, y1, fr)
        moving = (tsp < t < tsp + 0.8) or (tcu < t < tcu + 0.8) or (twk < t < twk + 2.0)
        p = walk_pose(t * 6, 1.0 if moving else 0.0)
        self.fig(im, mx, my, p, 1.0, alpha=ease((t - 3.0) / 0.6))
        # measure labels from the text
        for lab, t0 in (("a hand-span", tsp), ("a forearm's length", tcu), ("walking", twk)):
            k = ease((t - t0) / 0.5) * (1 - ease((t - t0 - 2.4) / 0.5))
            if k > 0:
                d.text((mx, my + 30 * u), lab, font=self.f_lab, fill=(240, 230, 210, int(230 * k)), anchor="ma")
        return self.finish(im, glow, dust=self.dust, t=t)


# ---------------------------------------------------------------- 10. a gamer's room (games ruling)
class GamerRoom(Stage):
    """Night room: rain on the window, a young man gaming in front of a TV. The TV turns into a checklist
    (the scholar's forbidden list, then the game's official rating descriptors), switches off,
    and he gets up to pray. No game footage or logos: the screen shows a generic neon city.
    Beats: hook, scholar, rule, list, esrb, verdict, prayer, cta."""
    ambience = "rain"

    def build(self):
        w, h, u, rng = self.w, self.h, self.u, self.rng
        self.base = vgrad(w, h, [(0, (8, 9, 14)), (0.55, (16, 16, 24)), (0.84, (20, 18, 24)), (1, (7, 7, 9))])
        self.gy = h * 0.84
        self.win = (w * 0.04, h * 0.45, w * 0.36, h * 0.69)
        self.tv = (w * 0.47, h * 0.505, w * 0.95, h * 0.665)
        x0, y0, x1, y1 = self.win
        sky = vgrad(int(x1 - x0), int(y1 - y0), [(0, (14, 18, 38)), (1, (40, 36, 60))])
        win = to_img(sky); d = ImageDraw.Draw(win, "RGBA")
        ww, wh = win.size
        x = 0
        while x < ww:                                       # distant towers with lit windows
            bw = rng.uniform(26, 60) * u; bh = rng.uniform(0.25, 0.75) * wh
            d.rectangle([x, wh - bh, x + bw, wh], fill=(12, 12, 22, 255))
            for yy in np.arange(wh - bh + 8 * u, wh - 6 * u, 14 * u):
                for xx in np.arange(x + 5 * u, x + bw - 6 * u, 11 * u):
                    if rng.random() < 0.35:
                        d.rectangle([xx, yy, xx + 4 * u, yy + 6 * u], fill=(255, 200, 120, int(rng.uniform(120, 230))))
            x += bw + rng.uniform(2, 10) * u
        mx = ww * 0.72                                      # a minaret among the towers
        d.rectangle([mx - 8 * u, wh * 0.18, mx + 8 * u, wh], fill=(12, 12, 22, 255))
        d.polygon([(mx - 10 * u, wh * 0.18), (mx, wh * 0.06), (mx + 10 * u, wh * 0.18)], fill=(12, 12, 22, 255))
        d.ellipse([mx - 4 * u, wh * 0.03, mx + 4 * u, wh * 0.06], fill=(150, 230, 170, 255))
        self.win_img = win
        self.minaret = (x0 + mx, y0 + wh * 0.10)
        self.rain = Rain(int(x1 - x0), int(y1 - y0), rng, n=60, alpha=(40, 90), slant=0.08, u=u)
        self.drops = [(rng.uniform(0, x1 - x0), rng.uniform(0, y1 - y0), rng.uniform(2, 5) * u, rng.uniform(0.2, 1.0)) for _ in range(40)]
        tx0, ty0, tx1, ty1 = self.tv
        self.cars = [(rng.uniform(0, 1), rng.uniform(0.55, 0.95), rng.uniform(0.15, 0.45), [(255, 80, 120), (80, 200, 255), (255, 220, 120)][int(rng.integers(3))]) for _ in range(26)]
        self.blds = [(rng.uniform(0, 1), rng.uniform(0.25, 0.55), rng.uniform(0.04, 0.09), [(255, 60, 160), (60, 200, 255), (160, 90, 255)][int(rng.integers(3))]) for _ in range(14)]
        self.f_head = self.font(LATIN, 34); self.f_row = self.font(LATIN, 32)
        self.dust = Motes(rng, 30, (0, h * 0.45, w, h), color=(200, 210, 255), r=(0.8 * u, 1.8 * u), rise=4)

    def screen(self, t, on):
        """Generic neon city on the TV (no real game content)."""
        tx0, ty0, tx1, ty1 = self.tv
        sw, sh = int(tx1 - tx0), int(ty1 - ty0)
        a = vgrad(sw, sh, [(0, (20, 10, 40)), (0.6, (60, 20, 70)), (1, (10, 8, 20))])
        im = to_img(a); d = ImageDraw.Draw(im, "RGBA")
        for bx, bh, bw, col in self.blds:
            x = ((bx - t * 0.03) % 1.1 - 0.05) * sw
            d.rectangle([x, sh * (1 - bh) - sh * 0.15, x + bw * sw, sh * 0.85], fill=(14, 10, 26, 255), outline=col + (200,), width=max(1, int(2 * self.u)))
        d.rectangle([0, sh * 0.85, sw, sh], fill=(18, 14, 26, 255))
        for cx, cy, sp, col in self.cars:
            x = ((cx + t * sp) % 1.2 - 0.1) * sw; y = sh * (0.86 + 0.12 * (cy - 0.55) / 0.4)
            d.line([(x - 40 * self.u, y), (x, y)], fill=col + (220,), width=max(2, int(3 * self.u)))
        return im

    def frame(self, t):
        w, h, u = self.w, self.h, self.u
        tl, te, tv, tp = self.bt("list"), self.bt("esrb"), self.bt("verdict"), self.bt("prayer")
        off = ease((t - tv - 0.6) / 0.5)
        flick = 0.85 + 0.15 * math.sin(t * 7.3) * math.sin(t * 3.1)
        tvc = np.array([140, 90, 230], np.float32) * (1 - off)
        arr = self.base + (radial(w, h, w * 0.70, h * 0.62, 620 * u) * 70 * flick)[..., None] * (tvc / 255)
        arr = arr + (radial(w, h, w * 0.20, h * 0.57, 340 * u) * 26)[..., None] * np.array([0.6, 0.7, 1.0], np.float32)
        im = to_img(arr); d = ImageDraw.Draw(im, "RGBA")
        glow = Image.new("L", (w, h), 0); dg = ImageDraw.Draw(glow)
        gy = self.gy
        self.floor(d, gy, col=(16, 14, 20), line=(46, 42, 54))
        # window with rain
        x0, y0, x1, y1 = self.win
        wi = self.win_img.copy(); wd = ImageDraw.Draw(wi, "RGBA")
        self.rain.draw(wd, t)
        for dx, dy, r, sp in self.drops:
            yy = (dy + t * 40 * u * sp) % (y1 - y0)
            wd.ellipse([dx - r, yy - r, dx + r, yy + r * 1.4], fill=(200, 210, 240, 90))
        im.paste(wi, (int(x0), int(y0)))
        d.rectangle([x0, y0, x1, y1], outline=(40, 38, 48, 255), width=int(10 * u))
        d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=(40, 38, 48, 255), width=int(8 * u))
        mx_, my_ = self.minaret
        dg.ellipse([mx_ - 30 * u, my_ - 30 * u, mx_ + 30 * u, my_ + 30 * u], fill=int(120 + 100 * ease((t - tp) / 1.0)))
        # TV
        tx0, ty0, tx1, ty1 = self.tv
        d.rectangle([tx0 - 12 * u, ty0 - 12 * u, tx1 + 12 * u, ty1 + 12 * u], fill=(10, 10, 12, 255))
        d.rectangle([w * 0.66, ty1 + 12 * u, w * 0.76, gy - 70 * u], fill=(20, 20, 24, 255))
        d.rectangle([w * 0.52, gy - 70 * u, w * 0.90, gy], fill=(26, 22, 26, 255))
        scr = self.screen(t, True)
        sd = ImageDraw.Draw(scr, "RGBA"); sw, sh = scr.size
        pl = ease((t - tl) / 0.5)
        if pl > 0:                                          # checklist panel over the game
            sd.rectangle([0, 0, sw, sh], fill=(8, 8, 14, int(235 * pl)))
            esr = t >= te
            head = "Official rating (ESRB)" if esr else "Forbidden in games"
            rows = ["Nudity", "Strong sexual content", "Intense violence", "Drugs and alcohol"] if esr else ["nudity", "gambling", "music", "violence and crime"]
            sd.text((24 * u, 22 * u), head, font=self.f_head, fill=(255, 226, 160, int(255 * pl)))
            for k, r in enumerate(rows):
                t0 = (te if esr else tl) + 0.3 + k * 0.35
                ka = ease((t - t0) / 0.3) * pl
                if ka <= 0:
                    continue
                yy = 80 * u + k * 56 * u
                sd.text((70 * u, yy), r, font=self.f_row, fill=(240, 236, 230, int(255 * ka)))
                cx, cy = 40 * u, yy + 18 * u
                if esr:
                    s = 13 * u
                    sd.line([(cx - s, cy - s), (cx + s, cy + s)], fill=(255, 70, 70, int(255 * ka)), width=max(3, int(5 * u)))
                    sd.line([(cx - s, cy + s), (cx + s, cy - s)], fill=(255, 70, 70, int(255 * ka)), width=max(3, int(5 * u)))
                else:
                    sd.ellipse([cx - 7 * u, cy - 7 * u, cx + 7 * u, cy + 7 * u], fill=(255, 226, 160, int(255 * ka)))
        if off > 0:                                         # CRT-style switch-off
            sq = max(0.0, 1 - off)
            blk = Image.new("RGBA", scr.size, (4, 4, 6, 255))
            if sq > 0.02:
                hh = int(sh * sq)
                band = scr.crop((0, (sh - hh) // 2, sw, (sh + hh) // 2))
                blk.paste(band, (0, (sh - hh) // 2))
            elif t < tv + 1.25:
                ImageDraw.Draw(blk).line([(sw * 0.3, sh / 2), (sw * 0.7, sh / 2)], fill=(255, 255, 255, 220), width=2)
            scr = blk
        im.paste(scr.convert("RGB"), (int(tx0), int(ty0)))
        dg.rectangle([tx0, ty0, tx1, ty1], fill=int(110 * (1 - off) * flick))
        # prayer mat appears when he gets up
        mk = ease((t - tp) / 0.8)
        matx = w * 0.17
        if mk > 0:
            d.polygon([(matx - 130 * u, gy + 6 * u), (matx + 150 * u, gy + 6 * u), (matx + 130 * u, gy + 30 * u), (matx - 150 * u, gy + 30 * u)], fill=(110, 36, 40, int(255 * mk)))
            d.line([(matx - 120 * u, gy + 18 * u), (matx + 120 * u, gy + 18 * u)], fill=(220, 180, 90, int(200 * mk)), width=max(2, int(3 * u)))
        # the young man: sitting with a controller -> stands -> walks to the mat -> sujood
        st = ease((t - tp - 0.2) / 0.8)
        walk = ease((t - tp - 1.0) / 1.4)
        sj = ease((t - tp - 2.6) / 0.9)
        x = lerp(w * 0.36, matx + 40 * u, walk)
        col = (int(lerp(200, 250, off)), int(lerp(190, 232, off)), int(lerp(255, 196, off)))
        cush = 1 - ease((t - tp - 1.0) / 0.4)
        if cush > 0:                                        # floor cushion he sits on
            d.rounded_rectangle([w * 0.36 - 90 * u, gy - 44 * u, w * 0.36 + 70 * u, gy], radius=int(20 * u), fill=(46, 40, 58, int(255 * cush)))
        if t < tp + 0.2:
            p = dict(POSES["sit_up"])
            p["ua"] = (-20, -26); p["fa"] = (10, 4)              # holding the controller
            p["head"] = 20 + 3 * math.sin(t * 1.7)
            self.fig(im, x, gy, p, 1.25, col=col)
            hx, hy = x + 88 * u, gy - 150 * u
            d.rounded_rectangle([hx - 26 * u, hy - 12 * u, hx + 26 * u, hy + 12 * u], radius=int(10 * u), fill=(20, 20, 26, 255), outline=(90, 90, 110, 255))
        elif walk <= 0:
            self.fig(im, x, gy, pose_mix("sit_up", "stand", st), 1.25, col=col)
        elif sj <= 0:
            self.fig(im, x, gy, walk_pose(t * 6, 1.0 if walk < 1 else 0.0), 1.25, col=col, flip=True)
        else:
            self.fig(im, x, gy, pose_mix("stand", "sujood", sj), 1.25, col=col, flip=True)
        return self.finish(im, glow, col=(190, 150, 255) if off < 0.5 else (170, 240, 190), dust=self.dust, t=t)


BATCH2 = {
    "anger_calm": AngerCalm, "charity_jar": CharityJar, "believer_two": BelieverTwo,
    "mother_rank": MotherRank, "river_five": RiverFive, "words_record": WordsRecord,
    "traveler_road": TravelerRoad, "three_darks": ThreeDarks, "nearer_path": NearerPath, "gamer_room": GamerRoom,
}
