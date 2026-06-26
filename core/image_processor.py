# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from PIL import Image, ImageOps

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def load_image(path: str, pixel_um: float = None) -> Image.Image:
    """Carga imagen o PDF.

    PDFs: se renderizan al DPI nativo de la impresora (25400 / pixel_um) para
    que cada píxel renderizado corresponda a un píxel de pantalla sin escalar.
    Si pixel_um no se proporciona, usa 600 DPI como fallback.

    Imágenes raster: se cargan tal cual (sin alterar la resolución).
    """
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        if not HAS_PYMUPDF:
            raise RuntimeError(
                "Soporte PDF no disponible. Instala PyMuPDF: pip install PyMuPDF"
            )
        target_dpi = (25_400.0 / pixel_um) if pixel_um else 600.0
        doc = fitz.open(path)
        page = doc[0]
        mat = fitz.Matrix(target_dpi / 72, target_dpi / 72)
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
    """Prepara la imagen para la impresora SIN escalar.

    La imagen se centra en el canvas. Si excede la pantalla se recorta;
    si es más pequeña queda rodeada de negro. Nunca se escala.
    """
    if invert:
        img = ImageOps.invert(img.convert("L"))

    canvas = Image.new("L", (res_x, res_y), 0)
    ox = (res_x - img.width) // 2
    oy = (res_y - img.height) // 2
    canvas.paste(img, (ox, oy))

    return canvas.convert("1")
