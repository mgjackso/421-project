from flask import Flask, render_template, request 
import sqlite3 

app = Flask(__name__) 

connect = sqlite3.connect('database.db') 
connect.execute( 
	'CREATE TABLE IF NOT EXISTS ORDERS (oid INTEGER PRIMARY KEY, name TEXT, address TEXT, total NUMBER)', 
	'CREATE TABLE IF NOT EXISTS SHOES (sid INTEGER PRIMARY KEY, name TEXT, stock NUMBER, price NUMBER)',
	'CREATE TABLE IF NOT EXISTS CONTAINS(sid INT, oid INT, PRIMARY KEY (bid,oid), FOREIGN KEY (oid) REFERENCES ORDERS (oid), FOREIGN KEY (bid) REFERENCES BOOKS (bid)')

# add date maybe later // check if oid type is correct


@app.route('/') 
@app.route('/home', methods=['GET', 'POST']) 
def home(): 
	if request.method == 'GET':

	return render_template('home.html') 

@app.route('/cart', methods=['GET', 'POST']) 
def join(): 
	if request.method == 'POST': 
		name = request.form['name'] 
		address = request.form['address'] 
		city = request.form['city'] 
		country = request.form['country'] 
		phone = request.form['phone'] 

		with sqlite3.connect("database.db") as users: 
			cursor = users.cursor() 
			cursor.execute("INSERT INTO PARTICIPANTS (name,email,city,country,phone) VALUES (?,?,?,?,?)", 
						(name, email, city, country, phone)) 
			users.commit() 
		return render_template("index.html") 
	else: 
		return render_template('join.html') 


@app.route('/participants') 
def participants(): 
	connect = sqlite3.connect('database.db') 
	cursor = connect.cursor() 
	cursor.execute('SELECT * FROM PARTICIPANTS') 

	data = cursor.fetchall() 
	return render_template("participants.html", data=data) 


if __name__ == '__main__': 
	app.run(debug=False) 
