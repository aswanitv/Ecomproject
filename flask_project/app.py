import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, jsonify, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")

DB_PATH = os.path.join(os.path.dirname(__file__), "shopuniverse_auth.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Customers (for /login and /register)
        # We store `username` because /login form asks for `username`.
        # Since the register form does not provide username, we set username=email (lowercase).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Example product storage to satisfy "products" + FK relationship requirement
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0,
                description TEXT,
                image_url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE ON UPDATE CASCADE
            )
            """
        )

        # Backfill/compat: add description column if DB already exists without it.
        # SQLite will throw if column exists; we ignore that.
        try:
            conn.execute("ALTER TABLE products ADD COLUMN description TEXT")
        except sqlite3.OperationalError:
            pass

        conn.commit()
    finally:
        conn.close()


def seller_login_required():
    return session.get("seller_id") is not None


def customer_login_required():
    return session.get("user_id") is not None


@app.route("/")
def index():
    # Featured products should be visible to everyone (no seller login required).
    conn = get_db_connection()
    try:
        products = conn.execute(
            """
            SELECT id, name, price, description, image_url, created_at
            FROM products
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT 12
            """
        ).fetchall()
    finally:
        conn.close()

    return render_template("index.html", products=products)


@app.route("/index")
def index2():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if customer_login_required():
        return redirect(url_for("index"))

    if request.method == "POST":
        credential = (request.form.get("email") or request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""

        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (credential,)).fetchone()
        finally:
            conn.close()

        if row is None or not check_password_hash(row["password_hash"], password):
            message = "Invalid username or password."
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": message}), 401
            flash(message, "login_error")
            return redirect(url_for("login"))

        session["user_id"] = row["id"]
        session["username"] = row["username"]
        session["full_name"] = row["full_name"]
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "redirect": url_for("index")})
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = (request.form.get("fullname") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not full_name or not email or not password:
            message = "All fields are required."
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": message}), 400
            flash(message, "register_error")
            return redirect(url_for("register"))

        if password != confirm_password:
            message = "Passwords do not match."
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": message}), 400
            flash(message, "register_error")
            return redirect(url_for("register"))

        username = email
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (full_name, email, username, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, email, username, password_hash, datetime.utcnow().isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            message = "Email or username already registered. Please login."
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": message}), 409
            flash(message, "register_error")
            return redirect(url_for("login"))
        finally:
            conn.close()

        message = "Account created. Please login."
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "message": message, "redirect": url_for("login")})
        flash(message, "register_success")
        return redirect(url_for("login"))

    return render_template("registerhere.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("full_name", None)
    flash("Logged out successfully.", "logout_success")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not customer_login_required():
        flash("Please login to access your dashboard.", "login_error")
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")



@app.route("/payment", methods=["GET", "POST"])
def payment():
    # Uses checkout data stored in session["last_checkout"]
    data = session.get("last_checkout") or {}

    if request.method == "POST":
        # Payment system is mocked for now.
        session["last_payment"] = {
            "payment_method": request.form.get("payment_method"),
            "created_at": datetime.utcnow().isoformat(),
        }
        # Clear checkout details after placing order (optional)
        # data remains for rendering success state.
        return render_template(
            "payment.html",
            success=True,
            product_name=data.get("product_name", ""),
            product_price=data.get("product_price", "0"),
            product_details=data.get("product_details", ""),
            product_image=data.get("product_image", ""),
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            pin_code=data.get("pin_code", ""),
        )

    return render_template(
        "payment.html",
        success=False,
        product_name=data.get("product_name", ""),
        product_price=data.get("product_price", "0"),
        product_details=data.get("product_details", ""),
        product_image=data.get("product_image", ""),
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        city=data.get("city", ""),
        state=data.get("state", ""),
        pin_code=data.get("pin_code", ""),
    )



@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    # Buy Now button should send product info via query string.
    if request.method == "GET":
        product_name = request.args.get("product_name", "")
        product_price = request.args.get("product_price", "0")
        product_details = request.args.get("product_details", "")
        product_image = request.args.get("product_image", "")

        return render_template(
            "checkout.html",
            product_name=product_name,
            product_price=product_price,
            product_details=product_details,
            product_image=product_image,
            full_name="",
            phone="",
            address="",
            city="",
            state="",
            pin_code="",
        )


    # POST: address submission
    product_name = request.form.get("product_name", "")
    product_price = request.form.get("product_price", "0")
    product_details = request.form.get("product_details", "")

    full_name = (request.form.get("full_name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    address = (request.form.get("address") or "").strip()
    city = (request.form.get("city") or "").strip()
    state = (request.form.get("state") or "").strip()
    pin_code = (request.form.get("pin_code") or "").strip()

    # This project doesn't have a real order/payment system yet.
    # We just show the address + order summary then redirect user back to cart.
    # Also capture product_image if provided
    product_image = request.args.get("product_image") or request.form.get("product_image") or ""

    session["last_checkout"] = {
        "product_name": product_name,
        "product_price": product_price,
        "product_details": product_details,
        "product_image": product_image,
        "full_name": full_name,
        "phone": phone,
        "address": address,
        "city": city,
        "state": state,
        "pin_code": pin_code,
        "created_at": datetime.utcnow().isoformat(),
    }

    # After entering shipping details, go to payment selection page.
    return redirect(url_for("payment"))



@app.route("/seller")
def seller():
    return render_template("seller.html")


@app.route("/seller/register", methods=["GET", "POST"])
def seller_register():
    if request.method == "POST":
        full_name = request.form.get("full_name") or request.form.get("fullname") or ""
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or request.form.get("confirm_password_") or ""

        if not full_name or not email or not password:
            flash("All fields are required.", "seller_error")
            return redirect(url_for("seller_register"))

        if password != confirm_password:
            flash("Passwords do not match.", "seller_error")
            return redirect(url_for("seller_register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO sellers (full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (full_name, email, password_hash, datetime.utcnow().isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered. Please login.", "seller_error")
            return redirect(url_for("seller_login"))
        finally:
            conn.close()

        flash("Seller account created. Please login.", "seller_success")
        return redirect(url_for("seller_login"))

    return render_template("seller_register.html")


@app.route("/seller/login", methods=["GET", "POST"])
def seller_login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM sellers WHERE email = ?", (email,)).fetchone()
        finally:
            conn.close()

        if row is None or not check_password_hash(row["password_hash"], password):
            flash("Invalid email or password.", "seller_error")
            return redirect(url_for("seller_login"))

        session["seller_id"] = row["id"]
        session["seller_email"] = row["email"]
        return redirect(url_for("seller_dashboard"))

    return render_template("seller.html")


@app.route("/seller/add_product", methods=["POST"])
def seller_add_product():
    if not seller_login_required():
        flash("Please login to add products.", "seller_error")
        return redirect(url_for("seller_login"))

    name = (request.form.get("name") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    description = (request.form.get("description") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()

    if not name:
        flash("Product name is required.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    try:
        price = float(price_raw) if price_raw else 0.0
    except ValueError:
        flash("Invalid price.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO products (seller_id, name, price, description, image_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.get("seller_id"),
                name,
                price,
                description,
                image_url if image_url else None,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    flash("Product added successfully.", "seller_success")
    return redirect(url_for("seller_dashboard"))


@app.route("/seller/dashboard")
def seller_dashboard():
    if not seller_login_required():
        flash("Please login to access seller dashboard.", "seller_error")
        return redirect(url_for("seller_login"))

    conn = get_db_connection()
    try:
        products = conn.execute(
            """
            SELECT id, name, price, description, image_url, created_at
            FROM products
            WHERE seller_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (session.get("seller_id"),),
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        "seller_dashboard.html",
        seller_email=session.get("seller_email"),
        products=products,
    )


