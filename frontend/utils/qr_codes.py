from pathlib import Path
import segno
import base64
import math

LOGO_PATH = "static/images/logo/logo_main_compass_clear.png"

def create_qr_code(
        url: str,
        logo_filepath_relative: str = LOGO_PATH,
        output_path: str = None,
    ):

    LOGO_FILE = Path(__file__).resolve().parent.parent / logo_filepath_relative

    # FIXED OUTPUT SIZE (this is the key change)
    CANVAS_SIZE = 380

    BORDER_RATIO = 0.08  # percent padding inside canvas

    # -----------------------------
    # Generate QR (fixed version helps consistency too)
    # -----------------------------

    qr = segno.make(url, error="H", version=6)
    matrix = qr.matrix
    qr_size = len(matrix)

    # -----------------------------
    # Derived layout system
    # -----------------------------

    border = int(qr_size * BORDER_RATIO)

    grid_size = qr_size + border * 2

    scale = CANVAS_SIZE / grid_size

    center_x = CANVAS_SIZE / 2
    center_y = CANVAS_SIZE / 2

    radius = CANVAS_SIZE * 0.2

    # -----------------------------
    # Build SVG
    # -----------------------------

    svg_parts = []

    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" '
        f'shape-rendering="crispEdges">'
    )

    svg_parts.append('<rect width="100%" height="100%" fill="white"/>')

    # -----------------------------
    # Draw QR (scaled into fixed canvas)
    # -----------------------------

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if not val:
                continue

            px = (x + border) * scale
            py = (y + border) * scale

            dx = (px + scale / 2) - center_x
            dy = (py + scale / 2) - center_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < radius:
                continue

            svg_parts.append(
                f'<rect x="{px}" y="{py}" width="{scale}" height="{scale}" fill="#424f64"/>'
            )

    # -----------------------------
    # Add logo (fixed coordinate space)
    # -----------------------------

    png_bytes = LOGO_FILE.read_bytes()
    png_b64 = base64.b64encode(png_bytes).decode("utf-8")
    logo_data_uri = f"data:image/png;base64,{png_b64}"

    logo_size = radius * 5

    logo_x = center_x - logo_size / 2
    logo_y = center_y - logo_size / 2 + 8

    svg_parts.append(
        f'<image href="{logo_data_uri}" '
        f'x="{logo_x}" y="{logo_y}" '
        f'width="{logo_size}" height="{logo_size}" '
        f'preserveAspectRatio="xMidYMid meet" />'
    )

    svg_parts.append("</svg>")

    if output_path:
        Path(output_path).write_text("\n".join(svg_parts), encoding="utf-8")

    svg = "\n".join(svg_parts)
    return svg

if __name__ == '__main__':
    create_qr_code(
        "https://ballardgrapplingclub.com",
        output_path="ballard_branded_qr.svg"
    )
