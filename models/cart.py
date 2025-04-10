from pymongo import MongoClient
from bson import ObjectId

class Cart:
    def __init__(self, db, user_id):
        self.db = db
        self.collection = db.carts
        self.user_id = user_id

    def get_cart(self):
        cart = self.collection.find_one({'user_id': self.user_id})
        if not cart:
            cart = {
                'user_id': self.user_id,
                'items': [],
                'total_price': 0
            }
            self.collection.insert_one(cart)
        return cart

    def add_item(self, product_id, quantity):
        cart = self.get_cart()
        items = cart['items']
        
        # Check if item already exists in cart
        for item in items:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                break
        else:
            items.append({
                'product_id': product_id,
                'quantity': quantity
            })
        
        self.collection.update_one(
            {'user_id': self.user_id},
            {'$set': {'items': items}}
        )
        return self.calculate_total()

    def remove_item(self, product_id):
        cart = self.get_cart()
        items = [item for item in cart['items'] if item['product_id'] != product_id]
        
        self.collection.update_one(
            {'user_id': self.user_id},
            {'$set': {'items': items}}
        )
        return self.calculate_total()

    def update_quantity(self, product_id, quantity):
        cart = self.get_cart()
        items = cart['items']
        
        for item in items:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
        
        self.collection.update_one(
            {'user_id': self.user_id},
            {'$set': {'items': items}}
        )
        return self.calculate_total()

    def calculate_total(self):
        cart = self.get_cart()
        total = 0
        for item in cart['items']:
            product = self.db.products.find_one({'_id': ObjectId(item['product_id'])})
            if product:
                total += product['price'] * item['quantity']
        
        self.collection.update_one(
            {'user_id': self.user_id},
            {'$set': {'total_price': total}}
        )
        return total

    def clear_cart(self):
        self.collection.update_one(
            {'user_id': self.user_id},
            {'$set': {'items': [], 'total_price': 0}}
        )
        