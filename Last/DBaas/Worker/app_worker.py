import os
import sys
import json
import pika
import time
import logging
import requests
import constants
import worker_helper
import mysql.connector

from worker_helper import check_for_master
from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
logging.basicConfig()

def write_to_db(request):
    Response_data={}
    try:
        rideshare_db = mysql.connector.connect(
                        database = os.environ['DATABASE'],
                        host = os.environ['HOST'],
                        passwd = os.environ['PASSWD'],
                        user = os.environ['USER'])
        cursor = rideshare_db.cursor()

    except:
        print("Error Response")
        Response_data['data']='No connection'
        Response_data['status_code']=500
        return Response_data    

    request_json = request

    if "columns" not in request_json.keys() or \
        "values" not in request_json.keys() or \
        "operation" not in request_json.keys() or \
        "table" not in request_json.keys() :
        Response_data['data']="{}".format(request)
        Response_data['status_code']=400
        return Response_data

    columns = request["columns"]
    data = request["values"]
    operation = request["operation"].upper()
    table = request["table"].upper()
    try:
        if operation == "INSERT":
            values = ','.join([
                "'{}'".format(value) if type(value) == str \
                    else str(value) for value in data])
            query = "INSERT INTO {} ({}) VALUES ({});".format(
                table, ', '.join(columns), values)
            cursor.execute(query)
            rideshare_db.commit()
            Response_data['data']="{}"
            Response_data['status_code']=200
            return Response_data

        elif operation == "DELETE":
            argument_list = [
                "{} = '{}'".format(str(column_name), str(column_value)) \
                    if type(column_value) == str \
                    else "{} = {}".format(str(column_name), str(column_value)) \
                    for column_name, column_value in zip(columns, data)]
            
            query_argument = ' and '.join(argument_list)
            query = "DELETE FROM {} WHERE BINARY {};".format(table, query_argument)
            print(query)
            cursor.execute(query)
            rideshare_db.commit()
            Response_data['data']="{}"
            Response_data['status_code']=200
            return Response_data
        
        elif operation == "DELETEALL":
            query="DELETE FROM {} ;".format(table)
            cursor.execute(query)
            rideshare_db.commit()
            cursor.close()
            Response_data['data']="{}"
            Response_data['status_code']=200
            return Response_data

        else:
            Response_data['data']="{}"
            Response_data['status_code']=400
            return Response_data

    except Exception as e:
            Response_data['data']="{}".format(e)
            Response_data['status_code']=500
            return Response_data


def read_from_db(request):
    Response_data={}
    try:	
        rideshare_db = mysql.connector.connect(
                        database = os.environ['DATABASE'],
                        host = os.environ['HOST'],
                        passwd = os.environ['PASSWD'],
                        user = os.environ['USER'])
        cursor = rideshare_db.cursor()	

    except Exception as e:
        Response_data['data']="No Connection"
        Response_data['status_code']= 500
        return Response_data

    request_json = request

    if "columns" not in request_json.keys() or "table" not in request_json.keys():
        Response_data['data']="{}"
        Response_data['status_code']= 400
        return Response_data

    columns = request_json["columns"]
    table = request_json["table"].upper()
    wheres = None
    if "wheres" in request_json.keys():
        wheres = request_json["wheres"]
    try:
        column_list = ", ".join(columns)
        if wheres:
            where_list = " AND ".join(wheres)
            query = "SELECT {} FROM {} WHERE {};".format(column_list, table, where_list)
        else:
            query = "SELECT {} FROM {};".format(column_list, table)

        cursor.execute(query)
        query_set = cursor.fetchall()
        cursor.close()
        query_result = []
        for row in query_set:
            row = list(row)
            for i in range(len(row)):
                if type(row[i]) == bytearray:
                    row[i] = row[i].decode("utf-8")
            query_result.append(row)

        Response_data['data']=json.dumps({"query_result" : query_result})
        Response_data['status_code']= 200
        return Response_data

    except Exception as e:
        Response_data['data']="{}".format(e)
        Response_data['status_code']= 400
        return Response_data

def write_call_to_db(ch, method, properties_received, message_body):
    if(not(check_for_master(zoo_handler))):
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
        return
    Response_data=write_to_db(json.loads(message_body.decode("utf-8")))
    if(Response_data['status_code'] == 200):
        sync_channel.basic_publish(exchange='logs',routing_key='',body=message_body)
        connection.process_data_events()

    ch.basic_publish(exchange='',routing_key=properties_received.reply_to,body=json.dumps(Response_data),
    properties=pika.BasicProperties(correlation_id = properties_received.correlation_id,))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    return

def read_call_to_db(ch, method, properties_received, message_body):
    if(check_for_master(zoo_handler)):
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
        return
    Response_data=read_from_db(json.loads(message_body.decode("utf-8")))
    ch.basic_publish(exchange='',routing_key=properties_received.reply_to,body=json.dumps(Response_data),
    properties=pika.BasicProperties(correlation_id = properties_received.correlation_id,))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    return
    
def sync_data_to_db(ch, method, properties, message_body):
    if((check_for_master(zoo_handler))):
        return
    write_to_db(json.loads(message_body.decode("utf-8")))
    return

params = pika.ConnectionParameters(host='rmq')
params.heartbeat = 0
params.socket_timeout = 2
connection = pika.BlockingConnection(params)
#params.socket_timeout = 2
#Check the Usage tommorow
#params.heartbeat = 0
#connection = pika.BlockingConnection(params)
channel = connection.channel()

sync_channel = connection.channel()
sync_channel.exchange_declare(exchange='logs',exchange_type='fanout')
syncResult = channel.queue_declare(queue='',exclusive=True)
sync_queue_name = syncResult.method.queue
channel.queue_bind(exchange='logs',queue=sync_queue_name)
channel.basic_consume(queue=sync_queue_name, on_message_callback=sync_data_to_db,auto_ack=True)
channel.queue_declare(queue='Write_Queue', durable=True)
channel.basic_consume(queue='Write_Queue', on_message_callback=write_call_to_db)
channel.queue_declare(queue='Read_Queue', durable=True)
channel.basic_consume(queue='Read_Queue', on_message_callback=read_call_to_db)

zoo_handler=worker_helper.initial_setup()

@zoo_handler.ChildrenWatch("/Master")
def watch_master(children):
    if(len(children) == 1): #when initially any changes are made to the Master Node
        return
    children = zoo_handler.get_children("/Worker")
    children = [int(i) for i in children]
    children.sort()
    if(children[0] == os.getpid()):
        node_name = str(os.getpid())
        node_path ="/Master/{}".format(node_name) 
        zoo_handler.create(node_path,ephemeral = True,makepath = True,include_data = True)
        Data_Details = os.environ['Details'].encode('utf-8')
        zoo_handler.set(node_path,Data_Details)
        requests.post(url=constants.API_NOTIFY_ORCHES)
    return

@zoo_handler.ChildrenWatch("/Worker")
def watch_worker(children):
    # if(zoo_handler.exists("/Signal")):
    #     print("Scale Down",flush=True)
    #     return
    children = [int(i) for i in children]
    children.sort()
    if(children[0] == os.getpid()):
        if(len(zoo_handler.get_children("/Master")) == 0):
            watch_master(children)
        requests.post(url=constants.API_NOTIFY_ORCHES)
    return

channel.basic_qos(prefetch_count=1)
channel.start_consuming()
sync_channel.basic_qos(prefetch_count=1)
sync_channel.start_consuming()
