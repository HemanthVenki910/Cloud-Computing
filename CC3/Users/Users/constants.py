import csv

# Dictionary that maps Area Code to Area Name. 
# Data read from AreaNameEnum.csv
area_dict = {}
with open('AreaNameEnum.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter = ',')
    next(csv_reader)
    for row in csv_reader:
        area_dict[int(row[0])] = row[1]


# Url of API.
# TODO : Check if this still has to be 80
API_URL = "http://users:80"

#Url of API1
API1_URL = '/api/v1/users'

#Url of API2
API2_URL = '/api/v1/users'

#Url of API3
API3_URL = '/api/v1/users'
#Url of API8
API8_URL = '/api/v1/db/write'

#Url of API9
API9_URL = '/api/v1/db/read'

# Response message 400
MESSAGE_400 = "Bad Request."

API_RIDES_CLEAR_DB="http://3.214.11.21:80/api/v1/db/clear"

API_RIDES_DELETE_RIDES="http://3.214.11.21:80/api/v1/db/write"

API_COUNTER="/api/v1/_count"

#methods=["GET","POST","PUT","PATCH","DELETE","COPY","HEAD","OPTIONS","LINK","UNLINK","PURGE","LOCK","UNLOCK","PROPFIND","VIEW"]
trapping_methods_for_count=["POST","PUT","PATCH","COPY","HEAD","OPTIONS","LINK","UNLINK","PURGE","LOCK","UNLOCK","PROPFIND","VIEW"]

