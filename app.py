import os
import re
import json
import html
import bcrypt
import secrets
import hashlib
import sys

from datetime import datetime
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, redirect, make_response, send_file
from flask_socketio import SocketIO, join_room, leave_room, emit
from os.path import join
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired

mongo_client = MongoClient("mongo")
db = mongo_client["cse312Project"]

ID_collection = db["id"] # id
user_collection = db["users"] # username, password, auth, xsrf, place
post_collection = db["posts"] # ID, subject, body, creator
comments_collection = db["comments"] # POSTID, body, postowner

app = Flask(__name__)
app.config["SECRET_KEY"] = 'supersecretkey'
socketio = SocketIO(app)
app.config['UPLOAD_FOLDER'] = 'static/files'
ALLOWED_EXTENSIONS = {"jpg", "png", "gif"}
homepageimg = os.path.join('static', 'public')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET': return redirect("/")
    elif request.method == 'POST':

        # get user; username and pass then html escape it
        user_username = html.escape(request.form['login_username'])
        user_password = html.escape(request.form['login_password'])

        # check if they exist in database
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        if user != None:

            # check if password matches db password, if it doesn't then deny login.
            if bcrypt.checkpw(user_password.encode(), user["password"]): 

                # creating auth token and updating db
                auth_token = secrets.token_urlsafe(70)
                hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
                user_collection.update_one({"username":user_username}, {"$set": {"auth": hashed_auth}})

                # create a response with a httponly non session cookie containing their auth token
                resp = make_response(redirect('/'))
                resp.set_cookie(key = "auth", value = auth_token, max_age = 10000, httponly = True)
                return resp
            
            else: return redirect('/')
        else: return redirect('/')


@app.route('/signup', methods=['POST'])
def signup():

    # get user information and html escape it
    user_username = html.escape(request.form['login-username'])
    user_password =  html.escape(request.form['login-password'])
    user_repassword =  html.escape(request.form['login-password2'])
    
    # if any of there information was blank refresh the page
    if user_username == "" or user_password == "" or user_repassword == "": return redirect("/")

    elif user_password == user_repassword:
        hashed_pass = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())

        # Check if the username exists in the DB already, if it does ignore.
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        if user == None: user_collection.insert_one({"username":user_username, "password":hashed_pass, "auth":0, "xsrf":0, "place":-1})
    return redirect("/") 

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")


@app.route('/', methods=['POST', 'GET'])
def index():

    # if the user doesn't have a auth cookie; hide logout button and set their status as Guest
    if request.cookies.get('auth') == None:
        replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
        replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest<input hidden type='text' id='current-status' value='Guest'>")

    else:
        hashed_auth = hashlib.sha256(request.cookies.get('auth').encode()).hexdigest()

        # if the user's auth cookie is not in the db; hide logout button and set their status as Guest
        if user_collection.find_one({"auth":hashed_auth}, {"_id":0}) == None:
            replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
            replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest")

        # if the user's auth cooke is in db; reveal logout button, set their username to what's in db, and load the last comment they viewed
        else:
            user = user_collection.find_one({"auth":hashed_auth}, {"_id":0})
            replace_html_element("templates/main.html", 'class="logout" hidden.*', 'class="logout">')
            replace_html_element("templates/main.html", "Current status:.*", "Current status: " + user["username"]+"<input hidden type='text' id='current-status' value='"+ user["username"]+"'>")
            replace_html_element("templates/main.html", 'id="post_id" value=".*"', 'id="post_id" value="' + str(user["place"]) + '"')
            replace_html_element("templates/main.html", '<form action="/add_comment" method="POST">', '')
            replace_html_element("templates/main.html", '<input type="submit" id="submitcomment" value="Post">', '<button id="submitcomment">Post</button>')

    if request.method == 'POST': pass
    elif request.method == 'GET':
        # [HELP HELP!!!] Kameron here, idk what any of this is doing, please explain
        # line 20 and the following lines allow you to upload an image
        file1 = os.path.join(homepageimg, 'eagle.jpg')

        form = UploadFileForm()
        if form.validate_on_submit():

            # First grab the file
            file = form.file.data 
            
            # Then save the file
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
            return "File has been uploaded."
        
        # image1 and image2 are the files/images that are given into the html as an image in the html tag <img src = "{{image1}}">
        return render_template('main.html', form=form, image1=file1)


@app.route('/static/css/main.css', methods=['GET'])
def css(): return render_template('main.css')


