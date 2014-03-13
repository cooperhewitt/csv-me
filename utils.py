import os
import cooperhewitt.api.client
import csv
import boto
from boto.s3.key import Key

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

# s3_key = os.environ['S3_KEY']
# s3_secret = os.environ['S3_SECRET']
# s3_bucket = os.environ['S3_BUCKET']


def search_objects(query):

    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.search.objects'
    args = { 'query': query }

    rsp = api.call(method, **args)
    
    pages = int(rsp['pages'])
    
    data = ''
    
    filename = query + '.csv'
    
    ofile  = open('./' + filename, "wb")
    writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
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
    
    ofile.close()
    
    # conn = boto.connect_s3(s3_key, s3_secret)
    # bucket = conn.create_bucket(s3_bucket)
    # k = Key(bucket)
    # k.key = 'test.csv'
    # 
    # k.set_contents_from_filename(filename)
    # k.set_acl('public-read')
    
    return "done"     
    
    
def utf8ify_dict(stuff):
    
    for k, v in stuff.items():

        if v:
            try:
                v = v.encode('utf8')
            except Exception, e:
                v = ''

        stuff[k] = v

    return stuff	  

    