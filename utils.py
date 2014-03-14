import os
import cooperhewitt.api.client
import csv
import StringIO
import boto
from boto.s3.key import Key
import time
import datetime
import sendgrid

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

s3_key = os.environ['S3_KEY']
s3_secret = os.environ['S3_SECRET']
s3_bucket = os.environ['S3_BUCKET']

sendgrid_password = os.environ['SENDGRID_PASSWORD']
sendgrid_username = os.environ['SENDGRID_USERNAME']

def search_objects(data):

    query = data['meta']
    
    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.search.objects'
    args = { 'query': query }

    rsp = api.call(method, **args)
    
    pages = int(rsp['pages'])
    
    output = StringIO.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
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
    
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    
    filename = st + '_' + query + '.csv'
    upload_s3(filename, output)
    
    to_email = data['email'].encode('utf8')
    send_email(to_email, filename)
    
    success = "You just uploaded " + filename + " to S3 and emailed " + to_email + " about it."
    
    return success    
    
def random_objects(data):
    
    return "not quite done?"
    
def list_objects(data):
    
    return "not quite done?"

def upload_s3(filename, data):
    # upload the csv data to S3    
    conn = boto.connect_s3(s3_key, s3_secret)
    bucket = conn.create_bucket(s3_bucket)
    k = Key(bucket)
        
    k.key = filename # we need some kind of naming conv..
    
    k.set_contents_from_string(data.getvalue())
    k.make_public()
    

def send_email(to, filename):
    # send an email? er... sumptin
    
    sg = sendgrid.SendGridClient(sendgrid_username, sendgrid_password)
    message = sendgrid.Mail()
    
    body_html = 'Thanks for using csv-me. Here is a link to your file:<br><br> http://csvme.s3.amazonaws.com/' + filename
    body_text = 'Thanks for using csv-me. Here is a link to your file:\n\n http://csvme.s3.amazonaws.com/' + filename
        
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

    