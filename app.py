import os
from flask import Flask
from flask import render_template
from flask import request, redirect
from utils import *
from pprint import pprint
import re

from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, UserMixin, RoleMixin, login_required, current_user

from rq import Queue
from worker import conn

q = Queue(connection=conn)

import cooperhewitt.api.client

import json
import csv

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET']

MONGO_URL = os.environ.get("MONGOHQ_URL")

if MONGO_URL:
    credentials = re.sub(r"(.*?)//(.*?)(@hatch)", r"\2",MONGO_URL)
    username = credentials.split(":")[0]
    password = credentials.split(":")[1]
    app.config["MONGODB_DB"] = MONGO_URL.split("/")[-1]
    connect(
        MONGO_URL.split("/")[-1],
        host=MONGO_URL,
        port=1043,
        username=username,
        password=password
    )
else:
    app.config['MONGODB_DB'] = os.environ['DB_NAME']
    app.config['MONGODB_HOST'] = os.environ['DB_HOST']
    app.config['MONGODB_PORT'] = os.environ['DB_PORT']  # 27017

app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

db = MongoEngine(app)

class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])
    
class Log(db.Document):
    method = db.StringField(max_length=300)
    submitted_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    data = db.DynamicField()

# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route('/')
def index():
    # api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    # method = 'cooperhewitt.exhibitions.getList'
      
    # rsp = api.call(method) 
    # exhibitions = rsp['exhibitions']
    exhibitions = {}
    
    return render_template('index.html', exhibitions=exhibitions)
    
@app.route('/about/')
def about():
    return render_template('about.html', title="About")
    
@app.route('/email/', methods=['GET', 'POST'])
def get_email():
    if request.method == 'POST':
        data = request.form['meta']
        method = request.form['method']
        
        return render_template('get_email.html', title="Wait, we need your email!", method=method, data=data)
    else:
        return redirect('/')

@app.route('/thanks/')
def thanks():    
    return render_template('thanks.html', title="Thanks!")


@app.route('/random/', methods=['GET', 'POST'])
def random():
    if request.method == 'POST' and request.form['data']:
        meta = request.form['data']
        email = request.form['email']
        
        data = {}
        data['meta'] = meta
        data['email'] = email
        
        job = Log(method='random_objects', data=data).save()
        
        result = q.enqueue(
            random_objects, data)
        
        return redirect('/thanks/') ## should take us to a thanks page
    else:
        return redirect('/')  
        
@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST' and request.form['data']:
        meta = request.form['data']
        email = request.form['email']
        
        data = {}
        data['meta'] = meta
        data['email'] = email
       
        result = q.enqueue(search_objects, args=(data,), timeout=3600)
        
        return redirect('/thanks/') ## should take us to a thanks page
    else:
        return redirect('/')  

@app.route('/list/', methods=['GET', 'POST'])
def list():
    if request.method == 'POST' and request.form['data']:
        meta = request.form['data']
        email = request.form['email']
        
        data = {}
        data['meta'] = meta
        data['email'] = email
       
        result = q.enqueue(
            list_objects, data)
        
        return redirect('/thanks/') ## should take us to a thanks page
    else:
        return redirect('/')  


@app.route('/test/', methods=['GET', 'POST'])
def test():
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'millerfox.objectPackages.getList'
      
    #rsp = api.call(method)
    return render_template('test.html', rsp='')
    
    
    