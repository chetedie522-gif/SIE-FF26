# SIE FF26 — Sitio público (GitHub Pages)

Sitio estático con los tableros de la obra **FF26 · Ampliación nave 20x35** (Cúpula Estructuras).
Se publica con **GitHub Pages**. Es la copia **publicada**; la fuente de datos vive en OneDrive
(`SIE_FF26/`), y este sitio se **regenera** desde ahí.

## Estructura
```
index.html      portada con accesos
dashboard/      avance físico (público, sin plata) — index.html + datos.json
economico/      económico y flujo — index.html + economia.json
control/         control de material y cobros — index.html (datos embebidos)
pendientes/     tareas y alertas — index.html + pendientes.json
```
Cada tablero lee su `.json` con ruta relativa → en Pages queda **en vivo al refrescar**.
No se sube ningún JSON confidencial crudo (APU por insumo, registros de compra): solo lo que cada tablero muestra.

## Cómo actualizar el sitio
Desde la PC con Python (fuente en OneDrive):
```bash
# 1) regenerar los tableros que hayan cambiado (económico, pendientes, etc.) con los gen_*.py del _sistema
# 2) rearmar la carpeta del sitio:
python "<...>/SIE_FF26/_sistema/build_site.py"
# 3) publicar:
cd ~/SIE_FF26_site
git add -A && git commit -m "update datos" && git push
```
Esto se puede dejar como **tarea programada** (regenera + push solo).

## Dominio
Arranca en la URL gratis `https://<usuario>.github.io/<repo>/`.
Para usar `cupula.com.py` (ej. `ff26.cupula.com.py`): agregar un archivo `CNAME` con ese subdominio
y un registro **CNAME** en el DNS de cupula.com.py apuntando a `<usuario>.github.io`.
