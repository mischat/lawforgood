#!venv/bin/python

from flask import Flask, request
import twilio.twiml
import datetime
import json
from googleapiclient.discovery import build

app = Flask(__name__)

service = build('translate', 'v2',
            developerKey='YOUR_GOOGLE_TRANSLATE_API_KEY_HERE')


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

    data = {'from': sms_from,
            'original-body': sms_body,
            'original-language': language_id,
            'translated-body': translated_body,
            'time': sms_time}

    json_data = json.dumps(data)

    print(json_data)
    resp = twilio.twiml.Response()
    resp.message('Hello, Mobile Monkey')
    return str(resp)


@app.route('/voice/reply', methods=['GET', 'POST'])
def voice_hello_monkey():
    """Respond to incoming calls with a simple text message."""
           
    resp = twilio.twiml.Response()
    resp.message('Hello, Voice Monkey')
    return str(resp)

                    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


# vi:set expandtab sts=4 sw=4:
