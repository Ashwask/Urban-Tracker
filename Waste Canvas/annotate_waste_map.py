from PIL import Image, ImageDraw, ImageFont


BASE_IMAGE = "/Users/ashwinkulkarni/Downloads/codex-map-preview/Attachment287.pdf.png"
OUTPUT_IMAGE = "/Users/ashwinkulkarni/Documents/New project/india_waste_bottlenecks_annotated.png"


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


def draw_shadowed_box(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    shadow: int = 10,
) -> None:
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle([x1 + shadow, y1 + shadow, x2 + shadow, y2 + shadow], radius=radius, fill=(0, 0, 0, 28))
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=4)


def draw_marker(draw: ImageDraw.ImageDraw, center: tuple[int, int], number: int, color: tuple[int, int, int], font: ImageFont.ImageFont) -> None:
    x, y = center
    r = 22
    draw.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=(255, 255, 255, 255))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=(255, 255, 255, 255), width=3)
    draw.text((x, y - 1), str(number), font=font, fill="white", anchor="mm")


def draw_arrow(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color: tuple[int, int, int], width: int = 4) -> None:
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
    head = 14
    wing = 8
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
        elbow_x = map_x1 - 26
        return [start, (elbow_x, start[1]), (elbow_x, my), (mx - 28, my), marker]
    if side == "left":
        start = (x, y + h // 2)
        elbow_x = map_x2 + 26
        return [start, (elbow_x, start[1]), (elbow_x, my), (mx + 28, my), marker]
    if side == "bottom":
        start = (x + w // 2, y + h)
        elbow_y = map_y1 - 26
        return [start, (start[0], elbow_y), (mx, elbow_y), (mx, my - 28), marker]
    start = (x + w // 2, y)
    elbow_y = map_y2 + 26
    return [start, (start[0], elbow_y), (mx, elbow_y), (mx, my + 28), marker]


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
    draw_shadowed_box(draw, (x, y, x + w, y + h), radius=22, fill=(255, 255, 255, 250), outline=color + (255,))

    badge_cx, badge_cy = x + 28, y + 28
    draw.ellipse([badge_cx - 20, badge_cy - 20, badge_cx + 20, badge_cy + 20], fill=color + (255,))
    draw.text((badge_cx, badge_cy - 1), str(number), font=fonts["badge"], fill="white", anchor="mm")

    draw.text((x + 58, y + 12), title, font=fonts["title"], fill=color + (255,))

    current_y = y + 52
    for line in wrap_text(draw, metric, fonts["metric"], w - 34):
        draw.text((x + 18, current_y), line, font=fonts["metric"], fill=(45, 45, 45, 255))
        current_y += 28

    current_y += 2
    for line in wrap_text(draw, note, fonts["note"], w - 34):
        draw.text((x + 18, current_y), line, font=fonts["note"], fill=(95, 95, 95, 255))
        current_y += 24

    draw_marker(draw, marker, number, color, fonts["badge"])
    draw_arrow(draw, connector_points(box, marker, side, map_rect), color, width=4)


def main() -> None:
    base = Image.open(BASE_IMAGE).convert("RGBA")
    map_w, map_h = base.size

    canvas_w, canvas_h = 3400, 2050
    map_x, map_y = 700, 380
    map_rect = (map_x, map_y, map_x + map_w, map_y + map_h)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (247, 248, 244, 255))
    draw = ImageDraw.Draw(canvas)

    fonts = {
        "header": load_font(52, bold=True),
        "sub": load_font(22),
        "title": load_font(30, bold=True),
        "metric": load_font(24, bold=True),
        "note": load_font(22),
        "badge": load_font(26, bold=True),
        "footer_title": load_font(28, bold=True),
    }

    draw_shadowed_box(draw, (50, 50, 1880, 170), radius=26, fill=(255, 255, 255, 246), outline=(198, 202, 196, 255), shadow=0)
    draw.text((78, 68), "India Waste Ecosystem: Bottlenecks Applied on System Map", font=fonts["header"], fill=(28, 28, 28, 255))
    draw.text(
        (80, 126),
        "Mass-balance base: CPCB FY 2021-22 | Current signals: GFC 2024-25 and PIB January/March 2026",
        font=fonts["sub"],
        fill=(90, 90, 90, 255),
    )

    draw_shadowed_box(
        draw,
        (map_x - 16, map_y - 16, map_x + map_w + 16, map_y + map_h + 16),
        radius=18,
        fill=(255, 255, 255, 255),
        outline=(205, 209, 204, 255),
        shadow=10,
    )
    canvas.alpha_composite(base, (map_x, map_y))

    callouts = [
        {
            "number": 1,
            "title": "Source segregation gap",
            "metric": "20,830-ward gap between high collection and high segregation",
            "note": "Mixed waste enters at source and weakens every downstream recovery step.",
            "box": (60, 240, 560, 150),
            "anchor": (305, 640),
            "side": "right",
            "color": (206, 66, 66),
        },
        {
            "number": 2,
            "title": "Post-collection leakage",
            "metric": "13.9k TPD uncollected; 23.5k TPD collected but not scientifically routed",
            "note": "Material is still lost after collection, before circular processing fully begins.",
            "box": (60, 430, 560, 165),
            "anchor": (820, 690),
            "side": "right",
            "color": (206, 66, 66),
        },
        {
            "number": 3,
            "title": "Informal chain gap",
            "metric": "Value is captured informally, but formal integration remains weak",
            "note": "That limits traceability, quality control, and scale into the formal recycling chain.",
            "box": (60, 635, 560, 150),
            "anchor": (1135, 305),
            "side": "right",
            "color": (230, 126, 34),
        },
        {
            "number": 5,
            "title": "Offtake bottleneck",
            "metric": "Sorted material still needs buyers, specs, and stable demand",
            "note": "Without offtake, material backs up between aggregators and recyclers.",
            "box": (2780, 240, 560, 150),
            "anchor": (1600, 235),
            "side": "left",
            "color": (155, 89, 182),
        },
        {
            "number": 4,
            "title": "MRF quality bottleneck",
            "metric": "MRF capacity exists, but contaminated dry waste lowers output",
            "note": "The constraint is cleaner feedstock, not only more plants.",
            "box": (2780, 430, 560, 150),
            "anchor": (1320, 525),
            "side": "left",
            "color": (52, 152, 219),
        },
        {
            "number": 6,
            "title": "Residual dependence",
            "metric": "Only 54% of MSW was processed in FY 2021-22",
            "note": "Rejects still move to RDF, waste processing, or landfill instead of circular recovery.",
            "box": (2780, 620, 560, 165),
            "anchor": (1535, 760),
            "side": "left",
            "color": (46, 204, 113),
        },
        {
            "number": 7,
            "title": "Legacy waste drag",
            "metric": "~25 crore MT identified; >62% processed by Jan 31, 2026",
            "note": "~9.5 crore MT still remains nationally, keeping landfill pressure and remediation costs high.",
            "box": (940, 1540, 1520, 150),
            "anchor": (1445, 890),
            "side": "top",
            "color": (127, 140, 141),
        },
    ]

    for item in callouts:
        marker_abs = (map_x + item["anchor"][0], map_y + item["anchor"][1])
        draw_callout(
            draw=draw,
            fonts=fonts,
            number=item["number"],
            title=item["title"],
            metric=item["metric"],
            note=item["note"],
            box=item["box"],
            marker=marker_abs,
            side=item["side"],
            color=item["color"],
            map_rect=map_rect,
        )

    footer_rect = (60, 1810, 3340, 1985)
    draw_shadowed_box(draw, footer_rect, radius=22, fill=(255, 255, 255, 246), outline=(198, 202, 196, 255), shadow=0)
    draw.text((90, 1840), "Bottom line", font=fonts["footer_title"], fill=(30, 30, 30, 255))
    footer = (
        "India's main bottleneck is not just collection. It is moving clean, saleable material from generators "
        "through collectors and MRFs into aggregators and recyclers without leakage back into disposal."
    )
    for i, line in enumerate(wrap_text(draw, footer, fonts["note"], 3160)):
        draw.text((90, 1885 + i * 28), line, font=fonts["note"], fill=(85, 85, 85, 255))

    canvas.convert("RGB").save(OUTPUT_IMAGE, quality=95)


if __name__ == "__main__":
    main()
