#!/usr/bin/env python3
"""Build-time renderer for the entry image.

Draws one strawberry, big and glossy, on a dark slate background, and writes
entry.png (1024x1024, under 1 MiB). Runs at build time only; the submitted
main.py never imports Pillow, it just copies the finished entry.png.
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2048  # supersample, downscaled to 1024 at the end
W = H = S
CX = W * 0.50


def lerp(a, b, t):
    return a + (b - a) * t


def vgrad(size, top, bottom):
    """Vertical linear gradient image."""
    img = Image.new("RGB", (1, size[1]))
    px = img.load()
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        px[0, y] = tuple(int(lerp(top[i], bottom[i], t)) for i in range(3))
    return img.resize(size)


def radial_glow(size, center, radius, color, peak=110):
    """Soft radial glow, RGBA, fading to transparent at radius."""
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(peak * (1 - t) ** 2)
        d.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r],
                  fill=color + (a,))
    return glow.filter(ImageFilter.GaussianBlur(60))


def body_half_width(t):
    """Half-width of the strawberry body, t=0 top shoulder, t=1 tip."""
    base = 0.295 * W * (1 - t ** 2.6) ** 0.55
    shoulder = 0.58 + 0.42 * math.sin(math.pi * min(t * 1.5, 1.0)) ** 0.8
    return base * shoulder


def body_outline():
    """Outline points of the berry body, clockwise from top-left shoulder."""
    top_y, bot_y = H * 0.235, H * 0.905
    pts = []
    n = 90
    for i in range(n + 1):
        t = i / n
        y = top_y + (bot_y - top_y) * t
        pts.append((CX - body_half_width(t), y))
    for i in range(n, -1, -1):
        t = i / n
        y = top_y + (bot_y - top_y) * t
        pts.append((CX + body_half_width(t), y))
    # gentle dip at the top centre where the calyx sits
    top_arc = []
    for i in range(13):
        a = math.pi * i / 12  # 0..pi across the top
        top_arc.append((CX - body_half_width(0) * math.cos(a),
                        top_y - H * 0.028 * math.sin(a)))
    right_down = [(CX + body_half_width(i / n), top_y + (bot_y - top_y) * i / n)
                  for i in range(n + 1)]
    left_up = [(CX - body_half_width(i / n), top_y + (bot_y - top_y) * i / n)
               for i in range(n, -1, -1)]
    return top_arc + right_down[1:] + left_up[1:]


def main():
    # ---- background: dark teal, warm glow behind the berry ----
    bg = vgrad((W, H), (26, 46, 42), (8, 14, 12))
    bg.paste(radial_glow((W, H), (int(CX), int(H * 0.52)), int(W * 0.52),
                         (150, 60, 40), 66), (0, 0), radial_glow(
        (W, H), (int(CX), int(H * 0.52)), int(W * 0.52), (150, 60, 40), 66))
    d = ImageDraw.Draw(bg, "RGBA")
    # faint bokeh dots, out of focus, warm and cool
    for (bx, by, br, col, al) in [
            (W * 0.12, H * 0.20, 26, (255, 190, 120), 26),
            (W * 0.86, H * 0.16, 34, (140, 220, 200), 20),
            (W * 0.90, H * 0.78, 22, (255, 170, 110), 22),
            (W * 0.08, H * 0.72, 30, (120, 200, 190), 16),
            (W * 0.78, H * 0.88, 18, (255, 200, 140), 20)]:
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col + (al,))
    bg = bg.filter(ImageFilter.GaussianBlur(2))

    # ---- berry body: mask + red radial gradient ----
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(body_outline(), fill=255)
    body = Image.new("RGB", (W, H), (0, 0, 0))
    grad = Image.new("RGB", (W, H))
    gp = grad.load()
    cxg, cyg = int(W * 0.42), int(H * 0.42)
    maxr = W * 0.55
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            r = math.hypot(x - cxg, y - cyg) / maxr
            t = min(1.0, r)
            col = (lerp(255, 168, t), lerp(64, 12, t), lerp(52, 22, t))
            for dy in range(4):
                for dx in range(4):
                    if x + dx < W and y + dy < H:
                        gp[x + dx, y + dy] = (int(col[0]), int(col[1]), int(col[2]))
    body = Image.composite(grad, body, mask)

    # deep crimson shading on the lower-right edge, inside the mask
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.ellipse([CX - W * 0.05, H * 0.45, CX + W * 0.42, H * 0.98],
               fill=(90, 4, 10, 110))
    shade = shade.filter(ImageFilter.GaussianBlur(90))
    shaded = Image.composite(shade, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    body_rgba = body.convert("RGBA")
    body_rgba.alpha_composite(shaded)
    body = body_rgba.convert("RGB")
    bg.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(bg, "RGBA")

    # ---- glossy highlight, upper left, clipped to the body ----
    hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.ellipse([CX - W * 0.26, H * 0.26, CX + W * 0.02, H * 0.52],
               fill=(255, 235, 225, 105))
    hd.ellipse([CX - W * 0.20, H * 0.30, CX - W * 0.02, H * 0.44],
               fill=(255, 255, 255, 120))
    hi = hi.filter(ImageFilter.GaussianBlur(60))
    hi_masked = Image.composite(hi, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    bg.paste(hi_masked, (0, 0), hi_masked)
    d = ImageDraw.Draw(bg, "RGBA")
    # small hard specular dot, like light catching juice
    d.ellipse([CX - W * 0.175, H * 0.315, CX - W * 0.135, H * 0.355],
              fill=(255, 255, 255, 200))

    # ---- seeds (achenes): pale gold dots set into the flesh, in curved rows ----
    import random
    rng = random.Random(7)
    top_y, bot_y = H * 0.235, H * 0.905
    for row in range(9):
        t = 0.10 + row * 0.095
        y = top_y + (bot_y - top_y) * t
        half = body_half_width(t) * 0.86
        count = max(2, int(half / (W * 0.052)))
        stagger = (W * 0.026) if row % 2 else 0.0
        for k in range(count):
            fx = -1 + 2 * (k + 0.5) / count
            # rows bow gently downward toward the edges
            sx = CX + fx * half + stagger * (0.4 if fx > 0 else -0.4) + rng.uniform(-6, 6)
            sy = y + (fx * fx) * H * 0.018 + rng.uniform(-5, 5)
            if sy > bot_y - H * 0.02:
                continue
            js = rng.uniform(0.8, 1.2)
            sw, sh = W * 0.010 * js, H * 0.0145 * js
            d.ellipse([sx - sw, sy - sh + 3, sx + sw, sy + sh + 3],
                      fill=(120, 20, 16, 90))  # pit shadow, offset down
            d.ellipse([sx - sw, sy - sh, sx + sw, sy + sh],
                      fill=(247, 232, 160, 255))
            d.ellipse([sx - sw * 0.45, sy - sh * 0.55, sx + sw * 0.25, sy - sh * 0.05],
                      fill=(255, 250, 210, 255))

    # ---- calyx: five pointed green leaves + a short stem ----
    leaf_base = (CX, H * 0.245)
    leaf_specs = [(-0.62, 0.30, 0.26), (-0.34, 0.16, 0.30), (0.0, 0.02, 0.32),
                  (0.34, 0.16, 0.30), (0.62, 0.30, 0.26)]
    for (dx, dy, ln) in leaf_specs:
        tip = (CX + dx * W * 0.42, H * 0.245 - ln * H * 0.42 + dy * H * 0.10)
        left = (leaf_base[0] - W * 0.055 + dx * W * 0.10,
                leaf_base[1] + H * 0.012)
        right = (leaf_base[0] + W * 0.055 + dx * W * 0.10,
                 leaf_base[1] + H * 0.012)
        mid = ((tip[0] + leaf_base[0]) / 2 - dx * W * 0.02,
               (tip[1] + leaf_base[1]) / 2)
        d.polygon([left, mid, tip, right], fill=(46, 128, 52, 255))
        d.line([leaf_base, tip], fill=(30, 92, 36, 255), width=5)
    d.line([(CX, H * 0.245), (CX + W * 0.012, H * 0.175)],
           fill=(52, 110, 44, 255), width=16)
    d.ellipse([CX - W * 0.055, H * 0.225, CX + W * 0.055, H * 0.262],
              fill=(58, 140, 60, 255))

    # ---- water droplets on the skin ----
    for (dx, dy, r) in [(0.16, 0.38, 13), (-0.14, 0.52, 17), (0.20, 0.60, 11),
                        (-0.20, 0.42, 9), (0.05, 0.68, 14), (-0.06, 0.33, 10)]:
        px, py = CX + dx * W, H * dy
        d.ellipse([px - r, py - r, px + r, py + r],
                  fill=(255, 255, 255, 52), outline=(255, 255, 255, 130), width=3)
        d.ellipse([px - r * 0.45, py - r * 0.55, px - r * 0.05, py - r * 0.15],
                  fill=(255, 255, 255, 220))

    # ---- soft contact shadow under the tip ----
    sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh2).ellipse([CX - W * 0.20, H * 0.885, CX + W * 0.20, H * 0.945],
                                fill=(0, 0, 0, 110))
    sh2 = sh2.filter(ImageFilter.GaussianBlur(26))
    bg.paste(sh2, (0, 0), sh2)
    d = ImageDraw.Draw(bg, "RGBA")

    # ---- one line of text, small, at the bottom ----
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 52)
    except OSError:
        font = ImageFont.load_default()
    line = "One strawberry \u2014 taste it."
    tb = d.textbbox((0, 0), line, font=font)
    tw = tb[2] - tb[0]
    tx, ty = (W - tw) / 2, H * 0.955
    d.text((tx + 3, ty + 3), line, font=font, fill=(0, 0, 0, 160))
    d.text((tx, ty), line, font=font, fill=(245, 240, 230, 235))

    out = bg.convert("RGB").resize((1024, 1024), Image.LANCZOS)
    out.save("entry.png", optimize=True)
    import os
    print("entry.png bytes:", os.path.getsize("entry.png"))


if __name__ == "__main__":
    main()
