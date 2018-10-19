#!flask/bin/python3

########################################################################################################
# Libraries

import bcrypt
import sqlite3

from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

########################################################################################################
# Initialization

MAX_INDEX = 9223372036854775807
SALT_ROUNDS = 14
MAX_LOGIN_ATTEMTS = 3
DATABASE='test.db'

#######################################################################################################
# helper functions

def create_connection(db_file):
	""" 	
	Create database connection to the SQLite file
	:param db_file: name of the database file
	:return: Connection object or None
	"""

	# Set up users table if it does not exist

	sql = '''CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY, 
		date text NOT NULL, 
		user text NOT NULL, 
		hashed_pw text NOT NULL
	)'''

	try:
		conn = sqlite3.connect(db_file)
		c = conn.cursor()
		c.execute(sql)
		conn.commit()
	except Error as e:
		print (e)

	# set up sensors table if it does not exist

	sql = '''CREATE TABLE IF NOT EXISTS sensors (
		id INTEGER PRIMARY KEY, 
		date float NOT NULL, 
		uuid text NOT NULL, 
		temp float,
		moisture float,
		humidity float,
		friendly_name text
	)'''

	try:
		c.execute(sql)
		conn.commit()
		return conn
	except Error as e:
		print (e)

	return None

def update_db(data,conn):
	"""
	Update database with sensor information
	:param data: json object containing sensor readings
	:param conn: database object
	:return: sucess or failure status
	"""

	values = (data['timestamp'],
		data['uuid'],
		data['temp'],
		data['moisture'],
		data['humid'],
		data['friendly_name']
	)

	sql = '''INSERT INTO sensors (date,uuid,temp,moisture,humidity,friendly_name) VALUES (?,?,?,?,?,?)'''

	c = conn.cursor()
	c.execute(sql,(values))
	conn.commit()

	return True

def authenticate_user(username,password,conn):
	"""
	Authenticate an existing user
	:param username: username to be authenticated
	:param password: password to be tested
	:param conn: database object
	:return: sucess or failure status
	"""
	matched = False
	c = conn.cursor()
	sql = '''SELECT * FROM users WHERE user = ?'''

	c.execute(sql,(username,))
	value = c.fetchone()

	if bcrypt.checkpw(password,value[3]):
		matched = True
	else:
		matched = False

	return matched

def enumerate_sensor_data(conn,username,sensor_id):
	"""
	List all sensor information
	:param conn: database object
	:return: sucess or failure status
	"""
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	sql = '''SELECT * FROM sensors WHERE sensors.uuid = ?'''

	c.execute(sql,(sensor_id,))

	r = [dict((c.description[i][0],value)
		for i, value in enumerate(row)) for row in c.fetchall()]

	return r

#######################################################################################################
# Web End points

@app.route('/',methods=['GET'])
def welcome():
    return render_template("/login.html")

# Do authorization
@app.route('/authorize',methods=['POST'])
def authorize():
	uname = request.form['username'].encode('utf-8')
	pw = request.form['password'].encode('utf-8')
	db = create_connection(DATABASE)
	if uname !="" and pw != "":
		authenticated = authenticate_user(uname,pw,db)
		if authenticated:
			sensor_data = enumerate_sensor_data(db,request.form['username'],"B8-27-EB-63-80-16")
			return render_template("/dashboard.html",user=request.form['username'],sensor_data=sensor_data)
		else: return render_template("/login.html")

@app.route('/update_sensors',methods=['GET'])
def web_update_sensors():
	db = create_connection(DATABASE)
	sensor_data = enumerate_sensor_data(db,"Not used","B8-27-EB-63-80-16")
	return jsonify(sensor_data)

# Device end points

# Receive updates from the remote sensor
@app.route('/update',methods=['POST'])
def set():
	data = request.json
	db = create_connection(DATABASE)
	update_db(data,db)
	return "Success"

########################################################################################################
# The app

if __name__ == "__main__":
	app.run(host='ec2-18-223-2-215.us-east-2.compute.amazonaws.com',debug=True)
