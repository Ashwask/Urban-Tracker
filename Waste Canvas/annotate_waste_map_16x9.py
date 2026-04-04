from PIL import Image, ImageDraw, ImageFont


BASE_IMAGE = "/Users/ashwinkulkarni/Downloads/codex-map-preview/Attachment287.pdf.png"
OUTPUT_IMAGE = "/Users/ashwinkulkarni/Documents/New project/india_waste_bottlenecks_annotated_16x9.png"


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


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
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


def draw_box(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    shadow: int = 6,
) -> None:
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle([x1 + shadow, y1 + shadow, x2 + shadow, y2 + shadow], radius=radius, fill=(0, 0, 0, 24))
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=3)


def draw_marker(draw: ImageDraw.ImageDraw, center: tuple[int, int], number: int, color: tuple[int, int, int], font: ImageFont.ImageFont) -> None:
    x, y = center
    r = 15
    draw.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=(255, 255, 255, 255))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=(255, 255, 255, 255), width=2)
    draw.text((x, y - 1), str(number), font=font, fill="white", anchor="mm")


def draw_arrow(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color: tuple[int, int, int], width: int = 3) -> None:
    draw.line(points, fill=color + (255,), width=width, joint="curve")
    sx, sy = points[-2]
    ex, ey = points[-1]
    dx = ex - sx
    dy = ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    head = 10
    wing = 6
    draw.polygon(
        [
            (ex, ey),
            (int(ex - head * ux + wing * px), int(ey - head * uy + wing * py)),
            (int(ex - head * ux - wing * px), int(ey - head * uy - wing * py)),
        ],
        fill=color + (255,),
    )


