from flask import Flask, render_template
import sqlite3
from sqlite3 import Error

DATABASE = "kaibosh_table"

app = Flask(__name__)

def connect_database(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print(f'Error while connecting to database: {e}')
    return None

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/input')
def input():
    return render_template('input.html')

@app.route('/sort')
def sort():
    return render_template('sort.html')

@app.route('/output')
def output():
    return render_template('output.html')

@app.route('/login', methods=['POST', 'GET'])
def login():

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    con = connect_database(DATABASE)
    query = "SELECT "
    return render_template('signup.html')


if __name__ == '__main__':
    app.run()
