import bcrypt
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, redirect
# from flask_sqlalchemy import SQLAlchemy

mongo_client = MongoClient("mongo")
db = mongo_client["cse312Project"]
user_collection = db["users"] # username, password, auth, xsrf
post_collection = db["posts"] # ID, subject, body
comments_collection = db["comments"] # POSTID, body

app = Flask(__name__)
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
        print(user)
        if bcrypt.checkpw(user_password.encode(), user["password"]): return redirect("/")
        else: return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    # register the user
    user_username = request.form['login-username']
    user_password = request.form['login-password']
    user_repassword = request.form['login-password2']
    
    if user_password == user_repassword:
        # TODO: hash password before storing it
        hashed_pass = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())
        user_collection.insert_one({"username":user_username, "password": hashed_pass, "auth" : 0, "xsrf": 0})
        return redirect("/login")
    else: return render_template('register.html') 

# This is the path that is being traveled, can take 2 routes that it can take
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST': pass
    elif request.method == 'GET':
        return render_template('main.html')

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