def connector_points(
    box: tuple[int, int, int, int],
    marker: tuple[int, int],
    side: str,
    map_rect: tuple[int, int, int, int],
) -> list[tuple[int, int]]:
    x, y, w, h = box
    mx, my = marker
    map_x1, map_y1, map_x2, map_y2 = map_rect

    if side == "right":
        start = (x + w, y + h // 2)
        elbow_x = map_x1 - 18
        return [start, (elbow_x, start[1]), (elbow_x, my), (mx - 18, my), marker]
    if side == "left":
        start = (x, y + h // 2)
        elbow_x = map_x2 + 18
        return [start, (elbow_x, start[1]), (elbow_x, my), (mx + 18, my), marker]
    if side == "bottom":
        start = (x + w // 2, y + h)
        elbow_y = map_y1 - 18
        return [start, (start[0], elbow_y), (mx, elbow_y), (mx, my - 18), marker]
    start = (x + w // 2, y)
    elbow_y = map_y2 + 18
    return [start, (start[0], elbow_y), (mx, elbow_y), (mx, my + 18), marker]


def draw_callout(
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.ImageFont],
    number: int,
    title: str,
    metric: str,
    note: str,
    box: tuple[int, int, int, int],
    marker: tuple[int, int],
    side: str,
    color: tuple[int, int, int],
    map_rect: tuple[int, int, int, int],
) -> None:
    x, y, w, h = box
    draw_box(draw, (x, y, x + w, y + h), radius=18, fill=(255, 255, 255, 248), outline=color + (255,))
    badge_x, badge_y = x + 20, y + 20
    draw.ellipse([badge_x - 14, badge_y - 14, badge_x + 14, badge_y + 14], fill=color + (255,))
    draw.text((badge_x, badge_y - 1), str(number), font=fonts["badge"], fill="white", anchor="mm")

    draw.text((x + 42, y + 10), title, font=fonts["title"], fill=color + (255,))

    current_y = y + 40
    for line in wrap_text(draw, metric, fonts["metric"], w - 20):
        draw.text((x + 12, current_y), line, font=fonts["metric"], fill=(40, 40, 40, 255))
        current_y += 22

    current_y += 2
    for line in wrap_text(draw, note, fonts["note"], w - 20):
        draw.text((x + 12, current_y), line, font=fonts["note"], fill=(95, 95, 95, 255))
        current_y += 18

    draw_marker(draw, marker, number, color, fonts["badge"])
    draw_arrow(draw, connector_points(box, marker, side, map_rect), color)


def scale_point(point: tuple[int, int], scale: float, offset: tuple[int, int]) -> tuple[int, int]:
    return (int(offset[0] + point[0] * scale), int(offset[1] + point[1] * scale))


def main() -> None:
    base = Image.open(BASE_IMAGE).convert("RGBA")
    canvas_w, canvas_h = 1920, 1080
    map_w = 1080
    scale = map_w / base.width
    map_h = int(base.height * scale)
    map_x, map_y = 420, 150
    map_rect = (map_x, map_y, map_x + map_w, map_y + map_h)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (247, 248, 244, 255))
    draw = ImageDraw.Draw(canvas)

    fonts = {
        "header": load_font(24, bold=True),
        "sub": load_font(10),
        "title": load_font(15, bold=True),
        "metric": load_font(12, bold=True),
        "note": load_font(10),
        "badge": load_font(14, bold=True),
        "footer_title": load_font(13, bold=True),
    }

    draw_box(draw, (20, 18, 1060, 88), radius=14, fill=(255, 255, 255, 247), outline=(205, 209, 204, 255), shadow=0)
    draw.text((28, 24), "India Waste Ecosystem: Bottlenecks Applied on System Map", font=fonts["header"], fill=(30, 30, 30, 255))
    draw.text((30, 60), "Mass-balance base: CPCB FY 2021-22 | Current signals: GFC 2024-25 and PIB January/March 2026", font=fonts["sub"], fill=(95, 95, 95, 255))

    draw_box(draw, (map_x - 8, map_y - 8, map_x + map_w + 8, map_y + map_h + 8), radius=14, fill=(255, 255, 255, 255), outline=(205, 209, 204, 255))
    resized = base.resize((map_w, map_h), Image.Resampling.LANCZOS)
    canvas.alpha_composite(resized, (map_x, map_y))

    callouts = [
        {
            "number": 1,
            "title": "Source segregation gap",
            "metric": "20.8k-ward gap between high collection and high segregation",
            "note": "Mixed waste enters at source and weakens every downstream recovery step.",
            "box": (26, 150, 310, 92),
            "anchor": (305, 640),
            "side": "right",
            "color": (206, 66, 66),
        },
        {
            "number": 2,
            "title": "Post-collection leakage",
            "metric": "13.9k TPD uncollected; 23.5k TPD not scientifically routed",
            "note": "Material still leaks after collection before circular processing begins.",
            "box": (26, 262, 310, 104),
            "anchor": (820, 690),
            "side": "right",
            "color": (206, 66, 66),
        },
        {
            "number": 3,
            "title": "Informal chain gap",
            "metric": "Value is captured informally, but formal integration remains weak",
            "note": "Limits traceability, quality, and scale into formal recycling.",
            "box": (26, 386, 310, 92),
            "anchor": (1135, 305),
            "side": "right",
            "color": (230, 126, 34),
        },
        {
            "number": 5,
            "title": "Offtake bottleneck",
            "metric": "Sorted material still needs buyers, specs, and stable demand",
            "note": "Without offtake, flow backs up between aggregators and recyclers.",
            "box": (1584, 150, 310, 92),
            "anchor": (1600, 235),
            "side": "left",
            "color": (155, 89, 182),
        },
        {
            "number": 4,
            "title": "MRF quality bottleneck",
            "metric": "Capacity exists, but contaminated dry waste lowers output",
            "note": "Constraint is cleaner feedstock, not only more plants.",
            "box": (1584, 262, 310, 92),
            "anchor": (1320, 525),
            "side": "left",
            "color": (52, 152, 219),
        },
        {
            "number": 6,
            "title": "Residual dependence",
            "metric": "Only 54% of MSW was processed in FY 2021-22",
            "note": "Rejects still move to RDF, processing, or landfill.",
            "box": (1584, 374, 310, 92),
            "anchor": (1535, 760),
            "side": "left",
            "color": (46, 204, 113),
        },
        {
            "number": 7,
            "title": "Legacy waste drag",
            "metric": "~25 crore MT identified; >62% processed by Jan 31, 2026",
            "note": "~9.5 crore MT still remains nationally.",
            "box": (420, 760, 1080, 92),
            "anchor": (1445, 890),
            "side": "top",
            "color": (127, 140, 141),
        },
    ]

    for item in callouts:
        marker = scale_point(item["anchor"], scale, (map_x, map_y))
        draw_callout(
            draw=draw,
            fonts=fonts,
            number=item["number"],
            title=item["title"],
            metric=item["metric"],
            note=item["note"],
            box=item["box"],
            marker=marker,
            side=item["side"],
            color=item["color"],
            map_rect=map_rect,
        )

    draw_box(draw, (20, 950, 1898, 1050), radius=16, fill=(255, 255, 255, 247), outline=(205, 209, 204, 255), shadow=0)
    draw.text((30, 965), "Bottom line", font=fonts["footer_title"], fill=(32, 32, 32, 255))
    footer = "India's bottleneck is converting collected waste into clean, saleable material that can move through MRFs, aggregators, and recyclers instead of leaking back into disposal."
    for i, line in enumerate(wrap_text(draw, footer, load_font(11), 1828)):
        draw.text((30, 990 + i * 18), line, font=load_font(11), fill=(88, 88, 88, 255))

    canvas.convert("RGB").save(OUTPUT_IMAGE, quality=95)


if __name__ == "__main__":
    main()