@app.route('/logout', methods=['GET', 'POST'])
def logout():

    # remove the users auth token in the db
    token = hashlib.sha256(request.cookies.get('auth').encode()).hexdigest()
    user_collection.update_one({"auth":token}, {"$set": {"auth":""}})

    # reveal the logout button 
    replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
    replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest")

    # refresh the page but expire the users auth token
    resp = make_response(redirect('/'))
    resp.set_cookie(key = "auth", value = request.cookies.get('auth'), max_age = -1, httponly = True)
    return resp


def replace_html_element(filename, search_text, replace_text):
    with open(filename, 'r+') as f:
        file = f.read()
        file = re.sub(search_text, replace_text, file)
        f.seek(0)
        f.write(file)
        f.truncate()


@app.route('/public/homepage.jpg', methods=['GET'])
def homeimage():
    return send_file('static/public/homepage.jpg', mimetype = 'image/jpeg')


@app.route('/renderpostcreation', methods=["GET"])
def setuppost():
    return render_template("tempposts.html")


@app.route('/favicon.ico', methods=['GET'])
def tabicon():
    return send_file('static/public/eagle.ico', mimetype = 'image/x-icon')


@app.route('/makepost', methods = ["POST"])
def storepost():
    ID = 0
    increment = ID_collection.find_one({}, {"_id":0})

    # if the DB is not empty change ID to stored id, otherwise insert a id of 0 to db
    if increment != None: ID = increment["id"]
    else: ID_collection.insert_one({"id":0})

    # get subject and body, then html escape them
    subject = html.escape(request.form['subjectbox'])
    body = html.escape(request.form['messagebody'])

    # if the subject or body is empty reload the current page
    if subject == "" or body == "": return redirect('/renderpostcreation')

    # check to see if there is a user to the given auth_token
    auth_cookie = hashlib.sha256(request.cookies.get("auth","").encode()).hexdigest()
    PotentialCreator = user_collection.find_one({"auth":auth_cookie}, {"_id":0})

    # if authenticated change username to their username, otherwise leave as Guest
    username = "Guest"
    if PotentialCreator != None: username = PotentialCreator["username"]

    # add the subject, body, username, and place to post db. Increment ID in db. Then refresh page
    post_collection.insert_one({"ID": ID,"subject": subject,"body":body,"creator":username})
    user_collection.update_one({"username":username}, {"$set": {"place":ID}})
    ID_collection.update_one({"id":ID}, {"$set": {"id":ID + 1}})
    return redirect('/')


@app.route("/main.js", methods=["GET"])
def sendmainJS():
    return send_file("static/main.js",mimetype="text/javascript")


@app.route("/startup", methods=["GET"])
def sendpostdata():

    # check to see if there is a user to the given auth_token
    auth_cookie = hashlib.sha256(request.cookies.get("auth","").encode()).hexdigest()
    PotentialCreator = user_collection.find_one({"auth":auth_cookie}, {"_id":0})

    # if authenticated change username to their username, otherwise leave as Guest
    username = "Guest"
    if PotentialCreator != None: username = PotentialCreator["username"]

    posts = post_collection.find({}, {"_id":0})
    post_collection.update_one({}, {"$set": {"viewer":username}})
    return json.dumps(list(posts))


@app.route("/add_comment", methods=["POST"])
def add_comment():

    # get comment and post_id, then html escape them
    comment = html.escape(request.form["new_comment"])
    post = html.escape(request.form["post_id"])

    # check to see if there is a user to the given auth_token
    auth_cookie = hashlib.sha256(request.cookies.get("auth","").encode()).hexdigest()
    PotentialCreator = user_collection.find_one({"auth":auth_cookie}, {"_id":0})

    # if authenticated change username to their username, otherwise leave as Guest
    username = "Guest"
    if PotentialCreator != None: username = PotentialCreator["username"]

    # add the postid, comment, and username to comments db. Then refresh page
    comments_collection.insert_one({"POSTID":post,"body":comment,"postowner":username})
    return redirect("/")


@app.route("/getcomments/<postid>", methods=["GET"])
def getcomments(postid):
    comments = comments_collection.find({"POSTID":postid},{"_id":0})
    return json.dumps(list(comments))

users = {}
@socketio.on('connect')
def handleConnect():
    print("Someone connected.")

