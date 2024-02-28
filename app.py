from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' #/// is a relative path, //// is an absolute path
db = SQLAlchemy(app) #initializes the database for the app

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)    #creates a column in the database that holds an id of integer value
    content = db.Column(db.String(500), nullable=False) #creates a column that holds each task/content that is a string with a maximum length of 500
    date_created = db.Column(db.DateTime, default=datetime.utcnow) #creates a column that holds when each entry is created, this is set automatically

    def __repr__(self): #returns a string of the task and id whenever a new element is created
        return '<Task %r>' % self.id


@app.route('/') #This is the path that is being traveled
def index():    #This is what runs when you go to this path 
    return render_template('index.html') #it returns the rendering of the html file

if __name__ == "__main__":
    app.run(debug=True)