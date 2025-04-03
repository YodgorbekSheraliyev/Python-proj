class Order: 
    def __init__(self, user: str, products: list[dict]):
        self.user = user
        self.products = products