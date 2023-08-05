from flask import Flask
import base64

app = Flask(__name__)

@app.route('/')

def hello_world():
    decoded_text = base64.b64decode('SSBhbSB3YXRjaGluZyB5b3UsIE1hcml1cyBO').decode('utf-8')
    return decoded_text

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    