class Recipiente:
    def __init__(self, id, nombre, kilos: float, porcentaje_incremento: float = 0.0, max_sabores: int = 4):
        self.id = id
        self.nombre = nombre
        self.kilos = float(kilos)
        self.porcentaje_incremento = float(porcentaje_incremento)
        self.max_sabores = max_sabores

    def calcular_aportes(self, potes):
        """Reparte los kilos en partes iguales y calcula el aporte en $ de cada sabor."""
        cantidad = len(potes)
        kilos_por_sabor = self.kilos / cantidad
        factor_recargo = 1.0 + (self.porcentaje_incremento / 100.0)
        return [
            (pote, kilos_por_sabor, float(kilos_por_sabor * pote.sabor.precio_por_kilo * factor_recargo))
            for pote in potes
        ]

    def calcular_precio_total(self, potes) -> float:
        return float(sum(dinero for _, _, dinero in self.calcular_aportes(potes)))

    def etiqueta_combo(self):
        return (f"{self.nombre} · {self.kilos:g} kg "
                f"(+{self.porcentaje_incremento:g}% · hasta {self.max_sabores} sabores)")

    def detalle_precio(self, potes):
        gramos_por_sabor = (self.kilos * 1000) / len(potes)
        return (f"{len(potes)} sabor(es) ({gramos_por_sabor:g} g c/u) · "
                f"{self.kilos:g} kg total (+{self.porcentaje_incremento:g}%)")

    def texto_peso(self):
        return f"{self.kilos:g} kg" if self.kilos >= 1 else f"{self.kilos * 1000:g} g"

    def prefijo_precio(self):
        """El precio por peso depende de los sabores: se muestra 'desde'."""
        return "desde "

    def descripcion_precio(self):
        if self.porcentaje_incremento:
            return f"+{self.porcentaje_incremento:g}% sobre el kilo"
        return "precio por kilo"

    def __str__(self):
        return f"{self.nombre} ({self.kilos:g} kg)"


class PresentacionPorPorcion(Recipiente):
    """Presentación por porción a precio fijo (Cucurucho dulce, Vasito)."""
    def __init__(self, id, nombre, kilos: float, precio_fijo: float = 5000.0, max_sabores: int = 2):
        super().__init__(id, nombre, kilos, porcentaje_incremento=0.0, max_sabores=max_sabores)
        self.precio_fijo = float(precio_fijo)

    def calcular_aportes(self, potes):
        cantidad = len(potes)
        kilos_por_sabor = self.kilos / cantidad
        dinero_por_sabor = float(self.precio_fijo / cantidad)
        return [(pote, kilos_por_sabor, dinero_por_sabor) for pote in potes]

    def calcular_precio_total(self, potes) -> float:
        return float(self.precio_fijo)

    def etiqueta_combo(self):
        gramos = self.kilos * 1000
        return (f"{self.nombre} · {gramos:g} g "
                f"(${self.precio_fijo:,.0f} fijos · hasta {self.max_sabores} sabores)".replace(",", "."))

    def prefijo_precio(self):
        return ""

    def descripcion_precio(self):
        return "precio fijo"

    def detalle_precio(self, potes):
        gramos_por_sabor = (self.kilos * 1000) / len(potes)
        precio_txt = f"${self.precio_fijo:,.0f}".replace(",", ".")
        return f"{len(potes)} sabor(es) ({gramos_por_sabor:g} g c/u) · Precio fijo {precio_txt}"
