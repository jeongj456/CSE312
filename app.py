import os
import re
import json
import html
import bcrypt
import secrets
import hashlib
import random

from pymongo import MongoClient
from werkzeug.utils import secure_filename

from wtforms import FileField, SubmitField
from wtforms.validators import InputRequired

from flask_wtf import FlaskForm
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, request, redirect, make_response, send_file, session

mongo_client = MongoClient("mongo")
db = mongo_client["cse312Project"]

ID_collection = db["id"] # id
user_collection = db["users"] # username, password, auth, xsrf, place
post_collection = db["posts"] # ID, subject, body, creator
comments_collection = db["comments"] # POSTID, body, postowner

app = Flask(__name__)
app.config["SECRET_KEY"] = 'supersecretkey'
socketio = SocketIO(app)
limiter = Limiter(get_remote_address, app=app, meta_limits=["1/30seconds"], default_limits=["50 per 10 seconds"])
app.config['UPLOAD_FOLDER'] = 'static/files'
ALLOWED_EXTENSIONS = {"jpg", "png", "gif"}
homepageimg = os.path.join('static', 'public')

if ID_collection.find_one({}) == None: 
    post_collection.insert_one({"ID":0, "subject":"Greeting", "body":"Hello World", "creator":"Admin"})
    ID_collection.insert_one({"id":1})


@app.errorhandler(429)
def tooManyReqs(error):
    return render_template('429.html'), 429

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET' or session['username'] != "Guest": return redirect("/")
    elif request.method == 'POST':
        # get user; username and pass then html escape it

        user_username = request.form['login_username']
        user_password = request.form['login_password']

        user_username = user_username.replace('\\', '\\\\')
        user_password = user_password.replace('\\', '\\\\')

        user_username = html.escape(user_username)
        user_password = html.escape(user_password)

        # check if they exist in database
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        if user != None:

            # check if password matches db password, if it doesn't then deny login.
            if bcrypt.checkpw(user_password.encode(), user["password"]): 

                # creating auth token and updating db
                auth_token = secrets.token_urlsafe(70)
                hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
                PLACE = session.get('place', 0)
                user_collection.update_one({"username":user_username}, {"$set": {"auth": hashed_auth, "place":PLACE}})

                # create a response with a httponly non session cookie containing their auth token
                resp = make_response(redirect('/'))
                resp.set_cookie(key = "auth", value = auth_token, max_age = 10000, httponly = True)
                session['username'] = user_username
                return resp
            
            else: return redirect('/')
        else: return redirect('/')


@app.route('/signup', methods=['POST'])
def signup():

    # get user information and html escape it

    user_username = request.form['register-username']
    user_password = request.form['register-password']
    user_repassword = request.form['register-password2']

    user_username = user_username.replace('\\', '\\\\')
    user_password = user_password.replace('\\', '\\\\')
    user_repassword = user_repassword.replace('\\', '\\\\')

    user_username = html.escape(user_username)
    user_password = html.escape(user_password)
    user_repassword =  html.escape(user_repassword)
    
    # if any of there information was blank refresh the page
    if user_username == "" or user_password == "" or user_repassword == "": return redirect("/")

    elif user_password == user_repassword:
        hashed_pass = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())

        # Check if the username exists in the DB already, if it does ignore.
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        
        if user == None: user_collection.insert_one({"username":user_username, "password":hashed_pass, "auth":0, "xsrf":0, "place":0})
    return redirect("/") 

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

def substituteGuestHTML(PLACE):
        session['username'] = "Guest"
        replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
        replace_html_element("templates/main.html", '<div class="register" hidden>', '<div class="register">')
        replace_html_element("templates/main.html", '<div class="login" hidden>', '<div class="login">')
        replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest<input hidden type='text' id='current-status' value='Guest'>")
        replace_html_element("templates/main.html", 'id="post_id" value=".*"', 'id="post_id" value="' + str(PLACE) + '"')

@app.route('/', methods=['POST', 'GET'])
def index():
    ID = ID_collection.find_one({},{"_id":0})
    if ID == None: ID = 0;
    else: ID = ID['id']
    PLACE = session.get('place', ID-1);
    # if the user doesn't have a auth cookie; hide logout button and set their status as Guest
    if request.cookies.get('auth') == None:
        substituteGuestHTML(PLACE)

    else:
        hashed_auth = hashlib.sha256(request.cookies.get('auth').encode()).hexdigest()

        # if the user's auth cookie is not in the db; hide logout button and set their status as Guest
        if user_collection.find_one({"auth":hashed_auth}, {"_id":0}) == None:
            substituteGuestHTML(PLACE)

        # if the user's auth cooke is in db; reveal logout button, set their username to what's in db, and load the last comment they viewed
        else:
            user = user_collection.find_one({"auth":hashed_auth}, {"_id":0})
            # Set the session cookie username as it should be (this should resolve the bug of the username in session being lost on restart)
            session['username'] = user['username']
            # hide the logout button and change their status to their username
            replace_html_element("templates/main.html", 'class="logout" hidden.*', 'class="logout">')
            replace_html_element("templates/main.html", '<div class="register">', '<div class="register" hidden>')
            replace_html_element("templates/main.html", '<div class="login">', '<div class="login" hidden>')
            replace_html_element("templates/main.html", "Current status:.*", "Current status: " + user["username"]+"<input hidden type='text' id='current-status' value='"+ user["username"]+"'>")
            
            # update authenticated users place to where they were last viewing
            replace_html_element("templates/main.html", 'id="post_id" value=".*"', 'id="post_id" value="' + str(user["place"]) + '"')

            # stop autheticated users from submitting a comment, websockets will handle this without submitting
            
    if request.method == 'POST': pass
    elif request.method == 'GET': return render_template('main.html')


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
    session['username'] = "Guest"
    return resp


