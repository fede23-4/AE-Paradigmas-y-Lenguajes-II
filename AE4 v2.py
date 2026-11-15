from collections import defaultdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk


class Sabor:
    def __init__(self, id, nombre, elaboracion, precio_por_kilo):
        self.id = id
        self.nombre = nombre
        self.elaboracion = elaboracion  
        self.precio_por_kilo = precio_por_kilo

    def __str__(self):
        return f"{self.nombre} (${self.precio_por_kilo}/kg, {self.elaboracion})"


class Recipiente:
    def __init__(self, id, nombre, kilos, porcentaje_incremento):
        self.id = id
        self.nombre = nombre                               
        self.kilos = kilos                                
        self.porcentaje_incremento = porcentaje_incremento  

    def __str__(self):
        return f"{self.nombre} ({self.kilos} kg)"


class Pote:
    def __init__(self, id, sabor, fecha_incorporacion):
        self.id = id
        self.sabor = sabor
        self.fecha_incorporacion = fecha_incorporacion
        self.kilos_servidos = 0
        self.dinero_recaudado = 0

    def registrar_venta(self, kilos, dinero):
        self.kilos_servidos += kilos
        self.dinero_recaudado += dinero

    def __str__(self):
        return (f"Pote #{self.id} de {self.sabor.nombre} - "
                f"Servidos: {self.kilos_servidos:.2f} kg, Recaudado: ${self.dinero_recaudado:.2f}")


