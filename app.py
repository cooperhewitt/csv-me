import os
from flask import Flask
from flask import render_template
from flask import request

import cooperhewitt.api.client

import json
import csv

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

app = Flask(__name__)

@app.route('/')
def hello():
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.exhibitions.getList'
      
    rsp = api.call(method) 
    exhibitions = rsp['exhibitions']
    
    return render_template('index.html', exhibitions=exhibitions)