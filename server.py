import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions

import json
import logging

from jinja2 import Environment, Undefined

# Mongo database
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Date handling
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times

# Our own module
#import pre  # Preprocess schedule file


###
# Globals
###
app = flask.Flask(__name__)
#schedule = "static/schedule.txt"  # This should be configurable
import CONFIG


import uuid
app.secret_key = str(uuid.uuid4())
app.debug = CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)


try:
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.service
    collectionSchedules = db.schedules
    collectionClients = db.clients
    collectionAccounts = db.accounts
except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    #sys.exit(1)

###
# Pages
###


### Home Page ###

@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('index.html')

### Client Page ###

@app.route("/client")
def client():
    app.logger.debug("client page entry")
    return flask.render_template('client.html')

### Admin Page ###

@app.route("/admin")
def admin():
    app.logger.debug("admin page entry")
    if flask.session.get('login') != True:
        return flask.render_template('login.html')
    flask.session['clients'] = get_list("Clients")
    flask.session['schedules'] = get_list("Schedules")
    aTable = get_list("Times")
    if len(aTable)>0: aTable = aTable[0].get('tTable')
    else: aTable = []
    flask.session['timeTable'] = aTable
    return flask.render_template('admin.html')

@app.route('/login')
def login():
    if flask.session.get('login') == True:
        return flask.redirect(url_for('admin'))
    else:
        return flask.render_template('login.html')

@app.route('/createAdmin')
def createAdmin():
    if collectionAccounts.find_one({}) != None:
        return flask.redirect(url_for('login'))
    else:
        return flask.render_template('createAdmin.html')

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('page_not_found.html'), 404

################

###functions###

################

@app.route("/_login")
def portalSelector():
    objId = request.args.get('login', 0, type=str)
    app.logger.debug(objId)
    if objId == "client":
        return flask.redirect(url_for('client'))
    else:
        return flask.redirect(url_for('admin'))

@app.route("/_ClientsConfig")
@app.route("/_submitClientInfo")
def clientConfig():
    #collectionTemp = collectionClients
    app.logger.debug("Got a JSON request")
    funct = request.args.get('clientSetting',0,type=str)
    app.logger.debug(funct)
    if funct == "addClient":
        objId1 = request.args.get('fname',0,type=str)
        objId2 = request.args.get('studentid',0,type=str)
        objId3 = request.args.get('phonenum',0,type=str)
        objId4 = request.args.get('riders',0,type=str)
        objId5 = request.args.get('time',0,type=str)
        objId6 = request.args.get('pickup',0,type=str)
        objId7 = request.args.get('dropoff',0,type=str)
        ####################### if verifyinformation(val) #################
        record = { "name": objId1, "date":  arrow.utcnow().naive,
        "ID": objId2 , "phoneNum": objId3, "riders": objId4,
        "time": objId5, "pickup": objId6, "dropoff":objId7, "type": "Client", "status": "pending"}
        collectionClients.insert(record)
        d = {'result':'added'}
    elif funct == "removeClient":
        objId = request.args.get('ClientId',0,type=str)
        collectionClients.remove({"_id": ObjectId(objId)});
        return flask.redirect(url_for('admin'))
        #d = {'result':'removed'}
    else:
        d = {'result':'failed'}
    d = json.dumps(d)
    return jsonify(result = d)
    #return flask.redirect(url_for('client'))

@app.route("/_submitLoginRequest")
def loginGate():
    adminName = request.args.get('adminName',0,type=str)
    adminKey = request.args.get('adminKey',0,type=str)
    if collectionAccounts.find_one({'name':adminName,'password':adminKey}) != None:
        flask.session['login'] = True
        d = {'result':'success'}
    else:
        d = {'result':'failed'}
    d = json.dumps(d)
    return jsonify(result = d)

@app.route("/_adminSettings")
def adminSettings():
    setting = request.args.get('setting',0,type=str)
    adminName = request.args.get('adminName',0,type=str)
    adminKey = request.args.get('adminKey',0,type=str)
    if setting  == "requestAccess":
        if collectionAccounts.find_one({}) == None:
            record = {"name":adminName, "password":adminKey, "date":arrow.utcnow().naive}
            app.logger.debug(record)
            collectionAccounts.insert(record)
            d = {'result':'added'}
        else:
            d = {'result':'failed'}
    elif setting == "removeAdmin":
        collectionAccounts.remove({})
        flask.session['login'] = False
        return flask.redirect(url_for('login'))
    elif setting == "logout":
        flask.session['login'] = False
        return flask.redirect(url_for('login'))
    else:
        d = {'result':'wat'}
    d = json.dumps(d)
    return jsonify(result = d)

