from collections import defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk
from modelos.sabor import Sabor
from modelos.extra import Extra, Salsa
from modelos.combo import Combo
from modelos.recipiente import Recipiente, PresentacionPorPorcion
from modelos.venta import Venta
from modelos.pote import Pote


RUTA_SCRIPTS = Path(__file__).parent / "scripts"
RUTA_SABORES = RUTA_SCRIPTS / "sabores_iniciales.json"
RUTA_TAMANOS = RUTA_SCRIPTS / "tamanos_pote.json"
RUTA_POTES = RUTA_SCRIPTS / "potes.json"
RUTA_VENTAS = RUTA_SCRIPTS / "ventas.json"
RUTA_EXTRAS = RUTA_SCRIPTS / "extras.json"
RUTA_SUGERENCIAS = RUTA_SCRIPTS / "sugerencias.json"

CLASES_PRESENTACION = {
    "Recipiente": Recipiente,
    "PresentacionPorPorcion": PresentacionPorPorcion,
}

CLASES_EXTRA = {
    "Extra": Extra,
    "Salsa": Salsa,
}


def guardar_json(heladeria):
    # Los sabores y los potes se guardan por separado: un sabor puede tener varios potes
    sabores_data = [
        {
            "id": s.id,
            "nombre": s.nombre,
            "elaboracion": s.elaboracion,
            "precio": s.precio_por_kilo,
        }
        for s in heladeria.sabores
    ]
    RUTA_SABORES.write_text(
        json.dumps(sabores_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    potes_data = [
        {
            "id": p.id,
            "sabor_id": p.sabor.id,
            "fecha": p.fecha_incorporacion,
            "stock_kg": round(p.stock_kg, 4),
        }
        for p in heladeria.potes
    ]
    RUTA_POTES.write_text(
        json.dumps(potes_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    tamanos_data = []
    for r in heladeria.recipientes:
        item = {
            "id": r.id,
            "clase": type(r).__name__,
            "nombre": r.nombre,
            "kilos": r.kilos,
            "max_sabores": r.max_sabores,
        }
        if isinstance(r, PresentacionPorPorcion):
            item["precio_fijo"] = r.precio_fijo
        else:
            item["porcentaje_incremento"] = r.porcentaje_incremento
        tamanos_data.append(item)
    RUTA_TAMANOS.write_text(
        json.dumps(tamanos_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    ventas_data = [
        {
            "potes_ids": [p.id for p in v.potes],
            "recipiente_id": v.recipiente.id,
            "extras": [{"id": e.id, "cantidad": c} for e, c in v.extras],
            "salsas_ids": [s.id for s in v.salsas],
            "descuento_pct": v.descuento_pct,
            "combo_id": v.combo.id if v.combo else None,
        }
        for v in heladeria.ventas
    ]
    RUTA_VENTAS.write_text(
        json.dumps(ventas_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    combos_data = [
        {
            "id": k.id,
            "nombre": k.nombre,
            "descripcion": k.descripcion,
            "recipiente_id": k.recipiente.id,
            "sabores_ids": [sabor.id for sabor in k.sabores],
            "extras": [{"id": e.id, "cantidad": c} for e, c in k.extras],
            "salsas_ids": [salsa.id for salsa in k.salsas],
            "descuento_pct": k.descuento_pct,
        }
        for k in heladeria.combos
    ]
    RUTA_SUGERENCIAS.write_text(
        json.dumps({"combos": combos_data}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cargar_json(heladeria):
    sabores_json = json.loads(RUTA_SABORES.read_text(encoding="utf-8"))
    for item in sabores_json:
        heladeria.agregar_sabor(
            Sabor(item["id"], item["nombre"], item["elaboracion"], item["precio"]))

    sabores_por_id = {s.id: s for s in heladeria.sabores}
    if RUTA_POTES.exists():
        for item in json.loads(RUTA_POTES.read_text(encoding="utf-8")):
            sabor = sabores_por_id.get(item["sabor_id"])
            if sabor:
                heladeria.agregar_pote(
                    Pote(item["id"], sabor, item["fecha"], stock_kg=item["stock_kg"]))
    else:
        # Formato anterior (sin potes.json): un pote por sabor, con el mismo id,
        # y la fecha y el stock guardados junto al sabor.
        for item in sabores_json:
            heladeria.agregar_pote(Pote(
                item["id"], sabores_por_id[item["id"]],
                item.get("fecha", datetime.now().strftime("%Y-%m-%d")),
                stock_kg=item.get("stock_kg", Pote.STOCK_INICIAL_KG)))

    for item in json.loads(RUTA_TAMANOS.read_text(encoding="utf-8")):
        datos = dict(item)
        cls = CLASES_PRESENTACION[datos.pop("clase")]
        heladeria.agregar_recipiente(cls(**datos))

    if RUTA_EXTRAS.exists():
        for item in json.loads(RUTA_EXTRAS.read_text(encoding="utf-8")):
            datos = dict(item)
            cls = CLASES_EXTRA[datos.pop("clase")]
            heladeria.agregar_extra(cls(**datos))

    if RUTA_SUGERENCIAS.exists():
        cargar_sugerencias(heladeria, json.loads(RUTA_SUGERENCIAS.read_text(encoding="utf-8")))

    if RUTA_VENTAS.exists():
        potes_por_id = {p.id: p for p in heladeria.potes}
        recips_por_id = {r.id: r for r in heladeria.recipientes}
        extras_por_id = {e.id: e for e in heladeria.extras + heladeria.salsas}
        combos_por_id = {k.id: k for k in heladeria.combos}
        for item in json.loads(RUTA_VENTAS.read_text(encoding="utf-8")):
            potes_venta = [potes_por_id[pid] for pid in item["potes_ids"] if pid in potes_por_id]
            recip = recips_por_id.get(item["recipiente_id"])
            extras = [(extras_por_id[e["id"]], e["cantidad"])
                      for e in item.get("extras", []) if e["id"] in extras_por_id]
            salsas = [extras_por_id[sid] for sid in item.get("salsas_ids", [])
                      if sid in extras_por_id]
            if potes_venta and recip:
                venta = Venta(potes_venta, recip, extras, salsas,
                              item.get("descuento_pct", 0.0),
                              combos_por_id.get(item.get("combo_id")))
                for pote, kilos_aporte, dinero_aporte in venta.aportes:
                    pote.kilos_servidos += kilos_aporte
                    pote.dinero_recaudado += dinero_aporte
                heladeria.ventas.append(venta)


def cargar_sugerencias(heladeria, datos):
    """Combos sugeridos. Se ignora lo que apunte a ids inexistentes o sea inválido."""
    sabores = {s.id: s for s in heladeria.sabores}
    recipientes = {r.id: r for r in heladeria.recipientes}
    extras = {e.id: e for e in heladeria.extras + heladeria.salsas}
    for item in datos.get("combos", []):
        recip = recipientes.get(item["recipiente_id"])
        sabores_combo = [sabores[i] for i in item.get("sabores_ids", []) if i in sabores]
        if not recip or not sabores_combo:
            continue
        try:
            heladeria.agregar_combo(Combo(
                item["id"], item["nombre"], item.get("descripcion", ""), recip, sabores_combo,
                [(extras[e["id"]], e["cantidad"]) for e in item.get("extras", [])
                 if e["id"] in extras],
                [extras[i] for i in item.get("salsas_ids", []) if i in extras],
                item.get("descuento_pct", 0.0),
            ))
        except ValueError:
            continue


#Logica de la heladeria
class Heladeria:
    def __init__(self):
        self.potes = []
        self.ventas = []
        self.sabores = []
        self.recipientes = []
        self.extras = []   # agregados con costo (cucurucho, vasito...)
        self.salsas = []   # salsas sin costo
        self.combos = []

    @staticmethod
    def siguiente_id(elementos):
        """Id libre para un elemento nuevo (el mayor existente + 1, no la cantidad + 1)."""
        return max((e.id for e in elementos), default=0) + 1

    def agregar_pote(self, pote):
        self.potes.append(pote)

    def agregar_sabor(self, sabor):
        self.sabores.append(sabor)

    def agregar_recipiente(self, recipiente):
        self.recipientes.append(recipiente)

    def agregar_combo(self, combo):
        self.combos.append(combo)

    def reemplazar_combo(self, combo):
        """Guarda los cambios de un combo existente (mismo id) o lo agrega si es nuevo."""
        for i, existente in enumerate(self.combos):
            if existente.id == combo.id:
                self.combos[i] = combo
                return
        self.combos.append(combo)

    def eliminar_combo(self, combo):
        self.combos = [k for k in self.combos if k.id != combo.id]

    def pote_de(self, sabor, kilos=0.0):
        """Pote del sabor que puede servir esos kilos (o el primero que haya, o None)."""
        potes = [p for p in self.potes if p.sabor is sabor]
        return next((p for p in potes if p.puede_servir(kilos)), potes[0] if potes else None)

    def sabores_sin_stock(self, recipiente, sabores):
        """Sabores que no tienen ningún pote capaz de servir su porción en esa presentación."""
        if not sabores:
            return []
        kilos = recipiente.kilos / len(sabores)
        faltan = []
        for sabor in sabores:
            pote = self.pote_de(sabor, kilos)
            if not (pote and pote.puede_servir(kilos)):
                faltan.append(sabor)
        return faltan

    def agregar_extra(self, extra):
        # Las salsas (sin costo) se listan aparte de los agregados que se cobran
        (self.salsas if isinstance(extra, Salsa) else self.extras).append(extra)

    def vender(self, potes, recipiente, extras=None, salsas=None, combo=None):
        """Registra la venta. Si se cobra un combo tal cual, se aplica su descuento."""
        descuento = combo.descuento_pct if combo else 0.0
        venta = Venta(potes, recipiente, extras, salsas, descuento, combo)
        consumo_por_pote = defaultdict(float)
        for pote, kilos_aporte, _ in venta.aportes:
            consumo_por_pote[pote] += kilos_aporte

        faltantes = []
        for pote, kilos_pedidos in consumo_por_pote.items():
            if not pote.puede_servir(kilos_pedidos):
                restante = pote.stock_kg - kilos_pedidos
                faltantes.append(
                    f"- {pote.sabor.nombre}: stock {pote.stock_kg:.2f} kg, "
                    f"pedido {kilos_pedidos:.2f} kg (quedaría en {restante:.2f} kg; "
                    f"mínimo obligatorio: {Pote.STOCK_MINIMO_KG:.2f} kg)"
                )
        if faltantes:
            raise ValueError("Alerta de reposición de stock:\n" + "\n".join(faltantes))

        for pote, kilos_aporte, dinero_aporte in venta.aportes:
            pote.registrar_venta(kilos_aporte, dinero_aporte)
        self.ventas.append(venta)
        return venta

    

    def kilos_por_sabor(self):
        resultado = defaultdict(float)
        for venta in self.ventas:
            for pote, kilos_aporte, _ in venta.aportes:
                resultado[pote.sabor.nombre] += kilos_aporte
        return resultado

    def recaudacion_por_sabor(self):
        resultado = defaultdict(float)
        for venta in self.ventas:
            for pote, _, dinero_aporte in venta.aportes:
                resultado[pote.sabor.nombre] += dinero_aporte
        return resultado

    def sabores_populares(self, cantidad=5):
        """Ranking de sabores según cuántas ventas los incluyeron (se recalcula con cada venta).

        Empates: primero el que vendió más kilos y después el orden del catálogo.
        Devuelve [(sabor, cantidad_de_ventas)] solo con sabores que se vendieron al menos una vez.
        """
        pedidos, kilos = defaultdict(int), defaultdict(float)
        for venta in self.ventas:
            for sabor in {p.sabor for p in venta.potes}:
                pedidos[sabor] += 1
            for pote, kilos_aporte, _ in venta.aportes:
                kilos[pote.sabor] += kilos_aporte
        orden_catalogo = {sabor: i for i, sabor in enumerate(self.sabores)}
        ranking = sorted(pedidos, key=lambda s: (-pedidos[s], -kilos[s],
                                                 orden_catalogo.get(s, len(orden_catalogo))))
        return [(sabor, pedidos[sabor]) for sabor in ranking[:cantidad]]

    def cantidad_ventas_por_sabor(self):
        resultado = defaultdict(float)
        for venta in self.ventas:
            parte = 1.0 / len(venta.potes)
            for pote in venta.potes:
                resultado[pote.sabor.nombre] += parte
        return resultado

    #Punto 1
    def recaudacion_total(self):
        return sum(venta.calcular_precio_total() for venta in self.ventas)

    def recaudacion_helado(self):
        """Solo lo cobrado por helado (sin agregados): base de los % por sabor/pote."""
        return sum(venta.precio_helado for venta in self.ventas)

    def recaudacion_extras(self):
        return sum(venta.precio_extras for venta in self.ventas)

    #Punto 2
    def pote_mas_servido(self):
        if not self.potes:
            return None
        return max(self.potes, key=lambda pote: pote.kilos_servidos)

    def pote_menos_servido(self):
        if not self.potes:
            return None
        return min(self.potes, key=lambda pote: pote.kilos_servidos)

    #Punto 3
    def pote_mas_recaudado(self):
        if not self.potes:
            return None
        return max(self.potes, key=lambda pote: pote.dinero_recaudado)

    #Punto 4 (cantidad de ventas)
    def sabor_mas_vendido(self):
        resultado = self.cantidad_ventas_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=lambda s: resultado[s])

    #Punto 5
    def sabor_mas_recaudado(self):
        resultado = self.recaudacion_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=lambda s: resultado[s])

    #Punto 6
    def sabor_mas_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=lambda s: resultado[s])

    #Punto 7
    def sabor_menos_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return min(resultado, key=lambda s: resultado[s])

    #Punto 8 
    def recipiente_mas_solicitado(self):
        if not self.ventas:
            return None
        resultado = defaultdict(int)
        for venta in self.ventas:
            resultado[venta.recipiente.nombre] += 1
        return max(resultado, key=lambda r: resultado[r])

    #Punto 9 
    def porcentaje_venta_por_sabor(self):
        total = len(self.ventas)
        if total == 0:
            return {}
        cantidades = self.cantidad_ventas_por_sabor()
        return {sabor: (cantidad / total) * 100 for sabor, cantidad in cantidades.items()}

    #Punto 10 
    def porcentaje_recaudacion_por_sabor(self):
        total = self.recaudacion_helado()
        if total == 0:
            return {}
        recaudacion = self.recaudacion_por_sabor()
        return {sabor: (monto / total) * 100 for sabor, monto in recaudacion.items()}

    #Punto 11
    def porcentaje_venta_por_pote(self):
        total_kilos = sum(p.kilos_servidos for p in self.potes)
        if total_kilos == 0:
            return {}
        return {pote.id: (pote.kilos_servidos / total_kilos) * 100 for pote in self.potes}

    #Punto 12 
    def porcentaje_recaudacion_por_pote(self):
        total = self.recaudacion_helado()
        if total == 0:
            return {}
        return {pote.id: (pote.dinero_recaudado / total) * 100 for pote in self.potes}


#Interfaz

# Paleta de colores y fuentes de toda la interfaz (se cambian en un solo lugar)
COLORES = {
    "fondo": "#FFF7F2",
    "panel": "#FFFFFF",
    "primario": "#E85D75",
    "primario_hover": "#C9475F",
    "primario_suave": "#FFF0F3",
    "secundario": "#3FA69B",
    "secundario_suave": "#E3F4F1",
    "texto": "#3D2C2E",
    "texto_suave": "#8A7A7C",
    "texto_tenue": "#C4B5B2",
    "borde": "#F1E1D9",
    "borde_hover": "#F4B6C2",
    "resaltado": "#FBD3DA",
    "deshabilitado": "#FBF5F2",
    "error": "#C0392B",
    "aviso": "#D68A1C",
    "bocha": "#F7A8B8",
}
FUENTE = "Segoe UI"
CANTIDAD_POPULARES = 5  # cuántos sabores muestra el ranking
ELABORACIONES = [("artesanal", "Artesanal"), ("industrial", "Industrial")]
MAX_SABORES_POR_PRESENTACION = 4
DESCUENTOS_RAPIDOS = [0, 5, 10, 15, 20]  # botones de descuento al armar un combo
FUENTE_FUERTE = "Segoe UI Semibold"  # se reemplaza al iniciar si no existe

# Color de cada sabor (los que no figuran toman uno de la paleta de respaldo)
COLORES_SABOR = {
    "vainilla": "#F5E3A1",
    "crema del cielo": "#9ED3F2",
    "granizado": "#E8DCCB",
    "chocolate blanco": "#F3E6D0",
    "cereza": "#D9445F",
    "chocolate amargo": "#5E3624",
    "frutilla": "#F48FA6",
    "tiramisú": "#C29A73",
    "sambayón": "#F0C75E",
    "pistacho": "#9EC27A",
    "dulce de leche": "#B9772F",
    "caramelo": "#D9952B",
    "chocolate": "#5A3220",
}
PALETA_RESPALDO = ["#F7A8B8", "#A8D8EA", "#C3E6A6", "#FFD3A5", "#D5B8F0", "#F9E79F"]


def color_de(nombre):
    clave = nombre.strip().lower()
    if clave in COLORES_SABOR:
        return COLORES_SABOR[clave]
    return PALETA_RESPALDO[sum(map(ord, clave)) % len(PALETA_RESPALDO)]


def formato_dinero(monto, decimales=True):
    """Formato argentino: $12.345,67 (o $12.345 si se piden sin decimales)."""
    texto = f"{monto:,.2f}" if decimales else f"{monto:,.0f}"
    return "$" + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def dinero_corto(monto):
    """Sin centavos cuando el monto es redondo."""
    return formato_dinero(monto, decimales=round(monto, 2) != round(monto))


def formato_kilos(kilos):
    return f"{kilos:.2f}".replace(".", ",")


# ---------- Dibujo sobre Canvas ----------
def rect_redondeado(c, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
              x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
              x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
              x1, y1 + r, x1, y1]
    return c.create_polygon(puntos, smooth=True, **kw)


def dibujar_tilde(c, cx, cy, tam, color="white", grosor=2):
    c.create_line(cx - tam * 0.45, cy, cx - tam * 0.1, cy + tam * 0.35,
                  cx + tam * 0.5, cy - tam * 0.35, fill=color, width=grosor,
                  capstyle="round", joinstyle="round")


def icono_pote(c, cx, cy, s, bocha=None):
    bocha = bocha or COLORES["bocha"]
    c.create_oval(cx - .36 * s, cy - .46 * s, cx + .36 * s, cy + .06 * s, fill=bocha, outline="")
    c.create_polygon(cx - .42 * s, cy - .1 * s, cx + .42 * s, cy - .1 * s,
                     cx + .33 * s, cy + .46 * s, cx - .33 * s, cy + .46 * s,
                     fill="white", outline="#E7C9BF", width=1.5)
    c.create_polygon(cx - .39 * s, cy + .08 * s, cx + .39 * s, cy + .08 * s,
                     cx + .37 * s, cy + .2 * s, cx - .37 * s, cy + .2 * s,
                     fill=COLORES["primario"], outline="")
    rect_redondeado(c, cx - .47 * s, cy - .16 * s, cx + .47 * s, cy - .04 * s, 3,
                    fill="#FFE9EE", outline="#E7C9BF")


def icono_cono(c, cx, cy, s, bocha=None, banado=False):
    bocha = bocha or COLORES["bocha"]
    c.create_polygon(cx - .3 * s, cy - .04 * s, cx + .3 * s, cy - .04 * s, cx, cy + .52 * s,
                     fill="#EBBF7A", outline="#C99350", width=1.5)
    for d in (-.12, .06):
        c.create_line(cx + (d - .1) * s, cy + .02 * s, cx + (d + .12) * s, cy + .26 * s,
                      fill="#C99350")
    c.create_oval(cx - .33 * s, cy - .5 * s, cx + .33 * s, cy + .06 * s, fill=bocha, outline="")
    if banado:
        c.create_arc(cx - .33 * s, cy - .5 * s, cx + .33 * s, cy + .06 * s, start=0, extent=180,
                     fill="#6B3B22", outline="")
        c.create_oval(cx - .2 * s, cy - .26 * s, cx - .1 * s, cy - .1 * s, fill="#6B3B22", outline="")
        c.create_oval(cx + .08 * s, cy - .24 * s, cx + .17 * s, cy - .12 * s, fill="#6B3B22", outline="")


def icono_vaso(c, cx, cy, s, bocha=None):
    bocha = bocha or COLORES["bocha"]
    c.create_oval(cx - .32 * s, cy - .46 * s, cx + .32 * s, cy + .04 * s, fill=bocha, outline="")
    c.create_polygon(cx - .34 * s, cy - .08 * s, cx + .34 * s, cy - .08 * s,
                     cx + .23 * s, cy + .48 * s, cx - .23 * s, cy + .48 * s,
                     fill="#CFEDE8", outline="#86CBC1", width=1.5)
    for d in (-.14, 0, .14):
        c.create_line(cx + d * s * 1.2, cy - .04 * s, cx + d * s * .8, cy + .44 * s,
                      fill="#86CBC1", width=2)


def icono_bolsa(c, cx, cy, s, bocha=None):
    c.create_arc(cx - .18 * s, cy - .44 * s, cx + .18 * s, cy - .04 * s, start=0, extent=180,
                 style="arc", outline="#86CBC1", width=3)
    rect_redondeado(c, cx - .36 * s, cy - .2 * s, cx + .36 * s, cy + .46 * s, 6,
                    fill="#CFEDE8", outline="#86CBC1", width=1.5)
    c.create_line(cx - .36 * s, cy + .02 * s, cx + .36 * s, cy + .02 * s, fill="#86CBC1")


def icono_gota(c, cx, cy, s, color):
    c.create_polygon(cx, cy - .5 * s, cx - .26 * s, cy + .04 * s, cx + .26 * s, cy + .04 * s,
                     fill=color, outline="")
    c.create_oval(cx - .3 * s, cy - .14 * s, cx + .3 * s, cy + .46 * s, fill=color, outline="")
    c.create_oval(cx - .16 * s, cy + .02 * s, cx - .06 * s, cy + .16 * s, fill="white", outline="")


def dibujar_estrella(cx, cy, r_ext, r_int, puntas=5):
    """Puntos de una estrella para create_polygon."""
    puntos = []
    for i in range(puntas * 2):
        radio = r_ext if i % 2 == 0 else r_int
        angulo = math.pi / puntas * i - math.pi / 2
        puntos += [cx + radio * math.cos(angulo), cy + radio * math.sin(angulo)]
    return puntos


def icono_para(nombre):
    """Elige el dibujo según el nombre de la presentación o del agregado."""
    n = nombre.lower()
    if "bañado" in n:
        return lambda c, x, y, s, b=None: icono_cono(c, x, y, s, b, banado=True)
    if "cucurucho" in n or "cono" in n:
        return icono_cono
    if "vas" in n:
        return icono_vaso
    if "bolsa" in n or "térmic" in n:
        return icono_bolsa
    return icono_pote


_cache_fuentes = {}


def medir(texto, fuente):
    if fuente not in _cache_fuentes:
        _cache_fuentes[fuente] = tkfont.Font(font=fuente)
    return _cache_fuentes[fuente].measure(texto)


def fecha_corta(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return texto


def leer_numero(texto, con_miles=False):
    """Lee '0,25', '0.25' o (con_miles) '15.000' como número. Lanza ValueError si no se puede."""
    texto = texto.strip().replace(" ", "").replace("$", "").replace("%", "")
    if con_miles:
        texto = texto.replace(".", "")
    return float(texto.replace(",", "."))


def potes_de_muestra(sabores):
    """Potes sin stock real, solo para calcular precios de algo que todavía no se vende."""
    return [Pote(0, sabor, "") for sabor in sabores]


def precio_combo(recipiente, sabores, extras, salsas, descuento_pct):
    """(precio sin descuento, precio final) de un combo."""
    venta = Venta(potes_de_muestra(sabores), recipiente, extras, salsas, descuento_pct)
    return venta.subtotal, venta.precio_total


def recortar(texto, fuente, ancho):
    """Corta el texto con '…' para que entre en 'ancho' píxeles."""
    if fuente not in _cache_fuentes:
        _cache_fuentes[fuente] = tkfont.Font(font=fuente)
    f = _cache_fuentes[fuente]
    if f.measure(texto) <= ancho:
        return texto
    while texto and f.measure(texto + "…") > ancho:
        texto = texto[:-1]
    return texto.rstrip() + "…"


# ---------- Widgets dibujados ----------
class Lienzo(tk.Canvas):
    """Base de los botones/tarjetas dibujados: maneja hover, click y redibujo."""

    def __init__(self, padre, alto, ancho=1, comando=None, fondo=None):
        fondo = fondo or COLORES["fondo"]
        super().__init__(padre, height=alto, width=ancho, bg=fondo,
                         highlightthickness=0, bd=0)
        self.comando = comando
        self.hover = False
        self.habilitado = True
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", self._click)
        self.bind("<Configure>", lambda e: self.redibujar())

    def _set_hover(self, valor):
        self.hover = valor
        self.redibujar()

    def _click(self, evento):
        if self.habilitado:
            self.al_click(evento)

    def al_click(self, evento):
        if self.comando:
            self.comando()

    def redibujar(self):
        self.delete("all")
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho > 2:
            self.configure(cursor="hand2" if self.habilitado else "arrow")
            self.dibujar(ancho, alto)

    def dibujar(self, ancho, alto):
        raise NotImplementedError

    def _caja(self, ancho, alto, seleccionado, radio=14, apagado=False):
        """Fondo de tarjeta según el estado."""
        if seleccionado:
            relleno, borde, grosor = COLORES["primario_suave"], COLORES["primario"], 2
        elif apagado:
            relleno, borde, grosor = COLORES["deshabilitado"], COLORES["borde"], 1
        else:
            relleno = COLORES["panel"]
            borde = COLORES["borde_hover"] if self.hover and self.habilitado else COLORES["borde"]
            grosor = 1
        rect_redondeado(self, 1, 1, ancho - 2, alto - 2, radio,
                        fill=relleno, outline=borde, width=grosor)


class BotonPildora(Lienzo):
    """Botón redondeado. Variantes: 'primario', 'suave' y 'nav'."""

    def __init__(self, padre, texto, comando, variante="primario", alto=46, ancho=1, fondo=None):
        super().__init__(padre, alto, ancho, comando, fondo)
        self.texto = texto
        self.variante = variante
        self.activo = False

    def set(self, texto=None, habilitado=None, activo=None):
        if texto is not None:
            self.texto = texto
        if habilitado is not None:
            self.habilitado = habilitado
        if activo is not None:
            self.activo = activo
        self.redibujar()

    def dibujar(self, ancho, alto):
        c = COLORES
        if self.variante == "primario":
            if not self.habilitado:
                relleno, color = c["borde"], c["texto_suave"]
            else:
                relleno, color = (c["primario_hover"] if self.hover else c["primario"]), "white"
            fuente = (FUENTE_FUERTE, 13)
        elif self.variante == "nav":
            if self.activo:
                relleno, color = c["primario_suave"], c["primario"]
            else:
                relleno = c["fondo"] if self.hover else self["bg"]
                color = c["texto"] if self.hover else c["texto_suave"]
            fuente = (FUENTE_FUERTE, 11)
        else:  # suave
            relleno = c["borde"] if self.hover and self.habilitado else self["bg"]
            color = c["texto_suave"] if self.habilitado else c["texto_tenue"]
            fuente = (FUENTE, 10)
        rect_redondeado(self, 0, 0, ancho - 1, alto - 1, alto / 2, fill=relleno, outline="")
        self.create_text(ancho / 2, alto / 2, text=self.texto, fill=color, font=fuente)


class TarjetaPote(Lienzo):
    """Tarjeta de un tamaño de pote / presentación."""

    def __init__(self, padre, recipiente, comando):
        super().__init__(padre, alto=172, comando=comando)
        self.recipiente = recipiente
        self.seleccionado = False
        self.precio_desde = 0.0

    def dibujar(self, ancho, alto):
        r, c = self.recipiente, COLORES
        self._caja(ancho, alto, self.seleccionado, radio=18)
        # Los potes chicos se dibujan más chicos
        escala = 48 * (0.72 + 0.28 * min(r.kilos, 1.0)) if icono_para(r.nombre) is icono_pote else 52
        icono_para(r.nombre)(self, ancho / 2, 48, escala)
        if self.seleccionado:
            self.create_oval(ancho - 30, 10, ancho - 10, 30, fill=c["primario"], outline="")
            dibujar_tilde(self, ancho - 20, 20, 10)
        self.create_text(ancho / 2, 96, text=recortar(r.nombre, (FUENTE_FUERTE, 12), ancho - 16),
                         font=(FUENTE_FUERTE, 12), fill=c["texto"])
        self.create_text(ancho / 2, 116, text=f"{r.texto_peso()} · hasta {r.max_sabores} sabores",
                         font=(FUENTE, 9), fill=c["texto_suave"])
        self.create_text(ancho / 2, 132, text=r.descripcion_precio(),
                         font=(FUENTE, 9), fill=c["texto_suave"])
        self.create_text(ancho / 2, 153,
                         text=f"{r.prefijo_precio()}{dinero_corto(self.precio_desde)}",
                         font=(FUENTE_FUERTE, 10),
                         fill=c["primario"] if self.seleccionado or self.hover else c["texto"])


class ChipSabor(Lienzo):
    def __init__(self, padre, pote, comando, sabor=None):
        super().__init__(padre, alto=62, comando=comando)
        self.pote = pote
        self.sabor = sabor or pote.sabor
        self.orden = 0          # 0 = no elegido; si no, el número de bocha
        self.estado = "normal"  # normal | apagado | sin_stock

    def dibujar(self, ancho, alto):
        c, sabor = COLORES, self.sabor
        apagado = self.estado != "normal" and not self.orden
        self._caja(ancho, alto, bool(self.orden), apagado=apagado)
        cy = alto / 2
        self.create_oval(14, cy - 15, 44, cy + 15, fill=color_de(sabor.nombre),
                         outline="white", width=2)
        color_texto = c["texto_tenue"] if apagado else c["texto"]
        margen_der = 44 if (self.orden or self.estado == "sin_stock") else 14
        self.create_text(56, cy - 9, anchor="w", font=(FUENTE_FUERTE, 11), fill=color_texto,
                         text=recortar(sabor.nombre, (FUENTE_FUERTE, 11), ancho - 56 - margen_der))
        if self.estado == "sin_stock":
            sub, color_sub = "Sin stock suficiente", c["error"]
        else:
            sub = f"{sabor.elaboracion.capitalize()} · {dinero_corto(sabor.precio_por_kilo)}/kg"
            color_sub = c["texto_tenue"] if apagado else c["texto_suave"]
        self.create_text(56, cy + 10, anchor="w", font=(FUENTE, 9), fill=color_sub,
                         text=recortar(sub, (FUENTE, 9), ancho - 56 - margen_der))
        if self.orden:
            self.create_oval(ancho - 36, cy - 12, ancho - 12, cy + 12, fill=c["primario"], outline="")
            self.create_text(ancho - 24, cy, text=str(self.orden), fill="white",
                             font=(FUENTE_FUERTE, 10))


class FilaExtra(Lienzo):
    """Agregado con costo y un contador − n +."""

    def __init__(self, padre, extra, al_cambiar):
        super().__init__(padre, alto=66)
        self.extra = extra
        self.cantidad = 0
        self.al_cambiar = al_cambiar

    def al_click(self, evento):
        ancho = self.winfo_width()
        if evento.x >= ancho - 52:
            self.al_cambiar(self.extra, self.cantidad + 1)
        elif evento.x >= ancho - 112:
            if evento.x < ancho - 80:
                self.al_cambiar(self.extra, max(0, self.cantidad - 1))
        elif self.cantidad == 0:
            self.al_cambiar(self.extra, 1)

    def dibujar(self, ancho, alto):
        c, cy = COLORES, alto / 2
        self._caja(ancho, alto, self.cantidad > 0)
        icono_para(self.extra.nombre)(self, 34, cy, 40)
        self.create_text(64, cy - 9, anchor="w", font=(FUENTE_FUERTE, 11), fill=c["texto"],
                         text=recortar(self.extra.nombre, (FUENTE_FUERTE, 11), ancho - 64 - 120))
        sub = f"+{dinero_corto(self.extra.precio)} c/u"
        if self.cantidad:
            sub = f"{self.cantidad} × {dinero_corto(self.extra.precio)} = " \
                  f"{dinero_corto(self.extra.calcular_precio(self.cantidad))}"
        self.create_text(64, cy + 10, anchor="w", font=(FUENTE, 9),
                         fill=c["primario"] if self.cantidad else c["texto_suave"], text=sub)
        # Contador
        menos_activo = self.cantidad > 0
        self.create_oval(ancho - 108, cy - 14, ancho - 80, cy + 14,
                         fill=c["panel"] if menos_activo else c["deshabilitado"],
                         outline=c["primario"] if menos_activo else c["borde"], width=1.5)
        self.create_line(ancho - 100, cy, ancho - 88, cy, width=2,
                         fill=c["primario"] if menos_activo else c["texto_tenue"])
        self.create_text(ancho - 66, cy, text=str(self.cantidad), font=(FUENTE_FUERTE, 12),
                         fill=c["texto"] if self.cantidad else c["texto_tenue"])
        self.create_oval(ancho - 52, cy - 14, ancho - 24, cy + 14, fill=c["primario"], outline="")
        self.create_line(ancho - 44, cy, ancho - 32, cy, width=2, fill="white")
        self.create_line(ancho - 38, cy - 6, ancho - 38, cy + 6, width=2, fill="white")


class ChipSalsa(Lienzo):
    def __init__(self, padre, salsa, comando):
        super().__init__(padre, alto=54, comando=comando)
        self.salsa = salsa
        self.seleccionado = False

    def dibujar(self, ancho, alto):
        c, cy = COLORES, alto / 2
        self._caja(ancho, alto, self.seleccionado, radio=alto / 2)
        icono_gota(self, 28, cy, 26, color_de(self.salsa.nombre))
        self.create_text(48, cy, anchor="w", font=(FUENTE_FUERTE, 10), fill=c["texto"],
                         text=recortar(self.salsa.nombre, (FUENTE_FUERTE, 10), ancho - 48 - 34))
        if self.seleccionado:
            self.create_oval(ancho - 30, cy - 10, ancho - 10, cy + 10, fill=c["primario"], outline="")
            dibujar_tilde(self, ancho - 20, cy, 10)


class TarjetaCombo(Lienzo):
    """Combo sugerido: al tocarlo se carga entero en el pedido (o se edita, en Catálogo)."""

    def __init__(self, padre, combo, comando, texto_accion="Tocá para cargar"):
        super().__init__(padre, alto=128, comando=comando)
        self.combo = combo
        self.precio = 0.0
        self.precio_original = 0.0
        self.seleccionado = False
        self.incompleto = False  # algún sabor sin stock
        self.texto_accion = texto_accion
        self.texto_seleccionado = "Cargado"

    def dibujar(self, ancho, alto):
        c, combo = COLORES, self.combo
        r = combo.recipiente
        self._caja(ancho, alto, self.seleccionado, radio=18)
        # Ícono sobre un círculo de color
        self.create_oval(18, 22, 82, 86, fill=c["primario_suave"] if not self.seleccionado
                         else c["panel"], outline="")
        icono_para(r.nombre)(self, 50, 54, 46)
        if combo.tiene_descuento():
            rect_redondeado(self, 12, 12, 62, 32, 10, fill=c["secundario"], outline="")
            self.create_text(37, 22, text=f"-{combo.descuento_pct:g}%", fill="white",
                             font=(FUENTE_FUERTE, 9))
        x, ancho_texto = 98, ancho - 98 - 112
        self.create_text(x, 24, anchor="w", font=(FUENTE_FUERTE, 13), fill=c["texto"],
                         text=recortar(combo.nombre, (FUENTE_FUERTE, 13), ancho_texto))
        self.create_text(x, 45, anchor="w", font=(FUENTE, 9), fill=c["texto_suave"],
                         text=recortar(combo.descripcion or f"{r.nombre} · {r.texto_peso()}",
                                       (FUENTE, 9), ancho_texto))
        # Bochas de colores con los sabores
        bx = x
        for sabor in combo.sabores:
            self.create_oval(bx, 60, bx + 18, 78, fill=color_de(sabor.nombre),
                             outline="white", width=2)
            bx += 13
        self.create_text(bx + 12, 69, anchor="w", font=(FUENTE, 9), fill=c["texto"],
                         text=recortar(f"{r.nombre} · {combo.nombres_sabores()}", (FUENTE, 9),
                                       ancho - bx - 12 - 16))
        agregados = [f"{cant}× {e.nombre}" for e, cant in combo.extras]
        if combo.salsas:
            agregados.append("salsa de " + " y ".join(s.nombre.lower() for s in combo.salsas))
        self.create_text(x, 98, anchor="w", font=(FUENTE, 9), fill=c["texto_suave"],
                         text=recortar(" · ".join(agregados) or "Sin agregados", (FUENTE, 9),
                                       ancho - x - 130))
        # Precio (con el anterior tachado si hay descuento) y estado
        self.create_text(ancho - 18, 26, anchor="e", font=(FUENTE_FUERTE, 15), fill=c["primario"],
                         text=dinero_corto(self.precio))
        if combo.tiene_descuento():
            self.create_text(ancho - 18, 47, anchor="e", font=(FUENTE, 9, "overstrike"),
                             fill=c["texto_suave"], text=dinero_corto(self.precio_original))
        if self.incompleto:
            etiqueta, color = "Falta stock", c["error"]
        elif self.seleccionado:
            etiqueta, color = self.texto_seleccionado, c["secundario"]
        else:
            etiqueta = self.texto_accion
            color = c["primario"] if self.hover else c["texto_suave"]
        self.create_text(ancho - 18, 98, anchor="e", font=(FUENTE_FUERTE, 9), fill=color,
                         text=etiqueta)


class ChipPopular(Lienzo):
    """Sabor del ranking de populares: un toque lo suma al pedido."""

    def __init__(self, padre, sabor, puesto, pedidos, comando):
        super().__init__(padre, alto=118, comando=comando)
        self.sabor = sabor
        self.puesto = puesto
        self.pedidos = pedidos
        self.seleccionado = False
        self.estado = "normal"  # normal | apagado | sin_stock

    def dibujar(self, ancho, alto):
        c, cx = COLORES, ancho / 2
        apagado = self.estado != "normal" and not self.seleccionado
        self._caja(ancho, alto, self.seleccionado, radio=18, apagado=apagado)
        # Puesto en el ranking (el 1° destacado)
        primero = self.puesto == 1
        rect_redondeado(self, 10, 10, 44, 30, 10, outline="",
                        fill=c["primario"] if primero else c["resaltado"])
        self.create_text(27, 20, text=f"#{self.puesto}", font=(FUENTE_FUERTE, 9),
                         fill="white" if primero else c["primario_hover"])
        if self.seleccionado:
            self.create_oval(ancho - 30, 10, ancho - 10, 30, fill=c["primario"], outline="")
            dibujar_tilde(self, ancho - 20, 20, 10)
        # Bocha grande con brillito
        color = color_de(self.sabor.nombre)
        self.create_oval(cx - 24, 22, cx + 24, 70, fill=color, outline="white", width=3)
        self.create_oval(cx - 13, 32, cx - 4, 41, fill="white", outline="")
        self.create_text(cx, 86, font=(FUENTE_FUERTE, 11),
                         fill=c["texto_tenue"] if apagado else c["texto"],
                         text=recortar(self.sabor.nombre, (FUENTE_FUERTE, 11), ancho - 16))
        if self.estado == "sin_stock":
            sub, color_sub = "Sin stock", c["error"]
        else:
            sub = f"{self.pedidos} {'venta' if self.pedidos == 1 else 'ventas'}"
            color_sub = c["texto_tenue"] if apagado else c["texto_suave"]
        self.create_text(cx, 104, font=(FUENTE, 9), fill=color_sub, text=sub)


class TicketPedido(tk.Canvas):
    """Resumen con forma de ticket: el pedido en curso, o el combo que se está armando."""

    def __init__(self, padre, titulo="Tu pedido",
                 texto_vacio=("Elegí un pote para empezar", "El resumen aparece acá")):
        super().__init__(padre, bg=COLORES["fondo"], highlightthickness=0, bd=0, width=360)
        self.titulo = titulo
        self.texto_vacio = texto_vacio
        self.datos = None
        self.etiqueta = ""
        self.bind("<Configure>", lambda e: self.redibujar())

    def mostrar(self, datos, etiqueta):
        """datos: recipiente, sabores, extras, salsas, precio_helado (sin descuento),
        descuento (monto), texto_descuento y total."""
        self.datos, self.etiqueta = datos, etiqueta
        self.redibujar()

    def redibujar(self):
        self.delete("all")
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 10:
            return
        c, d = COLORES, self.datos
        rect_redondeado(self, 1, 1, ancho - 2, alto - 2, 20, fill=c["panel"], outline=c["borde"])
        izq, der = 24, ancho - 24
        self.create_text(izq, 32, anchor="w", text=self.titulo, font=(FUENTE_FUERTE, 16),
                         fill=c["texto"])
        self.create_text(der, 32, anchor="e", text=self.etiqueta, font=(FUENTE, 10),
                         fill=c["texto_suave"])
        self._separador(58, ancho)

        if not d or not d["recipiente"]:
            icono_pote(self, ancho / 2, alto / 2 - 40, 70, COLORES["borde"])
            self.create_text(ancho / 2, alto / 2 + 20, text=self.texto_vacio[0],
                             font=(FUENTE_FUERTE, 12), fill=c["texto_suave"])
            self.create_text(ancho / 2, alto / 2 + 42, text=self.texto_vacio[1],
                             font=(FUENTE, 10), fill=c["texto_tenue"])
            return

        r, sabores = d["recipiente"], d["sabores"]
        y = 84
        icono_para(r.nombre)(self, izq + 14, y, 30)
        self.create_text(izq + 38, y - 7, anchor="w", text=r.nombre, font=(FUENTE_FUERTE, 12),
                         fill=c["texto"])
        self.create_text(izq + 38, y + 11, anchor="w",
                         text=f"{r.texto_peso()} · {r.descripcion_precio()}",
                         font=(FUENTE, 9), fill=c["texto_suave"])
        self.create_text(der, y - 7, anchor="e", font=(FUENTE_FUERTE, 11), fill=c["texto"],
                         text=dinero_corto(d["precio_helado"]) if sabores else "—")
        y += 36

        if sabores:
            gramos = r.kilos * 1000 / len(sabores)
            for sabor in sabores:
                self.create_oval(izq + 8, y - 6, izq + 20, y + 6, fill=color_de(sabor.nombre),
                                 outline="")
                self.create_text(izq + 30, y, anchor="w", font=(FUENTE, 10), fill=c["texto"],
                                 text=recortar(sabor.nombre, (FUENTE, 10), der - izq - 110))
                self.create_text(der, y, anchor="e", font=(FUENTE, 10), fill=c["texto_suave"],
                                 text=f"{gramos:.0f} g")
                y += 24
        else:
            self.create_text(izq + 8, y, anchor="w", font=(FUENTE, 10), fill=c["primario"],
                             text=f"Elegí hasta {r.max_sabores} sabores")
            y += 24

        if d["extras"]:
            y += 6
            self.create_text(izq, y, anchor="w", text="AGREGADOS", font=(FUENTE_FUERTE, 8),
                             fill=c["texto_suave"])
            y += 20
            for extra, cant in d["extras"]:
                self.create_text(izq + 8, y, anchor="w", font=(FUENTE, 10), fill=c["texto"],
                                 text=f"{cant} × {extra.nombre}")
                self.create_text(der, y, anchor="e", font=(FUENTE, 10), fill=c["texto"],
                                 text=dinero_corto(extra.calcular_precio(cant)))
                y += 22

        if d["salsas"]:
            y += 6
            self.create_text(izq, y, anchor="w", text="SALSAS", font=(FUENTE_FUERTE, 8),
                             fill=c["texto_suave"])
            self.create_text(der, y, anchor="e", text="SIN COSTO", font=(FUENTE_FUERTE, 8),
                             fill=c["secundario"])
            y += 20
            x = izq + 8
            for salsa in d["salsas"]:
                ancho_txt = medir(salsa.nombre, (FUENTE, 10)) + 22
                if x + ancho_txt > der:
                    x, y = izq + 8, y + 22
                icono_gota(self, x + 5, y, 14, color_de(salsa.nombre))
                self.create_text(x + 16, y, anchor="w", text=salsa.nombre, font=(FUENTE, 10),
                                 fill=c["texto"])
                x += ancho_txt + 10
            y += 22

        # Descuento y total abajo de todo
        base = alto - 34
        if d.get("descuento") and sabores:
            yd = min(y + 16, base - 66)  # a continuación del detalle, sin pisar el total
            rect_redondeado(self, izq - 6, yd - 13, der + 6, yd + 13, 13,
                            fill=c["secundario_suave"], outline="")
            self.create_text(izq + 4, yd, anchor="w", font=(FUENTE_FUERTE, 10),
                             fill=c["secundario"],
                             text=recortar(d["texto_descuento"], (FUENTE_FUERTE, 10),
                                           der - izq - 100))
            self.create_text(der - 4, yd, anchor="e", font=(FUENTE_FUERTE, 10),
                             fill=c["secundario"], text=f"−{dinero_corto(d['descuento'])}")
        self._separador(base - 44, ancho)
        self.create_text(izq, base, anchor="w", text="Total", font=(FUENTE_FUERTE, 13),
                         fill=c["texto"])
        self.create_text(der, base, anchor="e", font=(FUENTE_FUERTE, 22), fill=c["primario"],
                         text=dinero_corto(d["total"]) if sabores else "$0")

    def _separador(self, y, ancho):
        self.create_line(20, y, ancho - 20, y, fill=COLORES["borde"], dash=(5, 4), width=1.5)


class CampoTexto(tk.Canvas):
    """Campo de texto redondeado (reemplaza al Entry del sistema), con prefijo/sufijo opcionales."""

    def __init__(self, padre, placeholder="", prefijo="", sufijo="", al_enter=None,
                 al_escribir=None, fondo=None, alto=44):
        super().__init__(padre, height=alto, width=1, bg=fondo or COLORES["fondo"],
                         highlightthickness=0, bd=0, cursor="xterm")
        c = COLORES
        self.placeholder, self.prefijo, self.sufijo = placeholder, prefijo, sufijo
        self.enfocado = False
        self.error = False
        self._con_placeholder = False
        self.entrada = tk.Entry(self, relief="flat", bd=0, highlightthickness=0, bg=c["panel"],
                                fg=c["texto"], insertbackground=c["primario"],
                                font=(FUENTE, 11), selectbackground=c["resaltado"],
                                selectforeground=c["texto"])
        self._ventana = self.create_window(0, alto / 2, window=self.entrada, anchor="w")
        self.entrada.bind("<FocusIn>", lambda e: self._foco(True))
        self.entrada.bind("<FocusOut>", lambda e: self._foco(False))
        if al_enter:
            self.entrada.bind("<Return>", lambda e: al_enter())
        if al_escribir:
            self.entrada.bind("<KeyRelease>", lambda e: al_escribir())
        self.bind("<Button-1>", lambda e: self.entrada.focus_set())
        self.bind("<Configure>", lambda e: self.redibujar())
        self._poner_placeholder()

    def _poner_placeholder(self):
        if not self.entrada.get() and self.placeholder and not self.enfocado:
            self.entrada.insert(0, self.placeholder)
            self.entrada.configure(fg=COLORES["texto_tenue"])
            self._con_placeholder = True

    def _sacar_placeholder(self):
        if self._con_placeholder:
            self.entrada.delete(0, tk.END)
            self.entrada.configure(fg=COLORES["texto"])
            self._con_placeholder = False

    def _foco(self, valor):
        self.enfocado = valor
        if valor:
            self._sacar_placeholder()
            self.error = False
        else:
            self._poner_placeholder()
        self.redibujar()

    def get(self):
        return "" if self._con_placeholder else self.entrada.get().strip()

    def set(self, texto):
        self._sacar_placeholder()
        self.entrada.delete(0, tk.END)
        self.entrada.insert(0, texto)
        self._poner_placeholder()

    def limpiar(self):
        self.set("")

    def marcar_error(self):
        self.error = True
        self.redibujar()

    def focus(self):
        self.entrada.focus_set()

    def redibujar(self):
        self.delete("deco")
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 10:
            return
        c = COLORES
        if self.error:
            borde, grosor = c["error"], 2
        elif self.enfocado:
            borde, grosor = c["primario"], 2
        else:
            borde, grosor = c["borde"], 1
        rect_redondeado(self, 1, 1, ancho - 2, alto - 2, 12, fill=c["panel"], outline=borde,
                        width=grosor, tags="deco")
        x = 14
        if self.prefijo:
            self.create_text(x, alto / 2, anchor="w", text=self.prefijo, font=(FUENTE_FUERTE, 11),
                             fill=c["texto_suave"], tags="deco")
            x += medir(self.prefijo, (FUENTE_FUERTE, 11)) + 6
        derecha = 14
        if self.sufijo:
            self.create_text(ancho - 14, alto / 2, anchor="e", text=self.sufijo, font=(FUENTE, 10),
                             fill=c["texto_suave"], tags="deco")
            derecha += medir(self.sufijo, (FUENTE, 10)) + 8
        self.coords(self._ventana, x, alto / 2)
        self.itemconfigure(self._ventana, width=max(10, ancho - x - derecha))
        self.tag_lower("deco")


class Segmentado(Lienzo):
    """Selector de una opción entre varias, en forma de píldora (reemplaza combos y radios)."""

    def __init__(self, padre, opciones, valor, al_cambiar, alto=40, ancho=1, fondo=None):
        super().__init__(padre, alto, ancho, fondo=fondo)
        self.opciones = list(opciones)  # [(valor, texto)]
        self.valor = valor
        self.al_cambiar = al_cambiar
        self._x_hover = None
        self.bind("<Motion>", self._mover)

    def _mover(self, evento):
        self._x_hover = evento.x
        self.redibujar()

    def _set_hover(self, valor):
        if not valor:
            self._x_hover = None
        super()._set_hover(valor)

    def set(self, valor):
        self.valor = valor
        self.redibujar()

    def _indice_en(self, x):
        n = len(self.opciones)
        return max(0, min(n - 1, int(x / (self.winfo_width() / n))))

    def al_click(self, evento):
        valor = self.opciones[self._indice_en(evento.x)][0]
        if valor != self.valor:
            self.valor = valor
            self.redibujar()
            if self.al_cambiar:
                self.al_cambiar(valor)

    def dibujar(self, ancho, alto):
        c = COLORES
        rect_redondeado(self, 0, 0, ancho - 1, alto - 1, alto / 2, fill=c["borde"], outline="")
        n = len(self.opciones)
        tramo = ancho / n
        hover = self._indice_en(self._x_hover) if self._x_hover is not None else None
        for i, (valor, texto) in enumerate(self.opciones):
            x1 = i * tramo
            elegido = valor == self.valor
            if elegido:
                rect_redondeado(self, x1 + 4, 4, x1 + tramo - 4, alto - 5, (alto - 8) / 2,
                                fill=c["panel"], outline="")
            color = (c["primario"] if elegido
                     else c["texto"] if i == hover else c["texto_suave"])
            self.create_text(x1 + tramo / 2, alto / 2, text=texto, fill=color,
                             font=(FUENTE_FUERTE, 10))


class ChipOpcion(Lienzo):
    """Presentación elegible en el armado de combos."""

    def __init__(self, padre, recipiente, comando):
        super().__init__(padre, alto=60, comando=comando)
        self.recipiente = recipiente
        self.seleccionado = False

    def dibujar(self, ancho, alto):
        c, r, cy = COLORES, self.recipiente, alto / 2
        self._caja(ancho, alto, self.seleccionado)
        icono_para(r.nombre)(self, 30, cy, 34)
        self.create_text(56, cy - 9, anchor="w", font=(FUENTE_FUERTE, 11), fill=c["texto"],
                         text=recortar(r.nombre, (FUENTE_FUERTE, 11), ancho - 64))
        self.create_text(56, cy + 10, anchor="w", font=(FUENTE, 9), fill=c["texto_suave"],
                         text=recortar(f"{r.texto_peso()} · hasta {r.max_sabores}", (FUENTE, 9),
                                       ancho - 64))


def columnas_potes(ancho):
    """Posición de cada columna de la lista de potes (la usan las filas y el encabezado)."""
    return {"sabor": 56, "stock": ancho * 0.40, "servido": ancho * 0.76, "recaudado": ancho - 18}


class FilaPote(Lienzo):
    """Pote del mostrador con su barra de stock."""

    def __init__(self, padre, pote, comando):
        super().__init__(padre, alto=62, comando=comando)
        self.pote = pote
        self.seleccionado = False

    def dibujar(self, ancho, alto):
        c, p, cy = COLORES, self.pote, alto / 2
        col = columnas_potes(ancho)
        self._caja(ancho, alto, self.seleccionado)
        self.create_oval(16, cy - 14, 44, cy + 14, fill=color_de(p.sabor.nombre),
                         outline="white", width=2)
        ancho_nombre = col["stock"] - col["sabor"] - 16
        self.create_text(col["sabor"], cy - 9, anchor="w", font=(FUENTE_FUERTE, 11),
                         fill=c["texto"],
                         text=recortar(p.sabor.nombre, (FUENTE_FUERTE, 11), ancho_nombre))
        self.create_text(col["sabor"], cy + 10, anchor="w", font=(FUENTE, 9),
                         fill=c["texto_suave"],
                         text=recortar(f"Pote #{p.id} · {p.sabor.elaboracion} · desde "
                                       f"{fecha_corta(p.fecha_incorporacion)}", (FUENTE, 9),
                                       ancho_nombre))
        # Barra de stock: roja en el mínimo, ámbar cerca, verde con margen
        if not p.puede_servir(0.0) or p.stock_kg <= Pote.STOCK_MINIMO_KG:
            color = c["error"]
        elif p.stock_kg < Pote.STOCK_MINIMO_KG * 2:
            color = c["aviso"]
        else:
            color = c["secundario"]
        largo = min(150, ancho * 0.2)
        x = col["stock"]
        rect_redondeado(self, x, cy - 4, x + largo, cy + 4, 4, fill=c["borde"], outline="")
        lleno = largo * min(1.0, p.stock_kg / max(Pote.STOCK_INICIAL_KG, p.stock_kg, 0.01))
        if lleno > 0:
            rect_redondeado(self, x, cy - 4, x + max(8, lleno), cy + 4, 4, fill=color, outline="")
        self.create_text(x + largo + 10, cy, anchor="w", font=(FUENTE_FUERTE, 10), fill=color,
                         text=f"{formato_kilos(p.stock_kg)} kg")
        self.create_text(col["servido"], cy, anchor="e", font=(FUENTE, 10), fill=c["texto"],
                         text=f"{formato_kilos(p.kilos_servidos)} kg")
        self.create_text(col["recaudado"], cy, anchor="e", font=(FUENTE_FUERTE, 10),
                         fill=c["texto"], text=dinero_corto(p.dinero_recaudado))


class PanelDesplazable(tk.Frame):
    """Frame con scroll vertical (rueda del mouse incluida)."""

    def __init__(self, padre, fondo):
        super().__init__(padre, bg=fondo)
        self.canvas = tk.Canvas(self, bg=fondo, highlightthickness=0, bd=0)
        self.barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                   style="Fina.Vertical.TScrollbar")
        self.interior = tk.Frame(self.canvas, bg=fondo)
        self._ventana = self.canvas.create_window(0, 0, window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=self.barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.barra.pack(side="right", fill="y", padx=(6, 0))
        self.interior.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._ventana, width=e.width))

    def contiene(self, widget):
        return widget is not None and str(widget).startswith(str(self))

    def desplazar(self, evento):
        if self.interior.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-evento.delta / 120) * 3, "units")


# ---------- Ventana principal ----------
class HeladeriaGUI:
    def __init__(self, heladeria):
        self.heladeria = heladeria
        self.ventana = tk.Tk()
        self.ventana.title("Heladería")
        self.ventana.geometry("1240x840")
        self.ventana.minsize(1080, 720)
        self.ventana.configure(bg=COLORES["fondo"])
        self._aviso_pendiente = None
        self._boton_reporte_activo = None
        self._reporte_actual = None

        # Pedido en armado
        self.sel_recipiente = None
        self.sel_potes = []
        self.sel_extras = {}
        self.sel_salsas = []
        self.sel_combo = None  # combo cargado (su descuento vale si no se modifica)

        global FUENTE_FUERTE
        if FUENTE_FUERTE not in tkfont.families(self.ventana):
            FUENTE_FUERTE = FUENTE

        self._configurar_estilos()
        self._armar_encabezado()
        self.toast = None  # cartel flotante de avisos (se crea al primer mensaje)

        contenedor = tk.Frame(self.ventana, bg=COLORES["fondo"])
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)

        self.tab_ventas = ttk.Frame(contenedor)
        self.tab_datos = ttk.Frame(contenedor)
        self.tab_reportes = ttk.Frame(contenedor)
        for tab in (self.tab_ventas, self.tab_datos, self.tab_reportes):
            tab.grid(row=0, column=0, sticky="nsew")

        self._armar_tab_ventas()
        self._armar_tab_datos()
        self._armar_tab_reportes()
        self._ir_a(self.tab_ventas)

        self.ventana.bind_all("<MouseWheel>", self._rueda)

    def _rueda(self, evento):
        try:
            widget = self.ventana.winfo_containing(evento.x_root, evento.y_root)
        except (KeyError, tk.TclError):  # p. ej. la lista desplegable de un combo
            return
        for panel in (self.panel_venta, self.panel_potes, self.panel_combos):
            if panel.contiene(widget):
                panel.desplazar(evento)
                return

    # ---------- Estilos y piezas reutilizables ----------
    def _configurar_estilos(self):
        c = COLORES
        estilo = ttk.Style(self.ventana)
        estilo.theme_use("clam")  # el tema "clam" es el que mas deja personalizar

        estilo.configure(".", background=c["fondo"], foreground=c["texto"], font=(FUENTE, 11))
        estilo.configure("TFrame", background=c["fondo"])
        estilo.configure("Panel.TFrame", background=c["panel"])
        estilo.configure("TLabel", background=c["fondo"])
        estilo.configure("Panel.TLabel", background=c["panel"])
        estilo.configure("Titulo.TLabel", background=c["panel"], font=(FUENTE_FUERTE, 14))
        estilo.configure("Suave.TLabel", background=c["panel"], foreground=c["texto_suave"])
        estilo.configure("Grande.TLabel", background=c["panel"], foreground=c["primario"],
                         font=(FUENTE_FUERTE, 28))

        estilo.configure("Reporte.TButton", background=c["panel"], foreground=c["texto"],
                         font=(FUENTE, 11), anchor="w", padding=(12, 6), borderwidth=0)
        estilo.map("Reporte.TButton",
                   background=[("pressed", c["resaltado"]), ("active", c["borde"])])
        # Boton del reporte que se esta mostrando
        estilo.configure("ReporteActivo.TButton", background=c["resaltado"],
                         foreground=c["primario_hover"], font=(FUENTE_FUERTE, 11),
                         anchor="w", padding=(12, 6), borderwidth=0)
        estilo.map("ReporteActivo.TButton", background=[("active", c["resaltado"])])

        estilo.configure("Treeview", background=c["panel"], fieldbackground=c["panel"],
                         rowheight=32, borderwidth=0)
        estilo.configure("Treeview.Heading", background=c["borde"], foreground=c["texto"],
                         font=(FUENTE_FUERTE, 10), borderwidth=0, padding=(8, 6))
        estilo.map("Treeview", background=[("selected", c["resaltado"])],
                   foreground=[("selected", c["texto"])])

        # Scrollbars finitas y sin flechas
        for nombre in ("Vertical.TScrollbar", "Fina.Vertical.TScrollbar"):
            estilo.layout(nombre, [("Vertical.Scrollbar.trough", {"children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})], "sticky": "ns"})])
            estilo.configure(nombre, troughcolor=c["fondo"], background=c["borde"],
                             bordercolor=c["fondo"], lightcolor=c["borde"], darkcolor=c["borde"],
                             gripcount=0, arrowsize=8)
            estilo.map(nombre, background=[("active", c["borde_hover"])])

    def _tarjeta(self, padre, titulo, subtitulo=""):
        """Panel blanco con titulo. Devuelve (tarjeta, cuerpo) para meter widgets adentro."""
        tarjeta = tk.Frame(padre, bg=COLORES["panel"], padx=20, pady=18,
                           highlightthickness=1, highlightbackground=COLORES["borde"])
        ttk.Label(tarjeta, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        if subtitulo:
            ttk.Label(tarjeta, text=subtitulo, style="Suave.TLabel").pack(anchor="w")
        cuerpo = ttk.Frame(tarjeta, style="Panel.TFrame")
        cuerpo.pack(fill="both", expand=True, pady=(12, 0))
        return tarjeta, cuerpo

    def _tabla(self, padre, columnas, alto=8):
        """Treeview con scrollbar. columnas = [(id, titulo, ancho, alineacion)]"""
        contenedor = ttk.Frame(padre, style="Panel.TFrame")
        contenedor.pack(fill="both", expand=True)
        tabla = ttk.Treeview(contenedor, columns=[c[0] for c in columnas],
                             show="headings", height=alto)
        for col_id, titulo, ancho, alineacion in columnas:
            tabla.heading(col_id, text=titulo, anchor=alineacion)
            tabla.column(col_id, width=ancho, anchor=alineacion, stretch=True)
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        tabla.tag_configure("par", background="#FFFBF7")
        return tabla

    @staticmethod
    def _llenar_tabla(tabla, filas):
        tabla.delete(*tabla.get_children())
        for i, fila in enumerate(filas):
            tabla.insert("", "end", values=fila, tags=("par",) if i % 2 else ())

    # ---------- Encabezado, navegación y barra de estado ----------
    def _armar_encabezado(self):
        c = COLORES
        encabezado = tk.Frame(self.ventana, bg=c["panel"])
        encabezado.pack(fill="x")
        tk.Frame(self.ventana, bg=c["borde"], height=1).pack(fill="x")

        marca = tk.Frame(encabezado, bg=c["panel"])
        marca.pack(side="left", padx=(22, 10), pady=12)
        logo = tk.Canvas(marca, width=46, height=46, bg=c["panel"], highlightthickness=0)
        logo.pack(side="left")
        logo.create_oval(1, 1, 45, 45, fill=c["primario_suave"], outline="")
        icono_cono(logo, 23, 22, 34)
        textos = tk.Frame(marca, bg=c["panel"])
        textos.pack(side="left", padx=(10, 0))
        tk.Label(textos, text="Heladería", bg=c["panel"], fg=c["texto"],
                 font=(FUENTE_FUERTE, 17)).pack(anchor="w")
        tk.Label(textos, text="Gestión de ventas y potes", bg=c["panel"], fg=c["texto_suave"],
                 font=(FUENTE, 9)).pack(anchor="w")

        # Navegación propia (reemplaza a las pestañas del sistema)
        nav = tk.Frame(encabezado, bg=c["panel"])
        nav.pack(side="left", padx=24)
        self.botones_nav = {}
        for nombre, texto in [("ventas", "Nueva venta"), ("datos", "Catálogo"),
                              ("reportes", "Resumen")]:
            boton = BotonPildora(nav, texto, None, variante="nav", alto=38, ancho=128,
                                 fondo=c["panel"])
            boton.comando = lambda n=nombre: self._ir_a(getattr(self, f"tab_{n}"))
            boton.pack(side="left", padx=3)
            self.botones_nav[nombre] = boton

        # Indicadores que se actualizan solos despues de cada venta
        indicadores = tk.Frame(encabezado, bg=c["panel"])
        indicadores.pack(side="right", padx=22)
        self.kpis = {}
        for clave, titulo in [("recaudado", "Recaudado"), ("ventas", "Ventas"), ("kilos", "Kilos")]:
            bloque = tk.Frame(indicadores, bg=c["panel"])
            bloque.pack(side="left", padx=12)
            tk.Label(bloque, text=titulo.upper(), bg=c["panel"], fg=c["texto_suave"],
                     font=(FUENTE_FUERTE, 8)).pack(anchor="e")
            self.kpis[clave] = tk.Label(bloque, text="-", bg=c["panel"], fg=c["texto"],
                                        font=(FUENTE_FUERTE, 14))
            self.kpis[clave].pack(anchor="e")
        self.kpis["recaudado"].configure(fg=c["primario"])

    def _ir_a(self, tab):
        tab.tkraise()
        for nombre, boton in self.botones_nav.items():
            boton.set(activo=getattr(self, f"tab_{nombre}") is tab)

    def _avisar(self, texto, error=False, alerta=False):
        """Cartel flotante abajo al centro durante unos segundos (en vez de un popup).

        Verde = listo, ámbar = advertencia, rojo = error. Se cierra solo o tocándolo.
        """
        c = COLORES
        color = c["error"] if error else c["aviso"] if alerta else c["secundario"]
        if error:
            self.ventana.bell()
        if self.toast is None:
            self.toast = tk.Canvas(self.ventana, bg=c["fondo"], highlightthickness=0, bd=0,
                                   cursor="hand2")
            self.toast.bind("<Button-1>", lambda e: self._ocultar_aviso())
        t = self.toast
        t.delete("all")
        fuente = (FUENTE, 10)
        ancho_texto = min(medir(texto, fuente), max(300, self.ventana.winfo_width() - 200))
        id_texto = t.create_text(52, 0, anchor="nw", text=texto, width=ancho_texto, font=fuente,
                                 fill="white")
        x1, y1, x2, y2 = t.bbox(id_texto)
        alto = max(48, (y2 - y1) + 26)
        ancho = (x2 - x1) + 52 + 24
        t.configure(width=ancho, height=alto)
        rect_redondeado(t, 0, 0, ancho - 1, alto - 1, 16, fill=c["texto"], outline="")
        cy = alto / 2
        t.create_oval(15, cy - 12, 39, cy + 12, fill=color, outline="")
        if error:
            for dx in (-1, 1):
                t.create_line(27 - 5, cy - 5 * dx, 27 + 5, cy + 5 * dx, fill="white", width=2.5,
                              capstyle="round")
        elif alerta:
            t.create_text(27, cy, text="!", fill="white", font=(FUENTE_FUERTE, 12))
        else:
            dibujar_tilde(t, 27, cy, 11, grosor=2.5)
        t.coords(id_texto, 52, (alto - (y2 - y1)) / 2)
        t.tag_raise(id_texto)
        t.place(relx=0.5, rely=1.0, anchor="s", y=-20)
        t.tk.call("raise", t._w)  # en un Canvas, lift() sube dibujos internos, no el widget
        if self._aviso_pendiente:
            self.ventana.after_cancel(self._aviso_pendiente)
        segundos = 8 if (error or alerta) else 5
        self._aviso_pendiente = self.ventana.after(segundos * 1000, self._ocultar_aviso)

    def _ocultar_aviso(self):
        self._aviso_pendiente = None
        if self.toast is not None:
            self.toast.place_forget()

    # ---------- Pestaña: Nueva venta ----------
    def _armar_tab_ventas(self):
        c = COLORES
        frame = self.tab_ventas
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0, minsize=380)
        frame.rowconfigure(0, weight=1)

        # Columna izquierda: los pasos, con scroll
        self.panel_venta = PanelDesplazable(frame, c["fondo"])
        self.panel_venta.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        interior = self.panel_venta.interior

        self.pasos = {}
        self.grilla_combos = self._seccion(interior, "combos", None, "Combos sugeridos",
                                           "Se cargan enteros · después podés cambiarlos",
                                           icono="combo")
        self.grilla_populares = self._seccion(interior, "populares", None,
                                              "Los más populares",
                                              "Según las ventas · tocá uno para sumarlo",
                                              icono="estrella")
        self.grilla_potes = self._seccion(interior, "pote", 1, "Elegí el pote",
                                          "Tamaño o presentación")
        self.grilla_sabores = self._seccion(interior, "sabores", 2, "Elegí los sabores",
                                            "Primero elegí un pote")
        self.grilla_extras = self._seccion(interior, "extras", 3, "¿Le sumamos algo?",
                                           "Opcional · se cobra aparte")
        self.grilla_salsas = self._seccion(interior, "salsas", 4, "Salsa de regalo",
                                           "Opcional · sin costo")
        self.tarjetas_pote, self.chips_sabor, self.filas_extra, self.chips_salsa = [], [], [], []
        self.tarjetas_combo, self.chips_popular = [], []
        self.aviso_populares = None

        # Columna derecha: ticket + cobrar + últimas ventas
        derecha = tk.Frame(frame, bg=c["fondo"], width=380)
        derecha.grid(row=0, column=1, sticky="nsew")
        derecha.rowconfigure(0, weight=1)
        derecha.columnconfigure(0, weight=1)
        self.ticket = TicketPedido(derecha)
        self.ticket.grid(row=0, column=0, sticky="nsew")
        self.boton_cobrar = BotonPildora(derecha, "Cobrar", self.registrar_venta, alto=54)
        self.boton_cobrar.grid(row=1, column=0, sticky="ew", pady=(12, 4))
        self.boton_vaciar = BotonPildora(derecha, "Vaciar pedido", self._vaciar_pedido,
                                         variante="suave", alto=32)
        self.boton_vaciar.grid(row=2, column=0, sticky="ew")
        self.lienzo_ultimas = tk.Canvas(derecha, height=128, bg=c["fondo"],
                                        highlightthickness=0, bd=0)
        self.lienzo_ultimas.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.lienzo_ultimas.bind("<Configure>", lambda e: self._dibujar_ultimas())

    def _seccion(self, padre, clave, numero, titulo, ayuda, icono=None):
        """Encabezado de sección (número o ícono + título + ayuda) y una grilla para el contenido."""
        c = COLORES
        bloque = tk.Frame(padre, bg=c["fondo"])
        bloque.pack(fill="x", pady=(0 if not self.pasos else 22, 0))
        self.bloques_seccion = getattr(self, "bloques_seccion", {})
        self.bloques_seccion[clave] = bloque
        cabecera = tk.Frame(bloque, bg=c["fondo"])
        cabecera.pack(fill="x", pady=(0, 10))
        insignia = tk.Canvas(cabecera, width=30, height=30, bg=c["fondo"], highlightthickness=0)
        insignia.pack(side="left")
        tk.Label(cabecera, text=titulo, bg=c["fondo"], fg=c["texto"],
                 font=(FUENTE_FUERTE, 14)).pack(side="left", padx=(10, 0))
        lbl_ayuda = tk.Label(cabecera, text=ayuda, bg=c["fondo"], fg=c["texto_suave"],
                             font=(FUENTE, 10))
        lbl_ayuda.pack(side="right")
        grilla = tk.Frame(bloque, bg=c["fondo"])
        grilla.pack(fill="x")
        self.pasos[clave] = (insignia, lbl_ayuda, numero)
        if icono == "combo":
            insignia.create_oval(1, 1, 29, 29, fill=c["primario_suave"], outline="")
            icono_cono(insignia, 15, 15, 20)
        elif icono == "estrella":
            insignia.create_oval(1, 1, 29, 29, fill="#FFF3D6", outline="")
            insignia.create_polygon(dibujar_estrella(15, 15, 9, 4), fill="#F0B429", outline="")
        return grilla

    def _marcar_paso(self, clave, completo, ayuda=None, destacar=False):
        insignia, lbl_ayuda, numero = self.pasos[clave]
        c = COLORES
        insignia.delete("all")
        if completo:
            insignia.create_oval(1, 1, 29, 29, fill=c["secundario"], outline="")
            dibujar_tilde(insignia, 15, 15, 12, grosor=2.5)
        else:
            insignia.create_oval(1, 1, 29, 29, fill=c["primario"] if destacar else c["panel"],
                                 outline=c["primario"] if destacar else c["borde"], width=1.5)
            insignia.create_text(15, 15, text=str(numero), font=(FUENTE_FUERTE, 11),
                                 fill="white" if destacar else c["texto_suave"])
        if ayuda is not None:
            lbl_ayuda.configure(text=ayuda)

    @staticmethod
    def _repartir(grilla, widgets, columnas):
        for widget in grilla.winfo_children():
            widget.grid_forget()
        for col in range(columnas):
            grilla.columnconfigure(col, weight=1, uniform="col")
        for i, widget in enumerate(widgets):
            fila, col = divmod(i, columnas)
            widget.grid(row=fila, column=col, sticky="ew",
                        padx=(0 if col == 0 else 6, 0 if col == columnas - 1 else 6),
                        pady=(0 if fila == 0 else 12, 0))

    def _construir_opciones_venta(self):
        """(Re)crea tarjetas y chips cuando cambia el catálogo."""
        h = self.heladeria
        for lista in (self.tarjetas_pote, self.chips_sabor, self.filas_extra, self.chips_salsa,
                      self.tarjetas_combo, self.chips_popular):
            for widget in lista:
                widget.destroy()
            lista.clear()

        self.tarjetas_pote.extend(
            TarjetaPote(self.grilla_potes, r, lambda r=r: self._elegir_recipiente(r))
            for r in h.recipientes)
        self.chips_sabor.extend(
            ChipSabor(self.grilla_sabores, p, lambda p=p: self._alternar_sabor(p))
            for p in h.potes)
        self.filas_extra.extend(
            FilaExtra(self.grilla_extras, e, self._cambiar_extra) for e in h.extras)
        self.chips_salsa.extend(
            ChipSalsa(self.grilla_salsas, s, lambda s=s: self._alternar_salsa(s))
            for s in h.salsas)

        self.tarjetas_combo.extend(
            TarjetaCombo(self.grilla_combos, combo, lambda k=combo: self._cargar_combo(k))
            for combo in h.combos)
        ranking = h.sabores_populares(CANTIDAD_POPULARES)
        self.chips_popular.extend(
            ChipPopular(self.grilla_populares, sabor, puesto, pedidos,
                        lambda s=sabor: self._alternar_sabor_popular(s))
            for puesto, (sabor, pedidos) in enumerate(ranking, start=1))
        # Sin combos cargados la sección no se muestra
        if not self.tarjetas_combo:
            self.bloques_seccion["combos"].pack_forget()

        self._repartir(self.grilla_combos, self.tarjetas_combo, 2)
        self._repartir(self.grilla_populares, self.chips_popular, CANTIDAD_POPULARES)
        self._repartir(self.grilla_potes, self.tarjetas_pote, 5)
        self._repartir(self.grilla_sabores, self.chips_sabor, 3)
        self._repartir(self.grilla_extras, self.filas_extra, 2)
        self._repartir(self.grilla_salsas, self.chips_salsa, 4)
        # Sin ventas todavía, el ranking muestra un aviso en lugar de quedar vacío
        if self.aviso_populares is not None:
            self.aviso_populares.destroy()
            self.aviso_populares = None
        if not self.chips_popular:
            self.aviso_populares = tk.Label(
                self.grilla_populares, bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                font=(FUENTE, 10), anchor="w",
                text="Todavía no hay ventas: el ranking se arma solo a medida que se vende.")
            self.aviso_populares.grid(row=0, column=0, columnspan=CANTIDAD_POPULARES, sticky="w")

        # Si el pedido apuntaba a algo que ya no existe, se limpia
        if self.sel_recipiente not in h.recipientes:
            self.sel_recipiente = None
        self.sel_potes = [p for p in self.sel_potes if p in h.potes]
        if self.sel_combo not in h.combos:
            self.sel_combo = None

    # ---- Acciones del pedido ----
    def _elegir_recipiente(self, recipiente):
        self.sel_recipiente = recipiente
        if len(self.sel_potes) > recipiente.max_sabores:
            quitados = self.sel_potes[recipiente.max_sabores:]
            self.sel_potes = self.sel_potes[:recipiente.max_sabores]
            self._avisar(f"{recipiente.nombre} lleva hasta {recipiente.max_sabores} sabores: "
                         f"saqué {', '.join(p.sabor.nombre for p in quitados)}.", error=True)
        self._actualizar_pedido()

    def _alternar_sabor(self, pote):
        r = self.sel_recipiente
        if r is None:
            self._avisar("Primero elegí el pote.", error=True)
            return
        if pote in self.sel_potes:
            self.sel_potes.remove(pote)
        elif len(self.sel_potes) >= r.max_sabores:
            self._avisar(f"{r.nombre} lleva hasta {r.max_sabores} sabores. "
                         "Sacá uno para cambiarlo.", error=True)
            return
        elif not pote.puede_servir(r.kilos / (len(self.sel_potes) + 1)):
            self._avisar(f"No queda stock suficiente de {pote.sabor.nombre} "
                         f"({formato_kilos(pote.stock_kg)} kg). Reponelo en Catálogo.", error=True)
            return
        else:
            self.sel_potes.append(pote)
        self._actualizar_pedido()

    def _cargar_combo(self, combo):
        """Reemplaza el pedido por lo que trae el combo (después se puede modificar)."""
        h, r = self.heladeria, combo.recipiente
        kilos = r.kilos / len(combo.sabores)
        potes, faltantes = [], []
        for sabor in combo.sabores:
            pote = h.pote_de(sabor, kilos)
            if pote and pote.puede_servir(kilos):
                potes.append(pote)
            else:
                faltantes.append(sabor.nombre)
        self.sel_recipiente, self.sel_potes = r, potes
        self.sel_extras = dict(combo.extras)
        self.sel_salsas = list(combo.salsas)
        self.sel_combo = combo
        self._actualizar_pedido()
        if faltantes:
            self._avisar(f"{combo.nombre} cargado, pero no hay stock de {', '.join(faltantes)}. "
                         "Elegí otro sabor.", error=True)
        else:
            descuento = (f" con {combo.descuento_pct:g}% de descuento"
                         if combo.tiene_descuento() else "")
            self._avisar(f"{combo.nombre} cargado{descuento}. Si lo modificás, se cobra "
                         "a precio normal.")

    def _alternar_sabor_popular(self, sabor):
        elegido = next((p for p in self.sel_potes if p.sabor is sabor), None)
        if elegido:
            self._alternar_sabor(elegido)
            return
        r = self.sel_recipiente
        kilos = r.kilos / (len(self.sel_potes) + 1) if r else 0.0
        pote = self.heladeria.pote_de(sabor, kilos)
        if pote is None:
            self._avisar(f"No hay ningún pote de {sabor.nombre} en el mostrador.", error=True)
            return
        self._alternar_sabor(pote)

    def _combo_coincide(self, combo):
        return (self.sel_recipiente is combo.recipiente
                and [p.sabor for p in self.sel_potes] == combo.sabores
                and self._extras_elegidos() == combo.extras
                and set(self.sel_salsas) == set(combo.salsas))

    def _cambiar_extra(self, extra, cantidad):
        if cantidad > 0:
            self.sel_extras[extra] = cantidad
        else:
            self.sel_extras.pop(extra, None)
        self._actualizar_pedido()

    def _alternar_salsa(self, salsa):
        if salsa in self.sel_salsas:
            self.sel_salsas.remove(salsa)
        else:
            self.sel_salsas.append(salsa)
        self._actualizar_pedido()

    def _vaciar_pedido(self):
        self.sel_recipiente, self.sel_potes = None, []
        self.sel_extras, self.sel_salsas = {}, []
        self.sel_combo = None
        self._actualizar_pedido()

    def _extras_elegidos(self):
        # En el orden del catálogo
        return [(e, self.sel_extras[e]) for e in self.heladeria.extras if e in self.sel_extras]

    def _salsas_elegidas(self):
        return [s for s in self.heladeria.salsas if s in self.sel_salsas]

    def _actualizar_pedido(self):
        """Refleja el pedido en curso en tarjetas, chips, pasos y ticket."""
        h, r = self.heladeria, self.sel_recipiente
        potes_baratos = sorted(h.potes, key=lambda p: p.sabor.precio_por_kilo)[:1]

        for tarjeta in self.tarjetas_pote:
            tarjeta.seleccionado = tarjeta.recipiente is r
            tarjeta.precio_desde = (tarjeta.recipiente.calcular_precio_total(potes_baratos)
                                    if potes_baratos else 0.0)
            tarjeta.redibujar()

        lleno = r is not None and len(self.sel_potes) >= r.max_sabores
        porcion_minima = min((x.kilos / x.max_sabores for x in h.recipientes), default=0.0)
        for chip in self.chips_sabor:
            pote = chip.pote
            chip.orden = self.sel_potes.index(pote) + 1 if pote in self.sel_potes else 0
            if r is None:
                kilos = porcion_minima
            else:
                kilos = r.kilos / max(1, len(self.sel_potes) + (0 if chip.orden else 1))
            if not chip.orden and not pote.puede_servir(kilos):
                chip.estado = "sin_stock"
            elif r is None or lleno:
                chip.estado = "apagado"
            else:
                chip.estado = "normal"
            chip.habilitado = chip.estado != "sin_stock"
            chip.redibujar()

        for chip in self.chips_popular:
            sabor = chip.sabor
            chip.seleccionado = any(p.sabor is sabor for p in self.sel_potes)
            if r is None:
                kilos = porcion_minima
            else:
                kilos = r.kilos / max(1, len(self.sel_potes) + (0 if chip.seleccionado else 1))
            pote = h.pote_de(sabor, kilos)
            if not chip.seleccionado and not (pote and pote.puede_servir(kilos)):
                chip.estado = "sin_stock"
            elif lleno:  # sin pote elegido se ven a color igual: son la vidriera
                chip.estado = "apagado"
            else:
                chip.estado = "normal"
            chip.habilitado = chip.estado != "sin_stock"
            chip.redibujar()

        for tarjeta in self.tarjetas_combo:
            combo = tarjeta.combo
            tarjeta.incompleto = bool(h.sabores_sin_stock(combo.recipiente, combo.sabores))
            tarjeta.precio_original, tarjeta.precio = precio_combo(
                combo.recipiente, combo.sabores, combo.extras, combo.salsas, combo.descuento_pct)
            tarjeta.seleccionado = self._combo_coincide(combo)
            tarjeta.redibujar()

        for fila in self.filas_extra:
            fila.cantidad = self.sel_extras.get(fila.extra, 0)
            fila.redibujar()
        for chip in self.chips_salsa:
            chip.seleccionado = chip.salsa in self.sel_salsas
            chip.redibujar()

        # Encabezados de cada paso
        self._marcar_paso("pote", r is not None,
                          f"{r.nombre} · {r.texto_peso()}" if r else "Tamaño o presentación",
                          destacar=r is None)
        if r is None:
            ayuda = "Primero elegí un pote"
        else:
            ayuda = f"{len(self.sel_potes)} de {r.max_sabores} elegidos"
        self._marcar_paso("sabores", bool(self.sel_potes), ayuda,
                          destacar=r is not None and not self.sel_potes)
        cant_extras = sum(self.sel_extras.values())
        self._marcar_paso("extras", cant_extras > 0,
                          f"{cant_extras} agregado(s)" if cant_extras else "Opcional · se cobra aparte")
        self._marcar_paso("salsas", bool(self.sel_salsas),
                          f"{len(self.sel_salsas)} elegida(s) · sin costo" if self.sel_salsas
                          else "Opcional · sin costo")

        # Ticket y botón de cobro
        extras, salsas = self._extras_elegidos(), self._salsas_elegidas()
        combo = self._combo_activo()
        datos = {"recipiente": r, "sabores": [p.sabor for p in self.sel_potes], "extras": extras,
                 "salsas": salsas, "precio_helado": 0.0, "descuento": 0.0, "total": 0.0,
                 "texto_descuento": (f"{combo.nombre} (-{combo.descuento_pct:g}%)"
                                     if combo else "")}
        if r and self.sel_potes:
            # Crear una Venta no la registra: solo calcula
            venta = Venta(self.sel_potes, r, extras, salsas,
                          combo.descuento_pct if combo else 0.0, combo)
            datos["precio_helado"] = r.calcular_precio_total(self.sel_potes)
            datos["descuento"], datos["total"] = venta.monto_descuento, venta.precio_total
            self.boton_cobrar.set(f"Cobrar {dinero_corto(venta.precio_total)}", habilitado=True)
        else:
            self.boton_cobrar.set("Cobrar", habilitado=False)
        hay_algo = bool(r or self.sel_potes or self.sel_extras or self.sel_salsas)
        self.boton_vaciar.set(habilitado=hay_algo)
        self.ticket.mostrar(datos, f"Venta #{len(h.ventas) + 1}")

    def _dibujar_ultimas(self):
        c, lienzo = COLORES, self.lienzo_ultimas
        lienzo.delete("all")
        ancho = lienzo.winfo_width()
        if ancho < 10:
            return
        lienzo.create_text(4, 12, anchor="w", text="ÚLTIMAS VENTAS", font=(FUENTE_FUERTE, 8),
                           fill=c["texto_suave"])
        ventas = list(enumerate(self.heladeria.ventas, start=1))[-3:][::-1]
        if not ventas:
            lienzo.create_text(4, 40, anchor="w", text="Todavía no hay ventas.",
                               font=(FUENTE, 10), fill=c["texto_tenue"])
            return
        y = 42
        for numero, venta in ventas:
            rect_redondeado(lienzo, 0, y - 15, ancho - 1, y + 15, 10, fill=c["panel"],
                            outline=c["borde"])
            lienzo.create_text(12, y, anchor="w", text=f"#{numero}", font=(FUENTE_FUERTE, 9),
                               fill=c["texto_suave"])
            precio = dinero_corto(venta.calcular_precio_total())
            detalle = f"{venta.recipiente.nombre} · {venta.nombres_sabores()}"
            lienzo.create_text(48, y, anchor="w", font=(FUENTE, 9), fill=c["texto"],
                               text=recortar(detalle, (FUENTE, 9), ancho - 48 - 90))
            lienzo.create_text(ancho - 12, y, anchor="e", text=precio, font=(FUENTE_FUERTE, 9),
                               fill=c["texto"])
            y += 36

    # ---------- Pestaña: Catálogo ----------
    def _armar_tab_datos(self):
        c = COLORES
        frame = self.tab_datos
        frame.configure(style="TFrame")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Sub-navegación del catálogo
        barra = tk.Frame(frame, bg=c["fondo"])
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.subnav_catalogo = Segmentado(
            barra, [("potes", "Sabores y potes"), ("presentaciones", "Presentaciones"),
                    ("combos", "Combos y descuentos")],
            "potes", self._ir_a_catalogo, alto=44, ancho=560)
        self.subnav_catalogo.pack(side="left")

        contenedor = tk.Frame(frame, bg=c["fondo"])
        contenedor.grid(row=1, column=0, sticky="nsew")
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        self.paginas_catalogo = {}
        for clave in ("potes", "presentaciones", "combos"):
            pagina = tk.Frame(contenedor, bg=c["fondo"])
            pagina.grid(row=0, column=0, sticky="nsew")
            self.paginas_catalogo[clave] = pagina

        # Estado de la pestaña
        self.cat_pote_sel = None
        self.filas_pote, self.tarjetas_presentacion, self.tarjetas_cat_combo = [], [], []
        self.chips_cb_recip, self.chips_cb_sabor, self.filas_cb_extra, self.chips_cb_salsa = \
            [], [], [], []
        self._cb_limpiar_estado()

        self._armar_cat_potes(self.paginas_catalogo["potes"])
        self._armar_cat_presentaciones(self.paginas_catalogo["presentaciones"])
        self._armar_cat_combos(self.paginas_catalogo["combos"])
        self._ir_a_catalogo("potes")

    def _ir_a_catalogo(self, clave):
        self.paginas_catalogo[clave].tkraise()
        self.subnav_catalogo.set(clave)

    # Piezas de formulario sobre el fondo crema
    def _titulo(self, padre, titulo, ayuda="", pady=(0, 6)):
        fila = tk.Frame(padre, bg=COLORES["fondo"])
        fila.pack(fill="x", pady=pady)
        lbl_titulo = tk.Label(fila, text=titulo, bg=COLORES["fondo"], fg=COLORES["texto"],
                              font=(FUENTE_FUERTE, 14))
        lbl_titulo.pack(side="left")
        lbl_ayuda = tk.Label(fila, text=ayuda, bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                             font=(FUENTE, 10))
        lbl_ayuda.pack(side="right")
        return lbl_titulo, lbl_ayuda

    def _etiqueta(self, padre, texto, pady=(10, 5)):
        lbl = tk.Label(padre, text=texto, bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                       font=(FUENTE_FUERTE, 9), anchor="w")
        lbl.pack(fill="x", pady=pady)
        return lbl

    def _nota(self, padre, texto):
        lbl = tk.Label(padre, text=texto, bg=COLORES["fondo"], fg=COLORES["texto_tenue"],
                       font=(FUENTE, 9), anchor="w", justify="left", wraplength=340)
        lbl.pack(fill="x", pady=(6, 0))
        return lbl

    # ---- Sabores y potes ----
    def _armar_cat_potes(self, pagina):
        c = COLORES
        pagina.columnconfigure(0, minsize=360)
        pagina.columnconfigure(1, weight=1)
        pagina.rowconfigure(0, weight=1)

        izq = tk.Frame(pagina, bg=c["fondo"])
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 32))
        self._titulo(izq, "Nuevo sabor", f"Abre un pote de {Pote.STOCK_INICIAL_KG:g} kg")
        self._etiqueta(izq, "Nombre", pady=(4, 5))
        self.campo_sabor_nombre = CampoTexto(izq, "Ej: Banana split", al_enter=self.agregar_sabor)
        self.campo_sabor_nombre.pack(fill="x")
        self._etiqueta(izq, "Elaboración")
        self.seg_elaboracion = Segmentado(izq, ELABORACIONES, ELABORACIONES[0][0], None)
        self.seg_elaboracion.pack(fill="x")
        self._etiqueta(izq, "Precio por kilo")
        self.campo_sabor_precio = CampoTexto(izq, "15000", prefijo="$", sufijo="por kg",
                                             al_enter=self.agregar_sabor)
        self.campo_sabor_precio.pack(fill="x")
        BotonPildora(izq, "Agregar sabor", self.agregar_sabor, alto=48).pack(fill="x", pady=(16, 0))

        self._titulo(izq, "Pote seleccionado", pady=(24, 8))
        self.lienzo_pote_sel = tk.Canvas(izq, height=62, bg=c["fondo"], highlightthickness=0)
        self.lienzo_pote_sel.pack(fill="x")
        self.lienzo_pote_sel.bind("<Configure>", lambda e: self._dibujar_pote_sel())
        self._etiqueta(izq, "Reponer stock")
        fila = tk.Frame(izq, bg=c["fondo"])
        fila.pack(fill="x")
        self.campo_reponer = CampoTexto(fila, "Cuántos kilos", sufijo="kg",
                                        al_enter=self.reponer_stock)
        self.campo_reponer.pack(side="left", fill="x", expand=True)
        self.boton_reponer = BotonPildora(fila, "Reponer", self.reponer_stock, alto=44, ancho=120)
        self.boton_reponer.pack(side="left", padx=(10, 0))
        self._etiqueta(izq, "Abrir otro pote del mismo sabor")
        fila = tk.Frame(izq, bg=c["fondo"])
        fila.pack(fill="x")
        self.campo_pote_fecha = CampoTexto(fila, "AAAA-MM-DD", al_enter=self.agregar_pote)
        self.campo_pote_fecha.set(datetime.now().strftime("%Y-%m-%d"))
        self.campo_pote_fecha.pack(side="left", fill="x", expand=True)
        self.boton_abrir_pote = BotonPildora(fila, "Abrir pote", self.agregar_pote, alto=44,
                                             ancho=120)
        self.boton_abrir_pote.pack(side="left", padx=(10, 0))

        der = tk.Frame(pagina, bg=c["fondo"])
        der.grid(row=0, column=1, sticky="nsew")
        _, self.lbl_ayuda_potes = self._titulo(der, "Potes en el mostrador")
        self.encabezado_potes = tk.Canvas(der, height=30, bg=c["fondo"], highlightthickness=0)
        self.encabezado_potes.pack(fill="x", padx=(0, 14))
        self.encabezado_potes.bind("<Configure>", lambda e: self._dibujar_encabezado_potes())
        self.panel_potes = PanelDesplazable(der, c["fondo"])
        self.panel_potes.pack(fill="both", expand=True)

    def _dibujar_encabezado_potes(self):
        lienzo, c = self.encabezado_potes, COLORES
        lienzo.delete("all")
        col = columnas_potes(lienzo.winfo_width())
        for clave, texto, ancla in (("sabor", "SABOR", "w"), ("stock", "STOCK", "w"),
                                    ("servido", "SERVIDO", "e"), ("recaudado", "RECAUDADO", "e")):
            lienzo.create_text(col[clave], 15, anchor=ancla, text=texto, fill=c["texto_suave"],
                               font=(FUENTE_FUERTE, 8))

    def _dibujar_pote_sel(self):
        lienzo, c, p = self.lienzo_pote_sel, COLORES, self.cat_pote_sel
        lienzo.delete("all")
        ancho, alto = lienzo.winfo_width(), lienzo.winfo_height()
        if ancho < 10:
            return
        if p is None:
            rect_redondeado(lienzo, 1, 1, ancho - 2, alto - 2, 14, fill=c["fondo"],
                            outline=c["borde"], dash=(4, 3))
            lienzo.create_text(ancho / 2, alto / 2, font=(FUENTE, 10), fill=c["texto_suave"],
                               text="Tocá un pote de la lista para reponerlo")
            return
        rect_redondeado(lienzo, 1, 1, ancho - 2, alto - 2, 14, fill=c["primario_suave"],
                        outline=c["primario"], width=2)
        cy = alto / 2
        lienzo.create_oval(16, cy - 16, 48, cy + 16, fill=color_de(p.sabor.nombre),
                           outline="white", width=2)
        lienzo.create_text(62, cy - 10, anchor="w", font=(FUENTE_FUERTE, 12), fill=c["texto"],
                           text=recortar(p.sabor.nombre, (FUENTE_FUERTE, 12), ancho - 80))
        lienzo.create_text(62, cy + 11, anchor="w", font=(FUENTE, 9), fill=c["texto_suave"],
                           text=f"Pote #{p.id} · quedan {formato_kilos(p.stock_kg)} kg")

    def _elegir_pote_catalogo(self, pote):
        self.cat_pote_sel = None if self.cat_pote_sel is pote else pote
        self._actualizar_catalogo()
        if self.cat_pote_sel:
            self.campo_reponer.focus()

    # ---- Presentaciones ----
    def _armar_cat_presentaciones(self, pagina):
        c = COLORES
        pagina.columnconfigure(0, minsize=360)
        pagina.columnconfigure(1, weight=1)
        pagina.rowconfigure(0, weight=1)

        izq = tk.Frame(pagina, bg=c["fondo"])
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 32))
        self._titulo(izq, "Nueva presentación")
        self._etiqueta(izq, "Nombre")
        self.campo_pres_nombre = CampoTexto(izq, "Ej: Copa grande",
                                            al_enter=self.agregar_recipiente)
        self.campo_pres_nombre.pack(fill="x")
        self._etiqueta(izq, "Cómo se cobra")
        self.seg_pres_tipo = Segmentado(izq, [("peso", "Por peso"), ("fijo", "Precio fijo")],
                                        "peso", lambda v: self._cambiar_tipo_presentacion())
        self.seg_pres_tipo.pack(fill="x")
        self.nota_pres_tipo = self._nota(izq, "")
        self._etiqueta(izq, "Capacidad")
        self.campo_pres_kilos = CampoTexto(izq, "Ej: 0,25 (un cuarto)", sufijo="kg",
                                           al_enter=self.agregar_recipiente)
        self.campo_pres_kilos.pack(fill="x")
        # Campo que cambia según el tipo
        self.cont_pres_tipo = tk.Frame(izq, bg=c["fondo"])
        self.cont_pres_tipo.pack(fill="x")
        self.frame_pres_recargo = tk.Frame(self.cont_pres_tipo, bg=c["fondo"])
        self._etiqueta(self.frame_pres_recargo, "Recargo sobre el precio por kilo")
        self.campo_pres_recargo = CampoTexto(self.frame_pres_recargo, "0", sufijo="%",
                                             al_enter=self.agregar_recipiente)
        self.campo_pres_recargo.pack(fill="x")
        self.frame_pres_fijo = tk.Frame(self.cont_pres_tipo, bg=c["fondo"])
        self._etiqueta(self.frame_pres_fijo, "Precio fijo")
        self.campo_pres_precio = CampoTexto(self.frame_pres_fijo, "5000", prefijo="$",
                                            al_enter=self.agregar_recipiente)
        self.campo_pres_precio.pack(fill="x")
        self._etiqueta(izq, "Máximo de sabores")
        self.seg_pres_sabores = Segmentado(
            izq, [(n, str(n)) for n in range(1, MAX_SABORES_POR_PRESENTACION + 1)],
            MAX_SABORES_POR_PRESENTACION, None)
        self.seg_pres_sabores.pack(fill="x")
        BotonPildora(izq, "Agregar presentación", self.agregar_recipiente,
                     alto=48).pack(fill="x", pady=(18, 0))
        self._cambiar_tipo_presentacion()

        der = tk.Frame(pagina, bg=c["fondo"])
        der.grid(row=0, column=1, sticky="nsew")
        _, self.lbl_ayuda_presentaciones = self._titulo(der, "A la venta", pady=(0, 14))
        self.grilla_presentaciones = tk.Frame(der, bg=c["fondo"])
        self.grilla_presentaciones.pack(fill="x")

    def _cambiar_tipo_presentacion(self):
        fijo = self.seg_pres_tipo.valor == "fijo"
        self.frame_pres_recargo.pack_forget()
        self.frame_pres_fijo.pack_forget()
        (self.frame_pres_fijo if fijo else self.frame_pres_recargo).pack(fill="x")
        self.nota_pres_tipo.configure(
            text="Siempre cuesta lo mismo, sin importar los sabores (como el cucurucho)."
            if fijo else "El precio sale de los sabores elegidos, más un recargo opcional.")

    # ---- Combos y descuentos ----
    def _armar_cat_combos(self, pagina):
        c = COLORES
        pagina.columnconfigure(0, weight=1)
        pagina.columnconfigure(1, minsize=380)
        pagina.rowconfigure(0, weight=1)

        self.panel_combos = PanelDesplazable(pagina, c["fondo"])
        self.panel_combos.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        interior = self.panel_combos.interior

        _, self.lbl_ayuda_cat_combos = self._titulo(
            interior, "Combos guardados", "Tocá uno para editarlo o cambiarle el descuento",
            pady=(0, 10))
        self.grilla_cat_combos = tk.Frame(interior, bg=c["fondo"])
        self.grilla_cat_combos.pack(fill="x")

        self.lbl_titulo_armado, self.lbl_ayuda_armado = self._titulo(
            interior, "Armá un combo", "Se guarda en el catálogo y aparece en Nueva venta",
            pady=(30, 0))
        nombres = tk.Frame(interior, bg=c["fondo"])
        nombres.pack(fill="x")
        nombres.columnconfigure(0, weight=2, uniform="n")
        nombres.columnconfigure(1, weight=3, uniform="n")
        col_nombre = tk.Frame(nombres, bg=c["fondo"])
        col_nombre.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        col_desc = tk.Frame(nombres, bg=c["fondo"])
        col_desc.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._etiqueta(col_nombre, "Nombre")
        self.campo_cb_nombre = CampoTexto(col_nombre, "Ej: Combo familiar",
                                          al_escribir=self._actualizar_combo_en_armado)
        self.campo_cb_nombre.pack(fill="x")
        self._etiqueta(col_desc, "Descripción (opcional)")
        self.campo_cb_desc = CampoTexto(col_desc, "Ej: Kilo con cucuruchos para todos")
        self.campo_cb_desc.pack(fill="x")

        _, self.lbl_cb_recip = self._subtitulo(interior, "Presentación", "")
        self.grilla_cb_recip = tk.Frame(interior, bg=c["fondo"])
        self.grilla_cb_recip.pack(fill="x")
        _, self.lbl_cb_sabores = self._subtitulo(interior, "Sabores", "")
        self.grilla_cb_sabores = tk.Frame(interior, bg=c["fondo"])
        self.grilla_cb_sabores.pack(fill="x")
        self._subtitulo(interior, "Agregados", "Se cobran aparte")
        self.grilla_cb_extras = tk.Frame(interior, bg=c["fondo"])
        self.grilla_cb_extras.pack(fill="x")
        self._subtitulo(interior, "Salsas de regalo", "Sin costo")
        self.grilla_cb_salsas = tk.Frame(interior, bg=c["fondo"])
        self.grilla_cb_salsas.pack(fill="x")
        self._subtitulo(interior, "Descuento", "Vale si el combo se cobra tal cual")
        fila = tk.Frame(interior, bg=c["fondo"])
        fila.pack(fill="x", pady=(0, 10))
        fila.columnconfigure(0, weight=3, uniform="d")
        fila.columnconfigure(1, weight=2, uniform="d")
        self.seg_cb_descuento = Segmentado(
            fila, [(d, f"{d}%" if d else "Sin") for d in DESCUENTOS_RAPIDOS], 0,
            self._cb_descuento_rapido, alto=44)
        self.seg_cb_descuento.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.campo_cb_descuento = CampoTexto(fila, "Otro", sufijo="% de descuento",
                                             al_escribir=self._cb_descuento_escrito)
        self.campo_cb_descuento.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Columna derecha: resumen, descuento y acciones
        der = tk.Frame(pagina, bg=c["fondo"])
        der.grid(row=0, column=1, sticky="nsew")
        der.rowconfigure(0, weight=1)
        der.columnconfigure(0, weight=1)
        self.ticket_combo = TicketPedido(der, titulo="Combo",
                                         texto_vacio=("Elegí una presentación",
                                                      "y armá el combo a la izquierda"))
        self.ticket_combo.grid(row=0, column=0, sticky="nsew")
        zona = tk.Frame(der, bg=c["fondo"])
        zona.grid(row=1, column=0, sticky="ew")
        self.boton_cb_guardar = BotonPildora(zona, "Guardar combo", self.guardar_combo, alto=50)
        self.boton_cb_guardar.pack(fill="x", pady=(12, 6))
        acciones = tk.Frame(zona, bg=c["fondo"])
        acciones.pack(fill="x")
        acciones.columnconfigure((0, 1), weight=1, uniform="a")
        self.boton_cb_nuevo = BotonPildora(acciones, "Empezar uno nuevo", self._cb_nuevo,
                                           variante="suave", alto=34)
        self.boton_cb_nuevo.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.boton_cb_eliminar = BotonPildora(acciones, "Eliminar combo", self.eliminar_combo,
                                              variante="suave", alto=34)
        self.boton_cb_eliminar.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _subtitulo(self, padre, titulo, ayuda):
        fila = tk.Frame(padre, bg=COLORES["fondo"])
        fila.pack(fill="x", pady=(20, 8))
        lbl_titulo = tk.Label(fila, text=titulo, bg=COLORES["fondo"], fg=COLORES["texto"],
                              font=(FUENTE_FUERTE, 11))
        lbl_titulo.pack(side="left")
        lbl_ayuda = tk.Label(fila, text=ayuda, bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                             font=(FUENTE, 9))
        lbl_ayuda.pack(side="right")
        return lbl_titulo, lbl_ayuda

    def _cb_limpiar_estado(self):
        self.cb_editando = None      # combo existente que se está editando (o None)
        self.cb_recipiente = None
        self.cb_sabores = []
        self.cb_extras = {}
        self.cb_salsas = []
        self.cb_descuento = 0.0
        self._cb_confirmar_borrado = False

    def _cb_nuevo(self):
        self._cb_limpiar_estado()
        self.campo_cb_nombre.limpiar()
        self.campo_cb_desc.limpiar()
        self.campo_cb_descuento.limpiar()
        self._actualizar_catalogo()

    def _cb_editar(self, combo):
        self._cb_limpiar_estado()
        self.cb_editando = combo
        self.cb_recipiente = combo.recipiente
        self.cb_sabores = list(combo.sabores)
        self.cb_extras = dict(combo.extras)
        self.cb_salsas = list(combo.salsas)
        self.cb_descuento = combo.descuento_pct
        self.campo_cb_nombre.set(combo.nombre)
        self.campo_cb_desc.set(combo.descripcion)
        self.campo_cb_descuento.set("" if combo.descuento_pct in DESCUENTOS_RAPIDOS
                                    else f"{combo.descuento_pct:g}")
        self._actualizar_catalogo()
        self._avisar(f"Editando {combo.nombre}: cambiá lo que quieras y tocá Guardar.")

    def _cb_elegir_recipiente(self, recipiente):
        self.cb_recipiente = recipiente
        if len(self.cb_sabores) > recipiente.max_sabores:
            self.cb_sabores = self.cb_sabores[:recipiente.max_sabores]
            self._avisar(f"{recipiente.nombre} lleva hasta {recipiente.max_sabores} sabores: "
                         "saqué los que sobraban.", error=True)
        self._actualizar_catalogo()

    def _cb_alternar_sabor(self, sabor):
        r = self.cb_recipiente
        if sabor in self.cb_sabores:
            self.cb_sabores.remove(sabor)
        elif r is None:
            self._avisar("Primero elegí la presentación del combo.", error=True)
            return
        elif len(self.cb_sabores) >= r.max_sabores:
            self._avisar(f"{r.nombre} lleva hasta {r.max_sabores} sabores.", error=True)
            return
        else:
            self.cb_sabores.append(sabor)
            if self.heladeria.sabores_sin_stock(r, [sabor]) or \
                    sabor in self.heladeria.sabores_sin_stock(r, self.cb_sabores):
                self._avisar(f"Ojo: no hay stock suficiente de {sabor.nombre}. Podés guardar el "
                             "combo, pero no se va a poder vender hasta reponerlo.", alerta=True)
        self._actualizar_catalogo()

    def _cb_cambiar_extra(self, extra, cantidad):
        if cantidad > 0:
            self.cb_extras[extra] = cantidad
        else:
            self.cb_extras.pop(extra, None)
        self._actualizar_catalogo()

    def _cb_alternar_salsa(self, salsa):
        if salsa in self.cb_salsas:
            self.cb_salsas.remove(salsa)
        else:
            self.cb_salsas.append(salsa)
        self._actualizar_catalogo()

    def _cb_descuento_rapido(self, valor):
        self.cb_descuento = float(valor)
        self.campo_cb_descuento.limpiar()
        self._actualizar_combo_en_armado()

    def _cb_descuento_escrito(self):
        texto = self.campo_cb_descuento.get()
        if not texto:
            self.cb_descuento = float(self.seg_cb_descuento.valor or 0)
        else:
            try:
                valor = leer_numero(texto)
            except ValueError:
                return
            if 0 <= valor < 100:
                self.cb_descuento = valor
        self._actualizar_combo_en_armado()

    def _actualizar_combo_en_armado(self):
        """Refresca solo el resumen del combo (para no redibujar todo al escribir)."""
        self.seg_cb_descuento.set(self.cb_descuento if self.cb_descuento in DESCUENTOS_RAPIDOS
                                  else None)
        r, sabores = self.cb_recipiente, self.cb_sabores
        extras = [(e, self.cb_extras[e]) for e in self.heladeria.extras if e in self.cb_extras]
        salsas = [s for s in self.heladeria.salsas if s in self.cb_salsas]
        datos = {"recipiente": r, "sabores": list(sabores), "extras": extras, "salsas": salsas,
                 "precio_helado": 0.0, "descuento": 0.0, "total": 0.0,
                 "texto_descuento": f"Descuento del combo ({self.cb_descuento:g}%)"}
        if r and sabores:
            original, final = precio_combo(r, sabores, extras, salsas, self.cb_descuento)
            datos["precio_helado"] = r.calcular_precio_total(potes_de_muestra(sabores))
            datos["descuento"], datos["total"] = original - final, final
        nombre = self.campo_cb_nombre.get()
        if self.cb_editando:
            etiqueta = f"Editando #{self.cb_editando.id}"
        else:
            etiqueta = "Nuevo"
        self.ticket_combo.titulo = recortar(nombre or "Combo", (FUENTE_FUERTE, 16), 220)
        self.ticket_combo.mostrar(datos, etiqueta)
        listo = bool(r and sabores)
        self.boton_cb_guardar.set(
            ("Guardar cambios" if self.cb_editando else "Guardar combo")
            + (f" · {dinero_corto(datos['total'])}" if listo else ""), habilitado=listo)

    # ---- Construcción y actualización del catálogo ----
    def _construir_catalogo(self):
        """(Re)crea filas y tarjetas del catálogo cuando cambian los datos."""
        h, c = self.heladeria, COLORES
        for lista in (self.filas_pote, self.tarjetas_presentacion, self.tarjetas_cat_combo,
                      self.chips_cb_recip, self.chips_cb_sabor, self.filas_cb_extra,
                      self.chips_cb_salsa):
            for widget in lista:
                widget.destroy()
            lista.clear()
        for grilla in (self.grilla_cat_combos,):
            for widget in grilla.winfo_children():
                widget.destroy()

        # Potes
        for i, pote in enumerate(h.potes):
            fila = FilaPote(self.panel_potes.interior, pote,
                            lambda p=pote: self._elegir_pote_catalogo(p))
            fila.pack(fill="x", pady=(0 if i == 0 else 8, 0))
            self.filas_pote.append(fila)
        if self.cat_pote_sel not in h.potes:
            self.cat_pote_sel = None
        bajos = sum(1 for p in h.potes if p.stock_kg < Pote.STOCK_MINIMO_KG * 2)
        self.lbl_ayuda_potes.configure(
            text=f"{len(h.potes)} potes" + (f" · {bajos} con stock bajo" if bajos else ""),
            fg=c["aviso"] if bajos else c["texto_suave"])

        # Presentaciones (solo para ver)
        potes_baratos = sorted(h.potes, key=lambda p: p.sabor.precio_por_kilo)[:1]
        for r in h.recipientes:
            tarjeta = TarjetaPote(self.grilla_presentaciones, r, None)
            tarjeta.habilitado = False
            tarjeta.precio_desde = r.calcular_precio_total(potes_baratos) if potes_baratos else 0
            self.tarjetas_presentacion.append(tarjeta)
        self._repartir(self.grilla_presentaciones, self.tarjetas_presentacion, 4)
        self.lbl_ayuda_presentaciones.configure(text=f"{len(h.recipientes)} presentaciones")

        # Combos guardados
        for combo in h.combos:
            tarjeta = TarjetaCombo(self.grilla_cat_combos, combo,
                                   lambda k=combo: self._cb_editar(k), texto_accion="Editar")
            tarjeta.texto_seleccionado = "Editando"
            tarjeta.incompleto = bool(h.sabores_sin_stock(combo.recipiente, combo.sabores))
            tarjeta.precio_original, tarjeta.precio = precio_combo(
                combo.recipiente, combo.sabores, combo.extras, combo.salsas, combo.descuento_pct)
            self.tarjetas_cat_combo.append(tarjeta)
        self._repartir(self.grilla_cat_combos, self.tarjetas_cat_combo, 2)
        if not h.combos:
            tk.Label(self.grilla_cat_combos, bg=c["fondo"], fg=c["texto_suave"],
                     font=(FUENTE, 10), text="Todavía no hay combos. Armá el primero abajo.")\
                .grid(row=0, column=0, sticky="w")
        if self.cb_editando and self.cb_editando not in h.combos:
            self._cb_limpiar_estado()

        # Armado de combos
        self.chips_cb_recip.extend(
            ChipOpcion(self.grilla_cb_recip, r, lambda r=r: self._cb_elegir_recipiente(r))
            for r in h.recipientes)
        self.chips_cb_sabor.extend(
            ChipSabor(self.grilla_cb_sabores, None, lambda s=s: self._cb_alternar_sabor(s), sabor=s)
            for s in h.sabores)
        self.filas_cb_extra.extend(
            FilaExtra(self.grilla_cb_extras, e, self._cb_cambiar_extra) for e in h.extras)
        self.chips_cb_salsa.extend(
            ChipSalsa(self.grilla_cb_salsas, s, lambda s=s: self._cb_alternar_salsa(s))
            for s in h.salsas)
        self._repartir(self.grilla_cb_recip, self.chips_cb_recip, 3)
        self._repartir(self.grilla_cb_sabores, self.chips_cb_sabor, 3)
        self._repartir(self.grilla_cb_extras, self.filas_cb_extra, 2)
        self._repartir(self.grilla_cb_salsas, self.chips_cb_salsa, 4)

    def _actualizar_catalogo(self):
        """Refleja selecciones y estados del catálogo sin recrear los widgets."""
        for fila in self.filas_pote:
            fila.seleccionado = fila.pote is self.cat_pote_sel
            fila.redibujar()
        self._dibujar_pote_sel()
        hay_pote = self.cat_pote_sel is not None
        self.boton_reponer.set(habilitado=hay_pote)
        self.boton_abrir_pote.set(habilitado=hay_pote)

        for tarjeta in self.tarjetas_cat_combo:
            tarjeta.seleccionado = tarjeta.combo is self.cb_editando
            tarjeta.redibujar()
        r = self.cb_recipiente
        for chip in self.chips_cb_recip:
            chip.seleccionado = chip.recipiente is r
            chip.redibujar()
        lleno = r is not None and len(self.cb_sabores) >= r.max_sabores
        sin_stock = set(self.heladeria.sabores_sin_stock(r, self.cb_sabores)) if r else set()
        for chip in self.chips_cb_sabor:
            chip.orden = self.cb_sabores.index(chip.sabor) + 1 if chip.sabor in self.cb_sabores else 0
            if r is not None and not chip.orden:
                # ¿alcanzaría el stock si se suma este sabor?
                faltaria = self.heladeria.sabores_sin_stock(r, self.cb_sabores + [chip.sabor])
                if chip.sabor in faltaria:
                    sin_stock.add(chip.sabor)
            if chip.sabor in sin_stock:
                chip.estado = "sin_stock"  # se puede elegir igual, pero queda marcado
            elif (r is None or lleno) and not chip.orden:
                chip.estado = "apagado"
            else:
                chip.estado = "normal"
            chip.redibujar()
        for fila in self.filas_cb_extra:
            fila.cantidad = self.cb_extras.get(fila.extra, 0)
            fila.redibujar()
        for chip in self.chips_cb_salsa:
            chip.seleccionado = chip.salsa in self.cb_salsas
            chip.redibujar()

        self.lbl_titulo_armado.configure(
            text=f"Editando: {self.cb_editando.nombre}" if self.cb_editando else "Armá un combo")
        self.lbl_cb_recip.configure(text=f"{r.nombre} · {r.texto_peso()}" if r
                                    else "Elegí una")
        self.lbl_cb_sabores.configure(text=f"{len(self.cb_sabores)} de {r.max_sabores} elegidos"
                                      if r else "Primero elegí la presentación")
        self._cb_confirmar_borrado = False
        self.boton_cb_eliminar.set("Eliminar combo", habilitado=self.cb_editando is not None)
        self._actualizar_combo_en_armado()

    # ---------- Pestaña: Resumen ----------
    def _armar_tab_reportes(self):
        frame = self.tab_reportes
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        tarjeta, cuerpo = self._tarjeta(frame, "Reportes")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        secciones = [
            ("GENERAL", [
                ("Historial de ventas", self.mostrar_historial_ventas),
                ("Recaudación total", self.mostrar_recaudacion_total),
                ("Recipiente más solicitado", self.mostrar_recipiente_mas_solicitado),
            ]),
            ("POTES", [
                ("Más servido", self.mostrar_pote_mas_servido),
                ("Menos servido", self.mostrar_pote_menos_servido),
                ("Más recaudado", self.mostrar_pote_mas_recaudado),
                ("% de venta por pote", self.mostrar_porcentaje_venta_por_pote),
                ("% de recaudación por pote", self.mostrar_porcentaje_recaudacion_por_pote),
            ]),
            ("SABORES", [
                ("Más vendido", self.mostrar_sabor_mas_vendido),
                ("Con más ganancia", self.mostrar_sabor_mas_recaudado),
                ("Con más kilos vendidos", self.mostrar_sabor_mas_kilos_vendidos),
                ("Con menos kilos vendidos", self.mostrar_sabor_menos_kilos_vendidos),
                ("% de venta por sabor", self.mostrar_porcentaje_venta_por_sabor),
                ("% de recaudación por sabor", self.mostrar_porcentaje_recaudacion_por_sabor),
            ]),
        ]
        self.botones_reporte = {}
        for titulo_seccion, botones in secciones:
            ttk.Label(cuerpo, text=titulo_seccion, style="Suave.TLabel",
                      font=(FUENTE_FUERTE, 8)).pack(anchor="w", pady=(6, 1))
            for texto, comando in botones:
                boton = ttk.Button(cuerpo, text=texto, style="Reporte.TButton", width=28)
                boton.configure(command=lambda b=boton, c=comando: self._elegir_reporte(b, c))
                boton.pack(fill="x")
                self.botones_reporte[comando.__name__] = boton

        # Panel de resultado (reemplaza a los messagebox)
        self.tarjeta_resultado = tk.Frame(frame, bg=COLORES["panel"], padx=26, pady=24,
                                          highlightthickness=1,
                                          highlightbackground=COLORES["borde"])
        self.tarjeta_resultado.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.lbl_resultado_titulo = ttk.Label(self.tarjeta_resultado, text="",
                                              style="Titulo.TLabel")
        self.lbl_resultado_titulo.pack(anchor="w")
        self.frame_resultado = ttk.Frame(self.tarjeta_resultado, style="Panel.TFrame")
        self.frame_resultado.pack(fill="both", expand=True, pady=(16, 0))

    def _elegir_reporte(self, boton, comando):
        """Resalta el boton elegido y muestra su reporte."""
        if self._boton_reporte_activo:
            self._boton_reporte_activo.configure(style="Reporte.TButton")
        boton.configure(style="ReporteActivo.TButton")
        self._boton_reporte_activo = boton
        self._reporte_actual = comando
        comando()

    def _limpiar_resultado(self, titulo):
        self.lbl_resultado_titulo.config(text=titulo)
        for widget in self.frame_resultado.winfo_children():
            widget.destroy()

    def _sin_ventas(self):
        ttk.Label(self.frame_resultado, text="Todavía no hay ventas registradas.",
                  style="Suave.TLabel").pack(anchor="w")

    def _mostrar_valor(self, titulo, valor, detalle=""):
        """Un resultado unico: numero grande + linea de detalle."""
        self._limpiar_resultado(titulo)
        if valor is None or not self.heladeria.ventas:
            self._sin_ventas()
            return
        ttk.Label(self.frame_resultado, text=valor, style="Grande.TLabel",
                  wraplength=650, justify="left").pack(anchor="w")
        if detalle:
            ttk.Label(self.frame_resultado, text=detalle, style="Suave.TLabel",
                      wraplength=650, justify="left").pack(anchor="w", pady=(6, 0))

    def _mostrar_barras(self, titulo, datos):
        """Porcentajes como grafico de barras horizontales, de mayor a menor."""
        self._limpiar_resultado(titulo)
        if not datos:
            self._sin_ventas()
            return
        for nombre, porcentaje in sorted(datos.items(), key=lambda par: par[1], reverse=True):
            fila = ttk.Frame(self.frame_resultado, style="Panel.TFrame")
            fila.pack(fill="x", pady=5)
            ttk.Label(fila, text=nombre, style="Panel.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(fila, text=f"{porcentaje:.1f}%", style="Panel.TLabel",
                      font=(FUENTE_FUERTE, 10)).grid(row=0, column=1, sticky="e")
            fila.columnconfigure(0, weight=1)
            barra = tk.Canvas(fila, height=12, bg=COLORES["panel"], highlightthickness=0)
            barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
            # La barra se dibuja cuando el canvas sabe su ancho real
            barra.bind("<Configure>", lambda e, c=barra, p=porcentaje: self._dibujar_barra(c, p, e.width))

    @staticmethod
    def _dibujar_barra(canvas, porcentaje, ancho):
        canvas.delete("all")
        rect_redondeado(canvas, 0, 0, ancho - 1, 11, 6, fill=COLORES["borde"], outline="")
        if porcentaje > 0:
            rect_redondeado(canvas, 0, 0, max(12, ancho * porcentaje / 100), 11, 6,
                            fill=COLORES["primario"], outline="")

    # ---------- Acciones del catálogo ----------
    def agregar_sabor(self):
        nombre = self.campo_sabor_nombre.get()
        try:
            precio = leer_numero(self.campo_sabor_precio.get(), con_miles=True)
        except ValueError:
            precio = 0
        if not nombre:
            self.campo_sabor_nombre.marcar_error()
            self._avisar("Poné el nombre del sabor.", error=True)
            return
        if any(s.nombre.lower() == nombre.lower() for s in self.heladeria.sabores):
            self.campo_sabor_nombre.marcar_error()
            self._avisar(f"Ya existe un sabor llamado {nombre}.", error=True)
            return
        if precio <= 0:
            self.campo_sabor_precio.marcar_error()
            self._avisar("El precio por kilo tiene que ser un número mayor a 0.", error=True)
            return
        sabor = Sabor(Heladeria.siguiente_id(self.heladeria.sabores), nombre,
                      self.seg_elaboracion.valor, precio)
        self.heladeria.agregar_sabor(sabor)
        pote = Pote(Heladeria.siguiente_id(self.heladeria.potes), sabor,
                    datetime.now().strftime("%Y-%m-%d"))
        self.heladeria.agregar_pote(pote)
        self.campo_sabor_nombre.limpiar()
        self.campo_sabor_precio.limpiar()
        self.campo_sabor_nombre.focus()
        self.cat_pote_sel = pote
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Sabor agregado: {sabor.nombre}, con un pote de "
                     f"{formato_kilos(pote.stock_kg)} kg.")

    def agregar_recipiente(self):
        """Agrega una presentación por peso o de precio fijo, con su máximo de sabores."""
        nombre = self.campo_pres_nombre.get()
        try:
            kilos = leer_numero(self.campo_pres_kilos.get())
        except ValueError:
            kilos = 0
        if not nombre:
            self.campo_pres_nombre.marcar_error()
            self._avisar("Poné el nombre de la presentación.", error=True)
            return
        if kilos <= 0:
            self.campo_pres_kilos.marcar_error()
            self._avisar("La capacidad tiene que ser mayor a 0 kg (por ejemplo 0,25).", error=True)
            return
        nuevo_id = Heladeria.siguiente_id(self.heladeria.recipientes)
        max_sabores = self.seg_pres_sabores.valor
        if self.seg_pres_tipo.valor == "fijo":
            campo = self.campo_pres_precio
            try:
                precio = leer_numero(campo.get(), con_miles=True)
            except ValueError:
                precio = 0
            if precio <= 0:
                campo.marcar_error()
                self._avisar("El precio fijo tiene que ser mayor a 0.", error=True)
                return
            recipiente = PresentacionPorPorcion(nuevo_id, nombre, kilos, precio, max_sabores)
        else:
            campo = self.campo_pres_recargo
            try:
                recargo = leer_numero(campo.get()) if campo.get() else 0.0
            except ValueError:
                recargo = -1
            if recargo < 0:
                campo.marcar_error()
                self._avisar("El recargo tiene que ser 0% o más.", error=True)
                return
            recipiente = Recipiente(nuevo_id, nombre, kilos, recargo, max_sabores)
        self.heladeria.agregar_recipiente(recipiente)
        for campo in (self.campo_pres_nombre, self.campo_pres_kilos, self.campo_pres_recargo,
                      self.campo_pres_precio):
            campo.limpiar()
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Presentación agregada: {recipiente.nombre} ({recipiente.texto_peso()}, "
                     f"{recipiente.descripcion_precio()}, hasta {max_sabores} sabores).")

    def agregar_pote(self):
        pote_ref = self.cat_pote_sel
        if pote_ref is None:
            self._avisar("Elegí en la lista el sabor del pote que querés abrir.", error=True)
            return
        fecha = self.campo_pote_fecha.get()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            self.campo_pote_fecha.marcar_error()
            self._avisar("La fecha debe tener el formato AAAA-MM-DD y ser válida.", error=True)
            return
        sabor = pote_ref.sabor
        pote = Pote(Heladeria.siguiente_id(self.heladeria.potes), sabor, fecha)
        self.heladeria.agregar_pote(pote)
        self.cat_pote_sel = pote
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Pote #{pote.id} de {sabor.nombre} abierto con "
                     f"{formato_kilos(pote.stock_kg)} kg.")

    def reponer_stock(self):
        pote = self.cat_pote_sel
        if pote is None:
            self._avisar("Elegí en la lista el pote a reponer.", error=True)
            return
        try:
            pote.reponer_stock(leer_numero(self.campo_reponer.get()))
        except ValueError:
            self.campo_reponer.marcar_error()
            self._avisar("Ingresá una cantidad de kilos mayor a 0.", error=True)
            return
        self.campo_reponer.limpiar()
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Stock repuesto en {pote.sabor.nombre}: ahora tiene "
                     f"{formato_kilos(pote.stock_kg)} kg.")

    def guardar_combo(self):
        nombre = self.campo_cb_nombre.get()
        texto_desc = self.campo_cb_descuento.get()
        if texto_desc:
            try:
                self.cb_descuento = leer_numero(texto_desc)
            except ValueError:
                self.campo_cb_descuento.marcar_error()
                self._avisar("El descuento tiene que ser un número (por ejemplo 12,5).", error=True)
                return
        if not nombre:
            self.campo_cb_nombre.marcar_error()
            self._avisar("Ponele un nombre al combo.", error=True)
            return
        otros = [k for k in self.heladeria.combos if k is not self.cb_editando]
        if any(k.nombre.lower() == nombre.lower() for k in otros):
            self.campo_cb_nombre.marcar_error()
            self._avisar(f"Ya hay un combo llamado {nombre}.", error=True)
            return
        id_combo = (self.cb_editando.id if self.cb_editando
                    else Heladeria.siguiente_id(self.heladeria.combos))
        try:
            combo = Combo(id_combo, nombre, self.campo_cb_desc.get(), self.cb_recipiente,
                          self.cb_sabores,
                          [(e, self.cb_extras[e]) for e in self.heladeria.extras
                           if e in self.cb_extras],
                          [s for s in self.heladeria.salsas if s in self.cb_salsas],
                          self.cb_descuento)
        except (ValueError, AttributeError) as err:
            if isinstance(err, AttributeError):
                err = "Elegí la presentación del combo."
            if "descuento" in str(err):
                self.campo_cb_descuento.marcar_error()
            self._avisar(str(err), error=True)
            return
        editado = self.cb_editando is not None
        self.heladeria.reemplazar_combo(combo)
        guardar_json(self.heladeria)
        self._cb_nuevo()
        self.refrescar()
        descuento = f" con {combo.descuento_pct:g}% de descuento" if combo.tiene_descuento() else ""
        accion = "actualizado" if editado else "guardado"
        faltan = self.heladeria.sabores_sin_stock(combo.recipiente, combo.sabores)
        if faltan:
            self._avisar(f"Combo {accion}: {combo.nombre}{descuento}. Ojo: no hay stock suficiente "
                         f"de {', '.join(s.nombre for s in faltan)}, así que no se va a poder "
                         "vender hasta reponer.", alerta=True)
        else:
            self._avisar(f"Combo {accion}: {combo.nombre}{descuento}. Ya aparece en Nueva venta.")

    def eliminar_combo(self):
        combo = self.cb_editando
        if combo is None:
            return
        # Se pide un segundo toque en lugar de un cuadro de diálogo del sistema
        if not self._cb_confirmar_borrado:
            self._cb_confirmar_borrado = True
            self.boton_cb_eliminar.set("Tocá de nuevo para eliminar")
            self.ventana.after(3000, self._cb_cancelar_borrado)
            return
        self.heladeria.eliminar_combo(combo)
        guardar_json(self.heladeria)
        self._cb_nuevo()
        self.refrescar()
        self._avisar(f"Combo eliminado: {combo.nombre}.")

    def _cb_cancelar_borrado(self):
        if self._cb_confirmar_borrado:
            self._cb_confirmar_borrado = False
            self.boton_cb_eliminar.set("Eliminar combo")

    # ---------- Venta ----------
    def _combo_activo(self):
        """El combo cargado, solo si el pedido sigue siendo exactamente ese combo."""
        combo = self.sel_combo
        return combo if combo and self._combo_coincide(combo) else None

    def registrar_venta(self):
        recipiente = self.sel_recipiente
        if recipiente is None or not self.sel_potes:
            self._avisar("Elegí el pote y al menos un sabor.", error=True)
            return
        try:
            venta = self.heladeria.vender(self.sel_potes, recipiente, self._extras_elegidos(),
                                          self._salsas_elegidas(), self._combo_activo())
        except ValueError as err:
            mensaje = str(err)
            self._avisar(mensaje.splitlines()[0], error=True)
            messagebox.showwarning("Alerta de reposición de stock", mensaje)
            return
        guardar_json(self.heladeria)
        self._vaciar_pedido()
        self.refrescar()
        agregados = venta.descripcion_agregados()
        self._avisar(f"Venta #{len(self.heladeria.ventas)} cobrada: {recipiente.nombre} de "
                     f"{venta.nombres_sabores()}" + (f" + {agregados}" if agregados else "") +
                     f" por {formato_dinero(venta.calcular_precio_total())}")

    # ---------- Actualizacion general de la pantalla ----------
    def refrescar(self):
        h = self.heladeria
        # Indicadores del encabezado
        self.kpis["recaudado"].config(text=dinero_corto(h.recaudacion_total()))
        self.kpis["ventas"].config(text=str(len(h.ventas)))
        self.kpis["kilos"].config(text=formato_kilos(sum(v.kilos for v in h.ventas)))

        # Pantalla de venta
        self._construir_opciones_venta()
        self._actualizar_pedido()
        self._dibujar_ultimas()

        # Catálogo
        self._construir_catalogo()
        self._actualizar_catalogo()

        if self._reporte_actual:  # el reporte abierto se recalcula solo
            self._reporte_actual()

    # Se mantiene el nombre anterior por compatibilidad
    refrescar_combos = refrescar

    # ---------- Muestra de reportes ----------
    def _nombre_pote(self, pote):
        return f"Pote #{pote.id} · {pote.sabor.nombre}"

    def _mostrar_pote(self, titulo, pote):
        if pote is None:
            self._mostrar_valor(titulo, None)
            return
        self._mostrar_valor(titulo, self._nombre_pote(pote),
                            f"{pote.kilos_servidos:.2f} kg servidos · "
                            f"{formato_dinero(pote.dinero_recaudado)} recaudados")

    def mostrar_historial_ventas(self):
        self._limpiar_resultado("Historial de ventas")
        if not self.heladeria.ventas:
            self._sin_ventas()
            return
        tabla = self._tabla(self.frame_resultado, [
            ("n", "#", 45, "center"),
            ("recipiente", "Pote", 120, "w"),
            ("sabor", "Sabores", 220, "w"),
            ("agregados", "Agregados", 200, "w"),
            ("total", "Total", 110, "e"),
        ], alto=14)
        self._llenar_tabla(tabla, [
            (i, v.recipiente.nombre, v.nombres_sabores(), v.descripcion_agregados() or "—",
             formato_dinero(v.calcular_precio_total()))
            for i, v in reversed(list(enumerate(self.heladeria.ventas, start=1)))
        ])

    def mostrar_recaudacion_total(self):
        h = self.heladeria
        detalle = f"Sobre {len(h.ventas)} ventas registradas"
        if h.recaudacion_extras():
            detalle += (f" · {formato_dinero(h.recaudacion_helado())} en helado y "
                        f"{formato_dinero(h.recaudacion_extras())} en agregados")
        self._mostrar_valor("Recaudación total", formato_dinero(h.recaudacion_total()), detalle)

    def mostrar_pote_mas_servido(self):
        self._mostrar_pote("Pote más servido", self.heladeria.pote_mas_servido())

    def mostrar_pote_menos_servido(self):
        self._mostrar_pote("Pote menos servido", self.heladeria.pote_menos_servido())

    def mostrar_pote_mas_recaudado(self):
        self._mostrar_pote("Pote más recaudado", self.heladeria.pote_mas_recaudado())

    def mostrar_sabor_mas_vendido(self):
        sabor = self.heladeria.sabor_mas_vendido()
        cantidad = self.heladeria.cantidad_ventas_por_sabor().get(sabor, 0)
        self._mostrar_valor("Sabor más vendido", sabor, f"{cantidad:g} ventas")

    def mostrar_sabor_mas_recaudado(self):
        sabor = self.heladeria.sabor_mas_recaudado()
        monto = self.heladeria.recaudacion_por_sabor().get(sabor, 0)
        self._mostrar_valor("Sabor con más ganancia", sabor, f"{formato_dinero(monto)} recaudados")

    def mostrar_sabor_mas_kilos_vendidos(self):
        sabor = self.heladeria.sabor_mas_kilos_vendidos()
        kilos = self.heladeria.kilos_por_sabor().get(sabor, 0)
        self._mostrar_valor("Sabor con más kilos vendidos", sabor, f"{kilos:.2f} kg vendidos")

    def mostrar_sabor_menos_kilos_vendidos(self):
        sabor = self.heladeria.sabor_menos_kilos_vendidos()
        kilos = self.heladeria.kilos_por_sabor().get(sabor, 0)
        self._mostrar_valor("Sabor con menos kilos vendidos", sabor, f"{kilos:.2f} kg vendidos")

    def mostrar_recipiente_mas_solicitado(self):
        recipiente = self.heladeria.recipiente_mas_solicitado()
        cantidad = sum(1 for v in self.heladeria.ventas if v.recipiente.nombre == recipiente)
        self._mostrar_valor("Recipiente más solicitado", recipiente, f"Pedido {cantidad} veces")

    def mostrar_porcentaje_venta_por_sabor(self):
        self._mostrar_barras("% de ventas por sabor", self.heladeria.porcentaje_venta_por_sabor())

    def mostrar_porcentaje_recaudacion_por_sabor(self):
        self._mostrar_barras("% de recaudación por sabor",
                             self.heladeria.porcentaje_recaudacion_por_sabor())

    def _por_pote(self, datos):
        potes = {p.id: p for p in self.heladeria.potes}
        return {self._nombre_pote(potes[id_pote]): pct for id_pote, pct in datos.items()}

    def mostrar_porcentaje_venta_por_pote(self):
        self._mostrar_barras("% de kilos servidos por pote",
                             self._por_pote(self.heladeria.porcentaje_venta_por_pote()))

    def mostrar_porcentaje_recaudacion_por_pote(self):
        self._mostrar_barras("% de recaudación por pote",
                             self._por_pote(self.heladeria.porcentaje_recaudacion_por_pote()))

    def iniciar(self):
        self.refrescar()
        # Pantalla inicial del Resumen
        self._elegir_reporte(self.botones_reporte["mostrar_recaudacion_total"],
                             self.mostrar_recaudacion_total)
        self.ventana.mainloop()


if __name__ == "__main__":
    heladeria = Heladeria()
    cargar_json(heladeria)

    gui = HeladeriaGUI(heladeria)
    gui.iniciar()
