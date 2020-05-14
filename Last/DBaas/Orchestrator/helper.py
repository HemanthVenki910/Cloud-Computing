import os
import json
import pika
import time
import uuid
import docker
import logging
import math
import sys
import threading

from random import random
from flask import Response
from multiprocessing import Value
from threading import Timer
from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler

logging.basicConfig()

def initial_setup():
	zk = KazooClient(hosts='zoo:2181')
	zk.start()

	if not zk.connected:
		zk.stop()
		raise Exception("Unable to connect.")

	if(not zk.exists("/Master")):
		zk.ensure_path("/Master")
	if(not zk.exists("/Worker")):
		zk.ensure_path("/Worker")
	return zk

class Query_To_Database(object):
	def __init__(self):
		self.params = pika.ConnectionParameters(host='rmq')
		self.params.heartbeat = 0
		self.params.socket_timeout = 2
		self.connection = pika.BlockingConnection(self.params)
		self.channel = self.connection.channel()
	
		self.write_response_data = None
		self.write_correl_id = None
		self.read_correl_id = None
		self.read_response_data = None
		self.write_lock = Value('i', 0)

		self.write_result = self.channel.queue_declare(queue='', exclusive=True)
		self.read_result = self.channel.queue_declare(queue='Response_Queue', exclusive=True)
		self.write_callback_queue = self.write_result.method.queue

		self.channel.basic_consume(queue=self.write_callback_queue,on_message_callback=self.write_response,auto_ack=True)
		self.channel.basic_consume(queue='Response_Queue',on_message_callback=self.read_response,auto_ack=True)

	def write_response(self,channel,method,properties,message_body):
		if self.write_correl_id == properties.correlation_id:
			self.write_response_data = json.loads(message_body)

	def read_response(self,channel,method,properties,message_body):
		if self.read_correl_id == properties.correlation_id:
			self.read_response_data = json.loads(message_body)
	
	def write_query_to_database(self,request_data):
		try:
			with self.write_lock.get_lock():
				self.write_response_data = None
				self.write_correl_id = str(uuid.uuid4())
				data_to_send = request_data.get_json()
				self.channel.basic_publish(exchange='',routing_key='Write_Queue',body=json.dumps(data_to_send),
				properties=pika.BasicProperties(reply_to=self.write_callback_queue,correlation_id=self.write_correl_id,))
				while(self.write_response_data is None):
					self.connection.process_data_events()
			return Response("{}".format(self.write_response_data['data']), status = self.write_response_data['status_code'],mimetype = 'application/json')
		except Exception as e:
			return Response("{}".format(e), status = 500, mimetype = 'application/json')
	
	def read_query_from_database(self,request_data):
		try:
			with self.write_lock.get_lock():
				self.read_response_data = None
				self.read_correl_id = str(uuid.uuid4())
				data_to_send = request_data.get_json()
				self.channel.basic_publish(exchange='',routing_key='Read_Queue',body=json.dumps(data_to_send),
				properties=pika.BasicProperties(reply_to='Response_Queue',correlation_id=self.read_correl_id,))
				while(self.read_response_data is None):
					self.connection.process_data_events()
			return Response("{}".format(self.read_response_data['data']), status = self.read_response_data['status_code'],mimetype = 'application/json')
		except Exception as e:
			return Response("{}".format(e), status = 500, mimetype = 'application/json')

