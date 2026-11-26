"""生成 Tauri 图标（简单蓝色方块 + 白色数据柱）。"""

from PIL import Image, ImageDraw


def make_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (22, 119, 255, 255))
    d = ImageDraw.Draw(img)
    pad = size // 6
    bar_w = (size - 2 * pad) // 4
    heights = [0.35, 0.6, 0.85]
    for i, h in enumerate(heights):
        x0 = pad + i * bar_w
        y0 = int(size - pad - h * (size - 2 * pad))
        d.rectangle([x0, y0, x0 + bar_w - pad // 2, size - pad], fill=(255, 255, 255, 255))
    return img


if __name__ == "__main__":
    import os

    out = "src-tauri/icons"
    os.makedirs(out, exist_ok=True)
    make_icon(32).save(f"{out}/32x32.png")
    make_icon(128).save(f"{out}/128x128.png")
    make_icon(256).save(f"{out}/128x128@2x.png")
    make_icon(512).save(f"{out}/icon.png")
    make_icon(256).save(f"{out}/icon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print("icons generated")
