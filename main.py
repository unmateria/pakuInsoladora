# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

from core.image_processor import load_image, prepare_for_printer, HAS_PYMUPDF
from core.formats.anycubic import PRINTERS, write_anycubic

PREVIEW_SIZE = (400, 600)

STRINGS = {
    "es": {
        "open_btn":      "Abrir imagen / PDF…",
        "no_file":       "(ningún archivo)",
        "printer_lbl":   "Impresora:",
        "exposure_lbl":  "Tiempo de exposición (s):",
        "invert_lbl":    "Invertir imagen",
        "fit_lbl":       "Ajustar a cama (escalar)",
        "export_btn":    "Exportar archivo…",
        "no_image_err":  "Abre una imagen primero.",
        "invalid_time":  "Tiempo de exposición inválido.",
        "saved_ok":      "✓ Guardado:\n{}",
        "error_pfx":     "Error: {}",
        "info_lbl":      "Sin imagen",
        "filetypes_all": "Imágenes y PDF",
        "filetypes_img": "Imágenes",
        "save_title":    "Archivo impresora (*{})",
        "save_all":      "Todos",
        "info_fmt":      "Imagen: {}×{} px  │  Cama: {:.1f}×{:.1f} mm  │  Pantalla: {}×{} px",
    },
    "en": {
        "open_btn":      "Open image / PDF…",
        "no_file":       "(no file)",
        "printer_lbl":   "Printer:",
        "exposure_lbl":  "Exposure time (s):",
        "invert_lbl":    "Invert image",
        "fit_lbl":       "Fit to bed (scale)",
        "export_btn":    "Export file…",
        "no_image_err":  "Open an image first.",
        "invalid_time":  "Invalid exposure time.",
        "saved_ok":      "✓ Saved:\n{}",
        "error_pfx":     "Error: {}",
        "info_lbl":      "No image",
        "filetypes_all": "Images and PDF",
        "filetypes_img": "Images",
        "save_title":    "Printer file (*{})",
        "save_all":      "All files",
        "info_fmt":      "Image: {}×{} px  │  Bed: {:.1f}×{:.1f} mm  │  Screen: {}×{} px",
    },
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("pakuInsoladora")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self._source_img = None
        self._source_path = None
        self._photo = None
        self._lang = "es"

        self._build_ui()

    def _s(self, key):
        return STRINGS[self._lang][key]

    def _build_ui(self):
        # ── Panel izquierdo ──────────────────────────────────────────────────
        left = tk.Frame(self, bg="#1e1e1e", padx=14, pady=14)
        left.pack(side=tk.LEFT, fill=tk.Y)

        # Fila superior: botón abrir + botón idioma
        top_row = tk.Frame(left, bg="#1e1e1e")
        top_row.pack(fill=tk.X, pady=(0, 0))

        self._btn_open = tk.Button(
            top_row, text=self._s("open_btn"),
            command=self._open_file,
            bg="#3c3c3c", fg="white", activebackground="#555",
            relief=tk.FLAT, padx=8, pady=6, cursor="hand2",
        )
        self._btn_open.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._btn_lang = tk.Button(
            top_row, text="EN",
            command=self._toggle_lang,
            bg="#3c3c3c", fg="#aaa", activebackground="#555",
            relief=tk.FLAT, padx=6, pady=6, cursor="hand2",
            font=("Courier", 9, "bold"),
        )
        self._btn_lang.pack(side=tk.LEFT, padx=(4, 0))

        self._lbl_file = tk.Label(
            left, text=self._s("no_file"), bg="#1e1e1e", fg="#888",
            wraplength=200, justify=tk.LEFT,
        )
        self._lbl_file.pack(pady=(4, 10), anchor=tk.W)

        ttk.Separator(left).pack(fill=tk.X, pady=6)

        self._lbl_printer = tk.Label(left, text=self._s("printer_lbl"), bg="#1e1e1e", fg="#ccc")
        self._lbl_printer.pack(anchor=tk.W)
        self._printer_var = tk.StringVar(value=list(PRINTERS.keys())[0])
        self._printer_menu = tk.OptionMenu(
            left, self._printer_var, *PRINTERS.keys(),
            command=lambda _: self._update_preview(),
        )
        self._printer_menu.config(bg="#3c3c3c", fg="white", activebackground="#555",
                                   relief=tk.FLAT, highlightthickness=0)
        self._printer_menu["menu"].config(bg="#3c3c3c", fg="white")
        self._printer_menu.pack(fill=tk.X, pady=(2, 10))

        self._lbl_exposure = tk.Label(left, text=self._s("exposure_lbl"), bg="#1e1e1e", fg="#ccc")
        self._lbl_exposure.pack(anchor=tk.W)
        self._exposure_var = tk.StringVar(value="8")
        tk.Entry(
            left, textvariable=self._exposure_var,
            bg="#3c3c3c", fg="white", insertbackground="white",
            relief=tk.FLAT, width=8,
        ).pack(anchor=tk.W, pady=(2, 10))

        self._invert_var = tk.BooleanVar(value=True)
        self._chk_invert = tk.Checkbutton(
            left, text=self._s("invert_lbl"),
            variable=self._invert_var, command=self._update_preview,
            bg="#1e1e1e", fg="#ccc", selectcolor="#3c3c3c",
            activebackground="#1e1e1e", activeforeground="white",
        )
        self._chk_invert.pack(anchor=tk.W)

        self._fit_var = tk.BooleanVar(value=True)
        self._chk_fit = tk.Checkbutton(
            left, text=self._s("fit_lbl"),
            variable=self._fit_var, command=self._update_preview,
            bg="#1e1e1e", fg="#ccc", selectcolor="#3c3c3c",
            activebackground="#1e1e1e", activeforeground="white",
        )
        self._chk_fit.pack(anchor=tk.W, pady=(0, 10))

        ttk.Separator(left).pack(fill=tk.X, pady=6)

        self._btn_export = tk.Button(
            left, text=self._s("export_btn"),
            command=self._export,
            bg="#0078d4", fg="white", activebackground="#006cc1",
            relief=tk.FLAT, padx=8, pady=6, cursor="hand2",
        )
        self._btn_export.pack(fill=tk.X)

        self._lbl_status = tk.Label(left, text="", bg="#1e1e1e", fg="#4ec94e",
                                     wraplength=200, justify=tk.LEFT)
        self._lbl_status.pack(pady=(6, 0), anchor=tk.W)

        # ── Panel derecho (preview) ───────────────────────────────────────────
        right = tk.Frame(self, bg="#111", padx=10, pady=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            right,
            width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1],
            bg="#111", highlightthickness=0,
        )
        self._canvas.pack()

        self._lbl_info = tk.Label(
            right, text=self._s("info_lbl"), bg="#111", fg="#555", font=("Courier", 9),
        )
        self._lbl_info.pack(pady=(6, 0))

    # ── Idioma ────────────────────────────────────────────────────────────────

    def _toggle_lang(self):
        self._lang = "en" if self._lang == "es" else "es"
        self._apply_lang()

    def _apply_lang(self):
        self._btn_lang.config(text="EN" if self._lang == "es" else "ES")
        self._btn_open.config(text=self._s("open_btn"))
        self._lbl_printer.config(text=self._s("printer_lbl"))
        self._lbl_exposure.config(text=self._s("exposure_lbl"))
        self._chk_invert.config(text=self._s("invert_lbl"))
        self._chk_fit.config(text=self._s("fit_lbl"))
        self._btn_export.config(text=self._s("export_btn"))
        if not self._source_path:
            self._lbl_file.config(text=self._s("no_file"))
        if not self._source_img:
            self._lbl_info.config(text=self._s("info_lbl"))
        else:
            self._update_preview()

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _open_file(self):
        ext_img = "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"
        if HAS_PYMUPDF:
            types = [(self._s("filetypes_all"), ext_img + " *.pdf")]
        else:
            types = [(self._s("filetypes_img"), ext_img)]
        path = filedialog.askopenfilename(filetypes=types)
        if not path:
            return
        try:
            self._source_img = load_image(path)
            self._source_path = path
            self._lbl_file.config(text=os.path.basename(path), fg="#ccc")
            self._lbl_status.config(text="")
            self._update_preview()
        except Exception as e:
            self._lbl_status.config(text=self._s("error_pfx").format(e), fg="#e05252")

    def _current_printer(self):
        return PRINTERS[self._printer_var.get()]

    def _update_preview(self):
        if self._source_img is None:
            return
        printer = self._current_printer()
        prepared = prepare_for_printer(
            self._source_img,
            printer["res_x"], printer["res_y"],
            self._invert_var.get(),
            self._fit_var.get(),
        )
        thumb = prepared.convert("L")
        thumb.thumbnail(PREVIEW_SIZE, Image.NEAREST)
        preview_canvas = Image.new("L", PREVIEW_SIZE, 0)
        ox = (PREVIEW_SIZE[0] - thumb.width) // 2
        oy = (PREVIEW_SIZE[1] - thumb.height) // 2
        preview_canvas.paste(thumb, (ox, oy))

        self._photo = ImageTk.PhotoImage(preview_canvas)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)

        self._lbl_info.config(
            text=self._s("info_fmt").format(
                self._source_img.width, self._source_img.height,
                printer["bed_x"], printer["bed_y"],
                printer["res_x"], printer["res_y"],
            ),
            fg="#666",
        )

    def _export(self):
        if self._source_img is None:
            self._lbl_status.config(text=self._s("no_image_err"), fg="#e05252")
            return
        try:
            exposure = float(self._exposure_var.get())
        except ValueError:
            self._lbl_status.config(text=self._s("invalid_time"), fg="#e05252")
            return

        printer = self._current_printer()
        ext = printer["ext"]
        base = os.path.splitext(os.path.basename(self._source_path or "pcb"))[0]

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=f"{base}{ext}",
            filetypes=[(self._s("save_title").format(ext), f"*{ext}"),
                       (self._s("save_all"), "*.*")],
        )
        if not path:
            return

        try:
            prepared = prepare_for_printer(
                self._source_img,
                printer["res_x"], printer["res_y"],
                self._invert_var.get(),
                self._fit_var.get(),
            )
            write_anycubic(path, prepared, printer, exposure)
            self._lbl_status.config(
                text=self._s("saved_ok").format(os.path.basename(path)), fg="#4ec94e"
            )
        except Exception as e:
            self._lbl_status.config(text=self._s("error_pfx").format(e), fg="#e05252")


if __name__ == "__main__":
    app = App()
    app.mainloop()
