import os
import sys
import json
import pika
import time
import docker
import logging
import requests
import constants
import mysql.connector 

from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.client import KazooState

def check_for_master(zoo_handler):
    if not zoo_handler.connected:
        zoo_handler.stop()
        raise Exception("Unable to connect.")

    Master_Path="/Master/{}".format(str(os.getpid()))
    
    try:
        if(zoo_handler.exists(Master_Path)):
            return True
        else:
            return False
    except Exception as error:
        print(error)
        return False

def database_setup():
    try:
	    mydb = mysql.connector.connect(host= os.environ['HOST'] , user="root", passwd="root", database="RideShare")
	    mycursor = mydb.cursor()
	    mycursor.execute("DROP TABLE IF EXISTS USERS;")
	    mycursor.execute("CREATE TABLE USERS (username VARCHAR(255) BINARY PRIMARY KEY,password VARCHAR(255));")
	    mycursor.execute("DROP TABLE IF EXISTS RIDES;")
	    mycursor.execute("CREATE TABLE RIDES (rideId INT AUTO_INCREMENT PRIMARY KEY,created_by VARCHAR(255) BINARY,timestamp VARCHAR(255),source INT,destination INT,FOREIGN KEY (created_by) REFERENCES USERS(username) ON DELETE CASCADE);")
	    mycursor.execute("DROP TABLE IF EXISTS RIDERS;")
	    mycursor.execute("CREATE TABLE RIDERS (rideId INT, username VARCHAR(255) BINARY,FOREIGN KEY (username) REFERENCES USERS(username) ON DELETE CASCADE,FOREIGN KEY (rideId) REFERENCES RIDES(rideId) ON DELETE CASCADE);") 
    
    except Exception as e:
        print(e)
    return

def executeScriptsFromFile(cursor,filename):
	fd = open(filename, 'r')
	sqlFile = fd.read()
	fd.close()
	sqlCommands = sqlFile.split(';')
	for command in sqlCommands :
		try:
			cursor.execute(command)
		except Exception :
			pass

def get_master_db_container(zk):
    master_path = "/Master"
    master_node = zk.get_children(master_path)[0]
    path_to_master="/Master/{}".format(str(master_node))
    data , _ = zk.get(path_to_master)
    data = json.loads(data.decode('utf-8'))
    return data['Database']

def initial_setup():
    sql_db_name="sql_db_" + str(os.getpid())
    
    zk = KazooClient(hosts='zoo:2181',timeout=0.5)
    zk.start()

    if not zk.connected:
        zk.stop()
        raise Exception("Unable to connect.")

    if(not zk.exists("/Master")):
	    zk.ensure_path("/Master")

    node_name=str(os.getpid())
    Data_Details ={}
    Data_Details['Pid'] = str(os.getpid())
    Data_Details['Database'] = sql_db_name
    Data_Details['Container'] = str(os.environ['container_name'])
    
    os.environ['Details'] = json.dumps(Data_Details)
    
    Data_Details = os.environ['Details'].encode('utf-8')

    if(len(zk.get_children("/Master")) == 0):
        node_path="/Master/{}".format(node_name) 
        zk.create(node_path,ephemeral=True,makepath=True,include_data=True)
        zk.set(node_path,Data_Details)
    
    node_path="/Worker/{}".format(node_name)
    zk.create(node_path,ephemeral=True,makepath=True,include_data=True)
    zk.set(node_path,Data_Details)

    os.environ['DATABASE'] = "RideShare"
    os.environ['HOST'] = sql_db_name
    os.environ['PASSWD'] ="root"
    os.environ['USER'] = "root"

    try:
        client = docker.from_env()
        client.containers.run("mysql:5.7.22",command = ["--default-authentication-plugin=mysql_native_password"],
        environment = ["MYSQL_ROOT_PASSWORD=root","MYSQL_USER=root","MYSQL_PASSWORD=root","Master=False"],
		ports={'3306/tcp':None}, tty = True, restart_policy={'Name':'on-failure'}, name = sql_db_name, 
		pid_mode = 'host', links = {'flask-orchestrator':'flask-orchestrator'}, network ='dbaas_default', detach = True)
        while True:
            try:
                time.sleep(1)
                mydb=mysql.connector.connect(host = os.environ['HOST'], user = "root",passwd="root")
                mycursor = mydb.cursor()
                mycursor.execute("DROP DATABASE IF EXISTS RideShare")
                mycursor.execute("CREATE DATABASE RideShare")
                mydb.commit()
                mycursor.close()
                if(check_for_master(zk)):
                    database_setup()
                    break
                
                mydb = mysql.connector.connect(host = os.environ['HOST'] ,user = "root",passwd = "root", database = "RideShare")
                mycursor = mydb.cursor()
                time.sleep(2)
                master_db = get_master_db_container(zk)
                command="docker exec {} /usr/bin/mysqldump -u root --password=root RideShare > master_db.sql".format(master_db)
                os.system(command)
                executeScriptsFromFile(mycursor,'master_db.sql')
                mydb.commit()
                mycursor.close()
                break
            
            except Exception as e:
                continue
        
    except Exception as e:
        print(e,file=sys.stderr)
        
    return zk