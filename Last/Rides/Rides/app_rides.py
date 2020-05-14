import constants
import flask
import json
import requests
import mysql.connector
import sys

from app_helper import *
from flask import Flask
from flask import jsonify
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

@app.route(constants.API3_URL, methods = ["POST"])
def new_ride():
    print(request.get_json(),file=sys.stderr)
    """API 3

    Adding a ride"""

    request_json = request.get_json()

    if "created_by" not in request_json.keys() or \
        "destination" not in request_json.keys() or \
        "source" not in request_json.keys() or \
        "timestamp" not in request_json.keys():
        return Response("{}", status = 400, mimetype = 'application/json')

    creator_username = request_json["created_by"]
    destination = int(request_json["destination"])
    source = int(request_json["source"])
    timestamp = request_json["timestamp"]
    
    # Using API 9 to ensure username exists in database
    user_api9_url = constants.API_LIST_USER
    headers={'Origin':'52.201.183.55'}
    user_api9_response = requests.get(url = user_api9_url,headers=headers)
    if user_api9_response.status_code == 200:
        if str(creator_username) not in list(user_api9_response.json()):
            return Response(
                "Invalid UserName ", 
                status = 400, 
                mimetype = 'application/json')
    else:
        return Response(
            "Internal Server Error", 
            status = 500, 
            mimetype = 'application/json')

    # Checking if source and destinationination is valid.
    if source not in constants.area_dict.keys() or \
        destination not in constants.area_dict.keys() :
        return Response(
                "Source or destination invalid.", 
                status = 400, 
                mimetype = 'application/json')

    # Checking if timestamp is valid.
    if not is_ridetime_valid(timestamp):
        return Response(
                "Timestamp invalid.", 
                status = 400, 
                mimetype = 'application/json')
    
    if(source < 1 or destination < 1 or source > 198 or destination > 198 ):
            return Response("Wrong Source or Destination",
                status = 400, mimetype = 'application/json')
    
    # Use API 8 to insert ride to ride table. 
    api8_url = constants.API8_URL
    request_data = {}       
    request_data["columns"] = [
        "created_by", 
        "destination",
        "source",
        "timestamp"]
    request_data["operation"] = "INSERT"
    request_data["table"] = "RIDES"
    request_data["values"] = [
        creator_username,
        destination,
        source,
        timestamp]
    
    api8_response = requests.post(url = api8_url, json = request_data)
    if(api8_response.status_code == 200):
        return Response("Entry added.", status = 201, mimetype = 'application/json')
    else:
        return Response("", status = 400, mimetype = 'application/json')


@app.route(constants.API4_URL, methods = ["GET"])
def list_rides():
    """API 4

    List all upcoming rides for a given source and destination."""

    request_json = dict(request.args)
    
    if "destination" not in request_json.keys() or \
        "source" not in request_json.keys() : 
        return Response("{}", status = 400, mimetype = 'application/json')

    destination = int(request_json["destination"])
    source = int(request_json["source"])

    if(source < 1 or destination < 1 or source > 198 or destination > 198 ):
            return Response("Wrong Source or Destination",
                status = 400, mimetype = 'application/json')

    api9_url = constants.API9_URL
    request_data = {}
    request_data["columns"] = ["rideId", "created_by", "timestamp"]
    request_data["table"] = "RIDES"
    request_data["wheres"] = [
        "{} = {}".format("source", source),
        "{} = {}".format("destination", destination)]

    
    api9_response = requests.post(url = api9_url, json =  request_data)
    if api9_response.status_code == 200:
        query_result = api9_response.json()['query_result']
        future_rides = []
        for row in query_result:
            if is_ridetime_in_future(row[2]):
                future_rides.append(dict(
                    rideId = str(row[0]),
                    username = row[1],
                    timestamp = row[2]))
        if len(future_rides) != 0:
            return Response(
                json.dumps(future_rides),
                status = 200, 
                mimetype = 'application/json')
        else:
            return Response(
                "No Content",
                status = 204, 
                mimetype = 'application/json')
    else:
        return Response(
            "Internal Server Error", 
            status = 500, 
            mimetype = 'application/json')

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
    with counter.get_lock():
        counter.value = 0
    return Response("{}",status=200,mimetype='application/json')

@app.route("/api/v1/_count",methods=constants.trapping_methods_for_count)
@exclude_from_analytics
def trap():
    return Response("{}",status=405,mimetype='application/json')

