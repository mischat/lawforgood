#!venv/bin/python

from flask import Flask, request, redirect
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
    resp.say('Hello, This is Hackney Law Help Center')

    with resp.gather(numDigits=1, action='/handle-key', method='POST') as g:
        g.say("""To record a message press 1""")

    return str(resp)


@app.route('/handle-key', methods=['GET', 'POST'])
def handle_key():
    """Handle key press from a user."""

    digit_pressed = request.values.get('Digits', None)
    if digit_pressed == '2':
        resp = twilio.twiml.Response()
        resp.say('Record your message after the tone and please press the hash key to stop recording')
        resp.record(maxLength='30', action='/handle-recording', finishOnKey='#', transcribe='true')
        return str(resp)

    # If the caller pressed anything but 1, redirect them to the homepage.
    else:
        return redirect('/voice/reply')


@app.route('/handle-recording', methods=['GET', 'POST'])
def handle_recording():
    """Play back the caller's recording."""

    recording_url = request.values.get('RecordingUrl', None)

    resp = twilio.twiml.Response()
    resp.say('Thanks for recording ... take a listen to what you howled.')
    resp.play(recording_url)
    resp.say('Goodbye.')
    return str(resp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


# vi:set expandtab sts=4 sw=4:
