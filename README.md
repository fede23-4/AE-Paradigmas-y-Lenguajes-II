# AE-Paradigmas-y-Lenguajes-II

Sistema de gestión de heladería desarrollado en **Python + Tkinter** con carga de datos desde **JSON**, correspondiente a la **Actividad de Evaluación 4 (PLP2-AE4-2026)**.

## Ejecución

```bash
uv run AE4v2.py
```

## Estructura del proyecto

- `AE4v2.py`: Aplicación principal (clase `Heladeria`, estadísticas e interfaz gráfica en Tkinter).
- `modelos/`: Modelo de dominio POO separado de la interfaz:
  - `modelos/sabor.py`: Clase `Sabor` (`id`, `nombre`, `elaboracion` industrial/artesanal, `precio_por_kilo`).
  - `modelos/pote.py`: Clase `Pote` (registro de kilos servidos y dinero recaudado por sabor).
  - `modelos/recipiente.py`: Jerarquía polimórfica de presentaciones sin condicionales `if` por tipo:
    - `Recipiente`: Presentaciones por peso (`Kilo`, `Medio kilo` +10%, `Cuarto kilo` +20%) con hasta 4 sabores.
    - `PresentacionPorPorcion(Recipiente)`: Presentaciones por porción a precio fijo de $5.000 (`Cucurucho dulce` 100 g, `Vasito` 120 g) con hasta 2 sabores.
  - `modelos/venta.py`: Clase `Venta` con soporte multi-sabor, agregados y salsas, y delegación polimórfica de cálculo de aportes y precio total.
  - `modelos/combo.py`: Clase `Combo` (pedido sugerido que se carga entero en la venta, con descuento opcional en %).
  - `modelos/extra.py`: Clase `Extra` (agregado con precio por unidad: cucurucho, vasito, etc.) y `Salsa(Extra)`, que redefine `calcular_precio` para ser siempre sin costo.
- `scripts/`: Archivos JSON de configuración inicial:
  - `scripts/sabores_iniciales.json`: 10 sabores iniciales (5 industriales a $12.000/kg y 5 artesanales a $15.000/kg).
  - `scripts/potes.json`: potes del mostrador (`id`, `sabor_id`, fecha de incorporación y stock). Un sabor puede tener varios potes. Se crea solo la primera vez que la app guarda; mientras no exista, los potes se leen del formato anterior de `sabores_iniciales.json`.
  - `scripts/tamanos_pote.json`: 5 tamaños de pote/presentaciones con sus parámetros de negocio.
  - `scripts/sugerencias.json`: combos (pote + sabores + agregados + salsas, por id, y `descuento_pct`). Se reescribe al crear, editar o eliminar combos desde Catálogo.
  - `scripts/extras.json`: agregados con precio (Cucurucho, Cucurucho bañado, Vasito, Bolsa térmica) y salsas sin costo (Chocolate, Dulce de leche, Caramelo, Frutilla).
- `contexto.plantuml`: Diagrama de contexto del sistema en PlantUML.
- `archive/`: Versiones anteriores archivadas (`archive/AE v2.py`).

## Cambios realizados

1. **Separación del modelo de dominio (`modelos/`):**
   - Se extrajeron las clases `Sabor`, `Pote`, `Recipiente`, `PresentacionPorPorcion` y `Venta` a módulos independientes dentro del paquete `modelos/`.
2. **Herencia y polimorfismo en presentaciones (sin `if`):**
   - Se simplificó el modelo de presentaciones en dos clases polimórficas (`Recipiente` para venta por peso con recargo porcentual y `PresentacionPorPorcion` para venta por unidad a precio fijo).
3. **Externalización de datos iniciales en JSON (`scripts/`):**
   - Se crearon `scripts/sabores_iniciales.json` y `scripts/tamanos_pote.json` para inicializar los 10 sabores del enunciado y las 5 presentaciones sin hardcodear listas en el arranque.
