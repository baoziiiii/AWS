import boto3
import requests
import json
import time

dynamodb = boto3.resource('dynamodb')
#
# # Instantiate a table resource object without actually
# # creating a DynamoDB table. Note that the attributes of this table
# # are lazy-loaded: a request is not made nor are the attribute
# # values populated until the attributes
# # on the table resource are accessed or its load() method is called.
table = dynamodb.Table('yelp-restaurants')

api_key = 'copy_your_yelp_api_here'
headers = {'Authorization': 'Bearer %s' % api_key}

cities = ['New York','Seattle','Los Angeles','Chicago','San Francisco','Washington', 'Denver', 'Boston',
          'Minneapolis', 'Austin', 'Atlanta', 'Phoenix', 'Dallas', 'Philadelphia', 'Detroit', 'Portland', 'Miami',
          'Houston', 'Las Vegas', 'San Antonio', 'Memphis', 'New Orleans', 'Oakland']
url = 'https://api.yelp.com/v3/businesses/search'
with table.batch_writer(overwrite_by_pkeys=['id']) as batch:
    for city in cities:
        for i in range(20):
            params = {'term': 'restaurants', 'location': city, 'sort_by': 'review_count', 'limit': 20, 'offset': i * 20}
            req = requests.get(url, params=params, headers=headers)
            parsed = json.loads(req.text)
            businesses = parsed["businesses"]
            for business in businesses:
                try:
                    id = business["id"]
                    name = business["name"]

                    state = business["location"]["state"]
                    city = business["location"]["city"]
                    address = business["location"]["address1"] if business["location"]["address1"] else None

                    latitude = str(business["coordinates"]["latitude"]) if business["coordinates"]["latitude"] else None
                    longitude = str(business["coordinates"]["longitude"]) if business["coordinates"][
                        "longitude"] else None
                    number_of_reviews = business["review_count"] if business["review_count"] else None
                    rating = str(business["rating"]) if business["rating"] else None
                    categories = business["categories"] if business["categories"] else None
                    ZIP = business["location"]["zip_code"] if business["location"]["zip_code"] else None
                    Phone = business["phone"] if business["phone"] else None
                    batch.put_item(
                        Item={
                            'id': id,
                            'name': name,
                            'state': state,
                            'city': city,
                            'address': address,
                            'latitude': latitude,
                            'longitude': longitude,
                            'number_of_reviews': number_of_reviews,
                            'rating': rating,
                            'categories': categories,
                            'ZIP': ZIP,
                            'phone': Phone,
                            'inserted_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                except:
                    continue
