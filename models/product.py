from pymongo import MongoClient
from bson import ObjectId

class Product:
    def __init__(self, db, name, description, price, image_url, stock, category):
        self.db = db
        self.collection = db.products
        self.name = name
        self.description = description
        self.price = price
        self.image_url = image_url
        self.stock = stock
        self.category = category

    def save(self):
        product_data = {
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
            "stock": self.stock,
            "category": self.category
        }
        return self.collection.insert_one(product_data).inserted_id

    @staticmethod
    def get_all_products(db):
        return list(db.products.find())

    @staticmethod
    def get_product_by_id(db, product_id):
        try:
            return db.products.find_one({'_id': ObjectId(product_id)})
        except:
            return None

    @staticmethod
    def update_stock(db, product_id, quantity):
        try:
            return db.products.update_one(
                {'_id': ObjectId(product_id)},
                {'$inc': {'stock': -quantity}}
            )
        except:
            return None