from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def index2():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # TODO: add real login check here
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # TODO: add real registration logic here
        return redirect(url_for('login'))
    return render_template('registerhere.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')
    
@app.route('/seller')
def seller():
    return render_template('seller.html')

@app.route('/casual')
def casual():
    return render_template('casual.html')

@app.route('/party')
def party():
    return render_template('party.html')

@app.route('/ethnic')
def ethnic():
    return render_template('ethnic.html')

if __name__ == '__main__':
    app.run(debug=True)