class Sabor:
    def __init__(self, id, nombre, elaboracion, precio_por_kilo):
        self.id = id
        self.nombre = nombre
        self.elaboracion = elaboracion  
        self.precio_por_kilo = precio_por_kilo

    def __str__(self):
        return f"{self.nombre} (${self.precio_por_kilo}/kg, {self.elaboracion})"