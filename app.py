from flask import Flask, render_template, redirect, request, session, url_for
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "kaibosh_table"

app = Flask(__name__)
app.secret_key = 'hhnatk'

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

@app.route('/collections', methods=['GET', 'POST'])
def collections():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        content = request.form.get('collected_box_contents').strip()
        weight = request.form.get('collected_box_weight')
        donor = request.form.get('donor').strip()

        insert_query = 'INSERT INTO collections (collected_box_contents, collected_box_weight, donor) VALUES (?, ?, ?)'
        cursor.execute(insert_query, (content, weight, donor))
        con.commit()

    cursor.execute("SELECT * FROM collections")
    boxes = cursor.fetchall()
    con.close()
    return render_template('collections.html', boxes=boxes, can_add=session.get('user_email') is not None)

@app.route('/sort', methods=['GET', 'POST'])
def sort():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        box_type = request.form.get('box_type')
        box_contents = request.form.get('box_contents')
        box_weight = request.form.get('box_weight')
        collected_box_id = request.form.get('collected_box_id')

        insert_query = 'INSERT INTO sorts (box_type, box_contents, box_weight, collected_box_id) VALUES (?, ?, ?, ?)'
        cursor.execute(insert_query, (box_type, box_contents, box_weight, collected_box_id))
        con.commit()

    cursor.execute("SELECT * FROM sorts")
    sorted_boxes = cursor.fetchall()
    collection_options, _ = get_dropdown_data()
    con.close()

    return render_template("sort.html", sorted_boxes=sorted_boxes, can_add=session.get('user_email') is not None, collection_options=collection_options)

@app.route('/receivers', methods=['GET', 'POST'])
def receivers():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        donation_contents = request.form.get('donation_contents')
        receiver_name = request.form.get('receiver_name')
        sort_id = request.form.get('sort_id')

        insert_query = 'INSERT INTO receivers (donation_contents, receiver_name, sort_id) VALUES (?, ?, ?)'
        cursor.execute(insert_query, (donation_contents, receiver_name, sort_id))
        con.commit()

    cursor.execute("SELECT donation_contents, receiver_name FROM receivers")
    donation_records = cursor.fetchall()
    _, sort_options = get_dropdown_data()
    con.close()

    return render_template("receivers.html", donation_records=donation_records, can_add=session.get('user_email') is not None, sort_options=sort_options)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')

        con = connect_database(DATABASE)
        cursor = con.cursor()
        query = "SELECT v_password FROM volunteer_signup WHERE v_email = ?"
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        con.close()

        if row and check_password_hash(row[0], password):
            session['user_email'] = email
            return redirect("/")
        else:
            return redirect("/login?error=invalid-credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

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

def get_dropdown_data():
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("SELECT box_id, collected_box_contents FROM collections WHERE box_id NOT IN (SELECT collected_box_id FROM sorts WHERE collected_box_id IS NOT NULL)")
    collection_options = cursor.fetchall()
    cursor.execute("SELECT sort_id, box_contents FROM sorts WHERE sort_id NOT IN (SELECT sort_id FROM receivers WHERE sort_id IS NOT NULL)")
    sort_options = cursor.fetchall()
    con.close()
    return collection_options, sort_options


if __name__ == '__main__':
    app.run()
