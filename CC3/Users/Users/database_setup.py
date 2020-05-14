import mysql.connector
from flask import Response

try:
	mydb = mysql.connector.connect(host = "users-db",user = "root",passwd="root")
	mycursor = mydb.cursor()
	mycursor.execute("DROP DATABASE IF EXISTS RideShare")
	mycursor.execute("CREATE DATABASE RideShare")

except Exception as e :
	print(e)

try:
	mydb = mysql.connector.connect(host="users-db",user="root",passwd="root",database="RideShare")
	mycursor = mydb.cursor()
	mycursor.execute("DROP TABLE IF EXISTS USERS;")
	mycursor.execute("CREATE TABLE USERS (username VARCHAR(255) PRIMARY KEY,password VARCHAR(255));")

except Exception as e:
	print(e)