class Venta:
    def __init__(self, pote, recipiente):
        self.pote = pote
        self.recipiente = recipiente
        self.kilos = recipiente.kilos
        # El precio se calcula y se guarda en el momento de la venta,
        # asi no cambia si despues se modifica el precio del sabor.
        precio_base = pote.sabor.precio_por_kilo * self.kilos
        incremento = precio_base * (recipiente.porcentaje_incremento / 100)
        self.precio_total = precio_base + incremento

    def calcular_precio_total(self):
        return self.precio_total

    def calcular_kilos(self):
        return self.kilos

    def __str__(self):
        return (f"Venta de {self.kilos} kg de {self.pote.sabor.nombre} "
                f"en {self.recipiente.nombre}: ${self.calcular_precio_total():.2f}")

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

    def vender(self, pote, recipiente):
        venta = Venta(pote, recipiente)
        pote.registrar_venta(venta.calcular_kilos(), venta.calcular_precio_total())
        self.ventas.append(venta)
        return venta

    

    def kilos_por_sabor(self):
        resultado = defaultdict(float)
        for venta in self.ventas:
            resultado[venta.pote.sabor.nombre] += venta.calcular_kilos()
        return resultado

    def recaudacion_por_sabor(self):
        resultado = defaultdict(float)
        for venta in self.ventas:
            resultado[venta.pote.sabor.nombre] += venta.calcular_precio_total()
        return resultado

    def cantidad_ventas_por_sabor(self):
        resultado = defaultdict(int)
        for venta in self.ventas:
            resultado[venta.pote.sabor.nombre] += 1
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
        return max(resultado, key=resultado.get)

    #Punto 5
    def sabor_mas_recaudado(self):
        resultado = self.recaudacion_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=resultado.get)

    #Punto 6
    def sabor_mas_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=resultado.get)

    #Punto 7
    def sabor_menos_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return min(resultado, key=resultado.get)

    #Punto 8 
    def recipiente_mas_solicitado(self):
        if not self.ventas:
            return None
        resultado = defaultdict(int)
        for venta in self.ventas:
            resultado[venta.recipiente.nombre] += 1
        return max(resultado, key=resultado.get)

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
        self.ventana.geometry("960x720")
        self.ventana.minsize(880, 680)
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

        estilo.configure(".", background=c["fondo"], foreground=c["texto"], font=(FUENTE, 10))
        estilo.configure("TFrame", background=c["fondo"])
        estilo.configure("Panel.TFrame", background=c["panel"])
        estilo.configure("TLabel", background=c["fondo"])
        estilo.configure("Panel.TLabel", background=c["panel"])
        estilo.configure("Titulo.TLabel", background=c["panel"], font=(FUENTE, 12, "bold"))
        estilo.configure("Suave.TLabel", background=c["panel"], foreground=c["texto_suave"])
        estilo.configure("Grande.TLabel", background=c["panel"], foreground=c["primario"],
                         font=(FUENTE, 24, "bold"))

        estilo.configure("TNotebook", background=c["fondo"], borderwidth=0, tabmargins=0)
        estilo.configure("TNotebook.Tab", padding=(18, 8), font=(FUENTE, 10, "bold"),
                         background=c["borde"], foreground=c["texto_suave"], borderwidth=0)
        estilo.map("TNotebook.Tab",
                   background=[("selected", c["fondo"])],
                   foreground=[("selected", c["primario"])])

        estilo.configure("Accent.TButton", background=c["primario"], foreground="white",
                         font=(FUENTE, 10, "bold"), padding=(16, 8), borderwidth=0)
        estilo.map("Accent.TButton", background=[("active", c["primario_hover"])])

        estilo.configure("Reporte.TButton", background=c["panel"], foreground=c["texto"],
                         anchor="w", padding=(12, 4), borderwidth=0)
        estilo.map("Reporte.TButton",
                   background=[("pressed", c["resaltado"]), ("active", c["borde"])])
        # Boton del reporte que se esta mostrando
        estilo.configure("ReporteActivo.TButton", background=c["resaltado"],
                         foreground=c["primario_hover"], font=(FUENTE, 10, "bold"),
                         anchor="w", padding=(12, 4), borderwidth=0)
        estilo.map("ReporteActivo.TButton", background=[("active", c["resaltado"])])

        estilo.configure("Treeview", background=c["panel"], fieldbackground=c["panel"],
                         rowheight=28, borderwidth=0)
        estilo.configure("Treeview.Heading", background=c["borde"], foreground=c["texto"],
                         font=(FUENTE, 9, "bold"), borderwidth=0, padding=(6, 4))
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
                                     bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                                     font=(FUENTE, 9), padx=20, pady=6)
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

        tarjeta, cuerpo = self._tarjeta(frame, "Registrar venta", "Elegí el pote y el recipiente")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.combo_venta_pote = self._campo(
            cuerpo, "Pote", ttk.Combobox(cuerpo, state="readonly"))
        self.combo_venta_recipiente = self._campo(
            cuerpo, "Recipiente", ttk.Combobox(cuerpo, state="readonly"))
        for combo in (self.combo_venta_pote, self.combo_venta_recipiente):
            combo.bind("<<ComboboxSelected>>", lambda e: self._actualizar_vista_previa())

        # Vista previa del precio antes de confirmar
        previa = ttk.Frame(cuerpo, style="Panel.TFrame")
        previa.pack(fill="x", pady=(8, 14))
        ttk.Label(previa, text="Total a cobrar", style="Suave.TLabel").pack(anchor="w")
        self.lbl_precio_previo = ttk.Label(previa, text="$0,00", style="Grande.TLabel")
        self.lbl_precio_previo.pack(anchor="w")
        self.lbl_detalle_previo = ttk.Label(previa, text="", style="Suave.TLabel", wraplength=300)
        self.lbl_detalle_previo.pack(anchor="w")

        ttk.Button(cuerpo, text="Registrar venta", style="Accent.TButton",
                   command=self.registrar_venta).pack(fill="x")

        tarjeta, cuerpo = self._tarjeta(frame, "Historial de ventas", "La más reciente arriba")
        tarjeta.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.tabla_ventas = self._tabla(cuerpo, [
            ("n", "#", 40, "center"),
            ("sabor", "Sabor", 150, "w"),
            ("recipiente", "Recipiente", 100, "w"),
            ("kilos", "Kilos", 60, "e"),
            ("total", "Total", 100, "e"),
        ])

    def _actualizar_vista_previa(self):
        idx_pote = self.combo_venta_pote.current()
        idx_recip = self.combo_venta_recipiente.current()
        if idx_pote < 0 or idx_recip < 0:
            self.lbl_precio_previo.config(text="$0,00")
            self.lbl_detalle_previo.config(text="Elegí un pote y un recipiente.")
            return
        pote = self.heladeria.potes[idx_pote]
        recipiente = self.heladeria.recipientes[idx_recip]
        # Crear una Venta no la registra: solo calcula el precio
        precio = Venta(pote, recipiente).calcular_precio_total()
        self.lbl_precio_previo.config(text=formato_dinero(precio))
        self.lbl_detalle_previo.config(
            text=f"{recipiente.kilos} kg × {formato_dinero(pote.sabor.precio_por_kilo)}/kg "
                 f"+ {recipiente.porcentaje_incremento:g}% por recipiente")

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

        # Tabla de potes
        tarjeta, cuerpo = self._tarjeta(frame, "Potes en el mostrador")
        tarjeta.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        self.tabla_potes = self._tabla(cuerpo, [
            ("id", "Pote", 50, "center"),
            ("sabor", "Sabor", 180, "w"),
            ("elaboracion", "Elaboración", 100, "w"),
            ("fecha", "Incorporado", 100, "center"),
            ("kilos", "Kg servidos", 90, "e"),
            ("recaudado", "Recaudado", 110, "e"),
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
                  wraplength=480, justify="left").pack(anchor="w")
        if detalle:
            ttk.Label(self.frame_resultado, text=detalle, style="Suave.TLabel",
                      wraplength=480, justify="left").pack(anchor="w", pady=(6, 0))

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
        self.entry_sabor_nombre.delete(0, tk.END)
        self.entry_sabor_precio.delete(0, tk.END)
        self.combo_elaboracion.set("")
        self.entry_sabor_nombre.focus()
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
        self.refrescar()
        self._avisar(f"Pote #{pote.id} de {sabor.nombre} agregado.")

    # ---------- Venta ----------
    def registrar_venta(self):
        idx_pote = self.combo_venta_pote.current()
        idx_recip = self.combo_venta_recipiente.current()
        if idx_pote < 0 or idx_recip < 0:
            self._avisar("Elegí un pote y un recipiente.", error=True)
            return
        pote = self.heladeria.potes[idx_pote]
        recipiente = self.heladeria.recipientes[idx_recip]
        venta = self.heladeria.vender(pote, recipiente)
        self.refrescar()
        self._avisar(f"Venta registrada: {venta.kilos} kg de {pote.sabor.nombre} en "
                     f"{recipiente.nombre} por {formato_dinero(venta.calcular_precio_total())}")

    # ---------- Actualizacion general de la pantalla ----------
    def refrescar(self):
        h = self.heladeria
        # Combos (se conserva lo que estaba elegido)
        combos = [
            (self.combo_pote_sabor, [f"{s.nombre} · {s.elaboracion} · "
                                     f"{formato_dinero(s.precio_por_kilo)}/kg" for s in h.sabores]),
            (self.combo_venta_pote, [f"Pote #{p.id} · {p.sabor.nombre}" for p in h.potes]),
            (self.combo_venta_recipiente, [f"{r.nombre} · {r.kilos:g} kg (+{r.porcentaje_incremento:g}%)"
                                           for r in h.recipientes]),
        ]
        for combo, valores in combos:
            seleccion = combo.current()
            combo["values"] = valores
            if 0 <= seleccion < len(valores):
                combo.current(seleccion)

        # Tablas
        self._llenar_tabla(self.tabla_ventas, [
            (i, v.pote.sabor.nombre, v.recipiente.nombre, f"{v.kilos:g}",
             formato_dinero(v.calcular_precio_total()))
            for i, v in reversed(list(enumerate(h.ventas, start=1)))
        ])
        self._llenar_tabla(self.tabla_potes, [
            (p.id, p.sabor.nombre, p.sabor.elaboracion, p.fecha_incorporacion,
             f"{p.kilos_servidos:.2f}", formato_dinero(p.dinero_recaudado))
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
    chocolate = Sabor(1, "Chocolate amargo", "artesanal", 9000)
    vainilla = Sabor(2, "Vainilla", "industrial", 7000)
    frutilla = Sabor(3, "Frutilla a la crema", "artesanal", 8500)

    vasito = Recipiente(1, "Vasito", 0.25, 8)
    copa = Recipiente(2, "Copa", 0.5, 8)
    balde = Recipiente(3, "Balde", 1, 8)

    heladeria = Heladeria()

    heladeria.agregar_sabor(chocolate)
    heladeria.agregar_sabor(vainilla)
    heladeria.agregar_sabor(frutilla)

    heladeria.agregar_recipiente(vasito)
    heladeria.agregar_recipiente(copa)
    heladeria.agregar_recipiente(balde)

    pote1 = Pote(1, chocolate, "2026-08-01")
    pote2 = Pote(2, vainilla, "2026-08-01")
    pote3 = Pote(3, frutilla, "2026-08-15")

    heladeria.agregar_pote(pote1)
    heladeria.agregar_pote(pote2)
    heladeria.agregar_pote(pote3)

    heladeria.vender(pote1, vasito)
    heladeria.vender(pote1, balde)
    heladeria.vender(pote2, copa)
    heladeria.vender(pote3, vasito)
    heladeria.vender(pote3, copa)

    gui = HeladeriaGUI(heladeria)
    gui.iniciar()