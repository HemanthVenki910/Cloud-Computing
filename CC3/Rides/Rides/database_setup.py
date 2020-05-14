import mysql.connector
from flask import Response

try:
	mydb = mysql.connector.connect(host = "rides-db",user = "root",passwd="root")
	mycursor = mydb.cursor()
	mycursor.execute("DROP DATABASE IF EXISTS RideShare")
	mycursor.execute("CREATE DATABASE RideShare")

except Exception as e :
	print(e)

try:
	mydb = mysql.connector.connect(host="rides-db",user="root",passwd="root",database="RideShare")
	mycursor = mydb.cursor()
	mycursor.execute("DROP TABLE IF EXISTS RIDES;")
	mycursor.execute("CREATE TABLE RIDES (rideId INT AUTO_INCREMENT PRIMARY KEY,created_by VARCHAR(255) BINARY,timestamp VARCHAR(255),source INT,destination INT);")
	mycursor.execute("DROP TABLE IF EXISTS RIDERS;")
	mycursor.execute("CREATE TABLE RIDERS (rideId INT, username VARCHAR(255) BINARY,FOREIGN KEY (rideId) REFERENCES RIDES(rideId) ON DELETE CASCADE);") 


except Exception as e:
	print(e)