#TODO: Fix this all
@socketio.on("SendMessage")
def sendMessage(data):
    postID = data['channel']
    message = data['message']
    SID = request.sid
    # POSTID, body, postowner
    comments_collection.insert_one({"POSTID":postID,"body":message,"postowner": users[SID]})
    inserted = comments_collection.find_one({"POSTID":postID,"body":message,"postowner": users[SID]},{"_id":0})
    emit(inserted,room=postID)

@socketio.on("join")
def joinRoom(data):
    postID = data['channel']
    username = data['user']
    SID = request.sid
    emit(postID)
    join_room(postID)
    users[SID] = username
    emit(f"User {users[SID]} joining Chat {postID}", room=postID)
    emit(users[SID], room=postID)
    comments = comments_collection.find({"POSTID":postID},{"_id":0})
    emit(list(comments), broadcast=False)


@socketio.on('leave')
def leaveRoom(data):
    postID = data['channel']
    leave_room(postID)
    emit(f"User leaving Chat {postID}", room=postID)

# This will be triggered every time the arrows were clicked
# Get the post that you moved to from server
# Get all pre-existing comments
# Send the post ID, send the comments
@socketio.on('getMax')
def maxPostID(data):
    increment = ID_collection.find_one({}, {"_id":0})
    if increment != None: ID = increment["id"]
    else: ID = 0
    direction = data['direction']
    post = data['postID']
    if direction == 0:
        comments = comments_collection.find({"POSTID":str(post)},{"_id":0})
        emit('get max', {"postID": post, 'comments':list(comments)}, broadcast=False)
    else:
        placement= post
        if direction == -1 and post > 0 or direction == 1 and ID != 0 and post < ID-1:
            placement += direction
        # For some reason this line appears to be retrieving nothing when stuff exists.
        comments = comments_collection.find({"POSTID":str(placement)},{"_id":0})
        emit('get max', {"postID": placement, 'comments':list(comments)}, broadcast=False)

@app.route("/modify_local", methods=["GET"])
def sendIDplusone():
    ID = ID_collection.find_one({},{"_id":0})
    if ID == None: return json.dumps(0)
    else: return json.dumps(ID["id"])


# Store multimedia posts
@app.route("/action_page", methods=["POST"])
def handleimageposts():
    
    # Get the user image
    file = request.files["filename"]
    userfile = file.filename
    extension = userfile.split(".", 1)[1]
    if not extension in ALLOWED_EXTENSIONS: return redirect("/")

    # grab ID
    ID = 0
    increment = ID_collection.find_one({}, {"_id":0})
    if increment != None: ID = increment["id"]
    else: ID_collection.insert_one({"id":0})

    # Create the path to the image (where it will be stored)
    imageroute = os.path.join("static", "public", "images")
    imagepath = os.path.join(imageroute, str(ID) + "." + extension)

    # Store it to disk with the unique message ID that will correspond to the post the image lies within
    file.save(imagepath)

    # authenticate
    auth_cookie = hashlib.sha256(request.cookies.get("auth","").encode()).hexdigest()
    PotentialCreator = user_collection.find_one({"auth":auth_cookie}, {"_id":0})

    # if authenticated change username to their username, otherwise leave as Guest
    username = "Guest"
    if PotentialCreator != None: username = PotentialCreator["username"]
    user_collection.update_one({"username":username}, {"$set": {"place":ID}})

    # insert into chat DB, increment message count
    imageelement = "<img src=\"" + imagepath + "\"/>"
    post_collection.insert_one({"ID": ID, "subject": "", "body":imageelement, "creator":username})
    ID_collection.update_one({"id":ID}, {"$set": {"id":ID + 1}})
    
    return redirect("/")


# the general route which will handle serving user-provided files stored on disk
@app.route("/static/public/images/<ID>", methods=["GET"])
def provideuserimage(ID):

    # find the type
    type = ""
    file = ID.replace('/','')
    if file[-3:] == "png": type = "image/png"
    elif file[-3:] == "jpg": type = "image/jpg"
    elif file[-3:] == "gif": type = "image/gif"

    # create the path and then send it with the mime type
    path = os.path.join("static", "public", "images", file)
    return send_file(path, mimetype=type)


@app.route("/update_place/<username>/<place>", methods=["GET"])
def server_place_update(username, place):

    # update the user's place then return the place
    user_collection.update_one({"username":username}, {"$set": {"place":place}})
    return json.dumps(place)


@app.after_request
def nosniff(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

if __name__ == "__main__": 
    app.run(debug=True, host="0.0.0.0", port=8080)
    socketio.run(app, allow_unsafe_werkzeug=True)