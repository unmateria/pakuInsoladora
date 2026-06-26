# pakuInsoladora — PCB exposure tool for MSLA resin printers
# Copyright (C) 2024 pakuInsoladora contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import struct
from PIL import Image

PRINTERS = {
    "Anycubic Photon Mono": {
        "res_x": 1620, "res_y": 2560,
        "bed_x": 82.62, "bed_y": 130.56,
        "pixel_um": 51.0,
        "ext": ".pwmo",
        "version": 515,
    },
    "Anycubic Photon Mono SE": {
        "res_x": 1620, "res_y": 2560,
        "bed_x": 82.62, "bed_y": 130.56,
        "pixel_um": 51.0,
        "ext": ".pwmo",
        "version": 515,
    },
    "Anycubic Photon Mono X": {
        "res_x": 3840, "res_y": 2400,
        "bed_x": 192.0, "bed_y": 120.0,
        "pixel_um": 50.0,
        "ext": ".pwmox",
        "version": 516,
    },
    "Anycubic Photon S": {
        "res_x": 1440, "res_y": 2560,
        "bed_x": 68.04, "bed_y": 120.96,
        "pixel_um": 47.25,
        "ext": ".pws",
        "version": 515,
    },
}


def encode_rle_pws(img_1bit: Image.Image) -> bytes:
    pixels = list(img_1bit.getdata())
    result = bytearray()
    i = 0
    total = len(pixels)
    while i < total:
        color = 1 if pixels[i] else 0
        run = 1
        while i + run < total and run < 128 and (1 if pixels[i + run] else 0) == color:
            run += 1
        result.append((color << 7) | (run - 1))
        i += run
    return bytes(result)


def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def generate_preview_rgb565(size=(224, 168)) -> bytes:
    w, h = size
    pixel = struct.pack("<H", _rgb565(20, 20, 20))
    return pixel * (w * h)


def _build_header(printer, exposure_time, print_time) -> bytes:
    data = bytearray()
    data += struct.pack("<f", printer["pixel_um"])
    data += struct.pack("<f", 0.05)            # LayerHeight
    data += struct.pack("<f", exposure_time)
    data += struct.pack("<f", 1.0)             # WaitTimeBeforeCure
    data += struct.pack("<f", exposure_time)   # BottomExposureTime
    data += struct.pack("<f", 0.0)             # BottomLayersCount
    data += struct.pack("<f", 5.0)             # LiftHeight
    data += struct.pack("<f", 60.0)            # LiftSpeed
    data += struct.pack("<f", 150.0)           # RetractSpeed
    data += struct.pack("<f", 0.0)             # VolumeMl
    data += struct.pack("<I", 1)               # AntiAliasing
    data += struct.pack("<I", printer["res_x"])
    data += struct.pack("<I", printer["res_y"])
    data += struct.pack("<f", 0.0)             # WeightG
    data += struct.pack("<f", 0.0)             # Price
    data += b'\x00\x00\x00\x00'               # PriceCurrencySymbol
    data += struct.pack("<I", 0)               # PerLayerSettings
    data += struct.pack("<I", print_time)      # PrintTime
    data += struct.pack("<I", 0)               # TransitionLayerCount
    data += struct.pack("<I", 0)               # AdvancedMode
    return bytes(data)


def write_anycubic(filepath: str, img: Image.Image, printer: dict, exposure_time: float) -> None:
    img_1bit = img.convert("1")
    rle_data = encode_rle_pws(img_1bit)
    non_zero = sum(1 for p in img_1bit.getdata() if p)

    software_name = b"pakuInsoladora"
    software_section = struct.pack("<I", len(software_name)) + software_name

    preview_w, preview_h = 224, 168
    preview_raw = generate_preview_rgb565((preview_w, preview_h))
    preview_section = (
        struct.pack("<I", preview_w) +
        struct.pack("<I", preview_h) +
        struct.pack("<I", len(preview_raw)) +
        preview_raw
    )

    print_time = max(1, int(exposure_time))
    header_section = _build_header(printer, exposure_time, print_time)

    color_table_section = b""
    extra_section = b""

    FILEMARK_SIZE = 48  # 12 + 9 * 4

    header_addr      = FILEMARK_SIZE
    software_addr    = header_addr + len(header_section)
    preview_addr     = software_addr + len(software_section)
    color_table_addr = preview_addr + len(preview_section)
    layer_def_addr   = color_table_addr + len(color_table_section)
    extra_addr       = layer_def_addr + 4 + 32  # LayerCount(4) + 1 entry(32)
    layer_image_addr = extra_addr + len(extra_section)

    # LayerDefinition entry (32 bytes):
    # DataAddress(I) DataLength(I) LiftHeight(f) LiftSpeed(f)
    # ExposureTime(f) LayerHeight(f) NonZeroPixelCount(I) Padding(I)
    layer_entry = struct.pack(
        "<IIffffII",
        layer_image_addr,
        len(rle_data),
        5.0,
        60.0,
        exposure_time,
        0.05,
        non_zero,
        0,
    )
    layer_def_section = struct.pack("<I", 1) + layer_entry  # LayerCount=1

    filemark = bytearray()
    filemark += b"ANYCUBIC\x00\x00\x00\x00"
    filemark += struct.pack("<I", printer["version"])
    filemark += struct.pack("<I", 8)               # NumberOfTables
    filemark += struct.pack("<I", header_addr)
    filemark += struct.pack("<I", software_addr)
    filemark += struct.pack("<I", preview_addr)
    filemark += struct.pack("<I", color_table_addr)
    filemark += struct.pack("<I", layer_def_addr)
    filemark += struct.pack("<I", extra_addr)
    filemark += struct.pack("<I", layer_image_addr)

    with open(filepath, "wb") as f:
        f.write(filemark)
        f.write(header_section)
        f.write(software_section)
        f.write(preview_section)
        f.write(color_table_section)
        f.write(layer_def_section)
        f.write(extra_section)
        f.write(rle_data)
