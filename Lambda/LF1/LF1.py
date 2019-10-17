"""
 This code sample demonstrates an implementation of the Lex Code Hook Interface
 in order to serve a bot which manages dentist appointments.
 Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
 as part of the 'MakeAppointment' template.

 For instructions on how to set up and test this bot, as well as additional samples,
 visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
import re
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message,
            'responseCard': response_card
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message,
            'responseCard': response_card
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_book_appointment(appointment_time,phone_number,email):
    if appointment_time:
        if re.match("^[0-9]{2}:[0-9]{2}",appointment_time)==None:
            return build_validation_result(False, 'Time', 'I did not recognize that, what time would you like to book your appointment?')
        
        hour, minute = appointment_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)

        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'Time', 'I did not recognize that, what time would you like to book your appointment?')
        if hour < 0 or hour > 23:
            return build_validation_result(False, 'Time', 'I did not recognize that, what time would you like to book your appointment?')

        if minute not in [30, 0]:
            # Must be booked on the hour or half hour
            return build_validation_result(False, 'Time', 'We schedule appointments every half hour, what time works best for you?')
    if phone_number:
        if re.match("\+[0-9]{9}",phone_number)==None:
            return build_validation_result(False, 'PhoneNumber', 'I am sorry. Please use phone format +1xxxxxxxxxx.')
        
    if email:
        if re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",email)==None:
            return build_validation_result(False, 'PhoneNumber', 'I am sorry. That may not be a correct email.')

    return build_validation_result(True, None, None)


def build_time_output_string(appointment_time):
    hour, minute = appointment_time.split(':')  # no conversion to int in order to have original string form. for eg) 10:00 instead of 10:0
    if int(hour) > 12:
        return '{}:{} p.m.'.format((int(hour) - 12), minute)
    elif int(hour) == 12:
        return '12:{} p.m.'.format(minute)
    elif int(hour) == 0:
        return '12:{} a.m.'.format(minute)

    return '{}:{} a.m.'.format(hour, minute)


""" --- Intents --- """


def appointment(intent_request):
    
    userID = intent_request['userId']
    location = intent_request['currentIntent']['slots']['Location']
    cuisine = intent_request['currentIntent']['slots']['Cuisine']
    appointment_time = intent_request['currentIntent']['slots']['Time']
    number_of_people = intent_request['currentIntent']['slots']['NumberOfPeople']
    phone_number = intent_request['currentIntent']['slots']['PhoneNumber']
    email = intent_request['currentIntent']['slots']['EmailAddress']
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        slots = intent_request['currentIntent']['slots']
        validation_result = validate_book_appointment(appointment_time,phone_number,email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message'],
                None
            )

        if not location:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Location',
                {'contentType': 'PlainText', 'content': 'Great. I can help you with that. What city are you looking to dine in?'},
                None
            )

        if not cuisine:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Cuisine',
                {'contentType': 'PlainText', 'content': 'Got it. What cuisine would you like to try?(e.g. Chinese/Thai/Sandwich)'},
                None
            )
            
        if not appointment_time:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Time',
                {'contentType': 'PlainText', 'content': 'Then what time?(format: 11:00 a.m./12:00 p.m.)'},
                None
            )
    
        if not number_of_people:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'NumberOfPeople',
                {'contentType': 'PlainText', 'content': 'Ok, how many people are in your party?'},
                None
            )
        
        if not phone_number:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'PhoneNumber',
                {'contentType': 'PlainText', 'content': 'May I have your phone number to which I will send you my findings?(US phone Format:+1xxxxxxxxxx)'},
                None
            )
            
        if not email:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'EmailAddress',
                {'contentType': 'PlainText', 'content': 'Lastly, I need your email address in case you don\'t receive text message.'},
                None
            )
        
        
        if location and cuisine and appointment_time and number_of_people and phone_number and email:
            if confirmation_status == "None":
                return confirm_intent(
                    output_session_attributes,
                    intent_request['currentIntent']['name'],
                    slots,
                        {
                            'contentType': 'PlainText',
                         'content': 'Okay, please check your information.[Location: {}];[Cuisine: {}];[Time: {}];[Number Of People: {}];[Phone Number: {}];[Email: {}]  '.format(location,cuisine,build_time_output_string(appointment_time),number_of_people,phone_number,email)
                        },None
                )
            elif confirmation_status == "Confirmed":
                # Create an SNS client
                sqs = boto3.client('sqs')
                # Publish a simple message to the specified SNS topic
                queue_url = 'https://sqs.us-east-1.amazonaws.com/645446725344/DiningSuggestion'

            # Send message to SQS queue
                response = sqs.send_message(
                    QueueUrl=queue_url,
                    DelaySeconds=1,
                    MessageAttributes={
                        'userID':{
                            'DataType' : 'String',
                            'StringValue' : userID
                        },
                            'Location': {
                            'DataType': 'String',
                            'StringValue': location
                        },
                        'Cuisine': {
                            'DataType': 'String',
                            'StringValue': cuisine
                        },
                        'Time': {
                            'DataType': 'String',
                            'StringValue': appointment_time
                        },
                        'NumberOfPeople': {
                            'DataType': 'Number',
                            'StringValue': number_of_people
                        },
                        'PhoneNumber': {
                             'DataType': 'String',
                            'StringValue': phone_number
                        },
                        'Email': {
                             'DataType': 'String',
                            'StringValue': email
                        }
                    },
                    MessageBody=(
                        'userID:{} time:{}'.format(userID, time.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                )
                return close(
                    output_session_attributes,
                    'Fulfilled',
                    {
                        'contentType': 'PlainText',
                        'content': 'You\'re all set! If I find suggestions, I will notify your phone or your email! Have a good day! '
                    }
                )
            elif confirmation_status == "Denied":
                return close(
                    output_session_attributes,
                    'Failed',
                    {
                        'contentType': 'PlainText',
                        'content': 'Okay, your order is canceled. You can say \'restaurant\' again now. '
                    }
                )
                
        return delegate(output_session_attributes, slots)

    return None


def greeting(intent_request):
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        output_session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Hi there, if you want to looking for restaurant, say \'restaurant\'.'
        }
    )


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    logger.debug(intent_name);
    # Dispatch to your bot's intent handlers
    if intent_name == 'DinningSuggestionsIntent':
        return appointment(intent_request)
    elif intent_name == 'GreetingIntent':
        return greeting(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
