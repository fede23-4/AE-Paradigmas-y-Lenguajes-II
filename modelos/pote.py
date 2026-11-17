class Pote:
    STOCK_MINIMO_KG = 1.0

    def __init__(self, id, sabor, fecha_incorporacion, stock_kg: float = 5.0):
        self.id = id
        self.sabor = sabor
        self.fecha_incorporacion = fecha_incorporacion
        self.stock_kg = float(stock_kg)
        self.kilos_servidos = 0.0
        self.dinero_recaudado = 0.0

    def puede_servir(self, kilos: float) -> bool:
        return round(self.stock_kg - float(kilos), 6) >= self.STOCK_MINIMO_KG

    def registrar_venta(self, kilos, dinero):
        self.stock_kg -= float(kilos)
        self.kilos_servidos += float(kilos)
        self.dinero_recaudado += float(dinero)

    def reponer_stock(self, kilos: float):
        kilos_val = float(kilos)
        if kilos_val <= 0:
            raise ValueError("La cantidad a reponer debe ser mayor a 0 kg.")
        self.stock_kg += kilos_val

    def __str__(self):
        return (f"Pote #{self.id} de {self.sabor.nombre} - "
                f"Stock: {self.stock_kg:.2f} kg, Servidos: {self.kilos_servidos:.2f} kg, "
                f"Recaudado: ${self.dinero_recaudado:.2f}")