@app.route("/seller/logout")
def seller_logout():
    session.pop("seller_id", None)
    session.pop("seller_email", None)
    flash("Logged out successfully.", "seller_success")
    return redirect(url_for("seller_login"))


@app.route("/seller/edit_product", methods=["POST"])
def seller_edit_product():
    if not seller_login_required():
        flash("Please login to edit products.", "seller_error")
        return redirect(url_for("seller_login"))

    product_id_raw = (request.form.get("product_id") or "").strip()
    name = (request.form.get("name") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    description = (request.form.get("description") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()

    if not product_id_raw.isdigit():
        flash("Invalid product id.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    if not name:
        flash("Product name is required.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    try:
        price = float(price_raw) if price_raw else 0.0
    except ValueError:
        flash("Invalid price.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    product_id = int(product_id_raw)

    conn = get_db_connection()
    try:
        # Ensure the product belongs to this seller
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ? AND seller_id = ?",
            (product_id, session.get("seller_id")),
        ).fetchone()

        if existing is None:
            flash("Product not found.", "seller_error")
            return redirect(url_for("seller_dashboard"))

        conn.execute(
            """
            UPDATE products
            SET name = ?, price = ?, description = ?, image_url = ?
            WHERE id = ? AND seller_id = ?
            """,
            (
                name,
                price,
                description if description else None,
                image_url if image_url else None,
                product_id,
                session.get("seller_id"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    flash("Product updated successfully.", "seller_success")
    return redirect(url_for("seller_dashboard"))


@app.route("/seller/delete_product", methods=["POST"])
def seller_delete_product():
    if not seller_login_required():
        flash("Please login to delete products.", "seller_error")
        return redirect(url_for("seller_login"))

    product_id_raw = (request.form.get("product_id") or "").strip()
    if not product_id_raw.isdigit():
        flash("Invalid product id.", "seller_error")
        return redirect(url_for("seller_dashboard"))

    product_id = int(product_id_raw)

    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ? AND seller_id = ?",
            (product_id, session.get("seller_id")),
        ).fetchone()

        if existing is None:
            flash("Product not found.", "seller_error")
            return redirect(url_for("seller_dashboard"))

        conn.execute(
            "DELETE FROM products WHERE id = ? AND seller_id = ?",
            (product_id, session.get("seller_id")),
        )
        conn.commit()
    finally:
        conn.close()

    flash("Product deleted successfully.", "seller_success")
    return redirect(url_for("seller_dashboard"))


@app.route("/casual")
def casual():
    return render_template("casual.html")


@app.route("/party")
def party():
    return render_template("party.html")



@app.route("/ethnic")
def ethnic():
    return render_template("ethnic.html")


# Nested product routes used inside ethnic.html
@app.route("/anarkali")
def anarkali_details():
    return render_template("html_project/anarkali.html")


@app.route("/kurti")
def kurti_details():
    return render_template("html_project/kurti.html")


@app.route("/lehenga")
def lehenga_details():
    return render_template("html_project/lehenga.html")


@app.route("/saree")
def saree_details():
    return render_template("html_project/saree.html")



# --- Product detail pages (wired for redirects from product cards) ---


@app.route("/floral")
def floral_details():
    return render_template("html_project/floral.html")


@app.route("/denim")
def denim_details():
    return render_template("html_project/denim.html")


@app.route("/cotton")
def cotton_details():
    return render_template("html_project/cotton.html")


@app.route("/loose")
def loose_details():
    return render_template("html_project/loose.html")

@app.route("/elegant")
def elegant_details():
    return render_template('html_project/elegant.html')


@app.route("/shimmer")
def shimmer_details():
    return render_template('html_project/shimmer.html')

@app.route("/red")
def red_details():
    return render_template('html_project/red.html')

@app.route("/black")
def black_details():
    return render_template('html_project/black.html')


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8001)
