from datetime import datetime 

def is_ridetime_valid(ride_timestamp):
    try:
        ride_time = datetime.strptime(ride_timestamp, "%d-%m-%Y:%H-%M-%S")
        return True
    except:
        return False

def is_ridetime_in_future(ride_timestamp):
    try:
        ride_time = datetime.strptime(ride_timestamp, "%d-%m-%Y:%H-%M-%S")
    except:
        return False

    now = datetime.now() # Get current date and time.
    if max(now,ride_time) != ride_time:
        return False
    return True
    
def is_SHA1(password):
    if len(password) != 40:
        return False
    try:
        sha_int = int(password, 16)
    except ValueError:
        return False
    return True
    