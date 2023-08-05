from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def serve_file():
    return send_file('test.txt')

if __name__ == '__main__':
    app.run()
