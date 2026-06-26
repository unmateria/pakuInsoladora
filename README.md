# pakuInsoladora

Herramienta open source para insolar PCBs presensibilizadas usando impresoras de resina MSLA (Anycubic Photon Mono, etc.).

## Flujo de uso

1. Exporta la capa de cobre de KiCad/Eagle como imagen (PNG o BMP a escala 1:1) o PDF
2. Abre `main.py`
3. Carga la imagen, selecciona la impresora y el tiempo de exposición
4. Exporta el archivo `.pwmo` al USB
5. Lanza la impresión — la pantalla UV insolará la placa en segundos

## Instalación

```bash
pip install -r requirements.txt
python main.py
```

## Impresoras soportadas

| Impresora              | Resolución    | Extensión |
|------------------------|---------------|-----------|
| Anycubic Photon Mono   | 1620 × 2560   | .pwmo     |
| Anycubic Photon Mono SE| 1620 × 2560   | .pwmo     |
| Anycubic Photon Mono X | 3840 × 2400   | .pwmox    |
| Anycubic Photon S      | 1440 × 2560   | .pws      |

## Tiempo de exposición

El tiempo depende de la placa presensibilizada y la potencia de la pantalla. Un punto de partida:

- Anycubic Photon Mono: **8 segundos**

Ajusta según el resultado del revelado.

## Sobre la inversión de imagen

KiCad exporta las pistas en **negro** sobre fondo blanco. Para insolar correctamente (las pistas protegen el cobre, el fondo se expone) hay que **invertir** la imagen — la opción viene activada por defecto.

## Licencia

[GNU General Public License v3.0](LICENSE) — cualquier fork o modificación debe seguir siendo software libre.
