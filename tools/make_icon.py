# -*- coding: utf-8 -*-
"""Kelime Oyunu ikonu: mor stüdyo kutusu + altın 'K'.
Üretir: favicon.ico (16/32/48), apple-touch-icon.png (180).
Çalıştır: python tools/make_icon.py"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
S = 256

def vgrad(w, h, top, bottom):
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return col.resize((w, h)).convert("RGBA")

def find_font(size):
    for p in ("C:/Windows/Fonts/trebucbd.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/Arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make(full_bleed):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    grad = vgrad(S, S, (91, 33, 182), (26, 11, 61))     # #5b21b6 -> #1a0b3d
    if full_bleed:                                       # apple: köşeler dolu (opak)
        img.paste(grad, (0, 0))
    else:
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).rounded_rectangle([8, 8, S - 8, S - 8], radius=56, fill=255)
        img.paste(grad, (0, 0), m)
        ImageDraw.Draw(img).rounded_rectangle([8, 8, S - 8, S - 8], radius=56,
                                              outline=(255, 210, 63, 120), width=6)
    # altın 'K'
    font = find_font(180)
    tmask = Image.new("L", (S, S), 0)
    td = ImageDraw.Draw(tmask)
    b = td.textbbox((0, 0), "K", font=font)
    tx = (S - (b[2] - b[0])) / 2 - b[0]
    ty = (S - (b[3] - b[1])) / 2 - b[1]
    td.text((tx, ty), "K", font=font, fill=255)
    gold = vgrad(S, S, (255, 243, 176), (255, 123, 0))   # #fff3b0 -> #ff7b00
    img.paste(gold, (0, 0), tmask)
    return img

icon = make(full_bleed=False)
icon.save(os.path.join(ROOT, "favicon.ico"),
          sizes=[(16, 16), (32, 32), (48, 48)])
make(full_bleed=True).resize((180, 180), Image.LANCZOS).save(
    os.path.join(ROOT, "apple-touch-icon.png"))
print("favicon.ico ve apple-touch-icon.png olusturuldu.")
