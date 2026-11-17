from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from modelos.sabor import Sabor
from modelos.recipiente import Recipiente, PresentacionPorPorcion
from modelos.venta import Venta
from modelos.pote import Pote


RUTA_SCRIPTS = Path(__file__).parent / "scripts"
RUTA_SABORES = RUTA_SCRIPTS / "sabores_iniciales.json"
RUTA_TAMANOS = RUTA_SCRIPTS / "tamanos_pote.json"
RUTA_VENTAS = RUTA_SCRIPTS / "ventas.json"

CLASES_PRESENTACION = {
    "Recipiente": Recipiente,
    "PresentacionPorPorcion": PresentacionPorPorcion,
}


def guardar_json(heladeria):
    sabores_data = [
        {
            "id": p.id,
            "nombre": p.sabor.nombre,
            "elaboracion": p.sabor.elaboracion,
            "precio": p.sabor.precio_por_kilo,
            "fecha": p.fecha_incorporacion,
            "stock_kg": round(p.stock_kg, 4),
        }
        for p in heladeria.potes
    ]
    RUTA_SABORES.write_text(
        json.dumps(sabores_data, indent=2, ensure_ascii=False) + "\n",
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
        }
        for v in heladeria.ventas
    ]
    RUTA_VENTAS.write_text(
        json.dumps(ventas_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cargar_json(heladeria):
    for item in json.loads(RUTA_SABORES.read_text(encoding="utf-8")):
        sabor = Sabor(item["id"], item["nombre"], item["elaboracion"], item["precio"])
        heladeria.agregar_sabor(sabor)
        heladeria.agregar_pote(
            Pote(item["id"], sabor, item["fecha"], stock_kg=item.get("stock_kg", 5.0))
        )

    for item in json.loads(RUTA_TAMANOS.read_text(encoding="utf-8")):
        datos = dict(item)
        cls = CLASES_PRESENTACION[datos.pop("clase")]
        heladeria.agregar_recipiente(cls(**datos))

    if RUTA_VENTAS.exists():
        potes_por_id = {p.id: p for p in heladeria.potes}
        recips_por_id = {r.id: r for r in heladeria.recipientes}
        for item in json.loads(RUTA_VENTAS.read_text(encoding="utf-8")):
            potes_venta = [potes_por_id[pid] for pid in item["potes_ids"] if pid in potes_por_id]
            recip = recips_por_id.get(item["recipiente_id"])
            if potes_venta and recip:
                venta = Venta(potes_venta, recip)
                for pote, kilos_aporte, dinero_aporte in venta.aportes:
                    pote.kilos_servidos += kilos_aporte
                    pote.dinero_recaudado += dinero_aporte
                heladeria.ventas.append(venta)


#Logica de la heladeria
class Heladeria:
    def __init__(self):
        self.potes = []
        self.ventas = []
        self.sabores = []
        self.recipientes = []

    
    def agregar_pote(self, pote):
        self.potes.append(pote)

    def agregar_sabor(self, sabor):
        self.sabores.append(sabor)

    def agregar_recipiente(self, recipiente):
        self.recipientes.append(recipiente)

    def vender(self, potes, recipiente):
        venta = Venta(potes, recipiente)
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
        total = self.recaudacion_total()
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
        total = self.recaudacion_total()
        if total == 0:
            return {}
        return {pote.id: (pote.dinero_recaudado / total) * 100 for pote in self.potes}


#Interfaz

# Paleta de colores y fuente de toda la interfaz (se cambian en un solo lugar)
COLORES = {
    "fondo": "#FFF8F0",
    "panel": "#FFFFFF",
    "primario": "#E85D75",
    "primario_hover": "#C9475F",
    "secundario": "#4FB3A9",
    "texto": "#3D2C2E",
    "texto_suave": "#8A7A7C",
    "borde": "#F3E3DA",
    "resaltado": "#FBD3DA",
    "error": "#C0392B",
}
FUENTE = "Segoe UI"


def formato_dinero(monto):
    """Formato argentino: $12.345,67"""
    texto = f"{monto:,.2f}"
    return "$" + texto.replace(",", "X").replace(".", ",").replace("X", ".")


class HeladeriaGUI:
    def __init__(self, heladeria):
        self.heladeria = heladeria
        self.ventana = tk.Tk()
        self.ventana.title("Heladería")
        self.ventana.geometry("1200x820")
        self.ventana.minsize(1040, 720)
        self.ventana.configure(bg=COLORES["fondo"])
        self._aviso_pendiente = None
        self._boton_reporte_activo = None
        self._reporte_actual = None

        self._configurar_estilos()
        self._armar_encabezado()
        # La barra de estado se arma ANTES del notebook: si no, el notebook
        # (que se expande) ocupa todo el espacio y la barra no se ve.
        self._armar_barra_estado()

        notebook = ttk.Notebook(self.ventana)
        notebook.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        self.tab_ventas = ttk.Frame(notebook, padding=14)
        self.tab_datos = ttk.Frame(notebook, padding=14)
        self.tab_reportes = ttk.Frame(notebook, padding=14)

        notebook.add(self.tab_ventas, text="Nueva venta")
        notebook.add(self.tab_datos, text="Catálogo")
        notebook.add(self.tab_reportes, text="Resumen")

        self._armar_tab_ventas()
        self._armar_tab_datos()
        self._armar_tab_reportes()

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
        estilo.configure("Titulo.TLabel", background=c["panel"], font=(FUENTE, 14, "bold"))
        estilo.configure("Suave.TLabel", background=c["panel"], foreground=c["texto_suave"])
        estilo.configure("Grande.TLabel", background=c["panel"], foreground=c["primario"],
                         font=(FUENTE, 28, "bold"))

        estilo.configure("TNotebook", background=c["fondo"], borderwidth=0, tabmargins=0)
        estilo.configure("TNotebook.Tab", padding=(20, 10), font=(FUENTE, 11, "bold"),
                         background=c["borde"], foreground=c["texto_suave"], borderwidth=0)
        estilo.map("TNotebook.Tab",
                   background=[("selected", c["fondo"])],
                   foreground=[("selected", c["primario"])])

        estilo.configure("Accent.TButton", background=c["primario"], foreground="white",
                         font=(FUENTE, 11, "bold"), padding=(18, 10), borderwidth=0)
        estilo.map("Accent.TButton", background=[("active", c["primario_hover"])])

        estilo.configure("Reporte.TButton", background=c["panel"], foreground=c["texto"],
                         font=(FUENTE, 11), anchor="w", padding=(12, 6), borderwidth=0)
        estilo.map("Reporte.TButton",
                   background=[("pressed", c["resaltado"]), ("active", c["borde"])])
        # Boton del reporte que se esta mostrando
        estilo.configure("ReporteActivo.TButton", background=c["resaltado"],
                         foreground=c["primario_hover"], font=(FUENTE, 11, "bold"),
                         anchor="w", padding=(12, 6), borderwidth=0)
        estilo.map("ReporteActivo.TButton", background=[("active", c["resaltado"])])

        estilo.configure("Treeview", background=c["panel"], fieldbackground=c["panel"],
                         rowheight=32, borderwidth=0)
        estilo.configure("Treeview.Heading", background=c["borde"], foreground=c["texto"],
                         font=(FUENTE, 10, "bold"), borderwidth=0, padding=(8, 6))
        estilo.map("Treeview", background=[("selected", c["resaltado"])],
                   foreground=[("selected", c["texto"])])

        estilo.configure("TEntry", padding=5)
        estilo.configure("TCombobox", padding=5)
        estilo.map("TCombobox", fieldbackground=[("readonly", c["panel"])],
                   selectbackground=[("readonly", c["panel"])],
                   selectforeground=[("readonly", c["texto"])])

    def _tarjeta(self, padre, titulo, subtitulo=""):
        """Panel blanco con titulo. Devuelve (tarjeta, cuerpo) para meter widgets adentro."""
        tarjeta = ttk.Frame(padre, style="Panel.TFrame", padding=18)
        ttk.Label(tarjeta, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        if subtitulo:
            ttk.Label(tarjeta, text=subtitulo, style="Suave.TLabel").pack(anchor="w")
        cuerpo = ttk.Frame(tarjeta, style="Panel.TFrame")
        cuerpo.pack(fill="both", expand=True, pady=(12, 0))
        return tarjeta, cuerpo

    def _campo(self, padre, texto, widget):
        """Etiqueta arriba y el campo abajo, ocupando todo el ancho."""
        ttk.Label(padre, text=texto, style="Panel.TLabel").pack(anchor="w")
        widget.pack(fill="x", pady=(2, 10))
        return widget

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

    # ---------- Encabezado y barra de estado ----------
    def _armar_encabezado(self):
        encabezado = tk.Frame(self.ventana, bg=COLORES["primario"])
        encabezado.pack(fill="x")

        titulos = tk.Frame(encabezado, bg=COLORES["primario"])
        titulos.pack(side="left", padx=22, pady=12)
        tk.Label(titulos, text="Heladería", bg=COLORES["primario"], fg="white",
                 font=(FUENTE, 20, "bold")).pack(anchor="w")
        tk.Label(titulos, text="Gestión de ventas y potes", bg=COLORES["primario"],
                 fg="#FFE3E8", font=(FUENTE, 10)).pack(anchor="w")

        # Indicadores que se actualizan solos despues de cada venta
        indicadores = tk.Frame(encabezado, bg=COLORES["primario"])
        indicadores.pack(side="right", padx=22)
        self.kpis = {}
        for clave, titulo in [("recaudado", "Recaudado"), ("ventas", "Ventas"), ("kilos", "Kilos")]:
            bloque = tk.Frame(indicadores, bg=COLORES["primario"])
            bloque.pack(side="left", padx=14)
            tk.Label(bloque, text=titulo.upper(), bg=COLORES["primario"], fg="#FFE3E8",
                     font=(FUENTE, 8, "bold")).pack(anchor="e")
            self.kpis[clave] = tk.Label(bloque, text="-", bg=COLORES["primario"], fg="white",
                                        font=(FUENTE, 15, "bold"))
            self.kpis[clave].pack(anchor="e")

    def _armar_barra_estado(self):
        self.barra_estado = tk.Label(self.ventana, text="Listo.", anchor="w",
                                     justify="left", wraplength=1140,
                                     bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                                     font=(FUENTE, 10), padx=20, pady=8)
        self.barra_estado.pack(fill="x", side="bottom")

    def _avisar(self, texto, error=False):
        """Muestra un mensaje abajo durante unos segundos (en vez de un popup)."""
        color = COLORES["error"] if error else COLORES["secundario"]
        self.barra_estado.config(text=("✖  " if error else "✔  ") + texto, fg=color)
        if error:
            self.ventana.bell()
        if self._aviso_pendiente:
            self.ventana.after_cancel(self._aviso_pendiente)
        self._aviso_pendiente = self.ventana.after(
            5000, lambda: self.barra_estado.config(text="Listo.", fg=COLORES["texto_suave"]))

    # ---------- Pestaña: Nueva venta ----------
    def _armar_tab_ventas(self):
        frame = self.tab_ventas
        frame.columnconfigure(0, weight=2, uniform="v")
        frame.columnconfigure(1, weight=3, uniform="v")
        frame.rowconfigure(0, weight=1)

        tarjeta, cuerpo = self._tarjeta(frame, "Registrar venta", "Elegí los sabores y el tamaño de pote")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(cuerpo, text="Sabores", style="Panel.TLabel").pack(anchor="w")
        self.combos_venta_sabores = []
        for i in range(4):
            combo = ttk.Combobox(cuerpo, state="readonly")
            combo.pack(fill="x", pady=(2, 6 if i < 3 else 10))
            combo.bind("<<ComboboxSelected>>", lambda e: self._actualizar_vista_previa())
            self.combos_venta_sabores.append(combo)
        self.combo_venta_pote = self.combos_venta_sabores[0]

        self.combo_venta_recipiente = self._campo(
            cuerpo, "Tamaño de pote", ttk.Combobox(cuerpo, state="readonly"))
        self.combo_venta_recipiente.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_recipiente())

        # Vista previa del precio antes de confirmar
        previa = ttk.Frame(cuerpo, style="Panel.TFrame")
        previa.pack(fill="x", pady=(8, 14))
        ttk.Label(previa, text="Total a cobrar", style="Suave.TLabel").pack(anchor="w")
        self.lbl_precio_previo = ttk.Label(previa, text="$0,00", style="Grande.TLabel")
        self.lbl_precio_previo.pack(anchor="w")
        self.lbl_detalle_previo = ttk.Label(previa, text="", style="Suave.TLabel", wraplength=420, justify="left")
        self.lbl_detalle_previo.pack(anchor="w")

        ttk.Button(cuerpo, text="Registrar venta", style="Accent.TButton",
                   command=self.registrar_venta).pack(fill="x")

        tarjeta, cuerpo = self._tarjeta(frame, "Historial de ventas", "La más reciente arriba")
        tarjeta.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.tabla_ventas = self._tabla(cuerpo, [
            ("n", "#", 45, "center"),
            ("sabor", "Sabores", 220, "w"),
            ("recipiente", "Tamaño de pote", 150, "w"),
            ("kilos", "Kilos", 75, "e"),
            ("total", "Total", 115, "e"),
        ])

    def _al_cambiar_recipiente(self):
        idx_recip = self.combo_venta_recipiente.current()
        if idx_recip >= 0:
            max_sab = self.heladeria.recipientes[idx_recip].max_sabores
            for i, combo in enumerate(self.combos_venta_sabores):
                if i < max_sab:
                    combo.configure(state="readonly")
                else:
                    if combo["values"]:
                        combo.current(0)
                    combo.configure(state="disabled")
        self._actualizar_vista_previa()

    def _obtener_potes_seleccionados(self):
        idx_recip = self.combo_venta_recipiente.current()
        max_sab = self.heladeria.recipientes[idx_recip].max_sabores if idx_recip >= 0 else 4
        potes = []
        for i, combo in enumerate(self.combos_venta_sabores[:max_sab]):
            idx = combo.current()
            if i == 0:
                if idx >= 0:
                    potes.append(self.heladeria.potes[idx])
            else:
                if idx > 0:
                    potes.append(self.heladeria.potes[idx - 1])
        return potes

    def _actualizar_vista_previa(self):
        potes = self._obtener_potes_seleccionados()
        idx_recip = self.combo_venta_recipiente.current()
        if not potes or idx_recip < 0:
            self.lbl_precio_previo.config(text="$0,00")
            self.lbl_detalle_previo.config(text="Elegí los sabores y el tamaño de pote.")
            return
        recipiente = self.heladeria.recipientes[idx_recip]
        # Crear una Venta no la registra: solo calcula el precio
        precio = Venta(potes, recipiente).calcular_precio_total()
        self.lbl_precio_previo.config(text=formato_dinero(precio))
        self.lbl_detalle_previo.config(text=recipiente.detalle_precio(potes))

    # ---------- Pestaña: Catálogo ----------
    def _armar_tab_datos(self):
        frame = self.tab_datos
        for col in range(3):
            frame.columnconfigure(col, weight=1, uniform="d")
        frame.rowconfigure(1, weight=1)

        # Sabor
        tarjeta, cuerpo = self._tarjeta(frame, "Nuevo sabor")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.entry_sabor_nombre = self._campo(cuerpo, "Nombre", ttk.Entry(cuerpo))
        self.combo_elaboracion = self._campo(cuerpo, "Elaboración", ttk.Combobox(
            cuerpo, values=["artesanal", "industrial"], state="readonly"))
        self.entry_sabor_precio = self._campo(cuerpo, "Precio por kilo ($)", ttk.Entry(cuerpo))
        ttk.Button(cuerpo, text="Agregar sabor", style="Accent.TButton",
                   command=self.agregar_sabor).pack(fill="x", side="bottom")

        # Recipiente
        tarjeta, cuerpo = self._tarjeta(frame, "Nuevo recipiente")
        tarjeta.grid(row=0, column=1, sticky="nsew", padx=6)
        self.entry_recip_nombre = self._campo(cuerpo, "Nombre", ttk.Entry(cuerpo))
        self.entry_recip_kilos = self._campo(cuerpo, "Capacidad (kg)", ttk.Entry(cuerpo))
        self.entry_recip_incremento = self._campo(cuerpo, "Incremento (%)", ttk.Entry(cuerpo))
        ttk.Button(cuerpo, text="Agregar recipiente", style="Accent.TButton",
                   command=self.agregar_recipiente).pack(fill="x", side="bottom")

        # Pote
        tarjeta, cuerpo = self._tarjeta(frame, "Nuevo pote")
        tarjeta.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        self.combo_pote_sabor = self._campo(cuerpo, "Sabor", ttk.Combobox(cuerpo, state="readonly"))
        self.entry_pote_fecha = self._campo(cuerpo, "Fecha de incorporación (AAAA-MM-DD)",
                                            ttk.Entry(cuerpo))
        self.entry_pote_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ttk.Button(cuerpo, text="Agregar pote", style="Accent.TButton",
                   command=self.agregar_pote).pack(fill="x", side="bottom")

        # Enter en cualquier campo confirma el formulario correspondiente
        for entrada in (self.entry_sabor_nombre, self.entry_sabor_precio):
            entrada.bind("<Return>", lambda e: self.agregar_sabor())
        for entrada in (self.entry_recip_nombre, self.entry_recip_kilos, self.entry_recip_incremento):
            entrada.bind("<Return>", lambda e: self.agregar_recipiente())
        self.entry_pote_fecha.bind("<Return>", lambda e: self.agregar_pote())

        # Tabla de potes y barra de reposición de stock
        tarjeta, cuerpo = self._tarjeta(frame, "Potes en el mostrador")
        tarjeta.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(12, 0))

        barra_stock = ttk.Frame(cuerpo, style="Panel.TFrame")
        barra_stock.pack(fill="x", pady=(0, 10))
        ttk.Label(barra_stock, text="Reponer stock:", style="Panel.TLabel").pack(side="left", padx=(0, 8))
        self.combo_reponer_pote = ttk.Combobox(barra_stock, state="readonly", width=32)
        self.combo_reponer_pote.pack(side="left", padx=(0, 8))
        ttk.Label(barra_stock, text="Kg:", style="Panel.TLabel").pack(side="left", padx=(0, 4))
        self.entry_reponer_kilos = ttk.Entry(barra_stock, width=8)
        self.entry_reponer_kilos.pack(side="left", padx=(0, 8))
        self.entry_reponer_kilos.bind("<Return>", lambda e: self.reponer_stock())
        ttk.Button(barra_stock, text="Reponer stock", style="Accent.TButton",
                   command=self.reponer_stock).pack(side="left")

        self.tabla_potes = self._tabla(cuerpo, [
            ("id", "Pote", 50, "center"),
            ("sabor", "Sabor", 170, "w"),
            ("elaboracion", "Elaboración", 95, "w"),
            ("fecha", "Incorporado", 95, "center"),
            ("stock", "Stock (kg)", 85, "e"),
            ("kilos", "Kg servidos", 90, "e"),
            ("recaudado", "Recaudado", 105, "e"),
        ], alto=5)

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
                      font=(FUENTE, 8, "bold")).pack(anchor="w", pady=(6, 1))
            for texto, comando in botones:
                boton = ttk.Button(cuerpo, text=texto, style="Reporte.TButton", width=28)
                boton.configure(command=lambda b=boton, c=comando: self._elegir_reporte(b, c))
                boton.pack(fill="x")
                self.botones_reporte[comando.__name__] = boton

        # Panel de resultado (reemplaza a los messagebox)
        self.tarjeta_resultado = ttk.Frame(frame, style="Panel.TFrame", padding=24)
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
                      font=(FUENTE, 10, "bold")).grid(row=0, column=1, sticky="e")
            fila.columnconfigure(0, weight=1)
            barra = tk.Canvas(fila, height=14, bg=COLORES["borde"], highlightthickness=0)
            barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
            # La barra se dibuja cuando el canvas sabe su ancho real
            barra.bind("<Configure>", lambda e, c=barra, p=porcentaje: self._dibujar_barra(c, p, e.width))

    @staticmethod
    def _dibujar_barra(canvas, porcentaje, ancho):
        canvas.delete("all")
        canvas.create_rectangle(0, 0, ancho * porcentaje / 100, 14,
                                fill=COLORES["primario"], width=0)

    # ---------- Acciones para agregar ----------
    def agregar_sabor(self):
        try:
            nombre = self.entry_sabor_nombre.get().strip()
            elaboracion = self.combo_elaboracion.get()
            precio = float(self.entry_sabor_precio.get().replace(",", "."))
            if not nombre or not elaboracion:
                raise ValueError("Faltan datos")
            if precio <= 0:
                raise ValueError("El precio debe ser mayor a 0")
        except ValueError:
            self._avisar("Revisá el sabor: nombre, elaboración y precio mayor a 0.", error=True)
            return
        sabor = Sabor(len(self.heladeria.sabores) + 1, nombre, elaboracion, precio)
        self.heladeria.agregar_sabor(sabor)
        self.heladeria.agregar_pote(
            Pote(len(self.heladeria.potes) + 1, sabor, datetime.now().strftime("%Y-%m-%d"))
        )
        self.entry_sabor_nombre.delete(0, tk.END)
        self.entry_sabor_precio.delete(0, tk.END)
        self.combo_elaboracion.set("")
        self.entry_sabor_nombre.focus()
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Sabor agregado: {sabor}")

    def agregar_recipiente(self):
        try:
            nombre = self.entry_recip_nombre.get().strip()
            kilos = float(self.entry_recip_kilos.get().replace(",", "."))
            incremento = float(self.entry_recip_incremento.get().replace(",", "."))
            if not nombre:
                raise ValueError("Falta el nombre")
            if kilos <= 0 or incremento < 0:
                raise ValueError("Valores fuera de rango")
        except ValueError:
            self._avisar("Revisá el recipiente: nombre, kilos mayor a 0 y % mayor o igual a 0.",
                         error=True)
            return
        recipiente = Recipiente(len(self.heladeria.recipientes) + 1, nombre, kilos, incremento)
        self.heladeria.agregar_recipiente(recipiente)
        for entrada in (self.entry_recip_nombre, self.entry_recip_kilos, self.entry_recip_incremento):
            entrada.delete(0, tk.END)
        self.entry_recip_nombre.focus()
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Recipiente agregado: {recipiente}")

    def agregar_pote(self):
        idx = self.combo_pote_sabor.current()
        if idx < 0:
            self._avisar("Elegí un sabor para el pote.", error=True)
            return
        fecha = self.entry_pote_fecha.get().strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            self._avisar("La fecha debe tener el formato AAAA-MM-DD y ser válida.", error=True)
            return
        sabor = self.heladeria.sabores[idx]
        pote = Pote(len(self.heladeria.potes) + 1, sabor, fecha)
        self.heladeria.agregar_pote(pote)
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Pote #{pote.id} de {sabor.nombre} agregado.")

    def reponer_stock(self):
        idx = self.combo_reponer_pote.current()
        if idx < 0:
            self._avisar("Elegí un pote para reponer stock.", error=True)
            return
        try:
            kilos = float(self.entry_reponer_kilos.get().replace(",", "."))
            pote = self.heladeria.potes[idx]
            pote.reponer_stock(kilos)
        except ValueError:
            self._avisar("Ingresá una cantidad de kilos mayor a 0.", error=True)
            return
        self.entry_reponer_kilos.delete(0, tk.END)
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Stock repuesto en {pote.sabor.nombre}: ahora tiene {pote.stock_kg:.2f} kg.")

    # ---------- Venta ----------
    def registrar_venta(self):
        potes = self._obtener_potes_seleccionados()
        idx_recip = self.combo_venta_recipiente.current()
        if not potes or idx_recip < 0:
            self._avisar("Elegí los sabores y el tamaño de pote.", error=True)
            return
        recipiente = self.heladeria.recipientes[idx_recip]
        try:
            venta = self.heladeria.vender(potes, recipiente)
        except ValueError as err:
            mensaje = str(err)
            self._avisar(mensaje.splitlines()[0], error=True)
            messagebox.showwarning("Alerta de reposición de stock", mensaje)
            return
        guardar_json(self.heladeria)
        self.refrescar()
        self._avisar(f"Venta registrada: {venta.kilos:g} kg ({venta.nombres_sabores()}) en "
                     f"{recipiente.nombre} por {formato_dinero(venta.calcular_precio_total())}")

    # ---------- Actualizacion general de la pantalla ----------
    def refrescar(self):
        h = self.heladeria
        opciones_sabores = [
            f"{p.sabor.nombre} · {p.sabor.elaboracion} · {formato_dinero(p.sabor.precio_por_kilo)}/kg · Stock: {p.stock_kg:.2f} kg"
            for p in h.potes
        ]
        # Combos (se conserva lo que estaba elegido)
        combos = [
            (self.combo_pote_sabor, [f"{s.nombre} · {s.elaboracion} · "
                                     f"{formato_dinero(s.precio_por_kilo)}/kg" for s in h.sabores]),
            (self.combo_reponer_pote, [f"Pote #{p.id} · {p.sabor.nombre} ({p.stock_kg:.2f} kg)" for p in h.potes]),
            (self.combos_venta_sabores[0], opciones_sabores),
            (self.combos_venta_sabores[1], ["(Sin 2° sabor)"] + opciones_sabores),
            (self.combos_venta_sabores[2], ["(Sin 3° sabor)"] + opciones_sabores),
            (self.combos_venta_sabores[3], ["(Sin 4° sabor)"] + opciones_sabores),
            (self.combo_venta_recipiente, [r.etiqueta_combo() for r in h.recipientes]),
        ]
        for combo, valores in combos:
            seleccion = combo.current()
            combo["values"] = valores
            if 0 <= seleccion < len(valores):
                combo.current(seleccion)
            elif combo in self.combos_venta_sabores[1:] and valores:
                combo.current(0)

        # Tablas
        self._llenar_tabla(self.tabla_ventas, [
            (i, v.nombres_sabores(), v.recipiente.nombre, f"{v.kilos:g}",
             formato_dinero(v.calcular_precio_total()))
            for i, v in reversed(list(enumerate(h.ventas, start=1)))
        ])
        self._llenar_tabla(self.tabla_potes, [
            (p.id, p.sabor.nombre, p.sabor.elaboracion, p.fecha_incorporacion,
             f"{p.stock_kg:.2f}", f"{p.kilos_servidos:.2f}", formato_dinero(p.dinero_recaudado))
            for p in h.potes
        ])

        # Indicadores del encabezado
        self.kpis["recaudado"].config(text=formato_dinero(h.recaudacion_total()))
        self.kpis["ventas"].config(text=str(len(h.ventas)))
        self.kpis["kilos"].config(text=f"{sum(v.kilos for v in h.ventas):.2f}")

        self._actualizar_vista_previa()
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

    def mostrar_recaudacion_total(self):
        self._mostrar_valor("Recaudación total",
                            formato_dinero(self.heladeria.recaudacion_total()),
                            f"Sobre {len(self.heladeria.ventas)} ventas registradas")

    def mostrar_pote_mas_servido(self):
        self._mostrar_pote("Pote más servido", self.heladeria.pote_mas_servido())

    def mostrar_pote_menos_servido(self):
        self._mostrar_pote("Pote menos servido", self.heladeria.pote_menos_servido())

    def mostrar_pote_mas_recaudado(self):
        self._mostrar_pote("Pote más recaudado", self.heladeria.pote_mas_recaudado())

    def mostrar_sabor_mas_vendido(self):
        sabor = self.heladeria.sabor_mas_vendido()
        cantidad = self.heladeria.cantidad_ventas_por_sabor().get(sabor, 0)
        self._mostrar_valor("Sabor más vendido", sabor, f"{cantidad} ventas")

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