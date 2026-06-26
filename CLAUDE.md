# CLAUDE.md — pakuInsoladora

Herramienta open source para insolar PCBs presensibilizadas con impresoras de resina MSLA.

## Stack

- **Python 3.8+** con tkinter (GUI), Pillow (imágenes), PyMuPDF/fitz (PDF)
- **Formato de salida**: binario ANYCUBIC (`.pwmo`, `.pws`, `.pwmox`) con RLE PWS 1-bit
- **Builds**: PyInstaller vía GitHub Actions — Windows runner → `.exe`, Ubuntu 22.04 → binario Linux
- **Licencia**: GPL v3

## Estructura

```
pakuInsoladora/
├── main.py                    # GUI tkinter bilingüe ES/EN
├── core/
│   ├── image_processor.py     # Carga PDF/imagen, invierte, escala
│   └── formats/
│       └── anycubic.py        # Genera binario ANYCUBIC + dict PRINTERS
├── .github/workflows/
│   └── release.yml            # CI: build Windows + Linux en cada tag v*
├── requirements.txt           # Pillow, PyMuPDF
└── LICENSE                    # GPL v3
```

## Workflow de release

```bash
# Editar código, luego:
git add -A
git commit -m "feat: ..."
git tag v0.X.Y
git push && git push origin v0.X.Y
```

El CI de GitHub Actions compila automáticamente y crea la release con los dos binarios.

**Ojo con Windows**: el archivo `nul` aparece a veces en el directorio de trabajo. Está en `.gitignore`. Si `git add -A` falla, usar `git add` con archivos específicos.

## Añadir impresoras

En `core/formats/anycubic.py`, dict `PRINTERS`. Campos necesarios:
- `res_x`, `res_y`: resolución pantalla en píxeles
- `bed_x`, `bed_y`: tamaño cama en mm
- `pixel_um`: tamaño de píxel en micrómetros
- `ext`: extensión del archivo (`.pwmo`, `.pws`, etc.)
- `version`: versión del formato ANYCUBIC (515=Mono, 516=Mono X)

## GUI bilingüe

Todas las cadenas de UI están en el dict `STRINGS` en `main.py` con claves `"es"` y `"en"`. Botón ES/EN en el panel de controles. Al añadir texto nuevo, añadirlo en ambos idiomas.

## Web

Página en coletasWorkshop:
- ES: `src/proyectos/pakuinsoladora.njk` → `coletas.es/proyectos/pakuinsoladora/`
- EN: `src/proyectos/pakuinsoladora-en.njk` → `coletas.es/en/pakuinsoladora/`
- Las fotos usan las imágenes del proyecto original: `/img/pcb-anycubic-photon/`
- Deploy con `C:\desarrollo\coletasWorkshop\deploy.ps1` (incremental por hash MD5)
