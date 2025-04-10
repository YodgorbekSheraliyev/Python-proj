from http.client import HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, g, jsonify, make_response, redirect, request, render_template, flash, url_for
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
)
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import dotenv
import os
import datetime

from errors.error import Unauthorized
from middlewares.auth import authorized
from models.user import User
from models.product import Product
from models.cart import Cart

# Load environment variables
dotenv.load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')   # For flash messages
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'fallback-jwt-secret')     # For JWT signing
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=15)
app.config['JWT_TOKEN_LOCATION'] = ['cookies'] 
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_COOKIE_SECURE'] = False 
app.config['JWT_COOKIE_SAMESITE'] = 'Strict'

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# MongoDB setup
db_url = os.getenv('MONGO_URI')
client = MongoClient(db_url)
db = client.backend


@app.context_processor
def global_user():
    try:
        verify_jwt_in_request()
        user=get_jwt_identity()
    except:
        user=None
    return dict(user=user)

# Routes
@app.route('/')
def home():
    return redirect('/products')

@app.route('/auth/login', methods=['GET'])
def get_login():
    return render_template('login.html', title='Login', hide_nav_footer=True)

@app.route('/auth/login', methods=['POST'])
def post_login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not (email and password):
        flash('Email and password are required', 'error')
        return redirect('/auth/login')

    user = db.users.find_one({'email': email})
    if not user: 
        flash("This user has not registered yet", "error")
        return redirect(url_for('get_login'))
    if not bcrypt.check_password_hash(user['password'], password):
        flash('Invalid password', 'error')
        return redirect(url_for("get_login"))

    with app.app_context():
        access_token = create_access_token(identity=email)
    response = make_response(redirect('/products'))
    set_access_cookies(response, access_token)
    flash('Logged in successfully', 'success')
    return response

@app.route('/auth/register', methods=['GET'])
def get_register():
    return render_template('register.html', title='Register', hide_nav_footer=True)

@app.route('/auth/register', methods=['POST'])
def register_user():
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if not (first_name and last_name and email and phone and password and password2):
        flash('All fields are required', 'error')
        return redirect('/auth/register')

    if password != password2:
        flash('Passwords do not match', 'error')
        return redirect('/auth/register')

    existing_user = db.users.find_one({'email': email})
    if existing_user:
        flash('Email already registered', 'error')
        return redirect('/auth/register')

    user = User(db, first_name, last_name, email, phone, password)
    user_id = user.save()
    with app.app_context():
        access_token = create_access_token(identity=email)
        print(access_token)
    response = make_response(redirect('/products'))
    set_access_cookies(response, access_token)
    flash('Registration successful', 'success')
    return response

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    response = make_response(redirect('/products'))
    unset_jwt_cookies(response)
    flash('Logged out successfully', 'success')
    return response

@app.route('/products')
def get_products():
    products = Product.get_all_products(db)
    products_list = [{**product, '_id': str(product['_id'])} for product in products]
    return render_template('home.html', products=products_list)

@app.route('/products/<id>')
def get_product(id):
    try:
        product = Product.get_product_by_id(db, id)
        if not product:
            return render_template('404.html', error='Product Not Found'), 404
        product['_id'] = str(product['_id'])
        return render_template('product.html', product=product)
    except InvalidId:
        return render_template('404.html', error='Invalid Product ID'), 400
    
# @app.post('/products/buy/<id>')
# def buy_product(id):
#     pass

@app.get('/cart')
@authorized
def get_cart():
    identity = get_jwt_identity()
    user = g.get('user')
    print(user)
    cart = Cart(db, user['_id'])
    cart_data = cart.get_cart()
    
    # Get product details for each item in cart
    cart_items = []
    for item in cart_data['items']:
        product = Product.get_product_by_id(db, item['product_id'])
        if product:
            product['_id'] = str(product['_id'])
            cart_items.append({
                'product': product,
                'quantity': item['quantity']
            })
    
    return render_template('cart.html', 
                         cart_items=cart_items,
                         total=cart_data['total'],
                         username=user['email'])

@app.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    identity = get_jwt_identity()
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    cart = Cart(db, identity['user_id'])
    cart.add_item(product_id, quantity)
    
    flash('Item added to cart', 'success')
    return redirect('/cart')

@app.route('/cart/remove/<product_id>', methods=['POST'])
@jwt_required()
def remove_from_cart(product_id):
    identity = get_jwt_identity()
    cart = Cart(db, identity['user_id'])
    cart.remove_item(product_id)
    
    flash('Item removed from cart', 'success')
    return redirect('/cart')

@app.route('/cart/update', methods=['POST'])
@jwt_required()
def update_cart():
    identity = get_jwt_identity()
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    cart = Cart(db, identity['user_id'])
    cart.update_quantity(product_id, quantity)
    
    flash('Cart updated', 'success')
    return redirect('/cart')

# Error handlers

@app.errorhandler(Unauthorized)
def handle_unauthorized(e):
    return render_template("404.html", error=e.message), 401

@app.errorhandler(HTTPException)
def handle_http_error(e):
    return render_template("404.html", error=e.description), e.code

@app.errorhandler(Exception)
def handle_generic_error(e):
    return render_template("404.html", error=f"Something went wrong. \nError: {e}"), 500


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv('PORT', 5000))