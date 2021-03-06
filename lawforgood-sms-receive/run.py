#!venv/bin/python
import requests
from flask import Flask, request, redirect, jsonify
import twilio.twiml
from twilio.rest import TwilioRestClient
import datetime
import json
from googleapiclient.discovery import build
import urllib
import os
import time
import apiai
import tinys3
from mailer import Mailer
from mailer import Message


app = Flask(__name__)

GOOGLE_TRANSLATE_API_KEY = 'YOUR_GOOGLE_TRANSLATE_API_KEY_HERE'

CLIENT_ACCESS_TOKEN = 'YOUR_AI_API_CLIENT_ACCESS_TOKEN_HERE'
SUBSCRIPTION_KEY = 'YOUR_AI_API_SUBSCRIPTION_KEY_HERE'

AWS_ACCESS_KEY_ID = 'YOUR_AWS_ACCESS_KEY_ID_HERE'
AWS_SECRET_ACCESS_KEY = 'YOUR_AWS_SECRET_ACCESS_KEY_HERE'

SMS_ACCOUNT_SID = 'YOUR_SMS_ACCOUNT_SID_HERE'
SMS_AUTH_TOKEN = 'YOUR_SMS_AUTH_TOKEN_HERE'

TRELLO_EMAIL = 'hackneylaw+kgy0nw2d5dxmvoxeqnfo@boards.trello.com'

GMAIL_USER = 'YOUR_GMAIL_USER_HERE'
GMAIL_PASSWORD = 'YOUR_GMAIL_PASSWORD_HERE'

service = build('translate', 'v2',
                developerKey=GOOGLE_TRANSLATE_API_KEY)


@app.route('/sms/send', methods=['POST'])
def send_sms():

    sms_to = request.json.get('to')
    sms_body = request.json.get('body')
    sms_lang = request.json.get('lang')

    account_sid = SMS_ACCOUNT_SID
    auth_token = SMS_AUTH_TOKEN
    client = TwilioRestClient(account_sid, auth_token)

    gt = service.translations().list(
        target=sms_lang,
        q=[sms_body]
    ).execute()

    translated_body = gt['translations'][0]['translatedText']

    client.messages.create(body=translated_body,
                           to=sms_to,
                           from_='+441253531170')

    return jsonify({'status': 'done'}), 201


@app.route('/sms/reply', methods=['GET', 'POST'])
def handle_sms():
    """Respond to incoming calls with a simple text message."""

    sms_body = str(request.args['Body'])
    sms_from = str(request.args['From'])
    sms_time = str(datetime.datetime.utcnow().isoformat())

    gt = service.translations().list(
        target='en',
        q=[sms_body]
    ).execute()

    language_id = gt['translations'][0]['detectedSourceLanguage']
    translated_body = gt['translations'][0]['translatedText']

    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN, SUBSCRIPTION_KEY)
    ai_request = ai.text_request()
    ai_request.lang = 'en'

    ai_request.query = translated_body

    ai_response = ai_request.getresponse().read()
    ai_response_dict = json.loads(ai_response)

    ai_intent_id = ''
    try:
        ai_intent_id = ai_response_dict['result']['metadata']['intentId']
    except KeyError:
        # Key is not present
        pass

    data = {'from': 'tel:' + sms_from,
            'original-body': sms_body,
            'original-language': language_id,
            'translated-body': translated_body,
            'intentId': ai_intent_id,
            'time': sms_time}

    json_data = json.dumps(data)
    print(json_data)

    message = Message(From='hackneylaw@mmt.me.uk',
                      To=TRELLO_EMAIL)
    message.Subject = 'Incoming call from' + sms_from + ' at ' + sms_time
    message.Html = json_data

    sender = Mailer('smtp.gmail.com', use_tls=True, usr=GMAIL_USER, pwd=GMAIL_PASSWORD)
    sender.send(message)

    try:
        requests.post('https://hackneylawclassifier.herokuapp.com/receive', data=data)
    except:
        pass

    reply = 'Hello, thank you for getting in contact, we understand your distress, someone will be in contact soon!'

    gt = service.translations().list(
        target=language_id,
        q=[reply]
    ).execute()

    resp = twilio.twiml.Response()
    resp.message(gt['translations'][0]['translatedText'])
    return str(resp)


