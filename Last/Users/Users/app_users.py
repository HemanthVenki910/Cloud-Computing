import constants
import flask
import json
import mysql
import requests
import mysql.connector

from app_helper import *
from flask import Flask
from flask import Response
from flask import request
from flask import url_for
from multiprocessing import Value

counter = Value('i', 0)

app = Flask(__name__)
app.config.from_object(__name__)

@app.before_request
def analytics_view(*args,**kwargs):
    run_analytics = True
    if request.endpoint in app.view_functions:
        view_func = app.view_functions[request.endpoint]
        run_analytics = not hasattr(view_func, '_exclude_from_analytics')
    if run_analytics:
        increment_storage()

def increment_storage():
    try:
        with counter.get_lock():
            counter.value += 1
    except Exception:
        pass

def exclude_from_analytics(func):
    func._exclude_from_analytics = True
    return func

@app.route('/')
@app.route('/Index')
@exclude_from_analytics
def index_page():
    """Default page."""
    return Response("{}", status = 200, mimetype = 'application/json')

@app.route(constants.API1_URL, methods = ["PUT"])
def add_user():
    """API 1

    Adding an user"""
    request_json = request.get_json()

    if "username" not in request_json.keys() or "password" not in request_json.keys():
        return Response("{}", status = 400, mimetype = 'application/json')

    username =  request_json["username"]
    password =  request_json["password"]

    if not is_SHA1(password):
        return Response("{}", status = 400, mimetype = 'application/json')

    # Use API 9 to ensure username is unique. 
    api9_url = constants.API9_URL
    request_data = {}
    request_data["columns"] = ["username"]
    request_data["table"] = "USERS"
    request_data["wheres"] = ["{} = \"{}\"".format("username", username)]

    api9_response = requests.post(url = api9_url, json = request_data)
    if api9_response.status_code == 200:
        if len(api9_response.json()['query_result']):
            return Response(
                "{}", 
                status = 400, 
                mimetype = 'application/json')
    else:
        return Response("{}".format(str(api9_response.json())), status = 500, mimetype = 'application/json')

    # Use API 8 to insert username and password. 
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["username", "password"]
    request_data["operation"] = "INSERT"
    request_data["table"] = "USERS"
    request_data["values"] = [username, password]
    
    api8_response = requests.post(url = api8_url, json = request_data)
    if(api8_response.status_code == 200):
        return Response("Entry added.", status = 201, mimetype = 'application/json')
    else:
        return Response("{}", status = 500, mimetype = 'application/json')

@app.route(constants.API2_URL + "/<username>", methods = ["DELETE"])
def remove_user(username):
    """API 2

    Removing an user."""

    if username == None:
        return Response("{}", status = 400, mimetype = 'application/json')

    # Using API 9 to ensure username exists in database
    api9_url = constants.API9_URL
    request_data = {}
    request_data["columns"] = ["username"]
    request_data["table"] = "USERS"
    request_data["wheres"] = ["{} = '{}'".format("username", username)]
    api9_response = requests.post(url = api9_url, json =  request_data)

    if api9_response.status_code == 200:
        if len(api9_response.json()['query_result']) == 0:
            return Response(
                "{}", 
                status = 400, 
                mimetype = 'application/json')
    else:
        return Response(
            "{}", 
            status = 500, 
            mimetype = 'application/json')

    # Use API 8 to delete entry.
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["username"]
    request_data["operation"] = "DELETE"
    request_data["table"] = "USERS"
    request_data["values"] = [username]
    
    api8_response = requests.post(url = api8_url, json =  request_data)
    
    if(api8_response.status_code == 200):
        return Response(".", status = 200, mimetype = 'application/json')
    else:
        return Response("{}", status = 500, mimetype = 'application/json')

@app.route("/api/v1/users", methods=["GET"])
def list_all_users():
    """API 3

	List of all the users in the database."""
    
    api9_url = constants.API9_URL
    request_data = {}
    request_data["columns"] = ["username"]
    request_data["table"] = "USERS"
    
    api9_response = requests.post(url=api9_url, json=request_data)

    if api9_response.status_code == 200 : 
        query_result = (api9_response.json()['query_result'])
        user_names = []
        for row in query_result:
            user_names.append(row[0])   
        if len(user_names) != 0:
            return Response(
                json.dumps(user_names),
                status=200,
                mimetype='application/json')
        else:
            return Response(
                " ",
                status=204,
                mimetype='application/json')

    else:
        return Response(
            " ", 
            status = 500, 
            mimetype = 'application/json')

@app.route("/api/v1/db/clear",methods=["POST"])
@exclude_from_analytics
def clear_db():
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["dummy"]
    request_data["operation"] = "DELETEALL"
    request_data["table"] = "USERS"
    request_data["values"] = ["dummy@123"]

    api8_response = requests.post(url = api8_url, json = request_data)
    try:
        requests.post(url = constants.API_RIDES_CLEAR_DB)
    except:
        return Response("{}", status=400, mimetype='application/json')
        
    if(api8_response.status_code == 200):
        return Response("{}", status=200, mimetype = 'application/json')
    else:
        return Response("{}", status=400, mimetype='application/json')

@app.route("/api/v1/_count",methods=["GET"])
@exclude_from_analytics
def get_counter():
    get_counter._exclude_from_analytics=True
    with counter.get_lock():
        print("\nCount is --> {}\n".format(counter.value))
        unique_value=[counter.value]
    return Response(json.dumps(unique_value),status=200,mimetype='application/json')

@app.route("/api/v1/_count",methods=["DELETE"])
@exclude_from_analytics
def clear_counter():
    with counter.get_lock():
        counter.value = 0
    return Response("{}",status=200,mimetype='application/json')

@app.route("/api/v1/_count",methods=constants.trapping_methods_for_count)
@exclude_from_analytics
def trap():
    return Response("{}",status=405,mimetype='application/json')


@app.route("/api/v1/users/request", methods = ["POST"])
@exclude_from_analytics
def requests_header():
    return "{}".format(request.headers)

if __name__=="__main__":
    app.run(host = "0.0.0.0", port=5000, debug = True)