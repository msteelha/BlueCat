"""
Very simple Flask web site, with one page
displaying a course schedule.

"""

import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions

import json
import logging

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
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)

try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.service
    collection = db.drivers
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
  #if 'page' not in flask.session:
  #    app.logger.debug("Processing raw schedule file")
  #    raw = open('static/schedule.txt')
  #    flask.session['page'] = pre.process(raw)

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
    flask.session['drivers'] = get_drivers()
    for memo in flask.session['drivers']:
        app.logger.debug("driver: " + str(memo))
    return flask.render_template('admin.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] =  flask.url_for("index")
    return flask.render_template('page_not_found.html'), 404


################

###functions###

@app.route("/_login")
def portalSelector():
    objId = request.args.get('login',0,type=str)
    app.logger.debug(objId)
    if objId == "client":
        return flask.redirect(url_for('client'))
    else:
        return flask.redirect(url_for('admin'))
        
@app.route("/_submitClientInfo")
def clientConfig():
	objId1 = request.args.get('fname',0,type=str)
	objId2 = request.args.get('lname',0,type=str)
	print objId1 + " " + objId2
	return flask.redirect(url_for('client'))
	
@app.route("/_DriverConfig")
def driverConfig():
    objId = request.args.get('DriverSetting',0,type=str)
    if objId == "add":
        name = request.args.get('name',0,type=str)
        app.logger.debug("driver added!")
        record = { "name": name, "date":  arrow.utcnow().naive, "driverID": "29838472983" ,"type": "Driver"}
        collection.insert(record)    
    elif objId == "remove":
        objId = request.args.get('DriverId',0,type=str)
        #d = {'objId': objId}
        collection.remove({"_id": ObjectId(objId)});
        #collection.remove({});
        #d = json.dumps(d)
    else:
        app.logger.debug("wat")
    return flask.redirect(url_for('admin'))


##############################

def get_drivers():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    #tempCollection = collection.find().sort( { date: 1 } )
    for record in collection.find( { "type": "Driver" } ).sort("date",1):
        record['date'] = arrow.get(record['date']).isoformat()
        try:
            record['_id'] = str(record['_id'])
        except:
            del record['_id']
        records.append(record)
    return records 


if __name__ == "__main__":
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT)
