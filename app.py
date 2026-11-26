# app.py
import os
import sqlite3
from flask import Flask, request, redirect, url_for, make_response, flash, render_template

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = 'a-very-secret-and-unique-key'

@app.route('/')
def home():
    logged_in_user = request.cookies.get('username')
    current_user = None

    conn = get_db_connection()
    
    if logged_in_user:
        query = "SELECT * FROM users WHERE username = ?"
        current_user = conn.execute(query, (logged_in_user,)).fetchone()

    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    # Jinja2 templates escape every {{ value }}, so user data cannot add HTML or scripts.
    return render_template('home.html', current_user=current_user, products=products)

@app.route('/about')
def about():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>About Us</title>
        <link rel="stylesheet" href="{ url_for('static', filename='css/style.css') }">
    </head>
    <body>
        <h1>About Our Shop</h1>
        <p>This is the page where we talk about ourselves.</p>
        <a href="/">Go back home</a>
    </body>
    </html>
    """
    return html

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
            query = "INSERT INTO users (username, password) VALUES (?, ?)"
            conn.execute(query, (username, password))
            conn.commit()
        except conn.IntegrityError:
            flash("Username already exists. Please choose another.")
            conn.close()
            return redirect(url_for('register'))
        
        conn.close()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register</title>
        <link rel="stylesheet" href="{ url_for('static', filename='css/style.css') }">
    </head>
    <body>
        <h1>Register for an Account</h1>
        <form method="post">
            <label for="username">Username</label>
            <input type="text" name="username" id="username" required>
            <br>
            <label for="password">Password</label>
            <input type="password" name="password" id="password" required>
            <br>
            <button type="submit">Register</button>
        </form>
    </body>
    </html>
    """
    return html

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        user = conn.execute(query, (username, password)).fetchone()
        conn.close()

        if user:
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('username', user['username'])
            return resp
        else:
            flash('Incorrect username or password.')
            return redirect(url_for('login'))

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <link rel="stylesheet" href="{ url_for('static', filename='css/style.css') }">
    </head>
    <body>
        <h1>Login</h1>
        <form method="post">
            <label for="username">Username</label>
            <input type="text" name="username" id="username" required>
            <br>
            <label for="password">Password</label>
            <input type="password" name="password" id="password" required>
            <br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
    return html

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('username')
    flash('You have been logged out.')
    return resp

@app.route('/become_seller', methods=('GET', 'POST'))
def become_seller():
    logged_in_user = request.cookies.get('username')
    if not logged_in_user:
        flash("You must be logged in to do this.")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        query = "UPDATE users SET is_seller = 1 WHERE username = ?"
        conn.execute(query, (logged_in_user,))
        conn.commit()
        conn.close()
        flash("Congratulations, you are now a seller!")
        return redirect(url_for('home'))

    html = f"""
    <!DOCTYPE html><html><body>
        <h1>Become a Seller</h1>
        <p>Click the button below to upgrade your account to a seller account.</p>
        <form method="post">
            <button type="submit">Become a Seller</button>
        </form>
        <br>
        <a href="{url_for('home')}">Go back</a>
    </body></html>
    """
    conn.close()
    return html

