import os
from app import app
from app.user import views
from flask import render_template, flash, redirect, url_for, request, current_app, session, g
from flask_login import login_required, current_user

import mysql.connector
from flask import jsonify,make_response
from flask import jsonify,json
import json as js

cnn = mysql.connector.connect(
	user = os.environ['RDS_USERNAME'], 
	password = os.environ['RDS_PASSWORD'],
	host = os.environ['RDS_HOSTNAME'],
	database = os.environ['RDS_DB_NAME'])

@app.route('/')
def main():
	return redirect(url_for('index'))

@app.route('/index')
def index():
	cur = cnn.cursor()
	movies = []
	cur.callproc('all_movie_titles')
	for result in cur.stored_results():
		movies += result.fetchall()
	
	return render_template('index.html', movies=movies)

@app.route('/api/v1/movie/<movieId>')
def movieAPI(movieId):
	#return charInMovie(movieId)
	return jsonify(charInMovie(movieId))

@app.route('/api/v1/<tablename>/delete', methods=['POST'])
def tableDelete(tablename):
	if tablename not in ["movies", "characters", "events", "organizations", "movies_characters", "movies_events", "events_characters", "movies_organizations_characters", "user_info"] or not current_user.is_authenticated:
		return None
	if tablename == "user_info" and current_user.username != "admin":
		flash("Access Denied")
		return redirect(url_for('dbtables'))
	print(request.json)
	clause = ''
	for key, value in request.json.items():
		clause += '`{}` = "{}" and '.format(key, value)
	clause = clause[:-5]
	print(clause)
	cur = cnn.cursor()
	query = "DELETE FROM {} WHERE {}".format(tablename, clause)
	try:
		cur.execute(query)
		cnn.commit()
	except:
		return json.dumps({'success':False}), 400, {'ContentType':'application/json'}
	return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/dbtables')
def dbtables():
	if current_user.is_authenticated:
		is_admin = (current_user.username == "admin")
		return render_template('dbtables.html', isAdmin = is_admin)
	return redirect(url_for('login'))	

@app.route('/table/<tablename>')
def table(tablename):
	if tablename not in ["movies", "characters", "events", "organizations", "movies_characters", "movies_events", "events_characters", "movies_organizations_characters", "user_info"] or not current_user.is_authenticated:
		return redirect(url_for('dbtables'))
	if tablename == "user_info" and current_user.username != "admin":
		flash("Access Denied")
		return redirect(url_for('dbtables'))
	cur = cnn.cursor()
	tableData = []
	query = "SELECT * FROM {}".format(tablename)
	cur.execute(query)
	columns = cur.description
	tableData = cur.fetchall()
	tableName = tablename.upper()
	tableName = tableName.replace('_', ' TO ')
	return render_template('table.html', tableData=tableData, columns=columns, tableName=tableName, url_name=tablename)

@app.route('/table/<tablename>/add', methods=['GET', 'POST'])
def tableAdd(tablename):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if request.method == 'POST':
		if tablename not in ["movies", "characters", "events", "organizations", "movies_characters", "movies_events", "events_characters", "movies_organizations_characters", "user_info"]:
			return redirect(url_for('dbtables'))
		if tablename == "user_info" and current_user.username != "admin":
			flash("Access Denied")
			return redirect(url_for('dbtables'))
		cur = cnn.cursor()
		query = "SELECT DATA_TYPE, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{}' and table_schema = 'MCU_VISUALIZATION'".format(tablename)
		cur.execute(query)
		tableInfo = cur.fetchall()
		print(request.form)
		print(tableInfo)
		s = "("
		for info in tableInfo:
			#f info[0] in ['int', 'decimal', 'date']:
			#	s += request.form[info[1]]
			#elif info[0] in ['varchar', 'text']:
			s += "'"
			s += request.form[info[1]]
			s += "'"
			s += ", "
			print(s)
		s = s[:-2]
		s += ")"
		print(s)
			
		cur = cnn.cursor()
		query = "INSERT INTO {} VALUES {}".format(tablename, s)
		print(query)
		cur.execute(query)
		cnn.commit()
		return redirect(url_for('dbtables'))
	else:
		if tablename not in ["movies", "characters", "events", "organizations", "movies_characters", "movies_events", "events_characters", "movies_organizations_characters", "user_info"]:
			return redirect(url_for('dbtables'))
		if tablename == "user_info" and current_user.username != "admin":
			flash("Access Denied")
			return redirect(url_for('dbtables'))
		cur = cnn.cursor()
		query = "SELECT DATA_TYPE, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{}' and table_schema = 'MCU_VISUALIZATION'".format(tablename)
		cur.execute(query)
		tableInfo = cur.fetchall()
		print(tableInfo)
		formTypes = []
		for info in tableInfo:
			if info[0] in ['int', 'decimal']:
				formTypes += [["number", info[1]]]
			elif info[0] in ['varchar', 'text']:
				formTypes += [["text", info[1]]]
			elif info[0] == 'date':
				formTypes += [["date", info[1]]]
		print(formTypes)
		tableName = tablename.upper()
		tableName = tableName.replace('_', ' TO ')
		return render_template('addForm.html', formTypes=formTypes, tableName=tableName)

