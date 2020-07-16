from flask import Flask, render_template, Response, request, redirect, url_for, send_from_directory, session, g
from flask_socketio import SocketIO, send, emit
from flask_sslify import SSLify
from flask_pymongo import PyMongo
from datetime import datetime
from hurry.filesize import size

app = Flask(__name__, static_url_path='/templates', static_folder='static')
#sslify = SSLify(app, subdomains=True) Uncomment if you are going to use https
app.config['SECRET_KEY'] = 'secret!'
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = 'files'
socketio = SocketIO(app)
app.config['MONGO_URI'] = "" # Place your mongodb uri here.
mongo = PyMongo(app)

from app import views