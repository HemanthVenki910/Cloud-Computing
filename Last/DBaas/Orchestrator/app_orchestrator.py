import os
import sys
import json
import math
import pika
import time
import uuid
import flask
import sched
import docker 
import helper
import logging
import requests
import constants
import mysql.connector
import threading

from flask import Flask
from flask import Response
from random import random
from threading import Timer
from flask import request
from flask import url_for
from multiprocessing import Process
from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.handlers.gevent import SequentialGeventHandler

from multiprocessing import Value
from datetime import timedelta

app = Flask(__name__)

logging.basicConfig()
zoo_handler = helper.initial_setup()
resource_handler = helper.Query_To_Database()
worker_handler = helper.control_slaves(zoo_handler)

@app.route('/')
@app.route('/Index')
def index_page():
    """Default page."""
    return Response("{}", status = 200, mimetype = 'application/json')

@app.route(constants.API_WRITE_URL, methods = ["POST"])
def write_to_db():
	return resource_handler.write_query_to_database(request)  

@app.route(constants.API_READ_URL,methods = ["POST"])
def read_from_db():
	worker_handler.increment_counter()
	return resource_handler.read_query_from_database(request)

@app.route(constants.API_READ_URL,methods = constants.trapping_methods_for_read_count)
def trap_for_read_methods():
	worker_handler.increment_counter()
	return Response("{}", status = 405, mimetype = 'application/json') 

@app.route(constants.API_CRASH_MASTER, methods = ["POST"])
def crash_master_node():
	master_details = worker_handler.get_master_details()
	worker_handler.crash_worker(master_details)
	master_pid = []
	master_pid.append(int(master_details['Pid']))
	return Response(json.dumps(master_pid), status = 200, mimetype = 'application/json') 

@app.route(constants.API_CRASH_SLAVE , methods = ["POST"])
def crash_slave_node():
	slave_details = worker_handler.get_slave_details()
	worker_handler.crash_worker(slave_details)
	slave_pid = []
	slave_pid.append(int(slave_details['Pid']))
	return Response(json.dumps(slave_pid), status = 200, mimetype = 'application/json') 

@app.route(constants.API_LIST_NODES, methods = ["GET"])
def list_slave_nodes():
	try:
		nodes = worker_handler.get_all_nodes_pid()
		if len(nodes) != 0:
		    return Response(json.dumps(nodes),status=200,mimetype='application/json')
		return Response("{}", status = 204, mimetype = 'application/json')
	except Exception as e:
		return Response("{}".format(e), status = 500, mimetype = 'application/json')

@app.route(constants.API_NOTIFY_ORCHES,methods=["POST"])
def check_znodes():
	worker_handler.handle_control_slaves()
	return Response("{}", status = 200, mimetype = 'application/json')

@app.route(constants.API_CLEAR_DB,methods = ["POST"])
def clear_db():
	api8_url =  "http://52.207.157.87:80/api/v1/db/write"
	request_data = {}
	request_data["columns"] = ["dummy"]
	request_data["operation"] = "DELETEALL"
	request_data["table"] = "USERS"
	request_data["values"] = ["dummy@123"]
	requests.post(url = api8_url, json = request_data)
	return Response("{}", status = 200, mimetype = 'application/json') 

if __name__=="__main__":
	app.run(host = "0.0.0.0", port=5000, debug = True,use_reloader=False)