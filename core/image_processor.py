# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from PIL import Image, ImageOps

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

PDF_DPI = 600  # Alta resolución para que el escalado posterior sea siempre hacia abajo


def load_image(path: str) -> Image.Image:
    """Carga imagen o PDF y devuelve Image en modo L."""
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        if not HAS_PYMUPDF:
            raise RuntimeError(
                "Soporte PDF no disponible. Instala PyMuPDF: pip install PyMuPDF"
            )
        doc = fitz.open(path)
        page = doc[0]
        mat = fitz.Matrix(PDF_DPI / 72, PDF_DPI / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        doc.close()
        return img
    else:
        return Image.open(path).convert("L")


def prepare_for_printer(
    img: Image.Image,
    res_x: int,
    res_y: int,
    invert: bool,
) -> Image.Image:
    """Prepara la imagen para la impresora.

    Escala siempre de forma proporcional para que quepa en la pantalla.
    Nunca deforma el aspecto. Centra en canvas negro.
    """
    if invert:
        img = ImageOps.invert(img.convert("L"))

    scale = min(res_x / img.width, res_y / img.height)
    new_w = max(1, round(img.width * scale))
    new_h = max(1, round(img.height * scale))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("L", (res_x, res_y), 0)
    ox = (res_x - new_w) // 2
    oy = (res_y - new_h) // 2
    canvas.paste(img, (ox, oy))

    return canvas.convert("1")
