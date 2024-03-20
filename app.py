import bcrypt
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, redirect
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired

mongo_client = MongoClient("mongo")
db = mongo_client["cse312Project"]
user_collection = db["users"] # username, password, auth, xsrf
post_collection = db["posts"] # ID, subject, body
comments_collection = db["comments"] # POSTID, body

app = Flask(__name__)
app.config["SECRET_KEY"] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'
homepageimg = os.path.join('static', 'public')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' #/// is a relative path, //// is an absolute path
#db = SQLAlchemy(app) #initializes the database for the app

# class Todo(db.Model):
#     id = db.Column(db.Integer, primary_key=True)    #creates a column in the database that holds an id of integer value
#     content = db.Column(db.String(500), nullable=False) #creates a column that holds each task/content that is a string with a maximum length of 500
#     date_created = db.Column(db.DateTime, default=datetime.utcnow) #creates a column that holds when each entry is created, this is set automatically

#     def __repr__(self): #returns a string of the task and id whenever a new element is created
#         return '<Task %r>' % self.id

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET': return render_template('login.html')
    elif request.method == 'POST':
        user_username = request.form['login_username']
        user_password = request.form['login_password']

        # check if they exist in database
        user = user_collection.find_one({"username": user_username}, {"_id":0})
        # Mike: To whoever put the statement below here... Why?
        print(user)
        if not user == None:
            if bcrypt.checkpw(user_password.encode(), user["password"]): 
                # TODO: Make authtoken, store authtoken
                return redirect("/")
            else:
                return render_template('login.html')
        else: 
            return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    # register the user
    user_username = request.form['login-username']
    user_password = request.form['login-password']
    user_repassword = request.form['login-password2']
    if user_username == "" or user_password == "":
        return render_template('register.html')
    
    if user_password == user_repassword:
        hashed_pass = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())
        # Check if the username exists in the DB already, if it does ignore.
        user = user_collection.find_one({"username": user_username}, {"_id":0})
        if user == None:
            user_collection.insert_one({"username":user_username, "password": hashed_pass, "auth" : 0, "xsrf": 0})
            return redirect("/login")
        else: 
            return render_template('register.html') 
    else: return render_template('register.html') 

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

# This is the path that is being traveled, can take 2 routes that it can take
@app.route('/', methods=['POST', 'GET'])
def index():
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
def css():
    return render_template('main.css')

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/logout', methods=['GET'])
def logout():
    return render_template('login.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