@app.route('/add', methods=('GET', 'POST'))
def add_product():
    logged_in_user = request.cookies.get('username')
    if not logged_in_user:
        flash("You need to be logged in.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (logged_in_user,)).fetchone()
    
    if not (user['is_seller'] or user['is_admin']):
        flash("You must be a seller or admin to add products.")
        conn.close()
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        query = "INSERT INTO products (name, price, description, seller_name) VALUES (?, ?, ?, ?)"
        conn.execute(query, (name, price, description, logged_in_user))
        conn.commit()
        conn.close()
        
        flash("Product listed successfully!")
        return redirect(url_for('home'))

    conn.close()
    html = """
    <!DOCTYPE html><html><body>
    <h1>List a New Product</h1>
    <form method="post">
        <label for="name">Product Name</label>
        <input type="text" name="name" id="name" required>
        <br>
        <label for="price">Price</label>
        <input type="number" step="0.01" name="price" id="price" required>
        <br>
        <label for="description">Description</label>
        <textarea name="description" id="description" required></textarea>
        <br>
        <button type="submit">List Product</button>
    </form>
    <br><a href="/">Cancel</a>
    </body></html>
    """
    return html

@app.route('/edit/<int:product_id>', methods=('GET', 'POST'))
def edit_product(product_id):
    logged_in_user = request.cookies.get('username')
    if not logged_in_user:
        flash("You need to be logged in.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_query = "SELECT * FROM users WHERE username = ?"
    user = conn.execute(user_query, (logged_in_user,)).fetchone()
    
    if not (user['is_seller'] or user['is_admin']):
        flash("You must be a seller or admin to manage products.")
        conn.close()
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        update_query = "UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?"
        conn.execute(update_query, (name, price, description, product_id))
        conn.commit()
        conn.close()
        
        flash("Product updated successfully!")
        return redirect(url_for('home'))

    product_query = f"SELECT * FROM products WHERE id = {product_id}"
    product = conn.execute(product_query).fetchone()
    conn.close()

    if not product:
        flash("Product not found.")
        return redirect(url_for('home'))

    return render_template('edit.html', product=product)

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    logged_in_user = request.cookies.get('username')
    if not logged_in_user:
        flash("You need to be logged in.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_query = "SELECT * FROM users WHERE username = ?"
    user = conn.execute(user_query, (logged_in_user,)).fetchone()
    
    if not (user['is_seller'] or user['is_admin']):
        flash("You must be a seller or admin to manage products.")
        conn.close()
        return redirect(url_for('home'))

    delete_query = f"DELETE FROM products WHERE id = {product_id}"
    conn.execute(delete_query)
    conn.commit()
    conn.close()
    
    flash("Product deleted successfully.")
    return redirect(url_for('home'))

@app.route('/product/<int:product_id>', methods=('GET', 'POST'))
def product_page(product_id):
    logged_in_user = request.cookies.get('username')
    current_user = None
    
    conn = get_db_connection()
    
    if logged_in_user:
        user_query = "SELECT * FROM users WHERE username = ?"
        current_user = conn.execute(user_query, (logged_in_user,)).fetchone()

    if request.method == 'POST':
        if not current_user:
            flash("You must be logged in to leave a review.")
            conn.close()
            return redirect(url_for('login'))
        
        comment = request.form['comment']
        query = "INSERT INTO reviews (product_id, author_name, comment) VALUES (?, ?, ?)"
        conn.execute(query, (product_id, logged_in_user, comment))
        conn.commit()
        flash("Your review has been submitted!")
        
        conn.close()
        return redirect(url_for('product_page', product_id=product_id))

    product_query = f'SELECT * FROM products WHERE id = {product_id}'
    product = conn.execute(product_query).fetchone()
    
    reviews_query = f'SELECT * FROM reviews WHERE product_id = {product_id}'
    reviews = conn.execute(reviews_query).fetchall()
    conn.close() 

    if not product:
        flash("Product not found.")
        return redirect(url_for('home'))

    can_edit = bool(current_user) and (
        current_user['is_admin'] or current_user['username'] == product['seller_name']
    )
    return render_template('product.html', product=product, reviews=reviews,
                           can_edit=can_edit, logged_in_user=logged_in_user)

@app.route('/admin')
def admin_panel():
    logged_in_user = request.cookies.get('username')
    if not logged_in_user:
        flash("You must be logged in to view this page.")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (logged_in_user,)).fetchone()
    
    if not user or not user['is_admin']:
        flash("You are not authorised to view this page.")
        conn.close()
        return redirect(url_for('home'))

    users = conn.execute('SELECT id, username FROM users').fetchall()
    products = conn.execute('SELECT id, name FROM products').fetchall()
    conn.close()

    return render_template('admin.html', user=user, users=users, products=products)

if __name__ == '__main__':
    # Debug mode only when FLASK_DEBUG=1 is set. It is off by default.
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
    