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
        "rle": "pw0",
    },
    "Anycubic Photon Mono SE": {
        "res_x": 1620, "res_y": 2560,
        "bed_x": 82.62, "bed_y": 130.56,
        "pixel_um": 51.0,
        "ext": ".pwmo",
        "rle": "pw0",
    },
    "Anycubic Photon Mono X": {
        "res_x": 3840, "res_y": 2400,
        "bed_x": 192.0, "bed_y": 120.0,
        "pixel_um": 50.0,
        "ext": ".pwmox",
        "rle": "pw0",
    },
    "Anycubic Photon S": {
        "res_x": 1440, "res_y": 2560,
        "bed_x": 68.04, "bed_y": 120.96,
        "pixel_um": 47.25,
        "ext": ".pws",
        "rle": "pws",
    },
}

_MARK_SIZE = 12
_BASE_LEN  = 16  # name(12) + length(4)


def _section(name: str, data: bytes, include_base_in_length: bool = False) -> bytes:
    n = name.encode("ascii").ljust(_MARK_SIZE, b"\x00")
    length = (len(data) + _BASE_LEN) if include_base_in_length else len(data)
    return n + struct.pack("<I", length) + data


# ── RLE encoders ─────────────────────────────────────────────────────────────

def encode_rle_pw0(img: Image.Image) -> bytes:
    """
    PW0 4-bit RLE (used by .pwmo, .pwmox, and all non-.pws Anycubic formats).

    Each run of black or white pixels encodes as 2 bytes:
      byte1 = (color_nibble << 4) | (run >> 8)   color: 0x0=black, 0xF=white
      byte2 = run & 0xFF
    Max run per pair: 4095 pixels.

    Grey values use 1 byte: (code << 4) | short_run  (max 15 px per byte).
    """
    pixels = list(img.convert("L").getdata())
    result = bytearray()
    i = 0
    total = len(pixels)
    while i < total:
        val = pixels[i]
        run = 1
        while i + run < total and run < 0xFFF and pixels[i + run] == val:
            run += 1
        run = min(run, 0xFFF)

        if val == 0:       # black: code 0x0, 2-byte extended run
            result.append(run >> 8)
            result.append(run & 0xFF)
        elif val >= 255:   # white: code 0xF, 2-byte extended run
            result.append(0xF0 | (run >> 8))
            result.append(run & 0xFF)
        else:              # grey: 1 byte, max 15 pixels per byte
            code = val >> 4
            if code == 0:    code = 1   # don't collide with black
            if code == 0xF:  code = 0xE  # don't collide with white
            short_run = min(run, 15)
            result.append((code << 4) | short_run)
            run = short_run

        i += run
    return bytes(result)


def encode_rle_pws(img: Image.Image) -> bytes:
    """
    PWS 1-bit RLE (used only by .pws — Photon S).
    Each byte: bit7=color (1=white, 0=black), bits0-6=run_length-1 (max 128).
    """
    pixels = list(img.convert("1").getdata())
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


# ── File sections ─────────────────────────────────────────────────────────────

def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _make_preview(res_x: int = 224, res_y: int = 168) -> bytes:
    """PREVIEW section data: ResX(4) + Mark(4) + ResY(4) + RGB565 pixels."""
    pixel = struct.pack("<H", _rgb565(20, 20, 20))
    return (
        struct.pack("<I", res_x) +
        b"\x2a\x00\x00\x00" +   # mark field as seen in real .pwmo files
        struct.pack("<I", res_y) +
        pixel * (res_x * res_y)
    )


def _make_header(printer: dict, exposure_time: float, print_time: int) -> bytes:
    """HEADER section data: exactly 80 bytes."""
    d = bytearray()
    d += struct.pack("<f", printer["pixel_um"])  # PixelSizeUm
    d += struct.pack("<f", 0.05)                 # LayerHeight
    d += struct.pack("<f", exposure_time)        # ExposureTime
    d += struct.pack("<f", 0.5)                  # WaitTimeBeforeCure
    d += struct.pack("<f", exposure_time)        # BottomExposureTime
    d += struct.pack("<f", 0.0)                  # BottomLayersCount
    d += struct.pack("<f", 6.0)                  # LiftHeight
    d += struct.pack("<f", 3.0)                  # LiftSpeed
    d += struct.pack("<f", 2.0)                  # RetractSpeed
    d += struct.pack("<f", 0.0)                  # VolumeMl
    d += struct.pack("<I", 1)                    # AntiAliasing
    d += struct.pack("<I", printer["res_x"])     # ResolutionX
    d += struct.pack("<I", printer["res_y"])     # ResolutionY
    d += struct.pack("<f", 0.0)                  # WeightG
    d += struct.pack("<f", 0.0)                  # Price
    d += b"\x00\x00\x00\x00"                    # PriceCurrencySymbol
    d += struct.pack("<I", 0)                    # PerLayerSettings
    d += struct.pack("<I", print_time)           # PrintTime
    d += struct.pack("<I", 0)                    # TransitionLayerCount
    d += struct.pack("<I", 0)                    # AdvancedMode
    assert len(d) == 80
    return bytes(d)


# ── Main writer ───────────────────────────────────────────────────────────────

def write_anycubic(filepath: str, img: Image.Image, printer: dict, exposure_time: float) -> None:
    print_time = max(1, int(exposure_time))

    # Encode layer image
    if printer.get("rle", "pw0") == "pws":
        rle_data = encode_rle_pws(img)
    else:
        rle_data = encode_rle_pw0(img)

    non_zero = sum(1 for p in img.convert("L").getdata() if p > 127)

    # Build named sections
    header_sec  = _section("HEADER",  _make_header(printer, exposure_time, print_time))
    preview_sec = _section("PREVIEW", _make_preview(), include_base_in_length=True)

    # Compute offsets
    FILEMARK_SIZE   = 48
    header_addr     = FILEMARK_SIZE
    preview_addr    = header_addr + len(header_sec)
    layerdef_addr   = preview_addr + len(preview_sec)
    layer_image_addr = layerdef_addr + _BASE_LEN + 4 + 32  # +base +LayerCount +1 LayerDef entry

    layer_entry = struct.pack(
        "<IIffffII",
        layer_image_addr,  # DataAddress (absolute file offset)
        len(rle_data),     # DataLength
        6.0,               # LiftHeight
        3.0,               # LiftSpeed
        exposure_time,     # ExposureTime
        0.05,              # LayerHeight
        non_zero,          # NonZeroPixelCount
        0,                 # Padding
    )
    layerdef_sec = _section("LAYERDEF", struct.pack("<I", 1) + layer_entry)

    # FileMark: mark(12) + version(4) + ntables(4) + 7 addresses(4 each) = 48 bytes
    filemark = (
        b"ANYCUBIC\x00\x00\x00\x00" +
        struct.pack("<I", 1) +              # Version = 1
        struct.pack("<I", 0) +              # NumberOfTables = 0 (unused in v1)
        struct.pack("<I", header_addr) +
        struct.pack("<I", 0) +              # SoftwareAddress = 0
        struct.pack("<I", preview_addr) +
        struct.pack("<I", 0) +              # LayerImageColorTableAddress = 0
        struct.pack("<I", layerdef_addr) +
        struct.pack("<I", 0) +              # ExtraAddress = 0
        struct.pack("<I", layer_image_addr)
    )
    assert len(filemark) == FILEMARK_SIZE

    with open(filepath, "wb") as f:
        f.write(filemark)
        f.write(header_sec)
        f.write(preview_sec)
        f.write(layerdef_sec)
        f.write(rle_data)
