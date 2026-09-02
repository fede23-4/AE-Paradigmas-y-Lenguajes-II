from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox


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
                f"Servidos: {self.kilos_servidos} kg, Recaudado: ${self.dinero_recaudado:.2f}")


class Venta:
    def __init__(self, pote, recipiente):
        self.pote = pote
        self.recipiente = recipiente
        self.kilos = recipiente.kilos

    def calcular_precio_total(self):
        precio_base = self.pote.sabor.precio_por_kilo * self.kilos
        incremento = precio_base * (self.recipiente.porcentaje_incremento / 100)
        return precio_base + incremento

    def calcular_kilos(self):
        return self.kilos

    def __str__(self):
        return (f"Venta de {self.kilos} kg de {self.pote.sabor.nombre} "
                f"en {self.recipiente.nombre}: ${self.calcular_precio_total():.2f}")


# Logica de la heladeria
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

    # Punto 1
    def recaudacion_total(self):
        return sum(venta.calcular_precio_total() for venta in self.ventas)

    # Punto 2
    def pote_mas_servido(self):
        if not self.potes:
            return None
        return max(self.potes, key=lambda pote: pote.kilos_servidos)

    def pote_menos_servido(self):
        if not self.potes:
            return None
        return min(self.potes, key=lambda pote: pote.kilos_servidos)

    # Punto 3
    def pote_mas_recaudado(self):
        if not self.potes:
            return None
        return max(self.potes, key=lambda pote: pote.dinero_recaudado)

    # Punto 4
    def sabor_mas_vendido(self):
        resultado = self.cantidad_ventas_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=resultado.get)

    # Punto 5
    def sabor_mas_recaudado(self):
        resultado = self.recaudacion_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=resultado.get)

    # Punto 6
    def sabor_mas_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return max(resultado, key=resultado.get)

    # Punto 7
    def sabor_menos_kilos_vendidos(self):
        resultado = self.kilos_por_sabor()
        if not resultado:
            return None
        return min(resultado, key=resultado.get)

    # Punto 8
    def recipiente_mas_solicitado(self):
        if not self.ventas:
            return None
        resultado = defaultdict(int)
        for venta in self.ventas:
            resultado[venta.recipiente.nombre] += 1
        return max(resultado, key=resultado.get)

    # Punto 9
    def porcentaje_venta_por_sabor(self):
        total = len(self.ventas)
        if total == 0:
            return {}
        cantidades = self.cantidad_ventas_por_sabor()
        return {sabor: (cantidad / total) * 100 for sabor, cantidad in cantidades.items()}

    # Punto 10
    def porcentaje_recaudacion_por_sabor(self):
        total = self.recaudacion_total()
        if total == 0:
            return {}
        recaudacion = self.recaudacion_por_sabor()
        return {sabor: (monto / total) * 100 for sabor, monto in recaudacion.items()}

    # Punto 11
    def porcentaje_venta_por_pote(self):
        total_kilos = sum(p.kilos_servidos for p in self.potes)
        if total_kilos == 0:
            return {}
        return {pote.id: (pote.kilos_servidos / total_kilos) * 100 for pote in self.potes}

    # Punto 12
    def porcentaje_recaudacion_por_pote(self):
        total = self.recaudacion_total()
        if total == 0:
            return {}
        return {pote.id: (pote.dinero_recaudado / total) * 100 for pote in self.potes}


