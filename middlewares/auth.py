from functools import wraps
import os
from flask import g, redirect, render_template, request, session
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from pymongo import MongoClient
from errors.error import Unauthorized

db_url = os.getenv("MONGO_URI")
client = MongoClient(db_url)
db = client.backend
User = client.backend.users

def authorized(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:            
            verify_jwt_in_request()

            email = get_jwt_identity()
            if not email:
                raise Unauthorized("Invalid token")
            
            user = User.find_one({"email": email}, {"_id": 1, "email": 1, "phone": 1})
            if not user:
                raise Unauthorized("User not found ")
            g.user = user
            
            return f(*args, **kwargs)
        except Exception as e:
            raise Exception(e)            
    return decorated
    