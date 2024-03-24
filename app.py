import bcrypt
import re
import secrets
import hashlib
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, redirect, make_response, send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired

mongo_client = MongoClient("mongo")
db = mongo_client["cse312Project"]
ID_collection = db["id"] # id
user_collection = db["users"] # username, password, auth, xsrf
post_collection = db["posts"] # ID, subject, body
comments_collection = db["comments"] # POSTID, body

app = Flask(__name__)
app.config["SECRET_KEY"] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'
homepageimg = os.path.join('static', 'public')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET': return redirect("/")
    elif request.method == 'POST':
        user_username = request.form['login_username']
        user_password = request.form['login_password']

        # check if they exist in database
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        if user != None:
            # check if password matches db password, if it doesn't then deny login.
            if bcrypt.checkpw(user_password.encode(), user["password"]): 
                # creating auth token and updating db
                auth_token = secrets.token_urlsafe(70)
                # auth_token = "".join(random.choices(string.ascii_letters, k=50))
                hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
                user_collection.update_one({"username":user_username}, {"$set": {"auth": hashed_auth}})

                resp = make_response(redirect('/'))
                resp.set_cookie(key="auth", value=auth_token, max_age=10000, httponly=True)
                return resp
            
            else: return redirect('/')
        else: return redirect('/')

@app.route('/signup', methods=['POST'])
def signup():
    # register the user
    user_username = request.form['login-username']
    user_password = request.form['login-password']
    user_repassword = request.form['login-password2']
    
    if user_username == "" or user_password == "" or user_repassword == "": 
        return redirect("/")
    elif user_password == user_repassword:
        hashed_pass = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())
        # Check if the username exists in the DB already, if it does ignore.
        user = user_collection.find_one({"username":user_username}, {"_id":0})
        if user == None: 
            user_collection.insert_one({"username":user_username, "password":hashed_pass, "auth":0, "xsrf":0})
    return redirect("/") 

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

# This is the path that is being traveled, can take 2 routes that it can take
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.cookies.get('auth') == None:
        replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
        replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest")
    else:
        hashed_auth = hashlib.sha256(request.cookies.get('auth').encode()).hexdigest()
        if user_collection.find_one({"auth":hashed_auth}, {"_id":0}) == None:
            replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
            replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest")
        else:
            replace_html_element("templates/main.html", 'class="logout" hidden.*', 'class="logout">')
            replace_html_element("templates/main.html", "Current status:.*", "Current status: " + user_collection.find_one({"auth":hashed_auth}, {"_id":0})["username"])


    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        file1 = os.path.join(homepageimg, 'eagle.jpg') #line 20 and the following lines allow you to upload an image
        file2 = os.path.join(homepageimg, 'owl.jpg')
        form = UploadFileForm()
        if form.validate_on_submit():
            file = form.file.data # First grab the file
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
            return "File has been uploaded."
        return render_template('main.html', form=form, image1=file1, image2=file2) #image1 and image2 are the files/images that are given into the html as an image in the html tag <img src = "{{image1}}">

@app.route('/static/css/main.css', methods=['GET'])
def css(): return render_template('main.css')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    token = hashlib.sha256(request.cookies.get('auth').encode()).hexdigest()
    user_collection.update_one({"auth":token}, {"$set": {"auth":""}})
    replace_html_element("templates/main.html", 'class="logout"', 'class="logout" hidden')
    replace_html_element("templates/main.html", "Current status:.*", "Current status: Guest")

    resp = make_response(redirect('/'))
    resp.set_cookie(key="auth", value=request.cookies.get('auth'), max_age=-1, httponly=True)
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

@app.route('/renderpostcreation',methods=["GET"])
def setuppost():
    return send_file("templates/tempposts.html", mimetype="text/html")

@app.route('/favicon.ico', methods=['GET'])
def tabicon():
    return send_file('static/public/eagle.ico', mimetype = 'image/x-icon')

@app.route('/makepost')
def storepost():
    ID = 0
    increment = ID_collection.find_one({"id":ID}, {"_id":0})
    if increment != None:
        ID = increment["id"]
    #Store subject and body
    subject = request.form['subjectbox']
    body = request.form['messagebody']
    if subject == "" or body == "":
        return redirect('/renderpostcreation')
    post_collection.insert_one({"ID": ID,"subject": subject,"body":body})
    #update the ID_collection count
    ID_collection.update_one({"id":ID}, {"$set": {"id":ID+1}})
    return redirect('/')

@app.after_request
def nosniff(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

if __name__ == "__main__": app.run(debug=True, host="0.0.0.0", port=8080)
