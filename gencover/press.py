"""A small simulated print shop for generative covers.

Each ink is its own PLATE (a cairo A8 mask). Drawing goes onto the current
plate. At the end the plates are 'printed' onto paper one at a time, each
with its own small offset and rotation (misregistration) and uneven ink
take-up, and the inks MULTIPLY where they overlap (overprinting makes the
third colour), the way 1960s two- and three-colour offset covers did.

Strokes are pen strokes: low-frequency wobble across the line, width
swelling and thinning with pressure, tapered ends, corners overshot.
"""
import math
import cairo
import numpy as np
from scipy.ndimage import zoom, gaussian_filter

W, H = 1400, 2100
PAPER = np.array([0.95, 0.925, 0.86])

INKS = {   # a fixed 1960s spot-ink set (per the Dover research)
    "black":   (0.11, 0.10, 0.10),
    "magenta": (0.85, 0.16, 0.45),
    "lime":    (0.66, 0.80, 0.20),
    "orange":  (0.95, 0.50, 0.13),
    "cobalt":  (0.13, 0.33, 0.62),
    "mustard": (0.88, 0.69, 0.16),
    "olive":   (0.47, 0.50, 0.24),
    "brown":   (0.42, 0.27, 0.17),
    "red":     (0.80, 0.22, 0.16),
    "sky":     (0.45, 0.70, 0.84),
    "teal":    (0.09, 0.50, 0.50),
    "violet":  (0.40, 0.26, 0.55),
    "yellow":  (0.97, 0.76, 0.12),     # Byrne's yellow
}


class _Pen:
    """A press with one plate selected: every drawing call re-selects it."""
    def __init__(self, press, plate):
        self._press, self._plate = press, plate

    def __getattr__(self, name):
        attr = getattr(self._press, name)
        if callable(attr):
            def bound(*a, **kw):
                self._press.plate = self._plate
                self._press.cx = self._press.plates[self._plate][1]
                return attr(*a, **kw)
            return bound
        return attr


