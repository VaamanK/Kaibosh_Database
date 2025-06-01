from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "kaibosh_table"

app = Flask(__name__)

def connect_database(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
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
    if request.method == 'POST':
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')

        try:
            con = connect_database(DATABASE)
            cursor = con.cursor()

            query = "SELECT v_password FROM volunteer_signup WHERE v_email = ?"
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            con.close()

            if row and check_password_hash(row[0], password):
                return redirect("/")
            else:
                return redirect("/login?error=invalid-credentials")

        except Error as e:
            print(f"Login error: {e}")
            return redirect("/login?error=database-error")

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        fname = request.form.get('volunteer_fname').title().strip()
        lname = request.form.get('volunteer_lname').title().strip()
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')
        password2 = request.form.get('volunteer_password2')

        if password != password2:
            return redirect("/signup?error=passwords-do-not-match")

        if len(password) < 8:
            return redirect("/signup?error=password-must-be-8-characters")

        hashed_pw = generate_password_hash(password)

        try:
            con = connect_database(DATABASE)
            cursor = con.cursor()

            query = "SELECT * FROM volunteer_signup WHERE v_email = ?"
            cursor.execute(query, (email,))
            if cursor.fetchone():
                return redirect("/signup?error=email-already-registered")

            query_insert = "INSERT INTO volunteer_signup (v_fname, v_lname, v_email, v_password) VALUES (?, ?, ?, ?)"

            cursor.execute(query_insert, (fname, lname, email, hashed_pw))
            con.commit()
            con.close()

            return redirect("/login?success=account-created")

    return render_template('signup.html')

if __name__ == '__main__':
    app.run()