# Interfaz mejorada
class HeladeriaGUI:
    def __init__(self, heladeria):
        self.heladeria = heladeria
        self.ventana = tk.Tk()
        self.ventana.title("Heladeria - Sistema de Gestion")
        self.ventana.geometry("960x680")
        self.ventana.minsize(800, 600)

        # Estilos
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Arial", 10, "bold"))

        # Notebook (pestanas)
        notebook = ttk.Notebook(self.ventana)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_venta = ttk.Frame(notebook)
        self.tab_datos = ttk.Frame(notebook)
        self.tab_reportes = ttk.Frame(notebook)

        notebook.add(self.tab_venta, text="  Nueva Venta  ")
        notebook.add(self.tab_datos, text="  Agregar Datos  ")
        notebook.add(self.tab_reportes, text="  Reportes  ")

        self._armar_tab_venta()
        self._armar_tab_datos()
        self._armar_tab_reportes()

    # ---- Pestaña de ventas ----
    def _armar_tab_venta(self):
        frame = self.tab_venta

        ttk.Label(frame, text="Registrar Nueva Venta", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(20, 15), padx=20)

        ttk.Label(frame, text="Pote:").grid(row=1, column=0, sticky="e", padx=20, pady=10)
        self.combo_venta_pote = ttk.Combobox(frame, state="readonly", width=38)
        self.combo_venta_pote.grid(row=1, column=1, padx=20, pady=10)

        ttk.Label(frame, text="Recipiente:").grid(row=2, column=0, sticky="e", padx=20, pady=10)
        self.combo_venta_recipiente = ttk.Combobox(frame, state="readonly", width=38)
        self.combo_venta_recipiente.grid(row=2, column=1, padx=20, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)

        tk.Button(
            btn_frame, text="Registrar venta", command=self.registrar_venta,
            width=22, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
            relief="raised", padx=8, pady=5, cursor="hand2"
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame, text="Actualizar listas", command=self.refrescar_combos,
            width=22, font=("Arial", 10), relief="raised", padx=8, pady=5, cursor="hand2"
        ).pack(side="left", padx=10)

        # Area de resultado
        ttk.Label(frame, text="Ultima venta:", style="Header.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))

        self.text_venta_resultado = tk.Text(
            frame, height=8, width=65, wrap="word",
            font=("Consolas", 10), bg="#f5f5f5", state="disabled", relief="sunken", bd=2
        )
        self.text_venta_resultado.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")

        frame.grid_rowconfigure(5, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    # ---- Pestaña de datos ----
    def _armar_tab_datos(self):
        frame = self.tab_datos

        # Canvas con scroll para el formulario
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", tags="inner")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig("inner", width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Sabores ---
        sabor_frame = ttk.LabelFrame(scrollable, text=" Nuevo Sabor ", style="Section.TLabelframe")
        sabor_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 5))

        ttk.Label(sabor_frame, text="Nombre:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.entry_sabor_nombre = ttk.Entry(sabor_frame, width=25)
        self.entry_sabor_nombre.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(sabor_frame, text="Elaboracion:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.combo_elaboracion = ttk.Combobox(
            sabor_frame, values=["artesanal", "industrial"], state="readonly", width=22
        )
        self.combo_elaboracion.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(sabor_frame, text="Precio por kilo:").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.entry_sabor_precio = ttk.Entry(sabor_frame, width=25)
        self.entry_sabor_precio.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(
            sabor_frame, text="Agregar Sabor", command=self.agregar_sabor,
            bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
            width=18, relief="raised", padx=5, pady=3, cursor="hand2"
        ).grid(row=3, column=0, columnspan=2, pady=8)

        # --- Recipientes ---
        recip_frame = ttk.LabelFrame(scrollable, text=" Nuevo Recipiente ", style="Section.TLabelframe")
        recip_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=5)

        ttk.Label(recip_frame, text="Nombre:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.entry_recip_nombre = ttk.Entry(recip_frame, width=25)
        self.entry_recip_nombre.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(recip_frame, text="Kilos:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.entry_recip_kilos = ttk.Entry(recip_frame, width=25)
        self.entry_recip_kilos.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(recip_frame, text="% incremento:").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.entry_recip_incremento = ttk.Entry(recip_frame, width=25)
        self.entry_recip_incremento.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(
            recip_frame, text="Agregar Recipiente", command=self.agregar_recipiente,
            bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
            width=18, relief="raised", padx=5, pady=3, cursor="hand2"
        ).grid(row=3, column=0, columnspan=2, pady=8)

        # --- Potes ---
        pote_frame = ttk.LabelFrame(scrollable, text=" Nuevo Pote ", style="Section.TLabelframe")
        pote_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 15))

        ttk.Label(pote_frame, text="Sabor:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.combo_pote_sabor = ttk.Combobox(pote_frame, state="readonly", width=28)
        self.combo_pote_sabor.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(pote_frame, text="Fecha (AAAA-MM-DD):").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.entry_pote_fecha = ttk.Entry(pote_frame, width=25)
        self.entry_pote_fecha.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(
            pote_frame, text="Agregar Pote", command=self.agregar_pote,
            bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
            width=18, relief="raised", padx=5, pady=3, cursor="hand2"
        ).grid(row=2, column=0, columnspan=2, pady=8)

    # ---- Pestaña de reportes ----
    def _armar_tab_reportes(self):
        frame = self.tab_reportes

        # Panel izquierdo - botones
        left = ttk.Frame(frame, width=360)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)
        left.pack_propagate(False)

        ttk.Label(left, text="Reportes", style="Title.TLabel").pack(pady=(0, 10))

        botones = [
            ("Recaudacion total", self.mostrar_recaudacion_total, "#4CAF50"),
            ("Pote mas servido", self.mostrar_pote_mas_servido, "#2196F3"),
            ("Pote menos servido", self.mostrar_pote_menos_servido, "#FF9800"),
            ("Pote mas recaudado", self.mostrar_pote_mas_recaudado, "#4CAF50"),
            ("Sabor mas vendido", self.mostrar_sabor_mas_vendido, "#9C27B0"),
            ("Sabor con mas ganancia", self.mostrar_sabor_mas_recaudado, "#4CAF50"),
            ("Sabor con mas kilos vendidos", self.mostrar_sabor_mas_kilos_vendidos, "#2196F3"),
            ("Sabor con menos kilos vendidos", self.mostrar_sabor_menos_kilos_vendidos, "#FF9800"),
            ("Recipiente mas solicitado", self.mostrar_recipiente_mas_solicitado, "#9C27B0"),
            ("% de venta por sabor", self.mostrar_porcentaje_venta_por_sabor, "#607D8B"),
            ("% de recaudacion por sabor", self.mostrar_porcentaje_recaudacion_por_sabor, "#607D8B"),
            ("% de venta por pote", self.mostrar_porcentaje_venta_por_pote, "#607D8B"),
            ("% de recaudacion por pote", self.mostrar_porcentaje_recaudacion_por_pote, "#607D8B"),
        ]

        for texto, cmd, color in botones:
            tk.Button(
                left, text=texto, command=cmd, width=32,
                bg=color, fg="white", font=("Arial", 9, "bold"),
                relief="raised", padx=5, pady=4, cursor="hand2"
            ).pack(pady=2, fill="x")

        # Panel derecho - resultados
        right = ttk.Frame(frame)
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        ttk.Label(right, text="Resultados:", style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        self.text_resultados = tk.Text(
            right, wrap="word", font=("Consolas", 10),
            bg="#f5f5f5", relief="sunken", bd=2
        )
        scroll_res = ttk.Scrollbar(right, command=self.text_resultados.yview)
        self.text_resultados.configure(yscrollcommand=scroll_res.set)

        scroll_res.pack(side="right", fill="y")
        self.text_resultados.pack(fill="both", expand=True)

        tk.Button(
            right, text="Limpiar", width=12, font=("Arial", 9),
            command=lambda: self.text_resultados.delete("1.0", tk.END)
        ).pack(pady=(5, 0))

    # ---- Utilidades ----
    def mostrar_resultado(self, titulo, texto):
        self.text_resultados.delete("1.0", tk.END)
        self.text_resultados.insert(
            tk.END, f"{'=' * 50}\n  {titulo}\n{'=' * 50}\n\n{texto}"
        )

    def mostrar_resultado_venta(self, texto):
        self.text_venta_resultado.configure(state="normal")
        self.text_venta_resultado.delete("1.0", tk.END)
        self.text_venta_resultado.insert(tk.END, texto)
        self.text_venta_resultado.configure(state="disabled")

    def refrescar_combos(self):
        sabores = [str(s) for s in self.heladeria.sabores]
        potes = [str(p) for p in self.heladeria.potes]
        recipientes = [str(r) for r in self.heladeria.recipientes]

        self.combo_pote_sabor["values"] = sabores
        self.combo_venta_pote["values"] = potes
        self.combo_venta_recipiente["values"] = recipientes

        # Seleccionar el primer elemento si no hay seleccion
        if sabores and self.combo_pote_sabor.current() < 0:
            self.combo_pote_sabor.current(0)
        if potes and self.combo_venta_pote.current() < 0:
            self.combo_venta_pote.current(0)
        if recipientes and self.combo_venta_recipiente.current() < 0:
            self.combo_venta_recipiente.current(0)

        # Forzar actualizacion visual de los comboboxes
        self.ventana.update_idletasks()

    # ---- Acciones de carga ----
    def agregar_sabor(self):
        try:
            nombre = self.entry_sabor_nombre.get().strip()
            elaboracion = self.combo_elaboracion.get()
            precio = float(self.entry_sabor_precio.get())
            if not nombre or not elaboracion:
                raise ValueError("Faltan datos")
            nuevo_id = len(self.heladeria.sabores) + 1
            sabor = Sabor(nuevo_id, nombre, elaboracion, precio)
            self.heladeria.agregar_sabor(sabor)
            messagebox.showinfo("Sabor agregado", str(sabor))
            self.entry_sabor_nombre.delete(0, tk.END)
            self.entry_sabor_precio.delete(0, tk.END)
            self.combo_elaboracion.set("")
            self.refrescar_combos()
        except ValueError:
            messagebox.showerror(
                "Error",
                "Verifica los datos del sabor (precio numerico, campos completos)."
            )

    def agregar_recipiente(self):
        try:
            nombre = self.entry_recip_nombre.get().strip()
            kilos = float(self.entry_recip_kilos.get())
            incremento = float(self.entry_recip_incremento.get())
            if not nombre:
                raise ValueError("Falta el nombre")
            nuevo_id = len(self.heladeria.recipientes) + 1
            recipiente = Recipiente(nuevo_id, nombre, kilos, incremento)
            self.heladeria.agregar_recipiente(recipiente)
            messagebox.showinfo("Recipiente agregado", str(recipiente))
            self.entry_recip_nombre.delete(0, tk.END)
            self.entry_recip_kilos.delete(0, tk.END)
            self.entry_recip_incremento.delete(0, tk.END)
            self.refrescar_combos()
        except ValueError:
            messagebox.showerror(
                "Error",
                "Verifica los datos del recipiente (kilos y % numericos, nombre completo)."
            )

    def agregar_pote(self):
        idx = self.combo_pote_sabor.current()
        if idx < 0:
            messagebox.showerror("Error", "Elegi un sabor para el pote.")
            return
        fecha = self.entry_pote_fecha.get().strip()
        if not fecha:
            messagebox.showerror("Error", "Ingresa la fecha de incorporacion.")
            return
        sabor = self.heladeria.sabores[idx]
        nuevo_id = len(self.heladeria.potes) + 1
        pote = Pote(nuevo_id, sabor, fecha)
        self.heladeria.agregar_pote(pote)
        messagebox.showinfo("Pote agregado", str(pote))
        self.entry_pote_fecha.delete(0, tk.END)
        self.refrescar_combos()

    # ---- Venta ----
    def registrar_venta(self):
        idx_pote = self.combo_venta_pote.current()
        idx_recip = self.combo_venta_recipiente.current()
        if idx_pote < 0 or idx_recip < 0:
            messagebox.showerror("Error", "Elegi un pote y un recipiente.")
            return
        pote = self.heladeria.potes[idx_pote]
        recipiente = self.heladeria.recipientes[idx_recip]
        venta = self.heladeria.vender(pote, recipiente)
        self.mostrar_resultado_venta(str(venta))
        self.refrescar_combos()

    # ---- Reportes ----
    def mostrar_recaudacion_total(self):
        total = self.heladeria.recaudacion_total()
        self.mostrar_resultado("Recaudacion Total", f"${total:.2f}")

    def mostrar_pote_mas_servido(self):
        pote = self.heladeria.pote_mas_servido()
        self.mostrar_resultado("Pote mas servido", str(pote) if pote else "Sin datos")

    def mostrar_pote_menos_servido(self):
        pote = self.heladeria.pote_menos_servido()
        self.mostrar_resultado("Pote menos servido", str(pote) if pote else "Sin datos")

    def mostrar_pote_mas_recaudado(self):
        pote = self.heladeria.pote_mas_recaudado()
        self.mostrar_resultado("Pote mas recaudado", str(pote) if pote else "Sin datos")

    def mostrar_sabor_mas_vendido(self):
        sabor = self.heladeria.sabor_mas_vendido()
        self.mostrar_resultado("Sabor mas vendido", str(sabor) if sabor else "Sin datos")

    def mostrar_sabor_mas_recaudado(self):
        sabor = self.heladeria.sabor_mas_recaudado()
        self.mostrar_resultado("Sabor con mas ganancia", str(sabor) if sabor else "Sin datos")

    def mostrar_sabor_mas_kilos_vendidos(self):
        sabor = self.heladeria.sabor_mas_kilos_vendidos()
        self.mostrar_resultado("Sabor con mas kilos vendidos", str(sabor) if sabor else "Sin datos")

    def mostrar_sabor_menos_kilos_vendidos(self):
        sabor = self.heladeria.sabor_menos_kilos_vendidos()
        self.mostrar_resultado("Sabor con menos kilos vendidos", str(sabor) if sabor else "Sin datos")

    def mostrar_recipiente_mas_solicitado(self):
        recip = self.heladeria.recipiente_mas_solicitado()
        self.mostrar_resultado("Recipiente mas solicitado", str(recip) if recip else "Sin datos")

    def mostrar_porcentaje_venta_por_sabor(self):
        datos = self.heladeria.porcentaje_venta_por_sabor()
        texto = "\n".join(f"  {s}: {p:.1f}%" for s, p in datos.items())
        self.mostrar_resultado("% de venta por sabor", texto or "Sin ventas registradas")

    def mostrar_porcentaje_recaudacion_por_sabor(self):
        datos = self.heladeria.porcentaje_recaudacion_por_sabor()
        texto = "\n".join(f"  {s}: {p:.1f}%" for s, p in datos.items())
        self.mostrar_resultado("% de recaudacion por sabor", texto or "Sin ventas registradas")

    def mostrar_porcentaje_venta_por_pote(self):
        datos = self.heladeria.porcentaje_venta_por_pote()
        texto = "\n".join(f"  Pote {id_p}: {p:.1f}%" for id_p, p in datos.items())
        self.mostrar_resultado("% de venta por pote", texto or "Sin ventas registradas")

    def mostrar_porcentaje_recaudacion_por_pote(self):
        datos = self.heladeria.porcentaje_recaudacion_por_pote()
        texto = "\n".join(f"  Pote {id_p}: {p:.1f}%" for id_p, p in datos.items())
        self.mostrar_resultado("% de recaudacion por pote", texto or "Sin ventas registradas")

    def iniciar(self):
        self.refrescar_combos()
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
