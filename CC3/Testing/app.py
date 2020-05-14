from flask import Flask , request
from flask import Response
import json
from multiprocessing import Value
from functools import wraps
import requests

trapping_methods=["POST", "HEAD", "POST", "OPTIONS", "PUT", "PATCH"]
counter = Value('i', 0)
with counter.get_lock():
    try:
        with open('Counter.txt', 'r+') as f:
            counter.value = int(f.readline(256).split(":")[1])
    except Exception as e:
            File=open('Counter.txt','w+')
            File.truncate(0)          
            File.writelines("Counter_Value :{}".format(0))
            File.close()

app = Flask(__name__)

@app.before_request
def analytics_view(*args,**kwargs):
    run_analytics = True
    if request.endpoint in app.view_functions:
        view_func = app.view_functions[request.endpoint]
        run_analytics = not hasattr(view_func, '_exclude_from_analytics')
    if run_analytics:
        increment_storage()

def increment_storage():
    with open('Counter.txt', 'r+') as f , counter.get_lock():
        counter.value = int(f.readline(256).split(':')[-1])
        counter.value += 1
        f.truncate(0)
        f.writelines("Counter_Value :{}".format(counter.value))


def exclude_from_analytics(func):
    func._exclude_from_analytics = True
    return func

@app.route('/',methods=["GET"])
@app.route("/Index")
def index():
    return "Hello {}".format("Hello")


@app.route('/count',methods=["POST"])
def counter1():
    return "Counter1"

@app.route('/count1',methods=["GET"])
def counter2():
    url="0.0.0.0:80"
    api="/request"
    api8_response=requests.post(url = url+api,Origin="127.0.0.1")
    return api8_response

@app.route("/request",methods=["GET"])
def counter3():
    return "{}".format(request.headers)
    
@app.route("/api/v1/_count",methods=["GET"])
@exclude_from_analytics
def get_counter():
    get_counter._exclude_from_analytics=True
    with counter.get_lock():
        unique_value=[counter.value]
    return Response(json.dumps(unique_value),status=200,mimetype='application/json')

@app.route("/api/v1/_count",methods=["DELETE"])
@exclude_from_analytics
def clear_counter():
    clear_counter._exclude_from_analytics=True
    with open('Counter.txt', 'r+') as f , counter.get_lock():
        counter.value = 0
        f.truncate(0)
        f.writelines("Counter_Value : {}".format(counter.value))
    return Response("{}",status=200,mimetype='application/json')

@app.route("/api/v1/_count",methods=trapping_methods)
@exclude_from_analytics
def trap():
    return "Hello Trapped"

if __name__=="__main__":
    app.run(host = "0.0.0.0",port=80, debug = True)
