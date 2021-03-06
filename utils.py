import os
import cooperhewitt.api.client
import csv
import StringIO
import boto
from boto.s3.key import Key
import time
import datetime
import sendgrid
import dropbox

import re

from mongoengine import *

import urllib2 as urllib			

MONGO_URL = os.environ.get("MONGOHQ_URL")

if MONGO_URL:
    credentials = re.sub(r"(.*?)//(.*?)(@hatch)", r"\2",MONGO_URL)
    username = credentials.split(":")[0]
    password = credentials.split(":")[1]
    connect(
        MONGO_URL.split("/")[-1],
        host=MONGO_URL,
        port=1043,
        username=username,
        password=password
    )
else:
    database = os.environ['DB_NAME']
    host = os.environ['DB_HOST']
    connect(
        database,
        host=host,
        port=27017
    )
    
class Log(Document):
    method = StringField(max_length=300)
    completed_at = DateTimeField(default=datetime.datetime.now, required=True)
    submitted_at = DateTimeField(default=datetime.datetime.now, required=True)
    data = DynamicField()

class Role(Document):
    name = StringField(max_length=80, unique=True)
    description = StringField(max_length=255)

class User(Document):
    email = StringField(max_length=255)
    password = StringField(max_length=255)
    active = BooleanField(default=True)
    confirmed_at = DateTimeField()
    roles = ListField(ReferenceField(Role), default=[])
    

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

s3_key = os.environ['S3_KEY']
s3_secret = os.environ['S3_SECRET']
s3_bucket = os.environ['S3_BUCKET']

sendgrid_password = os.environ['SENDGRID_PASSWORD']
sendgrid_username = os.environ['SENDGRID_USERNAME']

dropbox_access_token = os.environ['DROPBOX_ACCESS_TOKEN']

def search_objects(data):

    query = data['meta']
    
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.search.objects'
    args = { 'query': query }

    rsp = api.call(method, **args)
    
    pages = int(rsp['pages'])
    
    output = StringIO.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
    writer.writerow(['id', 'accession_number', 'creditline', 'date', 'decade', 'department_id', 'description', 'dimensions', 'inscribed', 'justification', 'markings', 'media_id', 'medium', 'period_id', 'provenance', 'signed', 'title', 'tms:id', 'type', 'type_id', 'url', 'woe:country', 'year_acquired', 'year_end', 'year_start', 'image url'])

    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    
    
   
    for x in range(0, pages):
        args = { 'query': query, 'page': x }
        rsp = api.call(method, **args)
        objects = rsp['objects']
        
        for obj in objects:
            img_url = ''
            for image in obj['images']:
                if image['b']['is_primary'] == '1':
                    img_url = image['b']['url']
                    
            
            obj = utf8ify_dict(obj)
            writer.writerow([obj['id'], obj['accession_number'], obj['creditline'], obj['date'], obj['decade'], obj['department_id'], obj['description'], obj['dimensions'], obj['inscribed'], obj['justification'], obj['markings'], obj['media_id'], obj['medium'], obj['period_id'], obj['provenance'], obj['signed'], obj['title'], obj['tms:id'], obj['type'], obj['type_id'], obj['url'], obj['woe:country'], obj['year_acquired'], obj['year_end'], obj['year_start'], img_url])
            if img_url != '':
                upload_dropbox(img_url, st)
    

    upload_csv_dropbox(output, st)
            
    dropbox_link = get_dropbox_share(st)
         
    to_email = data['email'].encode('utf8')
    send_email(to_email, dropbox_link)
    
    data = {}
    data['dropbox_link'] = dropbox_link
    data['dropbox_folder'] = st
    data['email'] = to_email
    
    job = Log(method='search_objects', data=data).save()
    
    success = "You just uploaded " + st + " to dropbox and emailed " + to_email + " about it."
    
    return success    
    
def random_objects(data):
    
    numobjects = data['meta']
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.objects.getRandom'
    
    output = StringIO.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
    writer.writerow(['id', 'accession_number', 'creditline', 'date', 'decade', 'department_id', 'description', 'dimensions', 'inscribed', 'justification', 'markings', 'media_id', 'medium', 'period_id', 'provenance', 'signed', 'title', 'tms:id', 'type', 'type_id', 'url', 'woe:country', 'year_acquired', 'year_end', 'year_start', 'image url'])

    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    
    for x in range(0, int(numobjects)):
        rsp = api.call(method)
        obj = rsp['object']
        img_url = ''
        # for image in obj['images']:
        #     if image['b']['is_primary'] == '1':
        #         img_url = image['b']['url']
        
        obj = utf8ify_dict(obj)
        writer.writerow([obj['id'], obj['accession_number'], obj['creditline'], obj['date'], obj['decade'], obj['department_id'], obj['description'], obj['dimensions'], obj['inscribed'], obj['justification'], obj['markings'], obj['media_id'], obj['medium'], obj['period_id'], obj['provenance'], obj['signed'], obj['title'], obj['tms:id'], obj['type'], obj['type_id'], obj['url'], obj['woe:country'], obj['year_acquired'], obj['year_end'], obj['year_start'], img_url])

    
    upload_csv_dropbox(output, st)
            
    dropbox_link = get_dropbox_share(st)
         
    to_email = data['email'].encode('utf8')
    send_email(to_email, dropbox_link)
    
    data = {}
    data['dropbox_link'] = dropbox_link
    data['dropbox_folder'] = st
    data['email'] = to_email
    
    job = Log(method='random_objects', data=data).save()
    
    success = "You just uploaded " + st + " to dropbox and emailed " + to_email + " about it."
            
