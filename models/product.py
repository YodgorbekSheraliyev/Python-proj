class Product:
    def __init__(self, name, description, price, amount, images=[]):
        self.name = name
        self.description = description
        self.price = price
        self.amount = amount
        self.images = images