class Press:
    # SCALE renders the same design at more pixels (the print build uses
    # ~1.25, ~330 ppi on a 5x8 front) so paper grain and ink texture are
    # drawn at the size they print, not stretched from the screen size
    SCALE = 1.0
    PAD = 60

    def __init__(self, seed, inks, w=W, h=H):
        self.rng = np.random.default_rng(seed)
        self.scale = Press.SCALE
        self.w, self.h = int(w * self.scale), int(h * self.scale)
        self.plates = {}
        for name in inks:
            # each plate extends PAD px past the page on every side, so a
            # full-bleed field survives being shifted out of register (a plate
            # clipped to the page left a strip of bare paper along one edge)
            s = cairo.ImageSurface(cairo.FORMAT_A8, self.w + 2 * self.PAD, self.h + 2 * self.PAD)
            c = cairo.Context(s)
            c.translate(self.PAD, self.PAD)
            c.scale(self.scale, self.scale)
            self.plates[name] = (s, c)
        self.order = list(inks)
        self.use(self.order[0])

    def use(self, plate):
        """Select a plate and return a PEN bound to it: `k = p.use("black")`
        keeps drawing on the black plate even after p.use("red") elsewhere.
        (It once returned the press itself, so a saved pen silently followed
        the last plate selected -- Darwin's black tree printed in mustard.)"""
        self.plate = plate
        self.cx = self.plates[plate][1]
        return _Pen(self, plate)

    def mark(self, label, size=28, y=84):
        """The edition, top right, where Dover printed its series code
        (Alex, 2026-10-13: a cover says whether it is a retelling, a
        restored edition or the original text). Knocked out of EVERY plate,
        so it reads as bare paper whatever lies under it; the generator's
        state is put back, so the design's print (misregistration, grain)
        is the one already approved."""
        state = self.rng.bit_generator.state
        cur = self.plate
        # over bare paper (Byrne's cream page) a knock-out would vanish:
        # print it in the key ink instead
        x0, x1 = int((W - 560) * self.scale) + self.PAD, int((W - 100) * self.scale) + self.PAD
        y0, y1 = int((y - size) * self.scale) + self.PAD, int(y * self.scale) + self.PAD
        covered = 0.0
        for name in self.order:
            surf = self.plates[name][0]; surf.flush()
            a = np.ndarray((surf.get_height(), surf.get_stride()), np.uint8, surf.get_data())
            covered = max(covered, a[y0:y1, x0:x1].mean() / 255)
        if covered < 0.5:
            key = "black" if "black" in self.order else self.order[-1]
            self.use(key).text(label.upper(), W - 100, y, size, font="Fira Sans Black",
                               align="right", track=0.12)
        else:
            for name in self.order:
                self.use(name).text(label.upper(), W - 100, y, size, font="Fira Sans Black",
                                    align="right", clear=True, track=0.12)
        self.use(cur)
        self.rng.bit_generator.state = state

    # ------------------------------------------------------------ noise
    def wobble(self, n, amp, freq=3):
        t = np.linspace(0, 1, n)
        out = np.zeros(n)
        for k in range(1, freq + 1):
            out += self.rng.normal() / k * np.sin(2 * math.pi * (k * t + self.rng.random()))
        return out * amp

    def resample(self, pts, step=3.0):
        pts = np.asarray(pts, float)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        L = np.concatenate([[0], np.cumsum(seg)])
        if L[-1] == 0:
            return pts
        s = np.linspace(0, L[-1], max(2, int(L[-1] / step)))
        return np.column_stack([np.interp(s, L, pts[:, 0]), np.interp(s, L, pts[:, 1])])

    # ------------------------------------------------------------ painting
    def _poly(self, p, clear=False, alpha=1.0):
        cx = self.cx
        if clear:
            cx.save(); cx.set_operator(cairo.OPERATOR_CLEAR)
        else:
            cx.set_source_rgba(0, 0, 0, alpha)
        cx.move_to(*p[0])
        for q in p[1:]:
            cx.line_to(*q)
        cx.close_path()
        cx.fill()
        if clear:
            cx.restore()

    def stroke(self, pts, width=4.0, jitter=1.6, taper=True, clear=False, alpha=1.0):
        p = self.resample(pts)
        n = len(p)
        if n < 2:
            return
        d = np.gradient(p, axis=0)
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        nrm /= np.maximum(np.hypot(*nrm.T), 1e-9)[:, None]
        L = np.hypot(*np.diff(p, axis=0).T).sum()
        p = p + nrm * self.wobble(n, min(jitter, 0.004 * L + 0.4), freq=4)[:, None]
        t = np.linspace(0, 1, n)
        pressure = 1 + 0.15 * self.wobble(n, 1, freq=3)
        if taper:
            pressure *= np.clip(np.minimum(t, 1 - t) * 10, 0.3, 1) ** 0.5
            pressure *= 1 + 0.12 * (np.exp(-t * 20) + np.exp(-(1 - t) * 20))   # ink blob at start/end
        wv = np.clip(width * pressure, width * 0.3, width * 1.6) / 2
        poly = np.vstack([p + nrm * wv[:, None], (p - nrm * wv[:, None])[::-1]])
        self._poly(poly, clear, alpha)

    def rope(self, pts, width, clear=False):
        """a smooth stroke with round ends (cairo's own), for rope and tube;
        the hand comes from a slight wobble of the path, not of the edge"""
        p = self.resample(pts, 4)
        p = p + self.rng.normal(0, 0.4, p.shape)
        cx = self.cx
        cx.save()
        if clear:
            cx.set_operator(cairo.OPERATOR_CLEAR)
        else:
            cx.set_source_rgba(0, 0, 0, 1)
        cx.set_line_width(width)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.move_to(*p[0])
        for q in p[1:]:
            cx.line_to(*q)
        cx.stroke()
        cx.restore()

    def line(self, a, b, **kw):
        self.stroke([a, b], **kw)

    def ring(self, c, r, n=None, wob=0.01, a0=0, a1=2 * math.pi):
        n = n or max(28, int(abs(a1 - a0) * r / 4))
        a = np.linspace(a0, a1, n)
        rr = r * (1 + self.wobble(n, wob, freq=3))
        return np.column_stack([c[0] + rr * np.cos(a), c[1] + rr * np.sin(a)])

    def circle(self, c, r, overshoot=0.25, **kw):
        a0 = self.rng.random() * 2 * math.pi
        self.stroke(self.ring(c, r, a0=a0, a1=a0 + 2 * math.pi + overshoot), **kw)

    def disc(self, c, r, clear=False, wob=0.03):
        self._poly(self.ring(c, r, n=40, wob=wob), clear)

    def fill(self, pts, clear=False, rough=1.0):
        p = self.resample(pts, 4)
        p = p + self.rng.normal(0, rough, p.shape)
        self._poly(p, clear)

    def field(self, x0, y0, x1, y1, rough=1.5):
        """a full block of ink with a hand-cut edge"""
        self.fill([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], rough=rough)

    def polyline(self, pts, closed=True, **kw):
        pts = list(pts)
        if closed:
            pts = pts + [pts[0], pts[1]]
        self.stroke(pts, taper=False, **kw)

    def text(self, s, x, y, size, font="EB Garamond", align="center", bold=False,
             italic=False, track=0.0, jit=0.0, clear=False):
        # LETTERING IS SET STRAIGHT (Alex, 2026-10-12: per-glyph drift read as
        # wobbly); the hand shows in the drawing and the misregistered print
        cx = self.cx
        MATH = "∃∀¬⊃∨∼≠→′"
        wt = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
        sl = cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL
        def face(ch):
            cx.select_font_face("DejaVu Serif" if ch in MATH else font, sl, wt)
            cx.set_font_size(size * (0.85 if ch in MATH else 1))
        widths = []
        for ch in s:
            face(ch)
            widths.append(cx.text_extents(ch).x_advance + track * size)
        total = sum(widths) - track * size
        xx = x - (total / 2 if align == "center" else total if align == "right" else 0)
        if clear:
            cx.save(); cx.set_operator(cairo.OPERATOR_CLEAR)
        else:
            cx.set_source_rgba(0, 0, 0, 1)
        for ch, w in zip(s, widths):
            cx.save()
            dy, rot = self.rng.normal(0, 1), self.rng.normal(0, 1)   # drawn regardless, so a design's
            cx.translate(xx, y + jit * dy)                              # random stream (its trees and stars)
            cx.rotate(0.02 * jit * rot)                                 # is the one Alex approved
            face(ch)
            cx.move_to(0, 0)
            cx.show_text(ch)
            cx.restore()
            xx += w
        if clear:
            cx.restore()
        return total

    # ------------------------------------------------------------ printing
    def _mask(self, name):
        s = self.plates[name][0]
        s.flush()
        stride = s.get_stride()
        a = np.ndarray((self.h, stride), np.uint8, s.get_data())[:, : self.w].astype(float) / 255
        return a

    def _misregister(self, name, sd_px):
        """re-render the plate shifted and turned a little"""
        s = self.plates[name][0]
        out = cairo.ImageSurface(cairo.FORMAT_A8, self.w, self.h)
        cx = cairo.Context(out)
        dx, dy = self.rng.normal(0, sd_px, 2)
        self.rng.normal(0, 0.0025)   # (the old rotation draw, kept so seeds reproduce)
        # SHIFT ONLY, never rotate (Alex, 2026-10-12): a turned plate skews the
        # full-bleed fields and leaves slivers of paper along the edges
        cx.translate(dx - self.PAD, dy - self.PAD)
        cx.set_source_surface(s, 0, 0)
        cx.paint()
        out.flush()
        return np.ndarray((self.h, out.get_stride()), np.uint8, out.get_data())[:, : self.w].astype(float) / 255

    def _takeup(self, strength):
        """uneven ink: big soft mottle + fine grain + rare dropouts"""
        big = zoom(self.rng.normal(0, 1, (self.h // 60 + 2, self.w // 60 + 2)), 60, order=3)[: self.h, : self.w]
        fine = gaussian_filter(self.rng.normal(0, 1, (self.h, self.w)), 0.7)
        # ink take-up: a faint, fine unevenness and grain, never visible blobs
        t = 1 - strength * (0.025 * np.abs(big) + 0.09 * np.clip(fine, 0, None))
        return np.clip(t, 0.55, 1)

    def print(self, path, misreg=3.5, takeup=1.0):
        img = np.ones((self.h, self.w, 3)) * PAPER
        # paper tooth
        img *= (1 + 0.025 * gaussian_filter(self.rng.normal(0, 1, (self.h, self.w)), 0.8))[:, :, None]
        for name in self.order:
            sd = (0.6 if name == "black" else misreg) * self.scale   # the key plate is the register
            m = self._misregister(name, sd) * self._takeup(takeup)
            ink = np.array(INKS[name] if isinstance(name, str) else name)
            img *= 1 - m[:, :, None] * (1 - ink)
        # fibres and specks
        out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        from PIL import Image, ImageDraw
        im = Image.fromarray(out)
        dr = ImageDraw.Draw(im, "RGBA")
        for _ in range(500):
            x, y = self.rng.random() * self.w, self.rng.random() * self.h
            a = self.rng.random() * math.pi
            L = self.rng.uniform(4, 14)
            dr.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(120, 95, 60, int(self.rng.uniform(15, 40))), width=1)
        im.save(path)
        return im
