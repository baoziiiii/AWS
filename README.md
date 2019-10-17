# AWS_RestaurantSuggest_ChatBot
A web AI customer chat service based on Amazon Web Service.
Covered Amazon Service: 
+ API Gateway
+ Amazon S3
+ Amazon Lex
+ Lambda
+ Simple Queue Service
+ DynamoDB
+ Elasticsearch Service
+ Simple Notification Service
+ Simple Email Service
+ CloudWatch

## Frontend
**src:** /web_JS_S3/     
**language:** js/css          
**deploy:** Amazon S3 bucket 

## API
**src:** msgAPI-swagger.yaml    
**format:** swagger.io       

## Lambda Function
**src:** /Lambda/

### LF0 
+ Bridge front-end web and Amazon Lex
+ Use the request/response model (API) specified in the msgAPI-swagger.yaml 

### LF1
+ Code hook for Lex, validing input, eliciting slots and fulfiling the intents
+ Two Intents: Greeting Intent and DiningSuggestionIntent
+ Slots: Location, Cuisine, Time, Number Of People, Phone Number, Email Address

### LF2
+ Auto-triggered by CloudWatch every n minutes
+ When triggered, pull a message from SQS(Message Queue), search cuisine in the message by ElasticSearch and get up to three random related restaurants IDs 
, acquire their details by query id field in dynamoDB
+ Send recommendations to customer by SNS text service and SES email service

## Restaurants Data
**src:** /scrapYelp/ 

Scrap 8000+ restaurants from Yelp API. Cover 50 US main cities.         
Store detailed information to dynamoDB, partition key is 'id' 
```
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
```
Store query information(categories and city) to ElasticSearch
```
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

```

### Example Chat
```
User 10/16/2019, 11:23:41 PM
Hi

AWS Chatbot 10/16/2019, 11:23:41 PM
Hi there, if you want to looking for restaurant, say 'restaurant'.

User 10/16/2019, 11:23:45 PM
restaurant

AWS Chatbot 10/16/2019, 11:23:45 PM
Great. I can help you with that. What city are you looking to dine in?

User 10/16/2019, 11:23:50 PM
New York

AWS Chatbot 10/16/2019, 11:23:51 PM
Got it. What cuisine would you like to try?(e.g. Chinese/Thai/Sandwich)

User 10/16/2019, 11:23:53 PM
Chinese

AWS Chatbot 10/16/2019, 11:23:53 PM
Then what time?(format: 12:00 p.m.)

User 10/16/2019, 11:23:58 PM
1:00 p.m.

AWS Chatbot 10/16/2019, 11:23:58 PM
Ok, how many people are in your party?

User 10/16/2019, 11:24:08 PM
5

AWS Chatbot 10/16/2019, 11:24:08 PM
May I have your phone number to which I will send you my findings?(US phone Format:+1xxxxxxxxxx)

User 10/16/2019, 11:24:13 PM
+1123456789

AWS Chatbot 10/16/2019, 11:24:14 PM
Lastly, I need your email address in case you don't receive text message.

User 10/16/2019, 11:24:18 PM
example@gmail.com

AWS Chatbot 10/16/2019, 11:24:19 PM
Okay, please check your information.[Location: New York];[Cuisine: Chinese];[Time: 1:00 p.m.];[Number Of People: 5];[Phone Number: +1123456789];[Email: example@gmail.com]

User 10/16/2019, 11:24:21 PM
ok

AWS Chatbot 10/16/2019, 11:24:23 PM
You're all set! If I find suggestions, I will notify your phone or your email! Have a good day!
```

### Suggestion Text:
```
Your Restaurant Suggestions
Hello! Here are my Chinese restaurant suggestions for 5 people, for 13:00. 
<1>BaoHaus, located at 238 E 14th St. 
<2>Wo Hop, located at 17 Mott St. 
<3>Vanessa's Dumpling House, located at 118A Eldridge St.

```
