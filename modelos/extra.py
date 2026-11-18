class Extra:
    """Agregado que se suma a una venta (cucurucho, vasito, etc.) y se cobra por unidad."""

    def __init__(self, id, nombre, precio: float = 0.0):
        self.id = id
        self.nombre = nombre
        self.precio = float(precio)

    def calcular_precio(self, cantidad: int) -> float:
        return self.precio * int(cantidad)

    def __str__(self):
        return f"{self.nombre} (${self.precio:g} c/u)"


class Salsa(Extra):
    """Salsa para el helado: siempre sin costo (polimorfismo sobre calcular_precio)."""

    def __init__(self, id, nombre, precio: float = 0.0):
        super().__init__(id, nombre, 0.0)

    def calcular_precio(self, cantidad: int = 1) -> float:
        return 0.0

    def __str__(self):
        return f"Salsa de {self.nombre.lower()}"
