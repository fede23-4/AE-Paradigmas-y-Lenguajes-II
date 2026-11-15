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

class HeladeriaGUI:
    def __init__(self, heladeria):
        self.heladeria = heladeria
        self.ventana = tk.Tk()
        self.ventana.title("Heladería")
        self.ventana.geometry("520x520")

        notebook = ttk.Notebook(self.ventana)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_datos = ttk.Frame(notebook)
        self.tab_ventas = ttk.Frame(notebook)
        self.tab_reportes = ttk.Frame(notebook)

        notebook.add(self.tab_ventas, text="Nueva Venta")
        notebook.add(self.tab_datos, text="Agregar datos")
        notebook.add(self.tab_reportes, text="Resumen")

        self._armar_tab_ventas()
        self._armar_tab_datos()
        self._armar_tab_reportes()

    
    def _armar_tab_datos(self):
        frame = self.tab_datos

        
        tk.Label(frame, text="Nuevo sabor", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))

        tk.Label(frame, text="Nombre:").grid(row=1, column=0, sticky="e", padx=20, pady=20)
        self.entry_sabor_nombre = tk.Entry(frame)
        self.entry_sabor_nombre.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(frame, text="Elaboración:").grid(row=2, column=0, sticky="e", padx=20, pady=20)
        self.combo_elaboracion = ttk.Combobox(
            frame, values=["artesanal", "industrial"], state="readonly", width=17)
        self.combo_elaboracion.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(frame, text="Precio por kilo:").grid(row=3, column=0, sticky="e", padx=20, pady=20)
        self.entry_sabor_precio = tk.Entry(frame)
        self.entry_sabor_precio.grid(row=3, column=1, padx=5, pady=2)

        tk.Button(frame, text="Agregar sabor", command=self.agregar_sabor).grid(
            row=4, column=0, columnspan=2, pady=5)

        #Para Armar el cuadrito de pote
        tk.Label(frame, text="Nuevo recipiente", font=("Arial", 10, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 0))

        tk.Label(frame, text="Nombre:").grid(row=6, column=0, sticky="e", padx=20, pady=20)
        self.entry_recip_nombre = tk.Entry(frame)
        self.entry_recip_nombre.grid(row=6, column=1, padx=5, pady=2)

        tk.Label(frame, text="Kilos:").grid(row=7, column=0, sticky="e", padx=20, pady=20)
        self.entry_recip_kilos = tk.Entry(frame)
        self.entry_recip_kilos.grid(row=7, column=1, padx=5, pady=2)

        tk.Label(frame, text="% incremento:").grid(row=8, column=0, sticky="e", padx=20, pady=20)
        self.entry_recip_incremento = tk.Entry(frame)
        self.entry_recip_incremento.grid(row=8, column=1, padx=5, pady=2)

        tk.Button(frame, text="Agregar recipiente", command=self.agregar_recipiente).grid(
            row=9, column=0, columnspan=2, pady=5)

        #Para Armar el cuadrito de pote
        tk.Label(frame, text="Nuevo pote", font=("Arial", 10, "bold")).grid(
            row=10, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 0))

        tk.Label(frame, text="Sabor:").grid(row=11, column=0, sticky="e", padx=5)
        self.combo_pote_sabor = ttk.Combobox(frame, state="readonly", width=25)
        self.combo_pote_sabor.grid(row=11, column=1, padx=5, pady=2)

        tk.Label(frame, text="Fecha (AAAA-MM-DD):").grid(row=12, column=0, sticky="e", padx=5)
        self.entry_pote_fecha = tk.Entry(frame)
        self.entry_pote_fecha.grid(row=12, column=1, padx=5, pady=2)

        tk.Button(frame, text="Agregar pote", command=self.agregar_pote).grid(
            row=13, column=0, columnspan=2, pady=5)

    #Pestaña registro de venta
    def _armar_tab_ventas(self):
        frame = self.tab_ventas

        tk.Label(frame, text="Pote:").grid(row=0, column=0, sticky="e", padx=20, pady=20)
        self.combo_venta_pote = ttk.Combobox(frame, state="readonly", width=30)
        self.combo_venta_pote.grid(row=0, column=1, padx=20, pady=20)

        tk.Label(frame, text="Recipiente:").grid(row=1, column=0, sticky="e", padx=20)
        self.combo_venta_recipiente = ttk.Combobox(frame, state="readonly", width=30)
        self.combo_venta_recipiente.grid(row=1, column=1, padx=5)

        tk.Button(frame, text="Registrar venta", command=self.registrar_venta).grid(
            row=2, column=0, columnspan=2, pady=15)

        tk.Button(frame, text="Actualizar listas", command=self.refrescar_combos).grid(
            row=3, column=0, columnspan=2)

    #Reportes
    def _armar_tab_reportes(self):
        frame = self.tab_reportes
        botones = [
            ("Recaudación total", self.mostrar_recaudacion_total),
            ("Pote más servido", self.mostrar_pote_mas_servido),
            ("Pote menos servido", self.mostrar_pote_menos_servido),
            ("Pote más recaudado", self.mostrar_pote_mas_recaudado),
            ("Sabor más vendido", self.mostrar_sabor_mas_vendido),
            ("Sabor con más ganancia", self.mostrar_sabor_mas_recaudado),
            ("Sabor con más kilos vendidos", self.mostrar_sabor_mas_kilos_vendidos),
            ("Sabor con menos kilos vendidos", self.mostrar_sabor_menos_kilos_vendidos),
            ("Recipiente más solicitado", self.mostrar_recipiente_mas_solicitado),
            ("% de venta por sabor", self.mostrar_porcentaje_venta_por_sabor),
            ("% de recaudación por sabor", self.mostrar_porcentaje_recaudacion_por_sabor),
            ("% de venta por pote", self.mostrar_porcentaje_venta_por_pote),
            ("% de recaudación por pote", self.mostrar_porcentaje_recaudacion_por_pote),
        ]
        for i, (texto, comando) in enumerate(botones):
            tk.Button(frame, text=texto, command=comando, width=32).grid(
                row=i, column=0, padx=10, pady=2)

    #Acciones para agregar
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
            self.refrescar_combos()
        except ValueError:
            messagebox.showerror("Error", "Verificá los datos del sabor (precio numérico, campos completos).")

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
            messagebox.showerror("Error", "Verificá los datos del recipiente (kilos y % numéricos, nombre completo).")

    def agregar_pote(self):
        idx = self.combo_pote_sabor.current()
        if idx < 0:
            messagebox.showerror("Error", "Elegí un sabor para el pote.")
            return
        fecha = self.entry_pote_fecha.get().strip()
        if not fecha:
            messagebox.showerror("Error", "Ingresá la fecha de incorporación.")
            return
        sabor = self.heladeria.sabores[idx]
        nuevo_id = len(self.heladeria.potes) + 1
        pote = Pote(nuevo_id, sabor, fecha)
        self.heladeria.agregar_pote(pote)
        messagebox.showinfo("Pote agregado", str(pote))
        self.entry_pote_fecha.delete(0, tk.END)
        self.refrescar_combos()

    #Venta
    def refrescar_combos(self):
        self.combo_pote_sabor["values"] = [str(s) for s in self.heladeria.sabores]
        self.combo_venta_pote["values"] = [str(p) for p in self.heladeria.potes]
        self.combo_venta_recipiente["values"] = [str(r) for r in self.heladeria.recipientes]

    def registrar_venta(self):
        idx_pote = self.combo_venta_pote.current()
        idx_recip = self.combo_venta_recipiente.current()
        if idx_pote < 0 or idx_recip < 0:
            messagebox.showerror("Error", "Elegí un pote y un recipiente.")
            return
        pote = self.heladeria.potes[idx_pote]
        recipiente = self.heladeria.recipientes[idx_recip]
        venta = self.heladeria.vender(pote, recipiente)
        messagebox.showinfo("Venta registrada", str(venta))
        self.refrescar_combos()

    #Muestra de reportes
    def mostrar_recaudacion_total(self):
        total = self.heladeria.recaudacion_total()
        messagebox.showinfo("Recaudación total", f"${total:.2f}")

    def mostrar_pote_mas_servido(self):
        pote = self.heladeria.pote_mas_servido()
        messagebox.showinfo("Pote más servido", f"{pote}")

    def mostrar_pote_menos_servido(self):
        pote = self.heladeria.pote_menos_servido()
        messagebox.showinfo("Pote menos servido", f"{pote}")

    def mostrar_pote_mas_recaudado(self):
        pote = self.heladeria.pote_mas_recaudado()
        messagebox.showinfo("Pote más recaudado", f"{pote}")

    def mostrar_sabor_mas_vendido(self):
        sabor = self.heladeria.sabor_mas_vendido()
        messagebox.showinfo("Sabor más vendido", f"{sabor}")

    def mostrar_sabor_mas_recaudado(self):
        sabor = self.heladeria.sabor_mas_recaudado()
        messagebox.showinfo("Sabor con más ganancia", f"{sabor}")

    def mostrar_sabor_mas_kilos_vendidos(self):
        sabor = self.heladeria.sabor_mas_kilos_vendidos()
        messagebox.showinfo("Sabor con más kilos vendidos", f"{sabor}")

    def mostrar_sabor_menos_kilos_vendidos(self):
        sabor = self.heladeria.sabor_menos_kilos_vendidos()
        messagebox.showinfo("Sabor con menos kilos vendidos", f"{sabor}")

    def mostrar_recipiente_mas_solicitado(self):
        recipiente = self.heladeria.recipiente_mas_solicitado()
        messagebox.showinfo("Recipiente más solicitado", f"{recipiente}")

    def mostrar_porcentaje_venta_por_sabor(self):
        datos = self.heladeria.porcentaje_venta_por_sabor()
        texto = "\n".join(f"{s}: {p:.1f}%" for s, p in datos.items())
        messagebox.showinfo("% de venta por sabor", texto or "Sin ventas registradas")

    def mostrar_porcentaje_recaudacion_por_sabor(self):
        datos = self.heladeria.porcentaje_recaudacion_por_sabor()
        texto = "\n".join(f"{s}: {p:.1f}%" for s, p in datos.items())
        messagebox.showinfo("% de recaudación por sabor", texto or "Sin ventas registradas")

    def mostrar_porcentaje_venta_por_pote(self):
        datos = self.heladeria.porcentaje_venta_por_pote()
        texto = "\n".join(f"Pote {id_pote}: {p:.1f}%" for id_pote, p in datos.items())
        messagebox.showinfo("% de venta por pote", texto or "Sin ventas registradas")

    def mostrar_porcentaje_recaudacion_por_pote(self):
        datos = self.heladeria.porcentaje_recaudacion_por_pote()
        texto = "\n".join(f"Pote {id_pote}: {p:.1f}%" for id_pote, p in datos.items())
        messagebox.showinfo("% de recaudación por pote", texto or "Sin ventas registradas")

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