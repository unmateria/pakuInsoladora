# pakuInsoladora

[🇪🇸 Español](#español) · [🇬🇧 English](#english)

---

## Español

Insoladora de PCBs para impresoras de resina MSLA. Carga un PDF o imagen de KiCad/Eagle, ajusta el tiempo de exposición y exporta el archivo listo para el USB. Sin UVtools. Sin historias.

![Pantalla UV de la Anycubic Photon Mono proyectando el trazado de una PCB](https://coletas.es/img/pcb-anycubic-photon/01-pcb-anycubic-photon-exposicion-uv.jpg)

![Placa presensibilizada apoyada sobre la pantalla con un móvil haciendo de peso](https://coletas.es/img/pcb-anycubic-photon/02-pcb-anycubic-placa-sobre-pantalla.jpg)

### Descargar

Descarga el binario desde la [página de releases](https://github.com/unmateria/pakuInsoladora/releases/latest) — sin instalación:

- **Windows** → `pakuInsoladora-windows.exe`
- **Linux** → `pakuInsoladora-linux` (luego `chmod +x`)

### Cómo funciona

1. Exporta la capa de cobre de KiCad/Eagle como PNG, BMP o PDF
2. Abre pakuInsoladora y carga el archivo
3. Selecciona la impresora y el tiempo de exposición (por defecto 8 s para la Photon Mono)
4. Marca **Invertir** si el export tiene las pistas en negro sobre blanco (por defecto en KiCad — así el cobre queda protegido)
5. Pulsa **Exportar** y copia el archivo al USB
6. Lanza la impresión — la pantalla UV insolará la placa en segundos

![PCB terminado después del grabado con percloruro: pistas limpias y precisas](https://coletas.es/img/pcb-anycubic-photon/03-pcb-anycubic-photon-resultado-final.jpg)

### Impresoras soportadas

| Impresora | Resolución | Archivo |
|-----------|-----------|---------|
| Anycubic Photon Mono | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono SE | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono X | 3840 × 2400 | `.pwmox` |
| Anycubic Photon S | 1440 × 2560 | `.pws` |

Para añadir otra impresora, abre un issue con la resolución y el tamaño de cama.

### Construir desde el fuente

Requiere Python 3.8+:

```bash
git clone https://github.com/unmateria/pakuInsoladora.git
cd pakuInsoladora
pip install -r requirements.txt
python main.py
```

### Licencia

[GNU General Public License v3.0](LICENSE) — cualquier fork debe seguir siendo software libre.

---

## English

PCB exposure tool for MSLA resin printers. Load a PDF or image from KiCad/Eagle, set the exposure time, export the file for the USB stick. No UVtools. No fuss.

![Anycubic Photon Mono UV screen projecting a PCB trace during exposure](https://coletas.es/img/pcb-anycubic-photon/01-pcb-anycubic-photon-exposicion-uv.jpg)

![Presensitized board resting on the screen with a phone as a weight to ensure contact](https://coletas.es/img/pcb-anycubic-photon/02-pcb-anycubic-placa-sobre-pantalla.jpg)

### Download

Grab the latest binary from the [Releases page](https://github.com/unmateria/pakuInsoladora/releases/latest) — no installation needed:

- **Windows** → `pakuInsoladora-windows.exe`
- **Linux** → `pakuInsoladora-linux` (then `chmod +x`)

### How it works

1. Export the copper layer from KiCad/Eagle as a PNG, BMP or PDF
2. Open pakuInsoladora and load the file
3. Select your printer and exposure time (default: 8 s for Photon Mono)
4. Tick **Invert** if your export has traces in black on white (KiCad default — this protects the copper)
5. Click **Export** and copy the file to the USB stick
6. Print — the UV screen exposes the board in seconds

![Finished PCB after ferric chloride etching: clean traces and well-defined pads](https://coletas.es/img/pcb-anycubic-photon/03-pcb-anycubic-photon-resultado-final.jpg)

### Supported printers

| Printer | Resolution | Output |
|---------|-----------|--------|
| Anycubic Photon Mono | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono SE | 1620 × 2560 | `.pwmo` |
| Anycubic Photon Mono X | 3840 × 2400 | `.pwmox` |
| Anycubic Photon S | 1440 × 2560 | `.pws` |

To add another printer, open an issue with the resolution and bed size.

### Run from source

Requires Python 3.8+:

```bash
git clone https://github.com/unmateria/pakuInsoladora.git
cd pakuInsoladora
pip install -r requirements.txt
python main.py
```

### License

[GNU General Public License v3.0](LICENSE) — forks must remain free software.