4. **Soporte de múltiples sabores por venta e interfaz gráfica (`AE4v2.py`):**
   - Se adaptó `Venta` y `Heladeria` para admitir mezclas de hasta 4 sabores (o hasta 2 en `Cucurucho dulce` y `Vasito`), prorrateando en partes iguales los kilos y calculando la recaudación proporcional en las estadísticas.
   - Se actualizaron las etiquetas de la pestaña *Nueva venta* a **Sabores** (4 selectores con bloqueo automático del 3° y 4° sabor según el máximo permitido por la presentación) y **Tamaño de pote**.
5. **Configuración y organización del repositorio:**
   - Se inicializó la configuración de `uv` (`pyproject.toml`, `uv.lock`, `.python-version`), se renombró el script principal a `AE4v2.py`, se sumó `contexto.plantuml` y se movió `AE v2.py` a `archive/`.
6. **Nueva venta por pasos y rediseño visual:**
   - La venta se arma en 4 pasos: **1)** elegir el pote, **2)** elegir los sabores (limitados según el pote y bloqueados si no hay stock), **3)** sumar agregados con contador (se cobran aparte) y **4)** elegir salsas de regalo.
   - Un ticket "Tu pedido" muestra en vivo el detalle, los gramos por sabor y el total; las últimas ventas quedan debajo y el historial completo pasó a *Resumen → Historial de ventas*.
   - Se reemplazaron las pestañas y combos del sistema por tarjetas, chips y botones dibujados (bordes redondeados e íconos de pote, cucurucho y vasito).
   - La recaudación total incluye los agregados; los porcentajes de recaudación por sabor/pote se calculan solo sobre lo cobrado por helado.
7. **Combos sugeridos y sabores más populares:**
   - Arriba de la venta hay combos que, al tocarlos, cargan solos el pote, los sabores, los agregados y las salsas (después se pueden modificar). Si falta stock de algún sabor, se avisa.
   - Los combos se definen en `scripts/sugerencias.json`.
   - La sección *Los más populares* muestra el top 5 de sabores calculado a partir de las ventas (`Heladeria.sabores_populares`): cuenta en cuántas ventas aparece cada sabor y se reordena sola después de cada venta. Tocando uno se suma al pedido.
8. **Corrección: sabores duplicados al agregar potes:**
   - Antes, `sabores_iniciales.json` se armaba recorriendo los potes, así que un segundo pote de un sabor se convertía en un sabor repetido al reiniciar. Ahora los sabores se guardan en `sabores_iniciales.json` y los potes en `scripts/potes.json`.
   - Los ids nuevos se calculan como el mayor id existente + 1 (`Heladeria.siguiente_id`) en lugar de la cantidad + 1.
9. **Catálogo rediseñado, presentaciones de precio fijo y combos con descuento:**
   - El Catálogo se divide en *Sabores y potes*, *Presentaciones* y *Combos y descuentos*, con campos, selectores y listas propias (sin los widgets del sistema).
   - *Sabores y potes*: alta de sabores, lista de potes con barra de stock (roja en el mínimo, ámbar cerca); al tocar un pote se puede reponer stock o abrir otro pote del mismo sabor.
   - *Presentaciones*: se elige si se cobra **por peso** (`Recipiente`, con recargo %) o a **precio fijo** (`PresentacionPorPorcion`), y el máximo de sabores (1 a 4).
   - *Combos y descuentos*: se arman combos (presentación, sabores, agregados, salsas y descuento) y se editan o eliminan los existentes. Todo se guarda en `scripts/sugerencias.json`.
   - En *Nueva venta*, el descuento del combo se aplica solo si se cobra tal cual; si se modifica, se cobra a precio normal. `Venta` guarda `descuento_pct` y `combo_id` en `ventas.json` y aplica el descuento proporcionalmente a lo cobrado por cada sabor, así los reportes siguen sumando 100%.
