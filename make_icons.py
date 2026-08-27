from PIL import Image, ImageDraw, ImageFont

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def gradient(w, h, c1, c2):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for i in range(h):
        d.line([(0, i), (w, i)], fill=lerp(c1, c2, i / max(h - 1, 1)))
    return img

def logo(d, cx, cy, s):
    d.rounded_rectangle([cx - s*.38, cy - s*.30, cx + s*.38, cy + s*.34],
                        radius=int(s*.22), fill="white")
    d.line([(cx, cy - s*.30), (cx, cy - s*.42)], fill="white", width=max(3, int(s*.03)))
    d.ellipse([cx - s*.05, cy - s*.48, cx + s*.05, cy - s*.38], fill="white")
    d.ellipse([cx - s*.22, cy - s*.12, cx - s*.08, cy + s*.02], fill="#2D3436")
    d.ellipse([cx + s*.08, cy - s*.12, cx + s*.22, cy + s*.02], fill="#2D3436")
    d.arc([cx - s*.14, cy + s*.06, cx + s*.14, cy + s*.24], start=20, end=160,
          fill="#2D3436", width=max(3, int(s*.03)))

icon = gradient(512, 512, (108, 92, 231), (9, 132, 227))
logo(ImageDraw.Draw(icon), 256, 256, 512)
icon.save("icon.png")

splash = gradient(1080, 1920, (25, 25, 45), (45, 35, 80))
d = ImageDraw.Draw(splash)
logo(d, 540, 800, 360)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
except Exception:
    font = ImageFont.load_default()
bbox = d.textbbox((0, 0), "EVA", font=font)
d.text(((1080 - (bbox[2] - bbox[0])) / 2, 1050), "EVA", fill="white", font=font)
splash.save("presplash.png")
print("icon.png + presplash.png generes")