class control_slaves(object):
	
	def __init__(self,zoo_handler):
		self.read_counter     = Value('i', 0)
		self.zoo_handler_lock = Value('i', 0)
		self.current_number   = Value('i', 2) 
		self.required_number  = Value('i', 2)
		self.client = docker.from_env()
		self.zoo_handler = zoo_handler
		self.start = False
		self.changes = threading.Lock()
		return
	
	def start_timer(self):
		if(not self.start):
			self.start = True
			timer = Timer(120.0,self.timer_on_counts)
			timer.start()
			print("Timer Called at {}".format(time.ctime()),file=sys.stderr,flush=True)
		return
	
	def handle_control_slaves(self):
		if(self.changes.locked()):
			pass
		else :
			threading.Thread(target=self.control_slaves,args=()).start()

	def timer_on_counts(self) :
		with self.read_counter.get_lock():
			total_slaves = self.read_counter.value
			self.read_counter.value=0
		total_slaves = math.ceil(total_slaves/20)
		if(total_slaves  ==  0):
			total_slaves = 1
		total_slaves += 1
		print("Timer Called at {}".format(time.ctime()),file=sys.stderr,flush=True)
		timer = Timer(120.0, self.timer_on_counts)
		timer.start()
		with self.required_number.get_lock():
			self.required_number.value = total_slaves
		self.handle_control_slaves()

	def increment_counter(self):
		try:
			with self.read_counter.get_lock():
				self.start_timer()
				self.read_counter.value += 1
		except Exception:
			pass

	def get_all_nodes_pid(self):
		with self.zoo_handler_lock.get_lock():
			znodes = self.zoo_handler.get_children("/Worker")
		znodes = [int(i) for i in znodes]
		znodes.sort()
		return znodes

	def get_master_details(self):
		with self.zoo_handler_lock.get_lock():
			master_path = "/Master"
			master_node = self.zoo_handler.get_children(master_path)[0]
			path_to_master="/Master/{}".format(str(master_node))
			data , _ = self.zoo_handler.get(path_to_master)
		data = json.loads(data.decode('utf-8'))
		return data
	
	def get_slave_details(self):
		children = self.get_all_nodes_pid()
		lowest_child = children[-1]
		path_to_slave="/Worker/{}".format(str(lowest_child))
		with self.zoo_handler_lock.get_lock():
			data , _ = self.zoo_handler.get(path_to_slave)	
		data = json.loads(data.decode('utf-8'))
		return data
	
	def create_worker(self):
		master_details = self.get_master_details()
		master_container = self.client.containers.get(master_details['Container'])
		master_image = master_container.commit(master_details['Container'])
		container_name = "worker" + str(math.ceil(random() * 100000))
		self.client.containers.run( master_image,command="python3 -u app_worker.py",
		environment=["container_name={}".format(container_name)],
		name =container_name,pid_mode = 'host',tty=True,restart_policy={'Name':'on-failure'}, 
		volumes={'/var/run/docker.sock':{'bind':'/var/run/docker.sock'}},
		links = {'flask-orchestrator':'flask-orchestrator'}, stop_signal = 'SIGINT',
		network='dbaas_default',detach = True)
		return 

	def crash_worker(self,worker_details):
		worker_container = self.client.containers.get(worker_details['Container'])
		worker_container.stop()
		worker_database = self.client.containers.get(worker_details['Database'])
		worker_database.stop()
		self.client.containers.prune()
	
	# def set_signal(self):
	# 	with self.zoo_handler_lock.get_lock():
	# 		self.zoo_handler.create("/Signal") 
	# 	return
	# def clear_signal(self):
	# 	with self.zoo_handler_lock.get_lock():
	# 		if self.zoo_handler.exists("/Signal"):
	# 			self.zoo_handler.delete("/Signal")
	# 	return
	
	def control_slaves(self):
		self.changes.acquire()
		with self.current_number.get_lock() and self.required_number.get_lock():
			znodes=self.get_all_nodes_pid()
			self.current_number.value=len(znodes)
			if(self.current_number.value == self.required_number.value):
				pass
			
			elif(self.current_number.value < self.required_number.value):
				# self.set_signal()
				while(self.current_number.value != self.required_number.value):
					self.create_worker()
					self.current_number.value += 1
				# self.clear_signal()

			elif(self.current_number.value > self.required_number.value):
				# self.set_signal()
				while(self.current_number.value != self.required_number.value):
					slave_details = self.get_slave_details()
					self.crash_worker(slave_details)
					self.current_number.value -= 1
				# self.clear_signal()
			time.sleep(5)
		self.changes.release() 
		return
