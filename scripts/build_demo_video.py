"""Generate Cereqo's four local video frames. Pillow is a build-time tool only."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "static" / "cereqo" / "video"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
NAVY = "#14213D"
WHITE = "#FFFFFF"
MINT = "#8FE3CF"
YELLOW = "#FFC857"
PALE = "#AEBBDA"
BLUE = "#4F6BFF"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def base(kicker):
    image = Image.new("RGB", (1280, 720), NAVY)
    draw = ImageDraw.Draw(image)
    draw.ellipse((1020, -180, 1420, 220), fill="#192C59")
    draw.text((80, 62), kicker, font=font(27, True), fill=MINT)
    draw.text((80, 640), "PAUSE  •  SET UP  •  SOLVE  •  CHECK", font=font(24), fill=PALE)
    return image, draw


def save_one():
    image, draw = base("CEREQO  •  MATH")
    draw.multiline_text((80, 150), "Linear equations:\nsee the structure", font=font(58, True), fill=WHITE, spacing=12)
    draw.rounded_rectangle((80, 344, 760, 348), 2, fill=BLUE)
    draw.text((80, 395), "Name the unknown first.", font=font(42, True), fill=YELLOW)
    image.save(OUT / "slide-1.png")


def save_two():
    image, draw = base("STEP 1  •  TRANSLATE")
    draw.multiline_text((80, 150), "A gym costs $24 to join\nplus $18 each month.", font=font(43), fill=WHITE, spacing=10)
    draw.rounded_rectangle((80, 300, 1050, 425), 22, fill="#20345F", outline=BLUE, width=2)
    draw.text((120, 340), "Total $132  →  24 + 18m = 132", font=font(45, True), fill=MINT)
    draw.text((80, 500), "m represents the number of months.", font=font(31), fill="#C9D4EB")
    image.save(OUT / "slide-2.png")


def save_three():
    image, draw = base("STEP 2  •  ISOLATE")
    draw.multiline_text((80, 145), "Use the same operation\non both sides.", font=font(52, True), fill=WHITE, spacing=8)
    draw.text((80, 345), "18m = 108   →   m = 6", font=font(64, True), fill=YELLOW)
    draw.text((80, 480), "Subtract 24, then divide by 18.", font=font(31), fill="#C9D4EB")
    image.save(OUT / "slide-3.png")


def save_four():
    image, draw = base("STEP 3  •  CHECK")
    draw.text((80, 155), "Substitute your answer.", font=font(54, True), fill=WHITE)
    draw.rounded_rectangle((80, 275, 900, 410), 22, fill="#173B48", outline="#35C9A5", width=2)
    draw.text((120, 318), "24 + 18(6) = 132  ✓", font=font(58, True), fill=MINT)
    draw.text((80, 485), "The value works in the original equation.", font=font(35, True), fill=YELLOW)
    image.save(OUT / "slide-4.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    save_one()
    save_two()
    save_three()
    save_four()
