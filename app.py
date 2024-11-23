from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'

connect = sqlite3.connect('database.db', check_same_thread=False)
connect.execute(
    'CREATE TABLE IF NOT EXISTS ORDERS (oid INTEGER PRIMARY KEY, name TEXT, address TEXT, total NUMBER)')
connect.execute(
    'CREATE TABLE IF NOT EXISTS SHOES (sid INTEGER PRIMARY KEY, name TEXT, stock NUMBER, price NUMBER)')
connect.execute(
    'CREATE TABLE IF NOT EXISTS CONTAINS(sid INT, oid INT, quantity NUMBER, PRIMARY KEY (sid, oid), FOREIGN KEY (oid) REFERENCES ORDERS (oid), FOREIGN KEY (sid) REFERENCES SHOES (sid))')

connect.execute('''
    CREATE TRIGGER IF NOT EXISTS decrement_stock
    AFTER INSERT ON CONTAINS
    FOR EACH ROW
    BEGIN
        UPDATE SHOES
        SET stock = stock - NEW.quantity
        WHERE sid = NEW.sid;
    END;
''')

# Insert initial data
with sqlite3.connect('database.db') as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM SHOES")
    cursor.execute("DELETE FROM ORDERS")
    cursor.execute("DELETE FROM CONTAINS")
    
    cursor.execute("INSERT INTO SHOES (name, stock, price) VALUES ('Sambas', 5, 100)")
    cursor.execute("INSERT INTO SHOES (name, stock, price) VALUES ('Reeboks', 5, 80)")
    cursor.execute("INSERT INTO SHOES (name, stock, price) VALUES ('Nikes', 7, 120)")
    conn.commit()

@app.route('/')
@app.route('/home', methods=['GET'])
def home():
    if request.method == 'GET':
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM SHOES")
            shoes = cursor.fetchall()
        return render_template('home.html', shoes=shoes)

@app.route('/add_to_cart/<int:sid>', methods=['POST'])
def add_to_cart(sid):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sid, name, price FROM SHOES WHERE sid = ?", (sid,))
        shoe = cursor.fetchone()
    
    if shoe:
        cart = session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}
        if str(shoe[0]) in cart:
            cart[str(shoe[0])]['quantity'] += 1
        else:
            cart[str(shoe[0])] = {'sid': shoe[0], 'name': shoe[1], 'price': shoe[2], 'quantity': 1}
        session['cart'] = cart
    return redirect(url_for('home'))

@app.route('/decrement_cart/<int:sid>', methods=['POST'])
def decrement_cart(sid):
    cart = session.get('cart', {})
    if str(sid) in cart:
        if cart[str(sid)]['quantity'] > 1:
            cart[str(sid)]['quantity'] -= 1
        else:
            del cart[str(sid)]
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']

        # Validate that the name contains only alphabetical letters
        if not re.match("^[A-Za-z]+$", name):
            flash("Name must contain only alphabetical letters.")
            return redirect(url_for('cart'))

        cart = session.get('cart', {})
        insufficient_stock = []

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            for item in cart.values():
                cursor.execute("SELECT stock FROM SHOES WHERE sid = ?", (item['sid'],))
                stock = cursor.fetchone()[0]
                if stock < item['quantity']:
                    insufficient_stock.append(item['name'])

            if insufficient_stock:
                flash(f"Not enough stock for: {', '.join(insufficient_stock)}")
                return redirect(url_for('cart'))

            cursor.execute("INSERT INTO ORDERS (name, address, total) VALUES (?, ?, ?)",
                           (name, address, 0))  # Assuming total is calculated later
            oid = cursor.lastrowid

            total_price = 0
            for item in cart.values():
                cursor.execute("INSERT INTO CONTAINS (sid, oid, quantity) VALUES (?, ?, ?)", (item['sid'], oid, item['quantity']))
                total_price += item['price'] * item['quantity']

            cursor.execute("UPDATE ORDERS SET total = ? WHERE oid = ?", (total_price, oid))
            conn.commit()

        session.pop('cart', None)
        return redirect(url_for('order', oid=oid))
    else:
        cart = session.get('cart', {})
        total_price = sum(item['price'] * item['quantity'] for item in cart.values())
        return render_template('cart.html', cart=cart.values(), total_price=total_price)

@app.route('/order/<int:oid>', methods=['GET'])
def order(oid):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ORDERS WHERE oid = ?", (oid,))
        order = cursor.fetchone()
        cursor.execute("SELECT SHOES.name, CONTAINS.sid, CONTAINS.quantity FROM CONTAINS JOIN SHOES ON CONTAINS.sid = SHOES.sid WHERE oid = ?", (oid,))
        items = cursor.fetchall()
    return render_template('order.html', order=order, items=items)

@app.route('/update_order/<int:oid>', methods=['POST'])
def update_order(oid):
    name = request.form['name']
    address = request.form['address']
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDERS SET name = ?, address = ? WHERE oid = ?", (name, address, oid))
        conn.commit()
    return redirect(url_for('order', oid=oid))

@app.route('/cancel_order/<int:oid>', methods=['POST'])
def cancel_order(oid):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sid, quantity FROM CONTAINS WHERE oid = ?", (oid,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute("UPDATE SHOES SET stock = stock + ? WHERE sid = ?", (item[1], item[0]))
        cursor.execute("DELETE FROM ORDERS WHERE oid = ?", (oid,))
        cursor.execute("DELETE FROM CONTAINS WHERE oid = ?", (oid,))
        conn.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)