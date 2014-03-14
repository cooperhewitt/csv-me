import os
from flask import Flask
from flask import render_template
from flask import request, redirect
from utils import *

from rq import Queue
from worker import conn

q = Queue(connection=conn)

import cooperhewitt.api.client

import json
import csv

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

app = Flask(__name__)

@app.route('/')
def index():
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.exhibitions.getList'
      
    rsp = api.call(method) 
    exhibitions = rsp['exhibitions']
    
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
       
        result = q.enqueue(
            search_objects, data)
        
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