@app.route("/_ScheduleConfig")
def scheduleConfig():
    #collectionTemp = collectionSchedules
    objId = request.args.get('ScheduleSetting',0,type=str)
    app.logger.debug(objId)
    if objId == "addSchedule":
        #name = request.args.get('name',0,type=str)
        numSchedules = request.args.get('name',0,type=int)
        #app.logger.debug("schedule added!")
        tempCount = collectionSchedules.find({}).count() + 1
        app.logger.debug(tempCount)
        if tempCount > 1:
            app.logger.debug("failed! schedules already here")
            #d = {'result':'failed! 4 schedules already'}
            #d = json.dumps(d)
            #return jsonify(result = d)
            return flask.redirect(url_for('admin'))
        slider1 = request.args.get('scheduleStart',0,type=str)
        app.logger.debug(slider1)
        slider1 = arrow.get(slider1,'H:mm A')

        app.logger.debug(slider1)
        slider2 = request.args.get('scheduleEnd',0,type=str)
        slider2 = arrow.get(slider2,'H:mm A')

        if slider2 < slider1:
            slider2 = slider2.replace(day=2)

        sliderS = str(slider1.timestamp)
        sliderF = str(slider2.timestamp)
        timeBlock = 5
        tTable = {}
        clientList = []
        #clientList = "0";
        while(sliderS!=sliderF):
            tTable.update({sliderS:clientList})
            slider1 = slider1.replace(minutes=+timeBlock)
            #sliderS = slider1.format('H:mm')
            sliderS = str(slider1.timestamp)
        tTable.update({sliderS:clientList})
        #flask.session['timeTable'] = tTable
        for i in range(1,numSchedules+1):
            #record = { "name": i, "date":  arrow.utcnow().naive, "ID": "29838472983" ,"type": "Schedule"}
            record = { "name": i, "date": arrow.utcnow().naive ,"type": "Schedule", "tTable": tTable}
            app.logger.debug(tTable)
            collectionSchedules.insert(record)
        #d = {'result':'success! added schedule'+tempCount}
        #d = json.dumps(d)
    elif objId == "removeSchedule":
        ScheduleId = request.args.get('ScheduleId',0,type=str)
        app.logger.debug(ScheduleId)
        if ScheduleId == "0":
            app.logger.debug("deleting all schedules")
            collectionSchedules.remove({})
        else:
            app.logger.debug("attempting to remove schedule" + str(ScheduleId))
            if collectionSchedules.remove({"_id": ObjectId(ScheduleId)}):
                app.logger.debug("success!")
            else:
                app.logger.debug("failed!")
    else:
        app.logger.debug("wat")
    return flask.redirect(url_for('admin'))


@app.route("/stream")
def stream():
    def eventStream():
        #pull data from database, see if new client submission
        with app.test_request_context():
            if flask.session.get('newClient') == True:
                yield "data: %s\n\n" % ("new rides requested")
    return flask.Response(eventStream(), mimetype="text/event-stream")


@app.route("/_scheduleClient")
def scheduleAddclient():
    status = request.args.get('settingType',0,type=str)

    scheduleId = request.args.get('schedulePicker',0,type=str)
    clientId = request.args.get('clientId',0,type=str)
    timeStart = request.args.get('clientStart',0,type=str)
    timeEnd = request.args.get('clientEnd',0,type=str)
    if status == 'deny':
        collectionClients.update(
            {"_id": ObjectId(clientId)},
            { "$set":
                {
                    "status":"denied"
                }
            }
        )
        return flask.redirect(url_for('admin'))
    timeBlock = 5
    timeStart = arrow.get(timeStart,'H:mm A')
    timeEnd = arrow.get(timeEnd,'H:mm A')
    timeEnd = timeEnd.replace(minutes=+timeBlock)

    if timeEnd < timeStart:
        timeEnd = timeEnd.replace(day=2)

    timeS = str(timeStart.timestamp)
    timeF = str(timeEnd.timestamp)

    aSchedule = collectionSchedules.find_one({"_id": ObjectId(scheduleId)})
    aTable = aSchedule['tTable']
    while(timeS!=timeF):
        theList = aTable[timeS]
        theList.append(clientId)
        aTable.update({timeS:theList})
        timeStart = timeStart.replace(minutes=+timeBlock)
        timeS = str(timeStart.timestamp)
    collectionClients.update({"_id": ObjectId(clientId)},{"$set":{"status":"approved"}})
    collectionSchedules.update({"_id": ObjectId(scheduleId)},{"$set":{"tTable":aTable}})
    return flask.redirect(url_for('admin'))

##############################
@app.template_filter('convert_time')
def convert_time(timestamp):
    val = arrow.get(timestamp)
    return val.format('h:mm A')

@app.template_filter('clientInfo')
def get_client_info(clientId):
    return collectionClients.find({"_id": ObjectId(clientId)})

def get_list(aType):
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = []
    #tempCollection = collection.find().sort( { date: 1 } )
    if aType == "Schedules":
        collectionTemp = collectionSchedules
    elif aType == "Clients":
        collectionTemp = collectionClients
    elif aType == "Times":
        collectionTemp = collectionSchedules
    else:
        collectionTemp = collectionClients
    for record in collectionTemp.find( {} ).sort("date",1): #"type": "Driver" "status": "pending"
        record['date'] = arrow.get(record['date']).isoformat()
        try:
            record['_id'] = str(record['_id'])
        except:
            del record['_id']
        records.append(record)
    return records

env = Environment()
env.filters['translateTime'] = convert_time
env.filters['clientInfo'] = get_client_info

if __name__ == "__main__":
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT,threaded=True)
