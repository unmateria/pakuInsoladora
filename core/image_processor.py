# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from PIL import Image, ImageOps

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def load_image(path: str) -> Image.Image:
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        if not HAS_PYMUPDF:
            raise RuntimeError(
                "Soporte PDF no disponible. Instala PyMuPDF: pip install PyMuPDF"
            )
        doc = fitz.open(path)
        page = doc[0]
        # 300 DPI para resolución suficiente
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        doc.close()
        return img
    else:
        img = Image.open(path)
        return img.convert("L")


def prepare_for_printer(
    img: Image.Image,
    res_x: int,
    res_y: int,
    invert: bool,
    fit: bool,
) -> Image.Image:
    if invert:
        img = ImageOps.invert(img.convert("L"))

    if fit:
        # thumbnail() solo reduce; resize explícito también agranda imágenes pequeñas
        scale = min(res_x / img.width, res_y / img.height)
        new_w = max(1, round(img.width * scale))
        new_h = max(1, round(img.height * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Centrar en fondo negro con la resolución exacta del printer
    canvas = Image.new("L", (res_x, res_y), 0)
    offset_x = (res_x - img.width) // 2
    offset_y = (res_y - img.height) // 2
    canvas.paste(img, (offset_x, offset_y))

    return canvas.convert("1")
