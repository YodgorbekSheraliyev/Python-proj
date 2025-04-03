from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, redirect, request, render_template, flash, session, url_for
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, get_current_user, decode_token, jwt_required
from flask_session import Session
import dotenv
import os
from pymongo import MongoClient
from errors.error import Unauthorized
from middlewares.auth import authorized
from models.user import User
import datetime


dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = "Wefewfg43erfe"
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET")
app.config['SESSION_TYPE'] = 'mongodb'
app.config["SESSION_PERMANENT"] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=15)

app.permanent_session_lifetime = datetime.timedelta(weeks=2)

Session(app=app)

jwt  = JWTManager(app)

# Database
db_url = os.getenv("MONGO_URI")
client = MongoClient(db_url)
db = client.backend

# app.secret_key = os.getenv("SESSION_SECRET")
# app.config['SESSION_TYPE'] = 'mongodb'
# Session(app)


@app.get('/')
def home():
    return redirect("/products")
    
@app.get('/auth/login')
def get_login():
    return render_template('login.html', title='Login', hide_nav_footer=True)
    
@app.get('/auth/register')
def get_register():
    return render_template('register.html', title='Register', hide_nav_footer=True)

@app.post('/auth/register')
def register_user():
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    print(first_name, last_name, email, phone, password, password2)
    if not (first_name and last_name and email and phone and password and password2):
        flash("All fields are required", "error")
        return redirect('/auth/register')
    if not (password == password2):
        flash("Password is not the same", "error")
        return redirect('/auth/register')
    
    exist_user = db.users.find_one({"email": email})
    if exist_user:
        flash("Email already registered", "error")
        return redirect('/auth/register')
    
    try:
        user = User(db, first_name, last_name, email, phone, password)
        print(user)
        user_id = user.save()
        token = create_access_token(identity={"user_id":str(user_id), "email": email})
        session['token'] = token
        
        
        return redirect('/products')        
    except Exception as e:
        flash(f"Registration failed: {str(e)}", "error")
        return redirect('/auth/register')
    
        
        

@app.get('/products')
def get_products():
    products = db.products.find()
    products_list = [{**product, "_id": str(product['_id'])} for product in products]
    return render_template("home.html", products=products_list)

@app.get('/products/<id>')
def get_product(id):
    try:
        product = db.products.find_one({"_id": ObjectId(id)})
        if not product:
            return render_template("404.html", error="Product Not Found"), 404
        product["_id"] = str(product["_id"])
        return render_template("product.html", product=product)
    except InvalidId:
        return render_template('404.html', error="Invalid Product Id"), 400
    
    


@app.route('/cart')
@authorized
def cart():
    return render_template('cart.html')
    
@app.errorhandler(404)
def bad_request(error):
    return render_template("404.html", error=error), 404

@app.errorhandler(401)
def unauthorized(error):
    return render_template("404.html", error=error), 401

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("404.html", error=error), 500

app.run(debug=True, port=os.getenv('PORT', 5000))
