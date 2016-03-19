#!venv/bin/python

from flask import Flask, request, redirect
import twilio.twiml
import datetime
import json
from googleapiclient.discovery import build
import urllib
import os
import time
import apiai


app = Flask(__name__)

service = build('translate', 'v2',
                developerKey='YOUR_GOOGLE_TRANSLATE_API_KEY_HERE')

CLIENT_ACCESS_TOKEN = 'YOUR_AI_API_CLIENT_ACCESS_TOKEN_HERE'
SUBSCRIPTION_KEY = 'YOUR_AI_API_SUBSCRIPTION_KEY_HERE'


@app.route('/sms/reply', methods=['GET', 'POST'])
def hello_monkey():
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

    data = {'from': sms_from,
            'original-body': sms_body,
            'original-language': language_id,
            'translated-body': translated_body,
            'intentId': ai_intent_id,
            'time': sms_time}

    json_data = json.dumps(data)
    print(json_data)

    reply = 'Hello, thank you for getting in contact, we understand your distress, someone will be in contact soon!'

    gt = service.translations().list(
        target=language_id,
        q=[reply]
    ).execute()

    resp = twilio.twiml.Response()
    resp.message(gt['translations'][0]['translatedText'])
    return str(resp)


@app.route('/voice/reply', methods=['GET', 'POST'])
def voice_hello_monkey():
    """Respond to incoming calls with a simple text message."""

    resp = twilio.twiml.Response()
    resp.say('Hello, welcome to the Hackney Community Law Center')

    with resp.gather(numDigits=1, action='/handle-key', method='POST') as g:
        g.say("""To record a voice message in English please press 1
              otherwise please text us in the language of your choice to
                01253531170 thanks you""")

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

    #here we create the JSON for Tom

    return str(resp)


@app.route('/wav', methods=['GET', 'POST'])
def handle_wave():

    epoch_filename = str(time.time()) + '.wav'

    wave_url = 'https://api.twilio.com/2010-04-01/Accounts/ACa8e6432e82557adb5a48fc44b32b963b/Recordings/REf479e71030485db784f5aa8fb72fd45f'

    urllib.urlretrieve(wave_url, '/tmp/' + epoch_filename )

    output = os.popen('/usr/local/bin/sox /tmp/' + epoch_filename + ' -r 16000 /tmp/working.' + epoch_filename).read()

    print output

    curl_wav = os.popen('curl -k -F "request={\'timezone\':\'America/New_York\',\'lang\':\'en\'};type=application/json" -F "voiceData=@/tmp/working.' + epoch_filename + ';type=audio/wav" -H "Authorization: Bearer 0e010641a9db48eb8f53079054de0526" -H "ocp-apim-subscription-key: 5c0f3443-00dd-4da5-8a19-f39d8b934956" "https://api.api.ai/v1/query?v=20150910"').read()

    print curl_wav

    os.remove('/tmp/' + epoch_filename)
    os.remove('/tmp/working.' + epoch_filename)

    return str('lame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


# vi:set expandtab sts=4 sw=4:
