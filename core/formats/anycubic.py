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
    },
    "Anycubic Photon Mono SE": {
        "res_x": 1620, "res_y": 2560,
        "bed_x": 82.62, "bed_y": 130.56,
        "pixel_um": 51.0,
        "ext": ".pwmo",
    },
    "Anycubic Photon Mono X": {
        "res_x": 3840, "res_y": 2400,
        "bed_x": 192.0, "bed_y": 120.0,
        "pixel_um": 50.0,
        "ext": ".pwmox",
    },
    "Anycubic Photon S": {
        "res_x": 1440, "res_y": 2560,
        "bed_x": 68.04, "bed_y": 120.96,
        "pixel_um": 47.25,
        "ext": ".pws",
    },
}

# Named section header: 12-byte name (ASCII, null-padded) + 4-byte length
_MARK_SIZE = 12
_BASE_LEN  = 16  # name(12) + length(4)


def _section(name: str, data: bytes, include_base_in_length: bool = False) -> bytes:
    """Wraps data in a named section block."""
    n = name.encode("ascii")
    n = n + b"\x00" * (_MARK_SIZE - len(n))
    length = (len(data) + _BASE_LEN) if include_base_in_length else len(data)
    return n + struct.pack("<I", length) + data


def encode_rle_pws(img_1bit: Image.Image) -> bytes:
    """1-bit PWS RLE: bit7=color, bits0-6=run_length-1 (max run 128)."""
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


def _make_preview(res_x: int = 224, res_y: int = 168) -> bytes:
    """PREVIEW section data: ResX(4) + Mark(4) + ResY(4) + RGB565 pixels."""
    pixel = struct.pack("<H", _rgb565(20, 20, 20))
    image_data = pixel * (res_x * res_y)
    # Mark = b'*\x00\x00\x00' as seen in real .pwmo files
    return (
        struct.pack("<I", res_x) +
        b"\x2a\x00\x00\x00" +
        struct.pack("<I", res_y) +
        image_data
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
    assert len(d) == 80, f"Header must be 80 bytes, got {len(d)}"
    return bytes(d)


def write_anycubic(filepath: str, img: Image.Image, printer: dict, exposure_time: float) -> None:
    img_1bit = img.convert("1")
    rle_data = encode_rle_pws(img_1bit)
    non_zero = sum(1 for p in img_1bit.getdata() if p)
    print_time = max(1, int(exposure_time))

    # Build named sections
    header_data  = _make_header(printer, exposure_time, print_time)
    header_sec   = _section("HEADER",  header_data)                   # 16 + 80 = 96 bytes

    preview_data = _make_preview()
    preview_sec  = _section("PREVIEW", preview_data, include_base_in_length=True)  # length includes base

    # LayerDef entry: DataAddr(I) DataLen(I) LiftH(f) LiftS(f) ExpTime(f) LayerH(f) NonZero(I) Pad(I)
    # DataAddress is filled in after we know layer_image_addr
    FILEMARK_SIZE = 48
    header_addr   = FILEMARK_SIZE
    preview_addr  = header_addr + len(header_sec)
    layerdef_addr = preview_addr + len(preview_sec)

    layer_entry_size = 32
    layerdef_data_size = 4 + layer_entry_size           # LayerCount(4) + 1 entry
    layer_image_addr = layerdef_addr + _BASE_LEN + layerdef_data_size

    layer_entry = struct.pack(
        "<IIffffII",
        layer_image_addr,  # DataAddress (absolute)
        len(rle_data),     # DataLength
        6.0,               # LiftHeight
        3.0,               # LiftSpeed
        exposure_time,     # ExposureTime
        0.05,              # LayerHeight
        non_zero,          # NonZeroPixelCount
        0,                 # Padding
    )
    layerdef_sec = _section("LAYERDEF", struct.pack("<I", 1) + layer_entry)

    # FileMark (48 bytes): mark(12) + version(4) + ntables(4) + 7 addresses(4 each)
    filemark = (
        b"ANYCUBIC\x00\x00\x00\x00" +
        struct.pack("<I", 1) +            # Version = 1
        struct.pack("<I", 0) +            # NumberOfTables = 0 (unused in v1)
        struct.pack("<I", header_addr) +
        struct.pack("<I", 0) +            # SoftwareAddress = 0 (not present in v1)
        struct.pack("<I", preview_addr) +
        struct.pack("<I", 0) +            # LayerImageColorTableAddress = 0
        struct.pack("<I", layerdef_addr) +
        struct.pack("<I", 0) +            # ExtraAddress = 0
        struct.pack("<I", layer_image_addr)
    )
    assert len(filemark) == FILEMARK_SIZE

    with open(filepath, "wb") as f:
        f.write(filemark)
        f.write(header_sec)
        f.write(preview_sec)
        f.write(layerdef_sec)
        f.write(rle_data)
