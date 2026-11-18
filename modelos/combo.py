class Combo:
    """Pedido sugerido: al elegirlo se carga solo el pote, los sabores, los agregados y las salsas.

    Puede tener un descuento (en %) que se aplica si se cobra tal cual.
    """

    def __init__(self, id, nombre, descripcion, recipiente, sabores, extras=None, salsas=None,
                 descuento_pct: float = 0.0):
        if not str(nombre).strip():
            raise ValueError("El combo necesita un nombre.")
        if not sabores:
            raise ValueError("El combo necesita al menos un sabor.")
        if len(sabores) > recipiente.max_sabores:
            raise ValueError(f"{recipiente.nombre} permite hasta {recipiente.max_sabores} sabores.")
        descuento_pct = float(descuento_pct)
        if not 0 <= descuento_pct < 100:
            raise ValueError("El descuento tiene que estar entre 0% y 99%.")
        self.id = id
        self.nombre = str(nombre).strip()
        self.descripcion = descripcion
        self.recipiente = recipiente
        self.sabores = list(sabores)
        self.extras = [(extra, int(cant)) for extra, cant in (extras or []) if int(cant) > 0]
        self.salsas = list(salsas or [])
        self.descuento_pct = descuento_pct

    def tiene_descuento(self):
        return self.descuento_pct > 0

    def nombres_sabores(self):
        return ", ".join(s.nombre for s in self.sabores)

    def __str__(self):
        return f"{self.nombre}: {self.recipiente.nombre} de {self.nombres_sabores()}"
