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
  - `modelos/venta.py`: Clase `Venta` con soporte multi-sabor y delegación polimórfica de cálculo de aportes y precio total.
- `scripts/`: Archivos JSON de configuración inicial:
  - `scripts/sabores_iniciales.json`: 10 sabores iniciales (5 industriales a $12.000/kg y 5 artesanales a $15.000/kg).
  - `scripts/tamanos_pote.json`: 5 tamaños de pote/presentaciones con sus parámetros de negocio.
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