def replace_html_element(filename, search_text, replace_text):
    with open(filename, 'r+') as f:
        file = f.read()
        file = re.sub(search_text, replace_text, file)
        f.seek(0)
        f.write(file)
        f.truncate()


@app.route('/public/homepage.jpg', methods=['GET'])
def homeimage(): return send_file('static/public/homepage.jpg', mimetype = 'image/jpeg')


@app.route('/renderpostcreation', methods=["GET"])
def setuppost(): return render_template("tempposts.html")


@app.route('/favicon.ico', methods=['GET'])
def tabicon(): return send_file('static/public/eagle.ico', mimetype = 'image/x-icon')


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
    if PotentialCreator != None: 
        username = PotentialCreator["username"]
        user_collection.update_one({"username":username}, {"$set": {"place":ID}})

    # add the subject, body, username, and place to post db. Increment ID in db. Then refresh page
    post_collection.insert_one({"ID":ID, "subject":subject, "body":body, "creator":username})
    ID_collection.update_one({"id":ID}, {"$set": {"id":ID + 1}})
    session['place'] = ID
    return redirect('/')


@app.route("/main.js", methods=["GET"])
def sendmainJS(): return send_file("static/main.js",mimetype="text/javascript")


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

@socketio.on('connect')
def handleConnect(data): print("Someone connected.")

@socketio.on("SendMessage")
def sendMessage(data):

    postID = data['channel']
    message = html.escape(data['message'])
    username = html.escape(session['username'])

    # update the comments with the users message and retrieve inserted message
    if message != "" :
        comments_collection.insert_one({"POSTID":str(postID), "body":message, "postowner":username})
        inserted = comments_collection.find_one({"POSTID":str(postID), "body":message, "postowner":username}, {"_id":0})

        emit("sent", {"message": inserted}, broadcast=True)

@socketio.on("join")
def joinRoom(data):

    postID = data['channel']
    username = session['username']

    emit(postID)
    join_room(postID)

    emit(f"User {username} joining Chat {postID}", room=postID)
    emit(username, room=postID)

    comments = comments_collection.find({"POSTID":postID},{"_id":0})
    emit(list(comments), broadcast=False)


@socketio.on('leave')
def leaveRoom(data):

    postID = data['channel']
    leave_room(postID)
    emit(f"User leaving Chat {postID}", room=postID)

# This will be triggered every time the arrows were clicked
@socketio.on('getMax')
def maxPostID(data):

    post = data['postID']
    direction = data['direction']

    # get the max post ID
    ID = 0
    increment = ID_collection.find_one({}, {"_id":0})
    if increment != None: ID = increment["id"]

    # move post to next if there is one above/below it
    if (direction == -1 and post > 0) or (direction == 1 and ID != 0 and post < ID-1): post += direction

    # Get the comments for post. For some reason this line appears to be retrieving nothing when stuff exists.
    comments = comments_collection.find({"POSTID":str(post)}, {"_id":0})
    emit('get max', {"postID": post, 'comments':list(comments)}, broadcast=False)

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
    try:
        extension = userfile.split(".", 1)[1]
    except:
        return redirect("/renderpostcreation")
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
    if PotentialCreator != None: 
        username = PotentialCreator["username"]
        user_collection.update_one({"username":username}, {"$set": {"place":ID}})

    # insert into chat DB, increment message count
    imageelement = "<img src=\"" + imagepath + "\"/>"
    post_collection.insert_one({"ID": ID, "subject": "", "body":imageelement, "creator":username})
    ID_collection.update_one({"id":ID}, {"$set": {"id":ID + 1}})
    session['place'] = ID
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
    if username == "Guest": session['place'] = place
    # update the user's place then return the place
    user_collection.update_one({"username":username}, {"$set": {"place":place}})
    return json.dumps(place)

@app.route("/randomPost", methods = ["GET"])
def assignRandom():
    # To make this simple, we can just use the systems that we already have
    # update the place that is being used to display where they are
    # then just refresh the page. Simple and easy... Right? Right???

    # check to see if there is a user to the given auth_token
    auth_cookie = hashlib.sha256(request.cookies.get("auth","").encode()).hexdigest()
    PotentialCreator = user_collection.find_one({"auth":auth_cookie}, {"_id":0})

    # if authenticated change username to their username, otherwise leave as Guest
    username = "Guest"
    if PotentialCreator != None: username = PotentialCreator["username"]
    # Now we have gotten the username, so now we can generate the random number.
    ID = ID_collection.find_one({}, {"_id":0})
    ran = random.randint(0, ID["id"]-1)
    session["place"] = ran
    if username != "Guest":
        user_collection.update_one({"username":username}, {"$set": {"place":ran}})
    # Seems it was that easy! Did some testing, everything still seems to work.
    # I DID encounter one weird bug where the comments stopped working
    # BUT I wasn't able to replicate it and I think it was just caused because I sent a message before the WebSockets handshake
    # finished. 
    return redirect('/')


@app.after_request
def nosniff(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

if __name__ == "__main__": 
    app.run(debug=True, host="0.0.0.0", port=8080)
    socketio.run(app, allow_unsafe_werkzeug=True)