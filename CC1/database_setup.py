import mysql.connector
from flask import Response

try:
	mydb = mysql.connector.connect(host = "localhost",user = "admin",passwd="admin@123")
	mycursor = mydb.cursor()
	mycursor.execute("DROP DATABASE IF EXISTS RideShare")
	mycursor.execute("CREATE DATABASE RideShare")

except Exception as e :
	print(e)

try:
	mydb = mysql.connector.connect(host="localhost",user="admin",passwd="admin@123",database="RideShare")
	mycursor = mydb.cursor()
	mycursor.execute("DROP TABLE IF EXISTS USERS;")
	mycursor.execute("CREATE TABLE USERS (username VARCHAR(255) BINARY PRIMARY KEY,password VARCHAR(255));")
	mycursor.execute("DROP TABLE IF EXISTS RIDES;")
	mycursor.execute("CREATE TABLE RIDES (rideId INT AUTO_INCREMENT PRIMARY KEY,created_by VARCHAR(255) BINARY,timestamp VARCHAR(255),source INT,destination INT,FOREIGN KEY (created_by) REFERENCES USERS(username) ON DELETE CASCADE);")
	mycursor.execute("DROP TABLE IF EXISTS RIDERS;")
	mycursor.execute("CREATE TABLE RIDERS (rideId INT, username VARCHAR(255) BINARY,FOREIGN KEY (username) REFERENCES USERS(username) ON DELETE CASCADE,FOREIGN KEY (rideId) REFERENCES RIDES(rideId) ON DELETE CASCADE);") 


except Exception as e:
	print(e)
