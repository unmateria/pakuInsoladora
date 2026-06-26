# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from PIL import Image, ImageOps

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

PDF_DPI = 600  # Renderizar PDFs a alta resolución para evitar bordes dentados


def load_image(path: str):
    """Carga imagen o PDF. Devuelve (img_L, source_dpi).
    source_dpi es PDF_DPI para PDFs, None para imágenes raster."""
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
        return img, PDF_DPI
    else:
        img = Image.open(path).convert("L")
        return img, None


def prepare_for_printer(
    img: Image.Image,
    res_x: int,
    res_y: int,
    pixel_um: float,
    invert: bool,
    fit: bool,
    source_dpi: int = None,
) -> Image.Image:
    """Procesa la imagen para la impresora.

    fit=True  → escala para rellenar la pantalla (cambia escala física).
    fit=False → escala 1:1 físico si se conoce source_dpi; si no, sin escala.
    """
    if invert:
        img = ImageOps.invert(img.convert("L"))

    if fit:
        scale = min(res_x / img.width, res_y / img.height)
    elif source_dpi is not None:
        # 1:1 físico: printer_dpi / source_dpi
        printer_dpi = 25_400.0 / pixel_um
        scale = printer_dpi / source_dpi
    else:
        scale = 1.0

    if abs(scale - 1.0) > 0.001:
        new_w = max(1, round(img.width * scale))
        new_h = max(1, round(img.height * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Centrar en canvas negro con la resolución exacta del printer
    canvas = Image.new("L", (res_x, res_y), 0)
    offset_x = (res_x - img.width) // 2
    offset_y = (res_y - img.height) // 2
    canvas.paste(img, (offset_x, offset_y))

    return canvas.convert("1")
