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

