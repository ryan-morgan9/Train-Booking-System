# Individual Travel booking system for trains
# Author: Ryan Morgan
# Group: Easy Travel

import mysql.connector
from mysql.connector import errorcode

#MYSQL CONFIG VARS
hostname = "localhost"
username = "ryan"
pw = "My.Database121"
database = "TrainDB"

def getConnection():
    try:
        conn = mysql.connector.connect(host=hostname,
                                        user=username,
                                        password = pw,
                                        database = database)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('Username or password is not working.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print('Database does not exist')
        else:
            print(err)
    else:
        return conn
