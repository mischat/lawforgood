#!venv/bin/python

from flask import Flask, request, redirect
import twilio.twiml
import datetime
import json
 
app = Flask(__name__)


@app.route('/sms/reply', methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming calls with a simple text message."""

    sms_body = str(request.args['Body'])
    sms_from = str(request.args['From'])
    sms_time = str(datetime.datetime.utcnow().isoformat())

    data = {'from': sms_from, 'body': sms_body, 'time': sms_time}
    json_data = json.dumps(data)

    print 'JSON: ' + json_data

    print('Message "' + sms_body + '" from " ' + sms_from + ' ' + sms_time)
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
