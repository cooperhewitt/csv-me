import os
from flask import Flask
from flask import render_template
from flask import request, redirect
from utils import search_objects

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
    

@app.route('/random/', methods=['GET', 'POST'])
def random():
    if request.method == 'POST' and request.form['numobjects']:
        numobjects = request.form['numobjects']
    
        return numobjects
    else:
        return redirect('/')
        
@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST' and request.form['searchinput']:
        searchinput = request.form['searchinput']
        
        result = q.enqueue(
            search_objects, searchinput)
        
        return redirect('/') 
    else:
        return redirect('/')  
