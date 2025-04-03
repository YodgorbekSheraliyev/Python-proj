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
            token = request.headers.get("Authorization")
            if token and token.startswith("Bearer"):
                token = token.split(" ")[1]
            else:
                token = session.get("token")
            if not token:
                raise Unauthorized("Token is missing or invalid")
            
            verify_jwt_in_request()
            decoded = get_jwt_identity()
            user = User.find_one({"email": decoded["email"]}, {"_id": 1, "email": 1, "phone": 1})

            if not user:
                raise Unauthorized("User not found ")
            g.user = user
            
            return f(*args, **kwargs)
        except Exception as e:
            raise Exception(e)            
    return decorated
    