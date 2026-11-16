from modelos.pote import Pote
class Venta:
    def __init__(self, potes, recipiente):
        if isinstance(potes, Pote):
            self.potes = [potes]
        else:
            self.potes = list(potes)
        if not self.potes:
            raise ValueError("Elegí al menos un sabor.")
        if len(self.potes) > recipiente.max_sabores:
            raise ValueError(
                f"{recipiente.nombre} permite hasta {recipiente.max_sabores} sabores."
            )
        self.pote = self.potes[0]
        self.recipiente = recipiente
        self.kilos = recipiente.kilos
        # El precio y los aportes se calculan por polimorfismo (sin ifs por tipo)
        self.aportes = recipiente.calcular_aportes(self.potes)
        self.precio_total = recipiente.calcular_precio_total(self.potes)

    def calcular_precio_total(self):
        return self.precio_total

    def calcular_kilos(self):
        return self.kilos

    def nombres_sabores(self):
        return ", ".join(p.sabor.nombre for p in self.potes)

    def __str__(self):
        return (f"Venta de {self.kilos:g} kg de {self.nombres_sabores()} "
                f"en {self.recipiente.nombre}: ${self.calcular_precio_total():.2f}")