# Individual Travel booking system for trains
# Author: Ryan Morgan
# Group: Easy Travel

from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector, dbfunc
from functools import wraps
import datetime
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SecretKey'

conn = dbfunc.getConnection()
DB_NAME = 'TrainDB'
TIMETABLE = 'TrainTimetable'
USERTABLE = 'User'
TRIPTABLE = 'TrainBooking'

#LOGIN VALIDATION

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:    
            print('Not logged in')        
            flash('You need to log in first.', category='error')
            return redirect(url_for('login'))    
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('logged_in' in session) and (session['usertype'] == 'admin'):
            return f(*args, **kwargs)
        else:            
            print("You are not logged in as an admin")
            flash('You are not logged in as an admin, therefore you cannot access this page.', category='error')
            return redirect(url_for('login'))   
    return wrap

def standard_user_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('logged_in' in session) and (session['usertype'] == 'customer'):
            return f(*args, **kwargs)
        else:            
            print("You are not logged in as a customer")
            flash('You are not logged in as a customer, therefore you cannot access this page.', category='error')
            return redirect(url_for('login'))  
    return wrap

#VIEWS

@app.route('/base')
def home():
    return render_template("base.html", logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/search')
def search():
    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                SELECT_statement = "SELECT DISTINCT departPlace FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()
                cities = []
                for city in rows:
                    city = str(city).strip("(")
                    city = str(city).strip(")")
                    city = str(city).strip(",")
                    city = str(city).strip("'")
                    cities.append(city)
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("trainlookup.html", trips=cities, logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template("trainlookup.html", logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route ('/returncity/', methods = ['POST', 'GET'])
def ajax_returncity():   
	print('/returncity') 

	if request.method == 'GET':
		deptcity = request.args.get('q')
		conn = dbfunc.getConnection()
		if conn != None:    #Checking if connection is None         
			print('MySQL Connection is established')                          
			dbcursor = conn.cursor()    #Creating cursor object            
			dbcursor.execute('SELECT DISTINCT arrivePlace FROM TrainTimetable WHERE departPlace = %s;', (deptcity,))   
			#print('SELECT statement executed successfully.')             
			rows = dbcursor.fetchall()
			total = dbcursor.rowcount                                    
			dbcursor.close()              
			conn.close() #Connection must be closed			
			return jsonify(returncities=rows, size=total)
		else:
			print('DB connection Error')
			return jsonify(returncities='DB Connection Error')
    

@app.route('/response', methods=['GET', 'POST'])
def response():
    if request.method == 'POST':
        departCity = request.form['departTrip']
        arriveCity = request.form['arrivalslist']
        departDate = request.form['departDate']
        returnDate = request.form['returnDate']
        triptype = request.form['triptype']
        NumSeatAdult = request.form['NumSeatAdult']
        NumSeatChild = request.form['NumSeatChild']
        lookupdata = [departCity, arriveCity, departDate, returnDate, triptype, NumSeatAdult, NumSeatChild]
        print(lookupdata)

        if (arriveCity == 'Dundee') or (arriveCity == 'Cardiff'):
            flash("Trains do not travel to " + str(arriveCity), category='error')
            print("Trains do not travel to " + str(arriveCity))
            return redirect(url_for('search'))

        if triptype == 'oneway':
            returnDate = None
            seatsavailableReturn = None

        date = departDate.split("-")
        print(date)
        date = datetime.date(int(date[0]), int(date[1]), int(date[2])).strftime('%A')
        print(date)

        dateReturn = None
        if returnDate != None:
            dateReturn = returnDate.split("-")
            print(dateReturn)
            dateReturn = datetime.date(int(dateReturn[0]), int(dateReturn[1]), int(dateReturn[2])).strftime('%A')
            print(dateReturn)

        if date == 'Saturday' or dateReturn == 'Saturday':
            flash("Trains do not run on Saturday's.", category='error')
            print("Train service does not run on Saturday.")
            return redirect(url_for('search'))

        if int(NumSeatAdult) == 0 and int(NumSeatChild) > 0:
            flash('Children must be accompanied by an adult.', category='error')
            return redirect(url_for('search'))

        conn = dbfunc.getConnection()
        if conn != None:    #Checking if connection is None         
            print('MySQL Connection is established')                          
            dbcursor = conn.cursor(buffered=True)    #Creating cursor object 
            try:         
                dbcursor.execute('SELECT * FROM TrainTimetable WHERE departPlace = %s AND arrivePlace = %s;', (departCity, arriveCity))            
                rows = dbcursor.fetchall()
                datarows=[]			
                for row in rows:
                    data = list(row)
                    #print(data)
                    datarows.append(data)			
                print(datarows)
                print(len(datarows))

                #Price For Number of People
                prices = []
                adultPrice = float(datarows[0][5]) * float(NumSeatAdult)
                childPrice = (float(datarows[0][5]) / 2) * float(NumSeatChild)
                totalPrice = float(adultPrice) + float(childPrice)
                prices.append(adultPrice)
                prices.append(childPrice)
                prices.append(totalPrice)

                #Getting seats availability
                dbcursor.execute('SELECT * FROM TrainBooking WHERE tripId = %s AND departDate = %s;', (datarows[0][0], departDate,)) 
                seatdata = dbcursor.fetchall()
                dataseats = []
                dataseatsReturn = [] #Return Trip Array - NOT ALWAYS USED
                for seat in seatdata:
                    sd = list(seat)
                    #print(sd)
                    dataseats.append(sd)
                seatsavailable = 200
                for seatrow in dataseats:
                    seatsavailable -= seatrow[5]
                    seatsavailable -= seatrow[6]
                #SEAT AVAILABILITY FOR RETURN TRIP    
                if triptype == 'return':
                    dbcursor.execute('SELECT * FROM TrainBooking WHERE tripId = %s AND departDate = %s;', (datarows[0][0], returnDate,)) 
                    seatdataReturn = dbcursor.fetchall()
                    for seatReturn in seatdataReturn:
                        sdReturn = list(seatReturn)
                        #print(sd)
                        dataseatsReturn.append(sdReturn)
                    seatsavailableReturn = 200
                    for seatrowReturn in dataseatsReturn:
                        seatsavailableReturn -= seatrowReturn[5]
                        seatsavailableReturn -= seatrowReturn[6]
                seatavailability = []
                seatavailability.append(seatsavailable)
                seatavailability.append(seatsavailableReturn)

                dbcursor.close()            
                conn.close() #Connection must be closed
                return render_template('trainresponse.html', resultset=datarows, lookupdata=lookupdata, seatavailability=seatavailability, triptype=triptype, prices=prices, logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print(e)
                return redirect(url_for('search'))
        else:
            print('DB connection Error')
            return redirect(url_for('book'))


@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                SELECT_statement = "SELECT DISTINCT departPlace FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()
                cities = []
                for city in rows:
                    city = str(city).strip("(")
                    city = str(city).strip(")")
                    city = str(city).strip(",")
                    city = str(city).strip("'")
                    cities.append(city)
                return render_template("trainbook.html", trips=cities, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)
                return redirect(url_for('book'))

            dbcursor.close()
            conn.close()
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'

@app.route('/selectbooking', methods=['GET', 'POST'])
@login_required
def selectbooking():
    if request.method == 'POST':
        #print('Select booking initiated')
        departCity = request.form['departTrip']
        arriveCity = request.form['arrivalslist']
        departDate = request.form['departDate']
        returnDate = request.form['returnDate']
        NumSeatAdult = request.form['NumSeatAdult']
        NumSeatChild = request.form['NumSeatChild']
        triptype = request.form['triptype']

        if triptype == 'oneway':
            returnDate = None

        lookupdata = [departCity, arriveCity, departDate, returnDate, NumSeatAdult, NumSeatChild, triptype]
        print(lookupdata)

        if (arriveCity == 'Dundee') or (arriveCity == 'Cardiff'):
            flash("Trains do not travel to " + str(arriveCity), category='error')
            print("Trains do not travel to " + str(arriveCity))
            return redirect(url_for('search'))

        date = departDate.split("-")
        print(date)
        date = datetime.date(int(date[0]), int(date[1]), int(date[2])).strftime('%A')
        print(date)

        dateReturn = None
        if returnDate != None:
            dateReturn = returnDate.split("-")
            print(dateReturn)
            dateReturn = datetime.date(int(dateReturn[0]), int(dateReturn[1]), int(dateReturn[2])).strftime('%A')
            print(dateReturn)

        if date == 'Saturday' or dateReturn == 'Saturday':
            flash("Trains do not run on Saturday's.", category='error')
            print("Train service does not run on Saturday.")
            return redirect(url_for('book'))

        if int(NumSeatAdult) == 0 and int(NumSeatChild) > 0:
            flash('Children must be accompanied by an adult.', category='error')
            return redirect(url_for('book'))

        conn = dbfunc.getConnection()
        if conn != None:    #Checking if connection is None         
            print('MySQL Connection is established')                          
            dbcursor = conn.cursor()    #Creating cursor object 
            try:           
                dbcursor.execute('SELECT * FROM TrainTimetable WHERE departPlace = %s AND arrivePlace = %s;', (departCity, arriveCity))   
            #	print('SELECT statement executed successfully.')             
                rows = dbcursor.fetchall()
                datarows=[]			
                for row in rows:
                    data = list(row)          
                    price = ((float(row[5]) * float(NumSeatAdult)) + ((float(row[5]) / 2) * float(NumSeatChild)))
                    if triptype == 'return':
                        price = price * 2
                    #print(price)
                    data.append(price)
                    #print(data)
                    datarows.append(data)			
                dbcursor.close()            
                conn.close() #Connection must be closed
                print(datarows)
                print(len(datarows))			
                return render_template('selectbooking.html', resultset=datarows, lookupdata=lookupdata, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print(e)
                return redirect(url_for('book'))
        else:
            print('DB connection Error')
            return redirect(url_for('book'))

@app.route('/paymentsuccess')
@login_required
def paymentsuccess():
    return render_template('paymentsuccess.html')

@app.route('/custconfirm', methods=['GET', 'POST'])
@login_required
def custconfirm():
    if request.method == 'POST':		
        #print('booking confirm initiated')
        journeyid = request.form['bookingchoice']		
        departPlace = request.form['departPlace']
        arrivePlace = request.form['arrivePlace']
        departDate = request.form['departDate']
        returnDate = request.form.get('returnDate', False)
        NumSeatAdult = request.form['NumSeatAdult']
        NumSeatChild = request.form['NumSeatChild']
        triptype = request.form['triptype']
        totalfare = request.form['totalfare']
        paytype = request.form['paytype']
        cardnumber = request.form['cardNum']

        if triptype == 'oneway':
            returnDate = None
            seatsavailableReturn = None

        bookingdata = [journeyid, departPlace, arrivePlace, departDate, returnDate, NumSeatAdult, NumSeatChild, triptype, totalfare]
        #print(bookingdata)
        conn = dbfunc.getConnection()
        if conn != None:    #Checking if connection is None         
            print('MySQL Connection is established')                          
            dbcursor = conn.cursor(buffered=True)    #Creating cursor object  
            try:
                #Getting seats availability
                totalseats = int(NumSeatAdult) + int(NumSeatChild)
                dbcursor.execute('SELECT * FROM TrainBooking WHERE tripId = %s AND departDate = %s;', (journeyid, departDate,)) 
                seatdata = dbcursor.fetchall()
                dataseats = []
                dataseatsReturn = [] #Return Trip Array - NOT ALWAYS USED
                for seat in seatdata:
                    sd = list(seat)
                    #print(sd)
                    dataseats.append(sd)
                seatsavailable = 200
                for seatrow in dataseats:
                    seatsavailable -= seatrow[5]
                    seatsavailable -= seatrow[6]
                if seatsavailable < totalseats:
                    flash('No seats available for trip.', category='error')
                    return redirect(url_for('book'))
                #SEAT AVAILABILITY FOR RETURN TRIP    
                if triptype == 'return':
                    dbcursor.execute('SELECT * FROM TrainBooking WHERE tripId = %s AND departDate = %s;', (journeyid, returnDate,)) 
                    seatdataReturn = dbcursor.fetchall()
                    for seatReturn in seatdataReturn:
                        sdReturn = list(seatReturn)
                        #print(sd)
                        dataseatsReturn.append(sdReturn)
                    seatsavailableReturn = 200
                    for seatrowReturn in dataseatsReturn:
                        seatsavailableReturn -= seatrowReturn[5]
                        seatsavailableReturn -= seatrowReturn[6]
                    if seatsavailableReturn < totalseats:
                        flash('No seats available for return.', category='error')
                        return redirect(url_for('book'))
                seatavailability = []
                seatavailability.append(seatsavailable)
                seatavailability.append(seatsavailableReturn)

                #Insert booking
                dbcursor.execute('INSERT INTO TrainBooking (\
                    userId, tripId, departDate, returnDate, adultNum, childNum, tripType, priceTotal, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now());', (session.get('userId'), journeyid, departDate, returnDate, NumSeatAdult, NumSeatChild, triptype, totalfare))   
                print('Booking statement executed successfully.')             
                conn.commit()	
                #dbcursor.execute('SELECT AUTO_INCREMENT - 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s;', ('TEST_DB', 'bookings'))   
                dbcursor.execute('SELECT LAST_INSERT_ID();')
                print('SELECT statement executed successfully.')             
                rows = dbcursor.fetchone()
                bookingid = rows[0]
                bookingdata.append(bookingid)
                dbcursor.execute('SELECT * FROM TrainTimetable WHERE tripId = %s;', (journeyid,))   			
                rows = dbcursor.fetchall()
                #print(rows)
                deptTime = rows[0][2]
                arrivTime = rows[0][4]
                bookingdata.append(deptTime)
                bookingdata.append(arrivTime)
                #print(bookingdata)
                #print(len(bookingdata))
                cardnumber = cardnumber[12:]
                print(cardnumber)
            except mysql.connector.Error as e:
                print(e)
                flash(e, category='error')
                return redirect(url_for('book'))

            #Creating text file receipt for user to download
            receipt_name = session.get('name')+"_Booking.txt"
            with open(session.get('name')+"_Booking.txt", "w") as cust_receipt:
                for item in bookingdata:
                    cust_receipt.write(str(item) + "\n")
                cust_receipt.close()

            dbcursor.close()              
            conn.close() #Connection must be closed
            return render_template('custconfirm.html', resultset=bookingdata, cardnumber=cardnumber, receipt_name=receipt_name, paytype=paytype, seatavailability=seatavailability, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection Error')
            return redirect(url_for('book'))
    return render_template("custconfirm.html")

@app.route("/custconfirm/<path>")
@login_required
def DownloadReceipt(path = None):
    return send_file(path, as_attachment=True)
    
@app.route('/customer', methods=['GET', 'POST'])
@login_required
def customer():
    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                session.pop('bookId', None)
                session.pop('priceOneway', None)
                session.pop('priceReturn', None)
                print('MySQL Connection is established.')
                TRIPS_SELECT = 'SELECT * FROM TrainBooking WHERE userId = %s;' 
                dbcursor = conn.cursor()

                customer_dataset = (session.get('userId'),)
                dbcursor.execute(TRIPS_SELECT, customer_dataset)
                print("SELECT successful.")
                user_bookings = dbcursor.fetchall()
                return render_template("customer.html", user_book=user_bookings, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("customer.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'

@app.route('/custupdate', methods=['GET', 'POST'])
@login_required
def custupdate():
    if request.method == 'POST':
        booking = request.form.get('booking')
        departTrip = request.form.get('departTrip')
        departDate = request.form.get('departDate')
        returnDate = request.form.get('returnDate')
        NumSeatAdult = request.form.get('NumSeatAdult')
        NumSeatChild = request.form.get('NumSeatChild')
        triptype = request.form.get('triptype')
        
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    if triptype == 'oneway':
                        returnDate = None

                    #VALIDATION FOR IF THE NEW DATE IS ON SATURDAY
                    date = departDate.split("-")
                    print(date)
                    date = datetime.date(int(date[0]), int(date[1]), int(date[2])).strftime('%A')
                    print(date)

                    dateReturn = None
                    if returnDate != None:
                        dateReturn = returnDate.split("-")
                        print(dateReturn)
                        dateReturn = datetime.date(int(dateReturn[0]), int(dateReturn[1]), int(dateReturn[2])).strftime('%A')
                        print(dateReturn)

                    if date == 'Saturday' or dateReturn == 'Saturday':
                        flash("Trains do not run on Saturday's.", category='error')
                        print("Train service does not run on Saturday.")
                        return redirect(url_for('custupdate'))

                    #validation for children being accompanied by an adult
                    if int(NumSeatAdult) == 0 and int(NumSeatChild) > 0:
                        flash('Children must be accompanied by an adult.', category='error')
                        return redirect(url_for('custupdate'))

                    #VALIDATION FOR NOT BEING ABLE TO CHANGE BOOKING 72 HOURS BEFORE DEPARTURE
                    booking_statement = 'SELECT * FROM TrainBooking WHERE bookId = %s;'
                    dbcursor.execute(booking_statement, (booking, ))
                    rows = dbcursor.fetchall()
                    print(rows)
                    datebook = str(rows[0][3]).split("-")
                    #print(datebook)
                    datebook = datetime.datetime(int(datebook[0]), int(datebook[1]), int(datebook[2]))
                    #print(datebook)
                    datebook = datebook - timedelta(days = 3)
                    print(datebook)
                    datenow = datetime.datetime.now()
                    print(datenow)

                    if datenow > datebook:
                        flash("You cannot modify a booking 72 hours before departure.", category='error')
                        print("cannot modify trips 72 hours before departure.")
                        return redirect(url_for('customer'))

                    #ONEWAY
                    tripId_statement = 'SELECT * FROM TrainTimetable WHERE tripId = %s;'
                    getId_dataset = (departTrip,)
                    dbcursor.execute(tripId_statement, getId_dataset)
                    print('SELECT statement executed successfully.')             
                    tid = dbcursor.fetchone()
                    print(tid)
                    print(tid[0], tid[5])

                    if (str(tid[3]) == 'Dundee') or (str(tid[3]) == 'Cardiff'):
                        flash("Trains do not travel to " + str(tid[3]), category='error')
                        print("Trains do not travel to " + str(tid[3]))
                        return redirect(url_for('custupdate'))

                    oneway_price = ((tid[5] * int(NumSeatAdult)) + ((tid[5] / 2) * int(NumSeatChild)))
                    return_price = 0

                    #RETURN
                    if triptype == 'return':
                        if returnDate != None:
                            return_price = ((tid[5] * int(NumSeatAdult)) + ((tid[5] / 2) * int(NumSeatChild)))
                        else:
                            print("Not all return details are present")
                            flash('Not all return details are filled in', category='error')
                            return redirect(url_for('book'))
                    else:
                        returnDate = None

                    total_price = oneway_price + return_price

                    #UPDATE BOOKING
                    UPDATE_BOOKING = 'UPDATE TrainBooking SET \
                    tripId = %s, \
                    departDate = %s, \
                    returnDate = %s, \
                    adultNum = %s, \
                    childNum = %s, \
                    tripType = %s, \
                    priceTotal = %s \
                    WHERE bookId = %s;'
                    book_dataset = (departTrip, departDate, returnDate, NumSeatAdult, NumSeatChild, triptype, total_price, booking,)
                    dbcursor.execute(UPDATE_BOOKING, book_dataset)
                    conn.commit()
                    print("UPDATE done successfully:\n", book_dataset)
                    flash('Booking Updated!', category='success')

                    return redirect(url_for('customer'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                #Getting trips to show on form
                SELECT_statement = "SELECT * FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()

                #Getting bookings to show on form
                TRIPS_SELECT = 'SELECT * FROM TrainBooking WHERE userId = %s;' 
                dbcursor = conn.cursor()
                customer_dataset = (session.get('userId'),)
                dbcursor.execute(TRIPS_SELECT, customer_dataset)
                print("SELECT successful.")
                user_bookings = dbcursor.fetchall()

                return render_template("custupdate.html", user_book=user_bookings, trips=rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("customer.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template("custupdate.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/custdel', methods=['GET', 'POST'])
@login_required
def custdel():
    if request.method == 'POST':
        booking = request.form.get('booking')
        
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    #FIND BOOKING FOR 50% REFUND AND DATE VALIDATION
                    delcustbooking = (booking, )
                    dbcursor.execute("SELECT * FROM TrainBooking WHERE bookId = %s;", delcustbooking)
                    rows = dbcursor.fetchone()
                    #print(rows)
                    refund = int(rows[8]) / 2

                    date = str(rows[3]).split("-")
                    #print(date)
                    date = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
                    #print(date)
                    date = date - timedelta(days = 3)
                    print(date)
                    datenow = datetime.datetime.now()
                    print(datenow)

                    if datenow > date:
                        flash("You cannot cancel a booking 72 hours before departure.", category='error')
                        print("cannot cancel trips 72 hours before departure.")
                        return redirect(url_for('customer'))
                    
                    #DELETE BOOKING
                    DELETE_BOOKING = "DELETE FROM TrainBooking WHERE bookId = %s"
                    dbcursor.execute(DELETE_BOOKING, delcustbooking)
                    conn.commit()
                    print("DELETE statement executed successfully, deleted booking:\n", booking)

                    flash("£" + str(refund) + " is to be refunded (50% \
                        of booking cost). Booking Cancelled.", category='success')

                    return redirect(url_for('customer'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                #Getting bookings to show on form
                TRIPS_SELECT = 'SELECT * FROM TrainBooking WHERE userId = %s;' 
                dbcursor = conn.cursor()
                customer_dataset = (session.get('userId'),)
                dbcursor.execute(TRIPS_SELECT, customer_dataset)
                print("SELECT successful.")
                user_bookings = dbcursor.fetchall()

                return render_template("custdel.html", user_book=user_bookings, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("customer.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template("custdel.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
    

@app.route('/admin')
@login_required
@admin_required
def admin():
    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            print('MySQL Connection is established.')
            TRIPS_SELECT = "SELECT * FROM TrainBooking"
            dbcursor = conn.cursor()

            dbcursor.execute(TRIPS_SELECT)
            print("SELECT successful.")
            booking_rows = dbcursor.fetchall()

            dbcursor.close()
            conn.close()
            return render_template("admin.html", cust_book=booking_rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'


@app.route('/adminupdate', methods=['GET', 'POST'])
@login_required
@admin_required
def adminupdate():
    if request.method == 'POST':
        booking = request.form.get('booking')
        departTrip = request.form.get('departTrip')
        departDate = request.form.get('departDate')
        returnTrip = request.form.get('returnTrip')
        returnDate = request.form.get('returnDate')
        NumSeatAdult = request.form.get('NumSeatAdult')
        NumSeatChild = request.form.get('NumSeatChild')
        triptype = request.form.get('triptype')

        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    session.pop('bookId', None)

                    #ONEWAY
                    tripId_statement = 'SELECT * FROM TrainTimetable WHERE tripId = %s;'
                    getId_dataset = (departTrip,)
                    dbcursor.execute(tripId_statement, getId_dataset)
                    print('SELECT statement executed successfully.')             
                    tid = dbcursor.fetchone()
                    print(tid)
                    print(tid[0], tid[5])

                    oneway_price = ((tid[5] * int(NumSeatAdult)) + ((tid[5] / 2) * int(NumSeatChild)))
                    return_price = 0

                    #RETURN
                    if triptype == 'return':
                        if returnDate != None:
                            return_price = ((tid[5] * int(NumSeatAdult)) + ((tid[5] / 2) * int(NumSeatChild)))
                        else:
                            print("Not all return details are present")
                            flash('Not all return details are filled in', category='error')
                            return redirect(url_for('book'))
                    else:
                        returnDate = None

                    total_price = oneway_price + return_price

                    #UPDATE BOOKING
                    UPDATE_BOOKING = 'UPDATE TrainBooking SET \
                    tripId = %s, \
                    departDate = %s, \
                    returnDate = %s, \
                    adultNum = %s, \
                    childNum = %s, \
                    tripType = %s, \
                    priceTotal = %s \
                    WHERE bookId = %s;'
                    book_dataset = (departTrip, departDate, returnDate, NumSeatAdult, NumSeatChild, triptype, total_price, booking,)
                    dbcursor.execute(UPDATE_BOOKING, book_dataset)
                    conn.commit()
                    print("UPDATE done successfully:\n", book_dataset)
                    flash('Booking Updated!', category='success')

                    return redirect(url_for('admin'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                #Getting trips to show on form
                SELECT_statement = "SELECT * FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()

                #Getting bookings to show on form
                TRIPS_SELECT = 'SELECT * FROM TrainBooking' 
                dbcursor = conn.cursor()
                dbcursor.execute(TRIPS_SELECT)
                print("SELECT successful.")
                user_bookings = dbcursor.fetchall()

                return render_template("adminupdate.html", user_book=user_bookings, trips=rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("admin.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template("adminupdate.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/admindel', methods=['GET', 'POST'])
@login_required
@admin_required
def admindel():
    if request.method == 'POST':
        booking = request.form.get('booking')
        
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    session.pop('bookId', None)
                    #DELETE BOOKING
                    DELETE_BOOKING = "DELETE FROM TrainBooking WHERE bookId = %s"
                    delcustbooking = (booking, )
                    dbcursor.execute(DELETE_BOOKING, delcustbooking)
                    conn.commit()
                    print("DELETE statement executed successfully, deleted booking:\n", booking)
                    flash('Booking Deleted.', category='success')

                    return redirect(url_for('customer'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                #Getting bookings to show on form
                TRIPS_SELECT = 'SELECT * FROM TrainBooking' 
                dbcursor = conn.cursor()
                dbcursor.execute(TRIPS_SELECT)
                print("SELECT successful.")
                user_bookings = dbcursor.fetchall()

                return render_template("admindel.html", user_book=user_bookings, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                print('Failed retrieving data')
                print(e)

            dbcursor.close()
            conn.close()
            return render_template("customer.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template("admindel.html", name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/adminrouteadd', methods=['GET', 'POST'])
@login_required
@admin_required
def adminroute():
    if request.method == 'POST':
        tripId = request.form.get('tripId')
        departPlace = request.form.get('departPlace')
        departTime = request.form.get('departTime')
        arrivePlace = request.form.get('arrivePlace')
        arriveTime = request.form.get('arriveTime')
        price = request.form.get('price')
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                try:
                    print('MySQL Connection is established.')
                    dbcursor = conn.cursor()
                    INSERT_JOURNEY = "INSERT INTO TrainTimetable (\
                    tripId, departPlace, departTime, arrivePlace, arriveTime, price) \
                    VALUES (%s, %s, %s, %s, %s, %s);"
                    journey_dataset = (tripId, departPlace, departTime, arrivePlace, arriveTime, price,)
                    dbcursor.execute(INSERT_JOURNEY, journey_dataset)
                    conn.commit()
                    print("INSERT done successfully:\n", journey_dataset)
                    flash('New Journey Added!', category='success')

                    dbcursor.close()
                    conn.close()
                    return redirect(url_for('admin'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)
                    return redirect(url_for('admin'))
            else:
                print('DB connection error...')
                return 'DB connection error...'
        else:
            print('dbfunc error...')
            return 'dbfunc error...'

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                SELECT_statement = "SELECT * FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()

                dbcursor.close()
                conn.close()
                return render_template('adminrouteadd.html', routes=rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                flash(e, category='error')
                print(e)
                return redirect(url_for('admin'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template('adminrouteadd.html', name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/adminroutemod', methods=['GET', 'POST']) #change this so there cannot be duplicate id's
@login_required
@admin_required
def adminmodify():
    if request.method == 'POST':
        tripId = request.form.get('tripId')
        departPlace = request.form.get('departPlace')
        departTime = request.form.get('departTime')
        arrivePlace = request.form.get('arrivePlace')
        arriveTime = request.form.get('arriveTime')
        price = request.form.get('price')
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                try:
                    print('MySQL Connection is established.')
                    dbcursor = conn.cursor()
                    UPDATE_JOURNEY = "UPDATE TrainTimetable SET \
                    departPlace = %s, \
                    departTime = %s, \
                    arrivePlace = %s, \
                    arriveTime = %s, \
                    price = %s \
                    WHERE tripId = %s;"
                    journey_dataset = (departPlace, departTime, arrivePlace, arriveTime, price, tripId, )
                    dbcursor.execute(UPDATE_JOURNEY, journey_dataset)
                    conn.commit()
                    print("UPDATE done successfully:\n", journey_dataset)
                    flash('Journey Has Been Modified!', category='success')

                    dbcursor.close()
                    conn.close()
                    return redirect(url_for('admin'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)
                    return redirect(url_for('admin'))
            else:
                print('DB connection error...')
                return 'DB connection error...'
        else:
            print('dbfunc error...')
            return 'dbfunc error...'

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                SELECT_statement = "SELECT * FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()

                dbcursor.close()
                conn.close()
                return render_template('adminroutemod.html', routes=rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                flash(e, category='error')
                print(e)
                return redirect(url_for('admin'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template('adminroutemod.html', name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/adminroutedel', methods=['GET', 'POST']) #change this so there cannot be duplicate id's
@login_required
@admin_required
def adminroutedel():
    if request.method == 'POST':
        tripId = request.form.get('tripId')
        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                try:
                    print('MySQL Connection is established.')
                    dbcursor = conn.cursor()
                    DELETE_JOURNEY = "DELETE FROM TrainTimetable \
                    WHERE tripId = %s;"
                    journey_dataset = (tripId, )
                    dbcursor.execute(DELETE_JOURNEY, journey_dataset)
                    conn.commit()
                    print("Successfully Deleted:\n", journey_dataset)
                    flash('Journey Has Been Deleted!', category='success')

                    dbcursor.close()
                    conn.close()
                    return redirect(url_for('admin'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)
                    return redirect(url_for('admin'))
            else:
                print('DB connection error...')
                return 'DB connection error...'
        else:
            print('dbfunc error...')
            return 'dbfunc error...'

    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            try:
                print('MySQL Connection is established.')
                SELECT_statement = "SELECT * FROM TrainTimetable"
                dbcursor = conn.cursor()
                dbcursor.execute(SELECT_statement)
                print("SELECT successful.")
                rows = dbcursor.fetchall()

                dbcursor.close()
                conn.close()
                return render_template('adminroutedel.html', routes=rows, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                flash(e, category='error')
                print(e)
                return redirect(url_for('admin'))
        else:
            print('DB connection error...')
            return 'DB connection error...'
    else:
        print('dbfunc error...')
        return 'dbfunc error...'
    return render_template('adminroutedel.html', name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/adminreportbookings', methods=['GET', 'POST'])
@login_required
@admin_required
def adminreportbookings():
    if request.method == 'POST':
        dateFirst = request.form.get('dateFirst')
        dateLast = request.form.get('dateLast')

        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    SELECT_BOOKINGS = 'SELECT * FROM TrainBooking WHERE departDate BETWEEN %s AND %s ORDER BY departDate DESC;'
                    dates_dataset = (dateFirst, dateLast, )
                    dbcursor.execute(SELECT_BOOKINGS, dates_dataset)
                    booked = dbcursor.fetchall()
                    bookedrows = dbcursor.rowcount

                    return render_template('adminreportbookingsresp.html', bookings=booked, bookingsrows=bookedrows, dateFirst=dateFirst, dateLast=dateLast, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)
                    return redirect(url_for('admin'))

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')
    return render_template('adminreportbookings.html', name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/adminreportpassenger', methods=['GET', 'POST'])
@login_required
@admin_required
def adminreportpassenger():
    if request.method == 'POST':
        trip = request.form.get('trip')
        dateJourney = request.form.get('dateJourney')

        conn = dbfunc.getConnection()
        if conn != None:
            if conn.is_connected():
                print('MySQL Connection is established.')
                dbcursor = conn.cursor()
                try:
                    SELECT_PASSENGERS = 'SELECT * FROM TrainBooking WHERE tripId = %s  AND departDate = %s OR tripId = %s  AND returnDate = %s ORDER BY userId ASC;'
                    passenger_dataset = (trip, dateJourney, trip, dateJourney, )
                    dbcursor.execute(SELECT_PASSENGERS, passenger_dataset)
                    passenger = dbcursor.fetchall()
                    passengerNum = dbcursor.rowcount

                    SELECT_TRIP = 'SELECT * FROM TrainTimetable WHERE tripId = %s;'
                    trip_dataset = (trip, )
                    dbcursor.execute(SELECT_TRIP, trip_dataset)
                    getTrip = dbcursor.fetchall()

                    return render_template('adminreportpassengerresp.html', passenger=passenger, passengerNum=passengerNum, getTrip=getTrip, trip=trip, dateJourney=dateJourney, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
                except mysql.connector.Error as e:
                    flash(e, category='error')
                    print(e)
                    return redirect(url_for('admin'))

                dbcursor.close()
                conn.close()
            else:
                print('DB connection error...')
        else:
            print('dbfunc error...')
    conn = dbfunc.getConnection()
    if conn != None:
        if conn.is_connected():
            print('MySQL Connection is established.')
            dbcursor = conn.cursor()
            try:
                SELECT_TRIPS = 'SELECT * FROM TrainTimetable;'
                dbcursor.execute(SELECT_TRIPS)
                trips = dbcursor.fetchall()

                return render_template('adminreportpassenger.html', trips=trips, name=session.get('name'), logged=session.get('logged_in'), usertype=session.get('usertype'))
            except mysql.connector.Error as e:
                flash(e, category='error')
                print(e)
                return redirect(url_for('admin'))

            dbcursor.close()
            conn.close()
        else:
            print('DB connection error...')
    else:
        print('dbfunc error...')
    

#USER ACCOUNT--------------------------------------------------------------------------------------------------

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('logged_in', None)
        session.pop('userId', None)
        session.pop('name', None)
        session.pop('usertype', None)

        email = request.form.get('email')
        password = request.form.get('password')

        conn = dbfunc.getConnection()
        if conn != None:    #Checking if connection is None
            if conn.is_connected(): #Checking if connection is established
                print('MySQL Connection is established')  
                try:  
                    SELECT_user = 'SELECT * FROM User \
                    WHERE email = %s;'  
                    dataset = (email,)
                    dbcursor = conn.cursor()    #Creating cursor object           
                    dbcursor.execute(SELECT_user, dataset)   
                    print('SELECT statement executed successfully.') 
                    user_row = dbcursor.fetchone()
                    print(user_row)
                    if user_row != None:
                        pw_check = check_password_hash(user_row[3], password)
                        if pw_check == True:
                            session['logged_in'] = True
                            session['userId'] = user_row[0]
                            session['name'] = user_row[2]
                            session['usertype'] = user_row[4]
                            print('Session created: ', session['userId'])
                            flash('Successfully logged in! Hello ' + user_row[2] + '.', category='success')
                            return redirect(url_for('search')) 
                        else:
                            print('Password is incorrect')
                            flash('Password is incorrect', category='error')
                    else:  
                        print('Account does not exist.')
                        flash('Account does not exist!', category='error')                  
                except mysql.connector.Error as e:
                    print('Failed to login with:\n', email)
                    print(e)

                dbcursor.close()              
                conn.close() #Connection must be closed
            else:
                print('DB connection error')
        else:
            print('DBFunc error')
    return render_template("login.html", logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/signup', methods=['GET', 'POST'])
def sign_up():   
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        usertype = request.form.get('usertype') 

        if len(name) < 3:
            flash('Name is too short (Less than 3 characters)', category='error')
        elif len(password1) < 7:
            flash('Password is too short (Less than 7 characters)', category='error')
        elif password1 != password2:
            flash('Passwords do not match!', category='error')
        else:
            conn = dbfunc.getConnection()
            if conn != None:
                if conn.is_connected():
                    hash_p1 = generate_password_hash(password1, method='pbkdf2:sha256', salt_length=8) #password is salted, its a random salt

                    print('MySQL Connection is established.')
                    dbcursor = conn.cursor()
                    try:
                        INSERT_USER = 'INSERT INTO User (\
                        email, name, password, usertype) VALUES (%s, %s, %s, %s);'
                        dataset = (email, name, hash_p1, usertype)
                        dbcursor.execute(INSERT_USER, dataset)
                        
                        conn.commit()
                        print("INSERT done successfully.")
                        flash('Account successfully created!', category='success')
                        return redirect(url_for('login'))
                    except mysql.connector.Error as e:
                        print('Failed Inserting Data:\n', dataset)
                        flash(e, category='error')
                        print(e)

                    dbcursor.close()
                    conn.close()
                else:
                    print('DB connection error...')
            else:
                print('dbfunc error...')

    return render_template("signup.html", logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/changepassword', methods=['GET', 'POST'])
def changepassword():
    if request.method == 'POST':
        email = request.form.get('email')
        oldpassword = request.form.get('oldpassword')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        conn = dbfunc.getConnection()
        if conn != None:    #Checking if connection is None
            if conn.is_connected(): #Checking if connection is established
                print('MySQL Connection is established')  
                try:  
                    SELECT_user = 'SELECT * FROM User \
                    WHERE email = %s;'  
                    dataset = (email,)
                    dbcursor = conn.cursor()    #Creating cursor object           
                    dbcursor.execute(SELECT_user, dataset)   
                    print('SELECT statement executed successfully.') 
                    user_row = dbcursor.fetchone()
                    print(user_row)
                    pw_check = check_password_hash(user_row[3], oldpassword)                 
                except mysql.connector.Error as e:
                    print('Failed to select with:\n', email)
                    print(e)

                dbcursor.close()              
                conn.close() #Connection must be closed
            else:
                print('DB connection error')
        else:
            print('DBFunc error')

        if len(password1) < 7:
            flash('Password is too short (Less than 7 characters)', category='error')
        elif password1 != password2:
            flash('New Passwords do not match!', category='error')
        elif (oldpassword == password2 or oldpassword == password1):
            flash('Old password is same as new password!', category='error')
        elif pw_check == False:
            flash('Old password is not correct!')
        elif pw_check == True:
            conn = dbfunc.getConnection()
            if conn != None:
                if conn.is_connected():
                    print('MySQL Connection is established.')
                    new_password = generate_password_hash(password1, method='pbkdf2:sha256', salt_length=8)
                    dbcursor = conn.cursor()
                    try:  
                        UPDATE_PASSWORD = 'UPDATE User SET \
                        password =  %s\
                        WHERE email = %s;' 

                        updatepw_dataset = (new_password, email)
                        dbcursor.execute(UPDATE_PASSWORD, updatepw_dataset)
                        conn.commit()
                        print("Update done successfully.")
                        flash('Password successfully changed!', category='success')
                    except mysql.connector.Error as e:
                        print('Failed Updating Data')
                        flash(e, category='error')
                        print(e)

                    dbcursor.close()
                    conn.close()
                else:
                    print('DB connection error...')
            else:
                print('dbfunc error...')

    return render_template("changepassword.html", logged=session.get('logged_in'), usertype=session.get('usertype'))

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('userId', None)
    session.pop('name', None)
    session.pop('usertype', None)
    session.clear()
    flash('You are no longer logged in. (Session Cleared)', category='success')
    return redirect(url_for('login'))


#GROUP IMPLEMENTATION---------------------------------------------------------------------------------------------
@app.route('/horizonTravelBookingService', methods=['GET', 'POST'])
def htbs():
    return render_template("horizonTravelBookingService.html")

@app.route('/htbsMakeBooking', methods=['GET', 'POST'])
def htbsBooking():
    # if request.method == 'POST':
    #     return redirect(url_for('horizonTravelBookingService'))
    return render_template("htbsMakeBooking.html")


#DATABASE CONFIG--------------------------------------------------------------------------------------------------

def dbCreate():
    if conn != None:
        if conn.is_connected():
            print('MySQL Connection is established.')
            DBStatement = 'CREATE DATABASE ' + DB_NAME + ';' #sql statement
            dbcursor = conn.cursor()
            try: #exception handling
                dbcursor.execute(DBStatement)
            except mysql.connector.Error as e:
                print('Failed creating Database ', DBNAME)
                print(e)
                exit(1)

            print("Database '{}' created successfully.".format(DB_NAME))

            dbcursor.close()
            conn.close()
        else:
            print('DB connection error...')
    else:
        print('dbfunc error...')

def table_Create():
    if conn != None:
        if conn.is_connected():
            # print('MySQL Connection is established.')
            # TIMETABLE_DESCRIPTION = 'CREATE TABLE TrainTimetable ( \
            # tripId VARCHAR(20) NOT NULL UNIQUE, \
            # departPlace VARCHAR(40) NOT NULL, \
            # departTime TIME(0) NOT NULL, \
            # arrivePlace VARCHAR(40) NOT NULL, \
            # arriveTime TIME(0) NOT NULL, \
            # price INT, \
            # PRIMARY KEY (tripId));'
            # dbcursor = conn.cursor()
            # try:
            #     dbcursor.execute('USE {};'.format(DB_NAME))
            #     dbcursor.execute(TIMETABLE_DESCRIPTION)
            #     print("Table {} created successfully.".format(TIMETABLE))
            # except mysql.connector.Error as e:
            #     print('Failed Creating Table ', TIMETABLE)
            #     print(e)
            #     exit(1)
            #BOOKING TABLE ------------------------------------
            BOOKING_DESCRIPTION = 'CREATE TABLE TrainBooking ( \
            bookId INT NOT NULL AUTO_INCREMENT UNIQUE, \
            userId INT, \
            tripId VARCHAR(20) NOT NULL, \
            departDate DATE NOT NULL, \
            returnDate DATE, \
            adultNum INT, \
            childNum INT, \
            tripType VARCHAR(20), \
            priceTotal INT, \
            timestamp DATETIME NOT NULL, \
            PRIMARY KEY (bookId), \
            FOREIGN KEY (userId) REFERENCES User(userId), \
            FOREIGN KEY (tripId) REFERENCES TrainTimetable(tripId));'
            dbcursor = conn.cursor()
            try:
                dbcursor.execute(BOOKING_DESCRIPTION)
                print("Table {} created successfully.".format(TRIPTABLE))
            except mysql.connector.Error as e:
                print('Failed Creating Table ', TRIPTABLE)
                print(e)
                exit(1)
            #USER TABLE ---------------------------------------
            # USER_DESCRIPTION = 'CREATE TABLE User ( \
            # userId INT NOT NULL AUTO_INCREMENT UNIQUE, \
            # email VARCHAR(40) NOT NULL UNIQUE, \
            # name VARCHAR(40) NOT NULL, \
            # password VARCHAR(110) NOT NULL, \
            # usertype VARCHAR(10) NOT NULL, \
            # PRIMARY KEY (userId));'
            # dbcursor = conn.cursor()
            # try:
            #     dbcursor.execute(USER_DESCRIPTION)
            #     print("Table '{}' created successfully.".format(USERTABLE))
            # except mysql.connector.Error as e:
            #     print('Failed Creating Table ', USERTABLE)
            #     print(e)
            #     exit(1)

            dbcursor.close()
            conn.close()
        else:
            print('DB connection error...')
    else:
        print('func error...')

def table_Insert():
    if conn != None:
        if conn.is_connected():
            print('MySQL Connection is established.')
            dbcursor = conn.cursor()
            try:
                INSERT_TIMETABLE = 'INSERT INTO TrainTimetable (\
                tripId, departPlace, departTime, arrivePlace, arriveTime, price) VALUES (%s, %s, %s, %s, %s, %s);'
                dataset = [ (1000, 'Newcastle', '16:45:00', 'Bristol', '23:00:00', 140),
                    (1001, 'Bristol', '08:00:00', 'Newcastle', '14:15:00', 140),
                    (1002, 'Cardiff', '06:00:00', 'Edinburgh', '13:30:00', 120),
                    (1003, 'Edinburgh', '18:30:00', 'Cardiff', '01:00:00', 120),
                    (1004, 'Bristol', '11:30:00', 'Manchester', '16:30:00', 100),
                    (1005, 'Manchester', '12:20:00', 'Bristol', '17:20:00', 100),
                    (1006, 'Bristol', '07:40:00', 'London', '11:00:00', 100),
                    (1007, 'London', '11:00:00', 'Manchester', '17:40:00', 130),
                    (1008, 'Manchester', '12:20:00', 'Glasgow', '18:10:00', 130),
                    (1009, 'Bristol', '07:40:00', 'Glasgow', '13:05:00', 160),
                    (1010, 'Glasgow', '14:30:00', 'Newcastle', '20:45:00', 130),
                    (1011, 'Newcastle', '16:15:00', 'Manchester', '20:25:00', 130),
                    (1012, 'Manchester', '18:25:00', 'Bristol', '23:50:00', 130),
                    (1013, 'Bristol', '06:20:00', 'Manchester', '11:20:00', 130),
                    (1014, 'Portsmouth', '12:00:00', 'Dundee', '22:00:00', 180),
                    (1015, 'Dundee', '10:00:00', 'Portsmouth', '20:00:00', 180),
                    (1016, 'Southampton', '12:00:00', 'Manchester', '19:30:00', 100),
                    (1017, 'Manchester', '19:00:00', 'Southampton', '01:30:00', 100),
                    (1018, 'Birmingham', '16:00:00', 'Newcastle', '23:30:00', 130),
                    (1019, 'Newcastle', '06:00:00', 'Brimingham', '13:30:00', 130),
                    (1020, 'Aberdeen', '07:00:00', 'Portsmouth', '17:00:00', 130) ]
                dbcursor.executemany(INSERT_TIMETABLE, dataset)
                # INSERT_USER = 'INSERT INTO ' + USERTABLE + ' (\
                # email, name, password, usertype) VALUES (%s, %s, %s, %s);'
                # dataset = ('ryan@email.com', 'ryan', 'ryanspassword', 'admin')
                # dbcursor.execute(INSERT_USER, dataset)
                
                conn.commit()
                print("INSERT done successfully.")
            except mysql.connector.Error as e:
                print('Failed Inserting Data:\n', dataset)
                print(e)
                exit(1)

            dbcursor.close()
            conn.close()
        else:
            print('DB connection error...')
    else:
        print('dbfunc error...')

if __name__ == '__main__':
    app.run(debug=True)