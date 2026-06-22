from flask import Flask, render_template, redirect, url_for, request
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/pictures'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            img TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Simple way to check if it's your sister (you can change this later)
def is_seller():
    # For testing: add ?seller=1 to the URL when your sister uses it
    return request.args.get("seller") == "1"

@app.route("/")
def home():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products, is_seller=is_seller())

@app.route("/product/<int:pid>")
def product_details(pid):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    conn.close()

    return render_template("product.html", product=product)

@app.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    conn = get_db_connection()
    conn.execute('''INSERT INTO cart (product_id) VALUES (?)''', (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("cart_view"))

@app.route("/cart")
def cart_view():
    conn = get_db_connection()

    cart_items_raw = conn.execute('SELECT * FROM cart').fetchall()

    cart_items = []
    for item in cart_items_raw:
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (item["product_id"],)
        ).fetchone()

        if product:
            cart_items.append({
                "cart_id": item["id"],
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "img": product["img"]
            })

    conn.close()

    total = sum(item["price"] for item in cart_items)

    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/sell", methods=["GET", "POST"])
def sell():
    if not is_seller():
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        price = float(request.form.get("price", 0))
        image = request.files.get("img")

        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_path = f"/static/pictures/{filename}"
        else:
            img_path = "/static/pictures/default.jpg"

        conn = get_db_connection()
        conn.execute("INSERT INTO products (name, price, img) VALUES (?, ?, ?)",
                     (name, price, img_path))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("sell.html")


@app.route("/buy/<int:pid>")
def buy(pid):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()

    if product:
        # Here you can add logic later (e.g. create order, reduce stock, etc.)
        conn.execute("INSERT INTO cart (product_id) VALUES (?)", (pid,))
        conn.commit()
        conn.close()
        return redirect(url_for("cart_view"))
    else:
        conn.close()
        return "Product not found", 404


@app.route("/buyer")
def buyer_portal():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("buyer.html", products=products)



@app.route("/seller")
def seller_portal():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()   # Later you can filter by user
    conn.close()
    return render_template("seller.html", products=products, title="Seller Portal")

@app.route("/delete_product/<int:pid>")
def delete_product(pid):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))

@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    conn= get_db_connection()
    conn.execute('''DELETE FROM cart WHERE id = ?''', (cart_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("cart_view"))

if __name__ == "__main__":
    app.run(debug=True)

