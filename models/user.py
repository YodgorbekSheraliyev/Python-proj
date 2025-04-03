from pymongo import MongoClient
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User:
    def __init__(self, db, first_name, last_name, email, phone, password, orders=[]):
        self.db = db
        self.collection = db.users
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.password = bcrypt.generate_password_hash(password)
        self.orders = orders

    def save(self):
        user_data = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "password": self.password,
            "orders": self.orders
        }
        return self.collection.insert_one(user_data).inserted_id
    
    # @staticmethod
    # def find_user_by_email(email):