#!venv/bin/python

from flask import Flask, request, redirect
import twilio.twiml
 
app = Flask(__name__)

@app.route('/sms/reply', methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming calls with a simple text message."""

    print(str(request.Body()))
           
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