@app.route(constants.API4_URL + "/<int:rideId>", methods = ["GET"])
def list_ride_details(rideId):
    """API 5

    List all the details of a given ride."""

    if rideId == None:
        return Response("{}", status = 400, mimetype = 'application/json')
    
    api9_url = constants.API9_URL

    # Using API 9 to get ride details from the RIDE table.
    request_data = {}
    request_data["columns"] = [
        "rideId", 
        "created_by", 
        "timestamp", 
        "source", 
        "destination"]
    request_data["table"] = "RIDES"
    request_data["wheres"] = ["{} = {}".format("rideId", rideId)]

    api9_response_rides = requests.post(url = api9_url, json =  request_data)
    
    if api9_response_rides.status_code != 200:
        return Response(
            "Internal Server Error", 
            status = 500, 
            mimetype = 'application/json')

    api9_result = api9_response_rides.json()['query_result']
    if len(api9_result) == 0:
        return Response(
            "No such ride",
            status = 400, 
            mimetype = 'application/json')
            
    api9_result = api9_result[0]
    ride_details = {}
    ride_details['rideId'] = str(api9_result[0])
    ride_details['created_by'] = api9_result[1]
    ride_details['timestamp'] = api9_result[2]
    ride_details['source'] = str(api9_result[3])
    ride_details['destination'] = str(api9_result[4])
    
    # Using API 9 to fetch username of all the users associated 
    # with the ride from the RIDERS table.
    request_data = {}
    request_data["columns"] = ["username"]
    request_data["table"] = "RIDERS"
    request_data["wheres"] = ["{} = {}".format("rideId", rideId)]

    api9_response_riders = requests.post(url = api9_url, json =  request_data)
    if api9_response_riders.status_code != 200:
        return Response(
        "Internal Server Error", 
        status = 500, 
        mimetype = 'application/json')
    riders = api9_response_riders.json()['query_result']
    ride_details['users'] = [rider[0] for rider in riders]

    return Response(
        json.dumps(ride_details),
        status = 200, 
        mimetype = 'application/json')

@app.route(constants.API6_URL + "/<rideId>", methods = ["POST"])
def join_existing_ride(rideId):
    """API 6.

    Join an existing ride."""

    request_json = request.get_json()        
    if "username" not in request_json.keys() or rideId == None:
        return Response("{}", status = 400, mimetype = 'application/json')

    username =  request_json["username"]
    
    user_api9_url = constants.API_LIST_USER
    headers={'Origin':'52.201.183.55'}
    user_api9_response = requests.get(url = user_api9_url,headers=headers)
    if user_api9_response.status_code == 200:
        if str(username) not in user_api9_response.json():
            return Response(
                "Username does not exist", 
                status = 400, 
                mimetype = 'application/json')
    
    # Use API 9 to ensure the ride exists
    request_data = {}
    request_data["columns"] = ["rideId", "created_by", "timestamp"]
    request_data["table"] = "RIDES"
    request_data["wheres"] = ["{} = {}".format("rideId", rideId)]
    
    user_api9_url = constants.API_LIST_USER
    headers={'Origin':'52.201.183.55'}
    api9_response = requests.post(url = user_api9_url, json =  request_data,headers=headers)
    if api9_response.status_code == 200:
        if len(api9_response.json()['query_result']) == 0:
            return Response(
                "Ride does not exist", 
                status = 400, 
                mimetype = 'application/json')

        if api9_response.json()['query_result'][0][1] == username:
            return Response(
                    "{}", 
                    status = 400, 
                    mimetype = 'application/json')

    # Use API 8 to insert user to ride.
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["username", "rideId"]
    request_data["operation"] = "INSERT"
    request_data["table"] = "RIDERS"
    request_data["values"] = [username, rideId]
    
    api8_response = requests.post(url = api8_url, json =  request_data)
    if(api8_response.status_code == 200):
        return Response("Entry added.", status = 200, mimetype = 'application/json')
    else:
        return Response("", status = 500, mimetype = 'application/json')

@app.route(constants.API7_URL + "/<rideId>", methods = ["DELETE"])
def remove_ride(rideId):
    """API 7

    Deleting a ride."""

    if rideId == None:
        return Response("{}", status = 400, mimetype = 'application/json')
    
    request_data = {}
    request_data["columns"] = ["rideId"]
    request_data["table"] = "RIDES"
    request_data["wheres"] = ["{} = {}".format("rideId", rideId)]
    
    api9_url = constants.API9_URL

    api9_response = requests.post(url = api9_url, json =  request_data)
    if api9_response.status_code == 200:
        if len(api9_response.json()['query_result']) == 0:
            return Response(
                "Ride does not exist", 
                status = 400, 
                mimetype = 'application/json')
    
    # Use API 8 to delete entry.
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["rideId"]
    request_data["operation"] = "DELETE"
    request_data["table"] = "RIDES"
    request_data["values"] = [rideId]
    
    api8_response = requests.post(url = api8_url, json =  request_data)
    if(api8_response.status_code == 200):
        return Response("Entry Deleted.", status = 200, mimetype = 'application/json')
    else:
        return Response("", status = 500, mimetype = 'application/json')

@app.route("/api/v1/db/clear",methods=["POST"])
@exclude_from_analytics
def clear_db():
    api8_url = constants.API8_URL
    request_data = {}
    request_data["columns"] = ["dummy"]
    request_data["operation"] = "DELETEALL"
    request_data["table"] = "RIDES"
    request_data["values"] = ["dummy@123"]

    api8_response = requests.post(url = api8_url, json = request_data)
    
    if(api8_response.status_code == 200):
        return Response("{}", status=200, mimetype = 'application/json')
    else:
        return Response("{}", status=400, mimetype='application/json')

@app.route("/api/v1/rides/count",methods=["GET"])
def total_rides_created():
    request_data={}
    request_data["columns"] = ["*"]
    request_data["table"] = "RIDES"
    
    api9_url = constants.API9_URL

    api9_response = requests.post(url = api9_url, json =  request_data)
    if api9_response.status_code == 200:
        total_rides=[len(api9_response.json()['query_result'])]
        return Response(
                json.dumps(total_rides),
                status = 200, 
                mimetype = 'application/json')
    else:
        return Response(
                "{}",
                status = 400, 
                mimetype = 'application/json')

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port=5000, debug = True)
