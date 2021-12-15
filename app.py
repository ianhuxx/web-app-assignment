#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, make_response
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess


client = pymongo.MongoClient("mongodb+srv://yh2931:Huyb010424@cluster0.qutr9.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.test

'''
mongo = pymongo.MongoClient(
    host = "localhost",
    port = 27018,
    SERVER_SELECTION_TIMEOUT=1000
    )

db = mongo.assignment
'''
# instantiate the app
app = Flask(__name__)

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
import credentials
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

'''
# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database
'''

# set up the routes

@app.route('/')
def home():
    """
    Route for the home page
    """
    teams = db.teams
    discussions = db.discussions
    most_recent_team = {db.teams.find({"_id": 0, "created_at": 1}).limit(1)}
    most_recent_discussion = {db.teams.find({"_id": 0, "created_at": 1}).limit(1)}
    return render_template('index.html', teams=teams, discussions=discussions, most_recent_team=most_recent_team, most_recent_discussion=most_recent_discussion)


@app.route('/read')
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
     # sort in descending order of created_at timestamp
    docs = db.discussions.find({}).sort("created_at", -1)
    return render_template('read.html', docs=docs) # render the read template

@app.route('/view_team')
def view_team():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
     # sort in descending order of created_at timestamp
    docs = db.teams.find({}).sort("created_at", -1)
    return render_template('view_team.html', docs=docs) # render the read template

@app.route('/create')
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template('create.html') # render the create template


@app.route('/create', methods=['POST'])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    name = request.form['fname']
    message = request.form['fmessage']


    # create a new document with the data the user entered
    doc = {
        "name": name,
        "message": message, 
        "created_at": datetime.datetime.utcnow()
    }
    db.discussions.insert_one(doc) # insert a new document

    return redirect(url_for('read')) # tell the browser to make a request for the /read route

@app.route('/create_team')
def create_team_1():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template('create_team.html') # render the create template


@app.route('/create_team', methods=['POST'])
def create_team():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    name = request.form['fname']
    email = request.form['femail']
    project_title = request.form['fproj_title']
    description = request.form['fdescription']

    # create a new document with the data the user entered
    doc = {
        "name": name,
        "email": email,
        "project_title": project_title,
        "description": description,
        "created_at": datetime.datetime.utcnow(),
        "team_members": [],
        "team_member_count": 1
    }
    doc["team_members"].append({"name": name, "email": email})
    db.teams.insert_one(doc) # insert a new document

    return redirect(url_for('view_team')) # tell the browser to make a request for the /read route

@app.route('/join_team')
def join_team_1():
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    docs = db.teams.find({}).sort("created_at", -1)
    return render_template('join_team.html', docs = docs) # render the edit template

@app.route('/join_team', methods=['POST'])
def join_team():
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    name = request.form['joined_name']
    email = request.form['joined_email']
    project_title = request.form['team_to_join']

    doc = dict(db.teams.find_one({"project_title": project_title}))
    doc["team_members"].append({"name": name, "email": email})
    doc["team_member_count"] = len(doc["team_members"])
    db.teams.update({"project_title": project_title}, doc)

    return redirect(url_for('view_team')) # tell the browser to make a request for the /read route
    

@app.route('/edit/<mongoid>')
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    doc = db.discussions.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc) # render the edit template


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    name = request.form['fname']
    message = request.form['fmessage']

    doc = {
        # "_id": ObjectId(mongoid), 
        "name": name, 
        "message": message, 
        "created_at": datetime.datetime.utcnow()
    }

    db.discussions.update_one(
        {"_id": ObjectId(mongoid)}, # match criteria
        { "$set": doc }
    )

    return redirect(url_for('read')) # tell the browser to make a request for the /read route


@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.discussions.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('read')) # tell the web browser to make a request for the /read route.

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the edit template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True)
