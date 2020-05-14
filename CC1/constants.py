import csv

# Dictionary that maps Area Code to Area Name. 
# Data read from AreaNameEnum.csv
area_dict = {}
with open('AreaNameEnum.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter = ',')
    next(csv_reader)
    for row in csv_reader:
        area_dict[int(row[0])] = row[1]


#Url of API.
URL = "http://0.0.0.0"

#Port number
PORT = "5000"

#API Url 
API_URL = URL + ":" + PORT

#Url of API1
API1_URL = '/api/v1/users'

#Url of API2
API2_URL = '/api/v1/users'

#Url of API3
API3_URL = '/api/v1/rides'

#Url of API4
API4_URL = '/api/v1/rides'

#Url of API5
API5_URL = '/api/v1/rides'

#Url of API6
API6_URL = '/api/v1/rides'

#Url of API7
API7_URL = '/api/v1/rides'

#Url of API8
API8_URL = '/api/v1/db/write'

#Url of API9
API9_URL = '/api/v1/db/read'

# Response message 400
MESSAGE_400 = "Bad Request."


