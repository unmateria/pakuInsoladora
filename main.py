# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

from core.image_processor import load_image, prepare_for_printer, HAS_PYMUPDF
from core.formats.anycubic import PRINTERS, write_anycubic

PREVIEW_SIZE = (400, 600)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("pakuInsoladora")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self._source_img = None
        self._source_path = None
        self._photo = None

        self._build_ui()

    def _build_ui(self):
        # ── Panel izquierdo ──────────────────────────────────────────────────
        left = tk.Frame(self, bg="#1e1e1e", padx=14, pady=14)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(
            left, text="Abrir imagen / PDF…",
            command=self._open_file,
            bg="#3c3c3c", fg="white", activebackground="#555",
            relief=tk.FLAT, padx=8, pady=6, cursor="hand2",
        ).pack(fill=tk.X)

        self._lbl_file = tk.Label(
            left, text="(ningún archivo)", bg="#1e1e1e", fg="#888",
            wraplength=200, justify=tk.LEFT,
        )
        self._lbl_file.pack(pady=(4, 10), anchor=tk.W)

        ttk.Separator(left).pack(fill=tk.X, pady=6)

        tk.Label(left, text="Impresora:", bg="#1e1e1e", fg="#ccc").pack(anchor=tk.W)
        self._printer_var = tk.StringVar(value=list(PRINTERS.keys())[0])
        printer_menu = tk.OptionMenu(
            left, self._printer_var, *PRINTERS.keys(),
            command=lambda _: self._update_preview(),
        )
        printer_menu.config(bg="#3c3c3c", fg="white", activebackground="#555",
                            relief=tk.FLAT, highlightthickness=0)
        printer_menu["menu"].config(bg="#3c3c3c", fg="white")
        printer_menu.pack(fill=tk.X, pady=(2, 10))

        tk.Label(left, text="Tiempo de exposición (s):", bg="#1e1e1e", fg="#ccc").pack(anchor=tk.W)
        self._exposure_var = tk.StringVar(value="8")
        tk.Entry(
            left, textvariable=self._exposure_var,
            bg="#3c3c3c", fg="white", insertbackground="white",
            relief=tk.FLAT, width=8,
        ).pack(anchor=tk.W, pady=(2, 10))

        self._invert_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            left, text="Invertir imagen",
            variable=self._invert_var, command=self._update_preview,
            bg="#1e1e1e", fg="#ccc", selectcolor="#3c3c3c",
            activebackground="#1e1e1e", activeforeground="white",
        ).pack(anchor=tk.W)

        self._fit_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            left, text="Ajustar a cama (escalar)",
            variable=self._fit_var, command=self._update_preview,
            bg="#1e1e1e", fg="#ccc", selectcolor="#3c3c3c",
            activebackground="#1e1e1e", activeforeground="white",
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Separator(left).pack(fill=tk.X, pady=6)

        tk.Button(
            left, text="Exportar archivo…",
            command=self._export,
            bg="#0078d4", fg="white", activebackground="#006cc1",
            relief=tk.FLAT, padx=8, pady=6, cursor="hand2",
        ).pack(fill=tk.X)

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
            right, text="Sin imagen", bg="#111", fg="#555", font=("Courier", 9),
        )
        self._lbl_info.pack(pady=(6, 0))

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _open_file(self):
        types = [("Imágenes y PDF", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.pdf")]
        if not HAS_PYMUPDF:
            types = [("Imágenes", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif")]
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
            self._lbl_status.config(text=f"Error: {e}", fg="#e05252")

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
        # Escalar para preview
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
            text=(
                f"Imagen: {self._source_img.width}×{self._source_img.height} px  │  "
                f"Cama: {printer['bed_x']:.1f}×{printer['bed_y']:.1f} mm  │  "
                f"Pantalla: {printer['res_x']}×{printer['res_y']} px"
            ),
            fg="#666",
        )

    def _export(self):
        if self._source_img is None:
            self._lbl_status.config(text="Abre una imagen primero.", fg="#e05252")
            return
        try:
            exposure = float(self._exposure_var.get())
        except ValueError:
            self._lbl_status.config(text="Tiempo de exposición inválido.", fg="#e05252")
            return

        printer = self._current_printer()
        ext = printer["ext"]
        base = os.path.splitext(os.path.basename(self._source_path or "pcb"))[0]
        default_name = f"{base}{ext}"

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=default_name,
            filetypes=[(f"Archivo impresora (*{ext})", f"*{ext}"), ("Todos", "*.*")],
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
                text=f"✓ Guardado:\n{os.path.basename(path)}", fg="#4ec94e"
            )
        except Exception as e:
            self._lbl_status.config(text=f"Error: {e}", fg="#e05252")


if __name__ == "__main__":
    app = App()
    app.mainloop()
