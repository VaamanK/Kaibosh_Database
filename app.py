from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error



DATABASE = "kaibosh_table"

app = Flask(__name__)
app.secret_key = 'hhnatk'


@app.context_processor
def inject_user_status():
    return dict(admin=is_admin(), login=is_login())


def connect_database(db_file):
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    return connection


def is_admin():
    if session.get('admin') == 1:
        return True
    else:
        return False


def is_login():
    print(session.get('user_email'))
    if session.get('user_email') == None:
        return False
    else:
        return True


@app.route('/', methods=['GET', 'POST'])
def homepage():
    return render_template('homepage.html', admin=is_admin(), login=is_login())


@app.route('/collections', methods=['GET', 'POST'])
def collections():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        content = request.form.get('collected_box_contents').strip()
        weight = request.form.get('collected_box_weight')
        donor = request.form.get('donor').strip()

        insert_query = 'INSERT INTO collections (collected_box_contents, collected_box_weight, donor, approved) VALUES (?, ?, ?, 0)'
        cursor.execute(insert_query, (content, weight, donor))
        con.commit()

    cursor.execute("SELECT * FROM collections WHERE approved = 1")
    boxes = cursor.fetchall()
    con.close()
    return render_template('collections.html', boxes=boxes, admin=is_admin(), login=is_login())


@app.route('/sort', methods=['GET', 'POST'])
def sort():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        box_type = request.form.get('box_type')
        box_contents = request.form.get('box_contents')
        box_weight = request.form.get('box_weight')
        collected_box_id = request.form.get('collected_box_id')

        insert_query = 'INSERT INTO sorts (box_type, box_contents, box_weight, collected_box_id, approved) VALUES (?, ?, ?, ?, 0)'
        cursor.execute(insert_query, (box_type, box_contents, box_weight, collected_box_id))
        con.commit()

    cursor.execute("SELECT * FROM sorts WHERE approved = 1")
    sorted_boxes = cursor.fetchall()
    collection_options, _ = get_dropdown_data()

    con.close()
    return render_template("sort.html", sorted_boxes=sorted_boxes, admin=is_admin(), login=is_login(), collection_options=collection_options)


@app.route('/receivers', methods=['GET', 'POST'])
def receivers():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('user_email'):
        donation_contents = request.form.get('donation_contents')
        receiver_name = request.form.get('receiver_name')
        sort_id = request.form.get('sort_id')

        insert_query = 'INSERT INTO receivers (donation_contents, receiver_name, sort_id, approved) VALUES (?, ?, ?, 0)'
        cursor.execute(insert_query, (donation_contents, receiver_name, sort_id))
        con.commit()

    cursor.execute("SELECT donation_contents, receiver_name FROM receivers WHERE approved = 1")
    donation_records = cursor.fetchall()
    _ ,sort_options = get_dropdown_data()
    con.close()

    return render_template("receivers.html", donation_records=donation_records, admin=is_admin(), login=is_login(),
                           sort_options=sort_options)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')

        query = "SELECT v_password, role, approved FROM signup WHERE v_email = ?"
        con = connect_database(DATABASE)
        cursor = con.cursor()
        cursor.execute(query, (email,))
        user_info = cursor.fetchone()
        con.close()

        if not user_info:
            return redirect("/login?error=user-not-found")

        v_password = user_info[0]
        approved = user_info[2]
        admin = user_info[1]

        if password != v_password:
            return redirect("/login?error=wrong-password")

        else:
            session['user_email'] = email
            session['approved'] = approved
            session['admin'] = admin
            print(session)
            if session['approved'] == 0:
                return redirect("/login?error=account-not-approved")
            return redirect("/")

    return render_template('login.html', admin=is_admin(), login=is_login())


@app.route('/logout')
def logout():
    session.clear()
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

        con = connect_database(DATABASE)
        cursor = con.cursor()

        query = "SELECT * FROM signup WHERE v_email = ?"
        cursor.execute(query, (email,))
        if cursor.fetchone():
            return redirect("/signup?error=email-already-registered")

        query_insert = "INSERT INTO signup (v_fname, v_lname, v_email, v_password, role, approved) VALUES (?, ?, ?, ?, 0, 0)"
        cursor.execute(query_insert, (fname, lname, email, password))
        con.commit()
        con.close()
        return redirect("/login?success=account-creation-pending")

    return render_template('signup.html')


def get_dropdown_data():
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute(
        "SELECT box_id, collected_box_contents FROM collections WHERE approved = 1 AND box_id NOT IN (SELECT collected_box_id FROM sorts WHERE collected_box_id IS NOT NULL)")
    collection_options = cursor.fetchall()
    cursor.execute(
        "SELECT sort_id, box_contents FROM sorts WHERE approved = 1 AND sort_id NOT IN (SELECT sort_id FROM receivers WHERE sort_id IS NOT NULL)")
    sort_options = cursor.fetchall()
    con.close()
    return collection_options, sort_options


@app.route('/admin_pending')
def admin_pending():
    con = connect_database(DATABASE)
    cursor = con.cursor()

    cursor.execute("SELECT * FROM collections WHERE approved = 0")
    pending_collections = cursor.fetchall()

    cursor.execute("SELECT * FROM sorts WHERE approved = 0")
    pending_sorts = cursor.fetchall()

    cursor.execute("SELECT * FROM receivers WHERE approved = 0")
    pending_receivers = cursor.fetchall()

    cursor.execute("SELECT * FROM signup WHERE approved = 0")
    pending_volunteers = cursor.fetchall()

    con.close()

    return render_template('admin_pending.html',
                           pending_collections=pending_collections,
                           pending_sorts=pending_sorts,
                           pending_receivers=pending_receivers,
                           pending_volunteers=pending_volunteers, admin=is_admin(), login=is_login())


@app.route('/admin/collections/approve', methods=['GET', 'POST'])
def approve_collection():
    box_id = request.form.get('box_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("UPDATE collections SET approved = 1 WHERE box_id = ?", (box_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/collections/reject', methods=['POST'])
def reject_collection():
    box_id = request.form.get('box_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("DELETE FROM collections WHERE box_id = ?", (box_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/sorts/approve', methods=['POST'])
def approve_sort():
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("UPDATE sorts SET approved = 1 WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/sorts/reject', methods=['POST'])
def reject_sort():
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("DELETE FROM sorts WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/receivers/approve', methods=['POST'])
def approve_receiver():
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("UPDATE receivers SET approved = 1 WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/receivers/reject', methods=['POST'])
def reject_receiver():
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("DELETE FROM receivers WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/volunteers/approve', methods=['POST'])
def approve_volunteer():
    v_id = request.form.get('v_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("UPDATE signup SET approved = 1 WHERE v_id = ?", (v_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


@app.route('/admin/volunteers/reject', methods=['POST'])
def reject_volunteer():
    v_id = request.form.get('v_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    cursor.execute("DELETE FROM signup WHERE v_id = ?", (v_id,))
    con.commit()
    con.close()
    return redirect('/admin_pending')


if __name__ == '__main__':
    app.run()