@app.route('/test/<movie_id>')
def testing(movie_id):
	return jsonify(charInMovie(movie_id))

def charInMovie(movie_ID):
	cur = cnn.cursor()
	links = []
	cur.callproc('org_movie_connections', [movie_ID])
	for result in cur.stored_results():
		links += result.fetchall()
	cur.callproc('char_movie_connections', [movie_ID])
	for result in cur.stored_results():
		links += result.fetchall()
	cur.callproc('char_org_connections', [movie_ID])
	for result in cur.stored_results():
		links += result.fetchall()
	cur.callproc('events_movie_connections', [movie_ID])
	for result in cur.stored_results():
		links += result.fetchall()
	cur.callproc('characters_events_connections', [movie_ID])
	for result in cur.stored_results():
		links += result.fetchall()

	cur.callproc('char_in_movie', [movie_ID])
	for result in cur.stored_results():
		charNodes = result.fetchall()
	cur.callproc('org_in_movie', [movie_ID])
	for result in cur.stored_results():
		orgNodes = result.fetchall()
	cur.callproc('movie_info', [movie_ID])
	for result in cur.stored_results():
		movieNode = result.fetchall()
	cur.callproc('events_in_movie', [movie_ID])
	for result in cur.stored_results():
		eventNodes = result.fetchall()

	result_json = {'nodes': jsonifyNodes(charNodes, orgNodes, movieNode, eventNodes)
		,"links" : createLinks(links)}


	return result_json

def createLinks(links):
	payload = []
	for link in links:
		payload.append(makeLink(link[0], link[1]))
	return payload

def makeLink(char1, char2):
	return {"source": char1, "target": char2, "value": 	20}

def jsonifyNodes(chars, orgs, movie, events):
	payload = []
	for char in chars:
		content = jsonifyAChar(char)
		payload.append(content)
		content = {}
	for event in events:
		content = jsonifyAEvent(event)
		payload.append(content)
		content = {}

	for org in orgs:
		content = jsonifyAOrg(org)
		payload.append(content)
		content = {}
	for mov in movie:
		content = jsonifyMovie(mov)
		payload.append(content)
		content = {}
	return payload

def jsonifyChars(char):
	payload = []
	content = {}
	for result in char:
		content = jsonifyAChar(result)
		payload.append(content)
		content = {}
	return payload


def jsonifyAChar(result):
	return {
	'id': result[1],
	'group': 'character',
	'image': result[6],
	'about': jsonAbout(result),
	'events': 'to connections'}

def jsonifyAEvent(result):
	return {
	'id': result[1],
	'group': 'event',
	'image': '../static/img/event.png',
	'about': result[2],
	'events': 'to connections'}

def jsonifyAOrg(result):
	return {
	'id': result[1],
	'group': 'organization',
	'image': result[3],
	'about': result[2],
	'events': 'to connections'}

def jsonifyMovie(result):
	return {
	'id': result[1],
	'group': 'movie',
	'image': result[7],
	'about': result[3],
	'events': 'to connections'}

def jsonAbout(char):
	return ', '.join([char[2], gender(char[3]), char[4]])

def gender(code):
	if code == 'F': return 'Female'
	else: return 'Male'


def eventToString(char):
	cur = cnn.cursor()
	char_id = char[0]
	#query3 = ("CALL eventDes('%s')") % char_id
	query_event = ("SELECT description FROM events_characters WHERE character_id = '%s'") % char_id
	cur.execute(query_event)
	rv = cur.fetchall()
	arr = []
	for des in rv:
		arr.append(des[0].replace('"', ''))
	return arr;

