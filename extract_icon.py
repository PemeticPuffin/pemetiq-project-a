"""One-time script to extract the puffin app icon from Logo set.png."""

from PIL import Image

src = Image.open("Logo set.png")
w, h = src.size
print(f"Logo set dimensions: {w} x {h}")

# The circular app icon (Panel 2, top-left icon) sits in the lower-left area.
# Crop proportionally: roughly left 28%, rows 48%–90% of the image.
left   = int(w * 0.20)
top    = int(h * 0.52)
right  = int(w * 0.42)
bottom = int(h * 0.95)

icon = src.crop((left, top, right, bottom))
icon = icon.resize((180, 180), Image.LANCZOS)
icon.save("puffin_icon.png")
print("Saved puffin_icon.png — check it looks right, then run the app.")
