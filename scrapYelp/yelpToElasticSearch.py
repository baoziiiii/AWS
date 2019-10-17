from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import requests
import json

api_key = 'w94RBe98SR8FXHwM4bFg2qwBxHWwSmxMVBPMZMDl9-tvMlMzyT01ONb7XJuAzqtCxaPz3YIKRpMDCnRz4YxTOlAjUsu3NYur5uQQnAg0PpA2gDJ2cLJprFBH9X2mXXYx'
headers = {'Authorization': 'Bearer %s' % api_key}

cities = ['New York', 'Seattle', 'Los Angeles', 'Chicago', 'San Francisco', 'Washington', 'Denver', 'Boston',
          'Minneapolis', 'Austin', 'Atlanta', 'Phoenix', 'Dallas', 'Philadelphia', 'Detroit', 'Portland', 'Miami',
          'Houston', 'Las Vegas', 'San Antonio', 'Memphis', 'New Orleans', 'Oakland']
url = 'https://api.yelp.com/v3/businesses/search'

## connect to aws es
host = 'search-cc-es-zomuhpncq75enpb6mjilbyjqce.us-east-1.es.amazonaws.com'
region = 'us-east-1'  # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


## yelp scrap
def scrap_yelp():
    api_key = 'w94RBe98SR8FXHwM4bFg2qwBxHWwSmxMVBPMZMDl9-tvMlMzyT01ONb7XJuAzqtCxaPz3YIKRpMDCnRz4YxTOlAjUsu3NYur5uQQnAg0PpA2gDJ2cLJprFBH9X2mXXYx'
    headers = {'Authorization': 'Bearer %s' % api_key}

    cities = ['New York', 'Seattle', 'Los Angeles', 'Chicago', 'San Francisco', 'Washington', 'Denver', 'Boston',
              'Minneapolis', 'Austin', 'Atlanta', 'Phoenix', 'Dallas', 'Philadelphia', 'Detroit', 'Portland', 'Miami',
              'Houston', 'Las Vegas', 'San Antonio', 'Memphis', 'New Orleans', 'Oakland']
    url = 'https://api.yelp.com/v3/businesses/search'
    for city in cities:
        for i in range(20):
            params = {'term': 'restaurants', 'location': city, 'sort_by': 'review_count', 'limit': 30, 'offset': i * 20}
            req = requests.get(url, params=params, headers=headers)
            parsed = json.loads(req.text)
            businesses = parsed["businesses"]
            for business in businesses:
                try:
                    id = business["id"]
                    categories = business["categories"] if business["categories"] else None
                    city = business["location"]["city"]
                    entry = {
                        'id': id,
                        'categories': categories,
                        'city' : city
                    }
                    insert_document(entry)
                    print("Inserted:{}".format(entry))
                except:
                    continue


## create index
def create_index():
    if es.indices.exists('restaurants'):
        return
    es.indices.create(index='restaurants')
    es.indices.put_mapping(
        index='restaurants',
        doc_type='Restaurant',
        include_type_name=True,
        body={
            'Restaurant': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'categories': {'type': 'nested'},
                    'city': {'type': 'text'}
                }
            }
        }
    )


def insert_document(entry):
    es.index(index='restaurants', doc_type='Restaurant', body=entry, id=entry['id'])


# es.indices.delete(index='restaurants')

# create_index()
scrap_yelp()
es.indices.refresh(index='restaurants')


searchsandich={
    'query':{
        "nested" : {
            "path" : "categories",
            "query" : { "fuzzy" : {"categories.alias" : "sandwich"} }
        }
    }
}

searchcity={
    'query':{"match":{"city":"New York City"}}
}

searchbody={
    "query":{
        "bool":{
            "must":[
                {
                    "nested" : {
                    "path" : "categories",
                    "query" : { "fuzzy" : {"categories.alias" : "sandwich"} }
                    }
                },
                {
                    "match":
                    {"city":"New York City"}
                }
            ]
        }
    }
}


res = es.search(index='restaurants',body=searchbody,filter_path=['hits.hits._source'])
hits = res["hits"]["hits"]
print(hits)
