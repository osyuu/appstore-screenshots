#!/usr/bin/env python3
"""
App Store Screenshot Generator
Usage: python generate.py --app MyApp [--device iphone|ipad|all]
"""

import argparse
import math
import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).parent
APPS_DIR = BASE_DIR / "apps"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = BASE_DIR / "assets" / "fonts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(app: str) -> dict:
    path = APPS_DIR / app / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_font(size: int, font_file: str | None = None) -> ImageFont.FreeTypeFont:
    if font_file:
        path = FONTS_DIR / font_file
        if path.exists():
            return ImageFont.truetype(str(path), size)
    for system_font in [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(system_font).exists():
            return ImageFont.truetype(system_font, size)
    return ImageFont.load_default()


def fit_font(size: int, font_file: str | None, text: str, max_width: int, draw: ImageDraw.ImageDraw) -> ImageFont.FreeTypeFont:
    while size > 16:
        font = load_font(size, font_file)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 2
    return load_font(size, font_file)


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=255)
    return mask


def draw_iphone_frame(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, bezel: int) -> None:
    r = int(w * 0.12)
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=r, fill=(20, 20, 20))
    draw.rounded_rectangle([(x+bezel, y+bezel), (x+w-bezel, y+h-bezel)], radius=int(r*0.75), fill=(0, 0, 0))
    iw = int(w * 0.28)
    ih = int(w * 0.035)
    draw.rounded_rectangle(
        [(x+(w-iw)//2, y+bezel+int(bezel*0.6)),
         (x+(w+iw)//2, y+bezel+int(bezel*0.6)+ih)],
        radius=ih//2, fill=(10, 10, 10)
    )


def draw_ipad_frame(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, bezel: int) -> None:
    r = int(w * 0.06)
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=r, fill=(20, 20, 20))
    draw.rounded_rectangle([(x+bezel, y+bezel), (x+w-bezel, y+h-bezel)], radius=int(r*0.6), fill=(0, 0, 0))
    # iPad: 小圓形 home 按鈕替代（或省略，直接用黑邊框）
    cam_r = int(bezel * 0.3)
    cam_x = x + w // 2
    cam_y = y + bezel // 2
    draw.ellipse([(cam_x-cam_r, cam_y-cam_r), (cam_x+cam_r, cam_y+cam_r)], fill=(30, 30, 30))


# ---------------------------------------------------------------------------
# Panoramic background
# ---------------------------------------------------------------------------

def make_panoramic_bg(total_w: int, h: int, bg_color: tuple,
                      n: int, wave_y_ratio: float, wave_amp_ratio: float) -> Image.Image:
    rng = random.Random(42)
    img = Image.new("RGBA", (total_w, h), (*bg_color, 255))
    draw = ImageDraw.Draw(img)

    line_y_center = int(h * wave_y_ratio)
    amplitude     = int(h * wave_amp_ratio)
    step          = 4
    points        = []

    for x in range(0, total_w + step, step):
        t = (x / total_w) * 2 * math.pi * n
        y = (line_y_center
             + amplitude * 0.55 * math.sin(t * 1.0 + 0.0)
             + amplitude * 0.28 * math.sin(t * 2.7 + 1.3)
             + amplitude * 0.12 * math.sin(t * 6.2 + 2.1)
             + amplitude * 0.06 * rng.uniform(-1, 1))
        points.append((float(x), y))

    for width, alpha in [(9, 18), (5, 45), (2, 110)]:
        color = (72, 200, 110, alpha)
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=width)

    return img


# ---------------------------------------------------------------------------
# Composite single screenshot
# ---------------------------------------------------------------------------

def composite(panoramic_bg: Image.Image, slot_x: int,
              item: dict, device_key: str,
              cfg: dict, app_dir: Path) -> Image.Image:
    style      = cfg["style"]
    dev_cfg    = cfg["devices"][device_key]
    out_w, out_h = dev_cfg["output_size"]
    font_file  = style.get("font")
    bg_color   = tuple(style["background_color"])

    canvas = panoramic_bg.crop((slot_x, 0, slot_x + out_w, out_h)).copy()

    # --- 固定裝置尺寸 ---
    bezel    = int(out_w * style["bezel_ratio"])
    bot_mar  = int(out_h * style["bottom_margin_ratio"])
    device_w = int(out_w * dev_cfg["device_width_ratio"])
    device_x = (out_w - device_w) // 2

    ss_path = app_dir / "screenshots" / device_key / item[device_key]
    if not ss_path.exists():
        ss_path = app_dir / "screenshots" / item[device_key]
    if not ss_path.exists():
        print(f"  ⚠️  截圖不存在: {ss_path}")
        return canvas.convert("RGB")

    screenshot = Image.open(ss_path).convert("RGBA")
    ss_aspect  = screenshot.width / screenshot.height
    inner_h    = int((device_w - bezel * 2) / ss_aspect)
    device_h   = inner_h + bezel * 2
    device_y   = out_h - device_h - bot_mar

    draw = ImageDraw.Draw(canvas)
    if device_key == "ipad":
        draw_ipad_frame(draw, device_x, device_y, device_w, device_h, bezel)
    else:
        draw_iphone_frame(draw, device_x, device_y, device_w, device_h, bezel)

    inner_w   = device_w - bezel * 2
    ss_scaled = screenshot.resize((inner_w, inner_h), Image.LANCZOS)
    mask      = rounded_mask((inner_w, inner_h), int(device_w * 0.09))
    ss_masked = Image.new("RGBA", (inner_w, inner_h), (0, 0, 0, 0))
    ss_masked.paste(ss_scaled, (0, 0))
    ss_masked.putalpha(mask)
    canvas.paste(ss_masked, (device_x + bezel, device_y + bezel), ss_masked)

    # --- 文字置中於裝置上方空間 ---
    draw         = ImageDraw.Draw(canvas)
    accent_color = tuple(item.get("accent_color", [20, 20, 20]))
    text_color   = tuple(item.get("text_color",   [100, 100, 100]))
    padding_x    = int(out_w * 0.07)
    max_text_w   = out_w - padding_x * 2
    headline     = item.get("headline", "")
    subheadline  = item.get("subheadline")

    font_h  = fit_font(int(out_h * dev_cfg["font_headline_ratio"]), font_file, headline, max_text_w, draw)
    bbox_h  = draw.textbbox((0, 0), headline, font=font_h)
    hh      = bbox_h[3] - bbox_h[1]

    if subheadline:
        font_s       = load_font(int(out_h * dev_cfg["font_sub_ratio"]), font_file)
        bbox_s       = draw.textbbox((0, 0), subheadline, font=font_s)
        sh           = bbox_s[3] - bbox_s[1]
        text_block_h = hh + int(out_h * 0.012) + sh
    else:
        text_block_h = hh

    text_y = (device_y - text_block_h) // 2
    hw     = bbox_h[2] - bbox_h[0]
    draw.text(((out_w - hw) // 2, text_y), headline, font=font_h, fill=(*accent_color, 255))

    if subheadline:
        sw = bbox_s[2] - bbox_s[0]
        draw.text(((out_w - sw) // 2, text_y + hh + int(out_h * 0.012)),
                  subheadline, font=font_s, fill=(*text_color, 255))

    return canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_device(app: str, device_key: str, cfg: dict) -> None:
    dev_cfg      = cfg["devices"][device_key]
    out_w, out_h = dev_cfg["output_size"]
    bg_color     = tuple(cfg["style"]["background_color"])
    screenshots  = cfg["screenshots"]
    n            = len(screenshots)
    app_dir      = APPS_DIR / app
    out_dir      = OUTPUT_DIR / app / device_key
    out_dir.mkdir(parents=True, exist_ok=True)

    panoramic = make_panoramic_bg(
        out_w * n, out_h, bg_color, n,
        dev_cfg["wave_y_ratio"], dev_cfg["wave_amplitude_ratio"]
    )

    print(f"  [{device_key}] 生成 {n} 張...")
    for i, item in enumerate(screenshots):
        filename = item[device_key]
        img      = composite(panoramic, i * out_w, item, device_key, cfg, app_dir)
        out_path = out_dir / filename
        img.save(str(out_path), "PNG")
        print(f"    ✓ {out_path.relative_to(BASE_DIR)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app",    required=True, help="App 名稱，對應 apps/ 下的資料夾")
    parser.add_argument("--device", default="all", choices=["iphone", "ipad", "all"])
    args = parser.parse_args()

    cfg     = load_config(args.app)
    devices = ["iphone", "ipad"] if args.device == "all" else [args.device]

    print(f"▶ {args.app}")
    for device_key in devices:
        generate_device(args.app, device_key, cfg)

    print(f"\n完成！輸出資料夾：{OUTPUT_DIR / args.app}")


if __name__ == "__main__":
    main()
