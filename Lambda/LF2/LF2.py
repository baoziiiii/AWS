from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import random
import requests
import json

credentials = boto3.Session().get_credentials()

def retrieve_sqs_messages(sqs_queue_url, num_msgs=2, wait_time=0, visibility_time=5):
    """Retrieve messages from an SQS queue

    The retrieved messages are not deleted from the queue.

    :param sqs_queue_url: String URL of existing SQS queue
    :param num_msgs: Number of messages to retrieve (1-10)
    :param wait_time: Number of seconds to wait if no messages in queue
    :param visibility_time: Number of seconds to make retrieved messages
        hidden from subsequent retrieval requests
    :return: List of retrieved messages. If no messages are available, returned
        list is empty. If error, returns None.
    """

    # Validate number of messages to retrieve
    if num_msgs < 1:
        num_msgs = 1
    elif num_msgs > 10:
        num_msgs = 10

    # Retrieve messages from an SQS queue
    sqs_client = boto3.client('sqs')
    try:
        msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                          MaxNumberOfMessages=num_msgs,
                                          WaitTimeSeconds=wait_time,
                                          VisibilityTimeout=visibility_time,
                                          MessageAttributeNames=["All"])
        # Return the list of retrieved messages
        return msgs['Messages']
    except:
        return None


def delete_sqs_message(sqs_queue_url, msg_receipt_handle):
    """Delete a message from an SQS queue

    :param sqs_queue_url: String URL of existing SQS queue
    :param msg_receipt_handle: Receipt handle value of retrieved message
    """

    # Delete the message from the SQS queue
    sqs_client = boto3.client('sqs')
    sqs_client.delete_message(QueueUrl=sqs_queue_url,
                              ReceiptHandle=msg_receipt_handle)


def get_es_client():
    ## connect to aws es
    host = 'search-cc-es-zomuhpncq75enpb6mjilbyjqce.us-east-1.es.amazonaws.com'
    region = 'us-east-1'  # e.g. us-west-1
    service = 'es'
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    return es


def search_restaurant_from_dynamoDB(id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    response = table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    return response


def es_search(es, cuisine, city):
    searchbody = {
        "query": {
            "bool": {
                "must": [
                    {
                        "nested": {
                            "path": "categories",
                            "query": {"fuzzy": {"categories.alias": cuisine}}
                        }
                    },
                    {
                        "match":
                            {"city": city}
                    }
                ]
            }
        }
    }
    res = es.search(index='restaurants', body=searchbody, filter_path=['hits.hits._source'])
    hits = res["hits"]["hits"]
    hit_set = set()
    for i in range(6):
        rand = random.randint(0, len(hits) - 1)
        hit_set.add(hits[rand]['_source']['id'])
        if len(hit_set) > 3:
            hit_set.pop()
    return hit_set


def send_text(dest_phone, message):
    client = boto3.client("sns")
    # Send your sms message.
    client.publish(
        PhoneNumber=dest_phone,
        Message=message,
        MessageAttributes = {
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Promotional'
            }
        }
    )


def send_email(dest_email,message):
       # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Baozi Chatbot<bwq15511@gmail.com>"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = dest_email

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "Your Restaurant Suggestions"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = message

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Your Restaurant Suggestions</h1>
      <p>{}</p>
    </body>
    </html>
                """.format(message)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def lambda_handler(event, context):
    es = get_es_client()
    queue_url = 'https://sqs.us-east-1.amazonaws.com/645446725344/DiningSuggestion'
    for i in range(2):
        msgs = retrieve_sqs_messages(queue_url)
        if msgs is None:
            break
        for msg in msgs:
            receipt_handle = msg['ReceiptHandle']
            attributes = msg['MessageAttributes']
            phone = attributes['PhoneNumber']['StringValue']
            email = attributes['Email']['StringValue']
            cuisine = attributes['Cuisine']['StringValue']
            number_of_people = attributes['NumberOfPeople']['StringValue']
            time = attributes['Time']['StringValue']
            text_msg = "Hello! Here are my {} restaurant suggestions for {} people, for {}.".format(cuisine,
                                                                                                   number_of_people,
                                                                                                   time)
            hit_set = es_search(es, cuisine, attributes['Location']['StringValue'])
            if len(hit_set) == 0:
                continue
            for j in range(len(hit_set)):
                hit = hit_set.pop()
                res = search_restaurant_from_dynamoDB(hit)
                if len(res['Items']) > 0:
                    rest = res['Items'][0]
                    res_name = rest['name']
                    res_address = rest['address']
                    text_msg += " <{}>{}, located at {}.".format(j + 1, res_name, res_address)
            send_text(phone, text_msg)
            send_email(email , text_msg)
            print("send Email to:{}\n{}\n".format(email, text_msg))
            # print("send SMS to:{}\n{}\n".format(phone, text_msg))
            delete_sqs_message(queue_url,receipt_handle)

    # TODO implement

    return {
        'statusCode': 200,
        'body': "Hello"
    }


