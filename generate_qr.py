import json
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

MAPPING_PATH = Path("data/mappings/qr_to_exhibit.json")
OUT_DIR = Path("data/qr")

QR_SIZE = 400
TEXT_HEIGHT = 60
FONT_SIZE = 32

# Yazı fontu (Mac/Linux için güvenli)
try:
    FONT = ImageFont.truetype("Arial.ttf", FONT_SIZE)
except:
    FONT = ImageFont.load_default()


def load_mapping() -> dict[str, str]:
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_qr_image(qr_id: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_id)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE))
    return qr_img


def combine_qr_and_text(qr_img: Image.Image, text: str) -> Image.Image:
    total_height = QR_SIZE + TEXT_HEIGHT
    canvas = Image.new("RGB", (QR_SIZE, total_height), "white")

    draw = ImageDraw.Draw(canvas)

    # QR'ı üste koy
    canvas.paste(qr_img, (0, 0))

    # Yazıyı ortala
    text_bbox = draw.textbbox((0, 0), text, font=FONT)
    text_width = text_bbox[2] - text_bbox[0]
    x = (QR_SIZE - text_width) // 2
    y = QR_SIZE + (TEXT_HEIGHT - FONT_SIZE) // 2

    draw.text((x, y), text, fill="black", font=FONT)

    return canvas


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = load_mapping()

    for qr_id in mapping.keys():
        qr_img = create_qr_image(qr_id)
        final_img = combine_qr_and_text(qr_img, qr_id)

        out_path = OUT_DIR / f"{qr_id}.png"
        final_img.save(out_path)

        print(f"Saved: {out_path}")

    print("\nAll QR codes generated successfully.")


if __name__ == "__main__":
    main()