@app.route('/voice/reply', methods=['GET', 'POST'])
def handle_voice():
    """Respond to incoming calls with a simple text message."""

    resp = twilio.twiml.Response()
    resp.say('Hello, welcome to the Hackney Community Law Center')

    with resp.gather(numDigits=1, action='/handle-key', method='POST') as g:
        g.say("""To record a voice message in English please press 1 otherwise please text us in the language of your choice to 01253531170 thank you""")

    return str(resp)


@app.route('/handle-key', methods=['GET', 'POST'])
def handle_key():
    """Handle key press from a user."""

    digit_pressed = request.values.get('Digits', None)
    if digit_pressed == '1':
        resp = twilio.twiml.Response()
        resp.say('Record your message after the tone and please press the hash key to stop recording')
        resp.record(maxLength='30',
                    action='/handle-recording',
                    finishOnKey='#')
        return str(resp)

    # If the caller pressed anything but 1, redirect them to the homepage.
    else:
        return redirect('/voice/reply')


@app.route('/handle-recording', methods=['GET', 'POST'])
def handle_recording():
    """Play back the caller's recording."""

    recording_url = request.values.get('RecordingUrl', None)
    print('This is the recording of the phone call ' + recording_url)

    resp = twilio.twiml.Response()
    resp.say('Thanks for leaving us a message ... take a listen to what you recorded.')
    resp.play(recording_url)
    resp.say('Goodbye.')

    epoch_filename = str(time.time()) + '.wav'
    urllib.urlretrieve(recording_url, '/tmp/' + epoch_filename)

    output = os.popen('/usr/local/bin/sox /tmp/' + epoch_filename + ' -r 16000 /tmp/working.' + epoch_filename).read()

    print output

    ai_response = os.popen('curl -k -F "request={\'timezone\':\'Europe/London\',\'lang\':\'en\'};type=application/json" -F "voiceData=@/tmp/working.' + epoch_filename + ';type=audio/wav" -H "Authorization: Bearer 0e010641a9db48eb8f53079054de0526" -H "ocp-apim-subscription-key: 5c0f3443-00dd-4da5-8a19-f39d8b934956" "https://api.api.ai/v1/query?v=20150910"').read()

    print ai_response
    ai_response_dict = json.loads(ai_response)

    ai_intent_id = ''
    try:
        ai_intent_id = ai_response_dict['result']['metadata']['intentId']
    except KeyError:
        # Key is not present
        pass

    conn = tinys3.Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,tls=True,endpoint='s3-eu-west-1.amazonaws.com')

    f = open('/tmp/working.' + epoch_filename, 'rb')
    conn.upload(epoch_filename, f, 'mischatlawaudio')

    os.remove('/tmp/' + epoch_filename)
    os.remove('/tmp/working.' + epoch_filename)

    wav_s3_url = 'https://s3-eu-west-1.amazonaws.com/mischatlawaudio/' + epoch_filename

    sms_from = str(request.values.get('From', None))
    sms_time = str(datetime.datetime.utcnow().isoformat())

    data = {'from': 'tel:' + sms_from,
            'wav-url': wav_s3_url,
            'intentId': ai_intent_id,
            'time': sms_time}

    json_data = json.dumps(data)
    print(json_data)

    message = Message(From='hackneylaw@mmt.me.uk',
                      To=TRELLO_EMAIL)
    message.Subject = 'Incoming call from' + sms_from + ' at ' + sms_time
    message.Html = json_data

    sender = Mailer('smtp.gmail.com', use_tls=True, usr=GMAIL_USER, pwd=GMAIL_PASSWORD)
    sender.send(message)

    try:
        requests.post('https://hackneylawclassifier.herokuapp.com/receive', data=data)
    except:
        pass

    return str(resp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


# vi:set expandtab sts=4 sw=4:
