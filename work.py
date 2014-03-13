def search_objects(query):
    import os
    import cooperhewitt.api.client

    access_token = os.environ['CH_API_KEY']
    hostname = os.environ['CH_API_HOST']

    api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
    method = 'cooperhewitt.search.objects'
    args = { 'query': query }

    rsp = api.call(method, **args)

    return rsp