def list_objects(data):
    obj_list = data['meta']
    obj_list = obj_list.splitlines()
    
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.objects.getInfo'
    
    output = StringIO.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
    writer.writerow(['id', 'accession_number', 'creditline', 'date', 'decade', 'department_id', 'description', 'dimensions', 'inscribed', 'justification', 'markings', 'media_id', 'medium', 'period_id', 'provenance', 'signed', 'title', 'tms:id', 'type', 'type_id', 'url', 'woe:country', 'year_acquired', 'year_end', 'year_start', 'image url'])

    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    
    for line in obj_list:
        args = { 'accession_number': line }
        rsp = api.call(method, **args)
        if rsp['stat'] == 'ok':
            obj = rsp['object']
            img_url = ''
            for image in obj['images']:
                if image['b']['is_primary'] == '1':
                    img_url = image['b']['url']
        
            obj = utf8ify_dict(obj)            
            writer.writerow([obj['id'], obj['accession_number'], obj['creditline'], obj['date'], obj['decade'], obj['department_id'], obj['description'], obj['dimensions'], obj['inscribed'], obj['justification'], obj['markings'], obj['media_id'], obj['medium'], obj['period_id'], obj['provenance'], obj['signed'], obj['title'], obj['tms:id'], obj['type'], obj['type_id'], obj['url'], obj['woe:country'], obj['year_acquired'], obj['year_end'], obj['year_start'], img_url])
            if img_url != '':
                upload_dropbox(img_url, st)
        else:
            writer.writerow(["Couldn't find a record for " + line])           
    
    
    upload_csv_dropbox(output, st)
            
    dropbox_link = get_dropbox_share(st)
         
    to_email = data['email'].encode('utf8')
    send_email(to_email, dropbox_link)
    
    data = {}
    data['dropbox_link'] = dropbox_link
    data['dropbox_folder'] = st
    data['email'] = to_email
    
    job = Log(method='list_objects', data=data).save()
    
    success = "You just uploaded " + st + " to dropbox and emailed " + to_email + " about it."
    
    return success    

def upload_s3(filename, data):
    # upload the csv data to S3    
    conn = boto.connect_s3(s3_key, s3_secret)
    bucket = conn.create_bucket(s3_bucket)
    k = Key(bucket)
        
    k.key = filename # we need some kind of naming conv..
    
    k.set_contents_from_string(data.getvalue())
    k.make_public()
    

def upload_dropbox(url, jobname):
    from cStringIO import StringIO
    client = dropbox.client.DropboxClient(dropbox_access_token)
    
    img_file = urllib.urlopen(url)
    im = StringIO(img_file.read())

    file_name = url.split('/')[-1]

    file_name = jobname + '/' + file_name
    response = client.put_file(file_name, im, overwrite=True)
        
    
def upload_csv_dropbox(data, jobname):
    from cStringIO import StringIO
    client = dropbox.client.DropboxClient(dropbox_access_token)
    
    filename = jobname + "/" + jobname + "_" + "data.csv"
    response = client.put_file(filename, data)
    
    
    
def get_dropbox_share(jobname):
    from cStringIO import StringIO
    client = dropbox.client.DropboxClient(dropbox_access_token)
        
    rsp = client.share(jobname, short_url=True)

    return rsp['url']    
    
    
    
def send_email(to, filename):
    # send an email? er... sumptin
    
    sg = sendgrid.SendGridClient(sendgrid_username, sendgrid_password)
    message = sendgrid.Mail()
    
    body_html = 'Thanks for using csv-me. Here is a link to your stuff:<br><br> '  + filename
    body_text = 'Thanks for using csv-me. Here is a link to your stuff:\n\n ' + filename
        
    message.add_to(to)
    message.set_subject('Yo, your file is ready!')
    message.set_html(body_html)
    message.set_text(body_text)
    message.set_from('Micah Walter <walterm@si.edu>') ## your webmaster
    status, msg = sg.send(message)
    
    
def utf8ify_dict(stuff):
    
    for k, v in stuff.items():

        if v:
            try:
                v = v.encode('utf8')
            except Exception, e:
                v = ''

        stuff[k] = v

    return stuff	      