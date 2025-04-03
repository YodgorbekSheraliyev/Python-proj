from turtle import st
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, make_response, redirect, request, render_template, flash, url_for
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
)
from pymongo import MongoClient
import bcrypt
import dotenv
import os
import datetime

from models.user import User

# Load environment variables
dotenv.load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')  # For flash messages
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'fallback-jwt-secret')  # For JWT signing
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=15)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # Store JWT in cookies
app.config['JWT_COOKIE_CSRF_PROTECT'] = True  # Protect against CSRF
app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['JWT_COOKIE_SAMESITE'] = 'Strict'

# Initialize extensions
jwt = JWTManager(app)

# MongoDB setup
db_url = os.getenv('MONGO_URI', 'mongodb://localhost:27017/backend')
client = MongoClient(db_url)
db = client.backend

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
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        flash('Invalid email or password', 'error')
        return redirect('/auth/login')

    # Create JWT and set in cookie
    access_token = create_access_token(identity={'user_id': str(user['_id']), 'email': user['email']})
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

    try:
        user = User(db, first_name, last_name, email, phone, password)
        user_id = user.save()
        access_token = create_access_token(identity={'user_id': str(user_id), 'email': email})
        response = make_response(redirect('/products'))
        set_access_cookies(response, access_token)
        flash('Registration successful', 'success')
        return response
    except Exception as e:
        flash(f'Registration failed: {str(e)}', 'error')
        return redirect('/auth/register')

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    response = make_response(redirect('/products'))
    unset_jwt_cookies(response)
    flash('Logged out successfully', 'success')
    return response

@app.route('/products')
def get_products():
    products = db.products.find()
    products_list = [{**product, '_id': str(product['_id'])} for product in products]
    return render_template('home.html', products=products_list)

@app.route('/products/<id>')
def get_product(id):
    try:
        product = db.products.find_one({'_id': ObjectId(id)})
        if not product:
            return render_template('404.html', error='Product Not Found'), 404
        product['_id'] = str(product['_id'])
        identity = get_jwt_identity()
        username = identity['email'] if identity else None
        return render_template('product.html', product=product, username=username)
    except InvalidId:
        return render_template('404.html', error='Invalid Product ID'), 400

@app.route('/cart')
@jwt_required()
def cart():
    identity = get_jwt_identity()
    user = db.users.find_one({'_id': ObjectId(identity['user_id'])})
    return render_template('cart.html', username=user['email'])

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error='Page Not Found'), 404

@app.errorhandler(401)
def unauthorized(error):
    flash('Please log in to access this page', 'error')
    return redirect('/auth/login')

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html', error='Internal Server Error'), 500

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    flash('Your session has expired. Please log in again.', 'error')
    response = make_response(redirect('/auth/login'))
    unset_jwt_cookies(response)
    return response

@jwt.unauthorized_loader
def unauthorized_callback(error):
    flash('Please log in to access this page', 'error')
    return redirect('/auth/login')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv('PORT', 5000))