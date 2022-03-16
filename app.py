
import json
from flask import Flask
from flask import Response
app = Flask(__name__)


@app.route('/test')
def v1_health():
    temp = "test"
    return Response(json.dumps(temp),  status=200, mimetype='application/json')

def print_test():
    print("hello world")

print_test()