# pakuInsoladora

Expose presensitized PCBs using a resin MSLA printer. Load a PDF or image from KiCad/Eagle, set the exposure time, export the file for the USB stick.

No UVtools. No slicer. No fuss.

## Download

Grab the latest binary from the [Releases page](https://github.com/unmateria/pakuInsoladora/releases/latest) — no installation needed:

- **Windows** → `pakuInsoladora-windows.exe`
- **Linux** → `pakuInsoladora-linux` (then `chmod +x`)

## How it works

1. Export the copper layer from KiCad/Eagle as a PNG, BMP or PDF
2. Open pakuInsoladora, load the file
3. Select your printer and exposure time (default: 8 s for Photon Mono)
4. Tick **Invert** if your export has traces in black on white (KiCad default — this protects the copper)
5. Click **Export** and copy the file to the USB stick
6. Print — the UV screen exposes the board in seconds

## Supported printers

| Printer | Resolution | Output |
|---------|-----------|--------|
| Anycubic Photon Mono | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono SE | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono X | 3840 × 2400 | `.pwmox` |
| Anycubic Photon S | 1440 × 2560 | `.pws` |

Adding a new printer is a one-liner in `core/formats/anycubic.py`. Open an issue with your printer's resolution and bed size if you'd like it added.

## Run from source

Requires Python 3.8+:

```bash
git clone https://github.com/unmateria/pakuInsoladora.git
cd pakuInsoladora
pip install -r requirements.txt
python main.py
```

## Build

Binaries are built automatically by GitHub Actions on every version tag using PyInstaller. To build locally:

```bash
pip install pyinstaller
# Windows
pyinstaller --onefile --windowed --name pakuInsoladora main.py
# Linux
pyinstaller --onefile --name pakuInsoladora main.py
```

## License

[GNU General Public License v3.0](LICENSE) — forks must remain free software.
