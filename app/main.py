from app import app
from app.user import views
from flask import render_template, flash, redirect, url_for, request, current_app, session

import json

@app.route('/')
def main():
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/guardians_of_galaxy')
def guardians_of_galaxy():
    return render_template('guardians_of_galaxy.html')