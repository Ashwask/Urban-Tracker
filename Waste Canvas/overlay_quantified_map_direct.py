from PIL import Image, ImageDraw, ImageFont


BASE_IMAGE = "/Users/ashwinkulkarni/Downloads/codex-map-preview/Attachment287.pdf.png"
OUTPUT_IMAGE = "/Users/ashwinkulkarni/Documents/New project/india_waste_quantified_direct_overlay.png"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = word if not line else f"{line} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_accent(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    color: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle([x, y, x + w, y + 10], radius=5, fill=color + (220,))


def nearest_point_on_rect(
    rect: tuple[int, int, int, int],
    anchor: tuple[int, int],
) -> tuple[int, int]:
    x1, y1, x2, y2 = rect
    ax, ay = anchor
    px = min(max(ax, x1), x2)
    py = min(max(ay, y1), y2)

    distances = {
        (x1, py): abs(ax - x1),
        (x2, py): abs(ax - x2),
        (px, y1): abs(ay - y1),
        (px, y2): abs(ay - y2),
    }
    return min(distances, key=distances.get)


def draw_tag(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    accent_width: int,
    color: tuple[int, int, int],
    metric: str,
    notes: list[str],
    fonts: dict[str, ImageFont.ImageFont],
    anchor: tuple[int, int] | None = None,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=18,
        fill=(255, 255, 255, 235),
        outline=color + (120,),
        width=2,
    )
    draw_accent(draw, x1 + 18, y1 + 12, accent_width, color)

    text_x = x1 + 18
    current_y = y1 + 28
    max_w = x2 - x1 - 36

    metric_lines = wrap_text(draw, metric, fonts["metric"], max_w)
    for line in metric_lines:
        draw.text((text_x, current_y), line, font=fonts["metric"], fill=color + (255,))
        current_y += 28

    current_y += 2
    for note in notes:
        for line in wrap_text(draw, note, fonts["note"], max_w):
            draw.text((text_x, current_y), line, font=fonts["note"], fill=(50, 50, 50, 255))
            current_y += 22

    if anchor is not None:
        px, py = nearest_point_on_rect(box, anchor)
        draw.line([anchor, (px, py)], fill=color + (180,), width=4)
        draw.ellipse([anchor[0] - 7, anchor[1] - 7, anchor[0] + 7, anchor[1] + 7], fill=color + (255,), outline=(255, 255, 255, 255), width=2)


def draw_halo(
    overlay: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    width: int = 5,
) -> None:
    overlay.ellipse(rect, fill=fill, outline=outline, width=width)


def main() -> None:
    base = Image.open(BASE_IMAGE).convert("RGBA")
    canvas = base.copy()
    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    odraw = ImageDraw.Draw(overlay)
    draw = ImageDraw.Draw(canvas)

    fonts = {
        "title": load_font(24, bold=True),
        "sub": load_font(14),
        "metric": load_font(18, bold=True),
        "note": load_font(16),
    }

    # soft region highlights on the map itself
    draw_halo(odraw, (260, 720, 970, 1010), (240, 90, 90, 18), (214, 76, 76, 95))
    draw_halo(odraw, (500, 195, 980, 430), (240, 90, 90, 15), (214, 76, 76, 85))
    draw_halo(odraw, (740, 505, 1255, 800), (245, 166, 35, 18), (230, 126, 34, 95))
    draw_halo(odraw, (1110, 460, 1560, 710), (52, 152, 219, 16), (52, 152, 219, 95))
    draw_halo(odraw, (1445, 200, 1945, 420), (155, 89, 182, 15), (155, 89, 182, 85))
    draw_halo(odraw, (1540, 650, 1875, 870), (46, 204, 113, 16), (46, 204, 113, 95))
    draw_halo(odraw, (1275, 825, 1765, 1038), (127, 140, 141, 18), (127, 140, 141, 95))

    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # compact header
    draw.text((42, 26), "India lens: quantified signals placed on the system map", font=fonts["title"], fill=(32, 32, 32, 255))
    draw.text((42, 58), "CPCB FY 2021-22 mass balance | GFC 2024-25 | PIB Jan/Mar 2026", font=fonts["sub"], fill=(90, 90, 90, 255))

    # anchored in-map tags
    draw_tag(
        draw,
        box=(255, 760, 660, 905),
        accent_width=120,
        color=(214, 76, 76),
        metric="170k TPD generated",
        notes=[
            "156k TPD collected (92%).",
            "This is no longer mainly a collection-scale problem.",
        ],
        fonts=fonts,
        anchor=(670, 795),
    )

    draw_tag(
        draw,
        box=(585, 150, 965, 270),
        accent_width=150,
        color=(214, 76, 76),
        metric="13.9k TPD not collected",
        notes=[
            "Leakage still enters before recovery starts.",
        ],
        fonts=fonts,
        anchor=(865, 265),
    )

    draw_tag(
        draw,
        box=(770, 500, 1185, 665),
        accent_width=170,
        color=(230, 126, 34),
        metric="60,478 vs 39,648 wards",
        notes=[
            ">90% collection has outrun >90% source segregation.",
            "This remains the biggest break in the chain.",
        ],
        fonts=fonts,
        anchor=(910, 705),
    )

    draw_tag(
        draw,
        box=(1140, 470, 1575, 610),
        accent_width=150,
        color=(52, 152, 219),
        metric="2,900 MRFs | 67k TPD",
        notes=[
            "Capacity exists on paper.",
            "Cleaner feedstock is the binding constraint.",
        ],
        fonts=fonts,
        anchor=(1500, 615),
    )

    draw_tag(
        draw,
        box=(1450, 165, 1905, 305),
        accent_width=150,
        color=(155, 89, 182),
        metric="~35% of MSW is dry waste",
        notes=[
            "Buyers, EPR and offtake must turn sorting into sales.",
        ],
        fonts=fonts,
        anchor=(1740, 265),
    )

    draw_tag(
        draw,
        box=(1510, 655, 1940, 790),
        accent_width=150,
        color=(46, 204, 113),
        metric="91.5k TPD processed (54%)",
        notes=[
            "Processing has scaled, but still cannot absorb the full stream.",
        ],
        fonts=fonts,
        anchor=(1735, 690),
    )

    draw_tag(
        draw,
        box=(1300, 835, 1765, 1000),
        accent_width=170,
        color=(127, 140, 141),
        metric="41.5k TPD landfilled (24%)",
        notes=[
            "~25 cr MT legacy waste identified.",
            "~9.5 cr MT still remains nationally.",
        ],
        fonts=fonts,
        anchor=(1510, 930),
    )

    canvas.save(OUTPUT_IMAGE)


if __name__ == "__main__":
    main()
