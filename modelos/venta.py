from modelos.pote import Pote


class Venta:
    def __init__(self, potes, recipiente, extras=None, salsas=None, descuento_pct=0.0, combo=None):
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
        # Agregados: lista de (Extra, cantidad). Salsas: lista de Salsa (sin costo).
        self.extras = [(extra, int(cant)) for extra, cant in (extras or []) if int(cant) > 0]
        self.salsas = list(salsas or [])
        # Descuento (por ejemplo, de un combo): se aplica parejo a todo lo cobrado,
        # así las estadísticas por sabor y por pote reflejan lo que realmente entró.
        self.combo = combo
        self.descuento_pct = float(descuento_pct)
        factor = 1.0 - self.descuento_pct / 100.0

        # El precio y los aportes se calculan por polimorfismo (sin ifs por tipo)
        self.aportes = [(pote, kilos, dinero * factor)
                        for pote, kilos, dinero in recipiente.calcular_aportes(self.potes)]
        precio_helado = recipiente.calcular_precio_total(self.potes)
        precio_extras = float(
            sum(extra.calcular_precio(cant) for extra, cant in self.extras)
            + sum(salsa.calcular_precio(1) for salsa in self.salsas)
        )
        self.subtotal = precio_helado + precio_extras        # sin descuento
        self.precio_helado = precio_helado * factor
        self.precio_extras = precio_extras * factor
        self.precio_total = self.precio_helado + self.precio_extras
        self.monto_descuento = self.subtotal - self.precio_total

    def calcular_precio_total(self):
        return self.precio_total

    def calcular_kilos(self):
        return self.kilos

    def nombres_sabores(self):
        return ", ".join(p.sabor.nombre for p in self.potes)

    def descripcion_agregados(self):
        partes = []
        if self.combo:
            partes.append(self.combo.nombre + (f" (-{self.descuento_pct:g}%)"
                                               if self.descuento_pct else ""))
        elif self.descuento_pct:
            partes.append(f"Descuento {self.descuento_pct:g}%")
        partes += [f"{cant}× {extra.nombre}" for extra, cant in self.extras]
        if self.salsas:
            partes.append("Salsa de " + ", ".join(s.nombre.lower() for s in self.salsas))
        return " · ".join(partes)

    def __str__(self):
        return (f"Venta de {self.kilos:g} kg de {self.nombres_sabores()} "
                f"en {self.recipiente.nombre}: ${self.calcular_precio_total():.2f}")
