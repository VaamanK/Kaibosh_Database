from flask import Flask, render_template, redirect, request, session
# Import Flask and related modules to create web routes
# handle HTML templates
# redirect users
# handle form data
# manage sessions.

import sqlite3
from sqlite3 import Error
# Import SQLite to connect and work with the database.
#Also import Error to handle any database errors.

from flask_bcrypt import Bcrypt
# Import Bcrypt for keeping passwords safe and hidden in the event of a data breach.

DATABASE = "kaibosh_table"
# Define the filename of your SQLite database.

app = Flask(__name__)
# Create a Flask application instance.

app.secret_key = 'hhnatk'
# Set a secret key to manage the flask session.
# This is used to sign cookies and keep user sessions secure (secret).

bcrypt = Bcrypt(app)
# Start using bcrypt with flask, it can now work with flask when coded (in the login and signup).

def insert_admin():
    # This function checks if there's an admin account under the email admin@kaibosh.nz
    # If there is not, then it will create one.
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()
    admin_email = "admin@kaibosh.nz"
    admin_password = "Kaibosh123"
    role = 1
    approved = 1
    # Query to see if admin email already exists
    cursor.execute("SELECT * FROM signup WHERE v_email = ?", (admin_email,))
    if cursor.fetchone():
        print("Admin already exists.")
        # If an admin account exists, it will print this in the console.
    else:
        # If admin does not exist
        # hash the password and insert admin into the signup table
        # with role=1 and approved=1.
        # role=1 states that the account is an admin, role=0 means they are a volunteer.
        #approved=1 states that the account has been approved by an admin.
        hashed_password = bcrypt.generate_password_hash(admin_password)
        cursor.execute("INSERT INTO signup (v_email, v_password, role, approved) VALUES (?, ?, ?, ?)",
                       (admin_email, hashed_password, role, approved))
        con.commit()
        print("Admin account created.")
    con.close()

insert_admin()
# This runs the function when app starts to make sure admin user exists.

@app.context_processor
def inject_user_status():
    # This function makes variables global across all templates.
    return dict(admin=is_admin(), login=is_login())
    # This return decides what variables are global, rather than unnecessarily having all of them.

def connect_database(db_file):
    # This function connects the file to sqlite.
    # set row factory so rows behave like dicts. This comes into play during admin accept/rejects.
    try:
        connection = sqlite3.connect(db_file)
        connection.row_factory = sqlite3.Row
        return connection
    except Error:
        print("An error occurred when connecting to the database.")

def is_admin():
    # This function cheks if the current session user is an admin
    return session.get('admin') == 1

def is_login():
    # This function checks if there is already a logged in user
    # It does so by checking if an email is stored in session
    return session.get('v_email') is not None

@app.route('/')
def homepage():
    # Route for homepage
    # Renders the homepage.html template.
    return render_template('homepage.html')

@app.route('/collections', methods=['GET', 'POST'])
def collections():
    # Route for viewing and adding collections.
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('v_email'):
        # If the form is submitted, by a user that is logged in.
        content = request.form.get('collected_box_contents').strip()
        weight = request.form.get('collected_box_weight')
        donor = request.form.get('donor').strip()
        # All of this will be inserted in the collection table, with approved=0.
        # It will require admin approval to display on the table to non admins.
        cursor.execute('INSERT INTO collections (collected_box_contents, collected_box_weight, donor, approved) VALUES (?, ?, ?, 0)',
                       (content, weight, donor))
        # This is the code that adds collected_box_contents, collected_box_weight, donor and approved into collections.
        con.commit()

    if is_admin():
        # Admins see all collections regardless of approval status.
        cursor.execute("SELECT * FROM collections")
    else:
        # Regular users only see approved collections.
        cursor.execute("SELECT * FROM collections WHERE approved = 1")
    boxes = cursor.fetchall()
    con.close()
    return render_template('collections.html', boxes=boxes)

@app.route('/sort', methods=['GET', 'POST'])
def sort():
    # Route for viewing and adding sorts.
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('v_email'):
        # If the form is submitted by a user that is logged in,
        # then box_type, box_contents, box_weight and collected_box_id will be inserted into a row in sorts.
        # It will have a default approval of 0, meaning it requires admin approval.
        box_type = request.form.get('box_type')
        box_contents = request.form.get('box_contents')
        box_weight = request.form.get('box_weight')
        collected_box_id = request.form.get('collected_box_id')
        cursor.execute('INSERT INTO sorts (box_type, box_contents, box_weight, collected_box_id, approved) VALUES (?, ?, ?, ?, 0)',
                       (box_type, box_contents, box_weight, collected_box_id))
        con.commit()

    if is_admin():
        # Admin sees all sorts.
        cursor.execute("SELECT * FROM sorts")
    else:
        # Regular users see only approved sorts.
        cursor.execute("SELECT * FROM sorts WHERE approved = 1")
    sorted_boxes = cursor.fetchall()

    # Get collection options for dropdown (to link sorts to collections).
    # This makes use of the foreign key in the table.
    collection_options, _ = get_dropdown_data()
    con.close()
    return render_template("sort.html", sorted_boxes=sorted_boxes, collection_options=collection_options)

@app.route('/receivers', methods=['GET', 'POST'])
def receivers():
    # Route for viewing and adding receiver (donation) records.
    con = connect_database(DATABASE)
    cursor = con.cursor()

    if request.method == 'POST' and session.get('v_email'):
        # If a form is submitted by someone who is logged in
        # Then donation_contents, receiver_name, sort_id, approved are inserted into a row in receivers.
        # It will have a default approval of 0, which means that it will require admin approval.
        donation_contents = request.form.get('donation_contents')
        receiver_name = request.form.get('receiver_name')
        sort_id = request.form.get('sort_id')
        cursor.execute('INSERT INTO receivers (donation_contents, receiver_name, sort_id, approved) VALUES (?, ?, ?, 0)',
                       (donation_contents, receiver_name, sort_id))
        con.commit()

    if is_admin():
        # Admin sees all receivers.
        cursor.execute("SELECT donation_contents, receiver_name FROM receivers")
    else:
        # Regular users see only approved receiver records.
        cursor.execute("SELECT donation_contents, receiver_name FROM receivers WHERE approved = 1")
    donation_records = cursor.fetchall()

    # Get sort options for dropdown.
    _, sort_options = get_dropdown_data()
    con.close()
    return render_template("receivers.html", donation_records=donation_records, sort_options=sort_options)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Route to handle login.
    if request.method == 'POST':
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')
        # If form is submitted, get the email and password from the form.
        # Lower and strip is used to make sure that there aren't any accidental errors.

        # Connect to the database
        con = connect_database(DATABASE)
        # Create a cursor object to execute SQL queries
        cursor = con.cursor()
        # Run a query to get the hashed password, role, and approval status
        # for the user with the given email from the signup sqlite table.
        cursor.execute("SELECT v_password, role, approved FROM signup WHERE v_email = ?", (email,))
        # Fetch one record from the query result (or None if no matching user)
        user_info = cursor.fetchone()
        # Close the database connection
        con.close()

        if not user_info:
            # If user not found, redirect with error.
            return redirect("/login?error=email-or-password-is-wrong")

        v_password, role, approved = user_info

        if not bcrypt.check_password_hash(v_password, password):
            # If password wrong, redirect with error.
            return redirect('/login?error=email-or-password-is-wrong')

        if approved == 0:
            # If account not approved, redirect with specific error.
            return redirect("/login?error=account-not-approved")

        # If everything okay, save user info in session.
        session['v_email'] = email
        session['approved'] = approved
        session['admin'] = role

        # Redirect admin users to admin_pending page, others to homepage.
        if role == 1:
            return redirect("/admin_pending")
        return redirect("/")

    # If GET request, just render login page.
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session and log out user.
    session.clear()
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Route for volunteer signup.
    if request.method == 'POST':
        fname = request.form.get('volunteer_fname').title().strip()
        lname = request.form.get('volunteer_lname').title().strip()
        email = request.form.get('volunteer_email').lower().strip()
        password = request.form.get('volunteer_password')
        password2 = request.form.get('volunteer_password2')
        # Get all the information from the form to here.

        if password != password2:
            # Passwords don't match, redirect with error.
            return redirect("/signup?error=passwords-do-not-match")
        if len(password) < 8:
            # Password too short, redirect with error.
            return redirect("/signup?error=password-must-be-8-characters")

        # Hash the plain text password securely using bcrypt
        hashed_pw = bcrypt.generate_password_hash(password)
        # Connect to the database
        con = connect_database(DATABASE)
        # Create a cursor object to execute SQL queries
        cursor = con.cursor()
        # Check if the email already exists in the signup table
        cursor.execute("SELECT * FROM signup WHERE v_email = ?", (email,))
        # If a record with this email is found
        if cursor.fetchone():
            # Email is already registered, so redirect to signup page with an error message
            return redirect("/signup?error=email-already-registered")

        # Insert new user into the signup sqlite table.
        cursor.execute("INSERT INTO signup (v_fname, v_lname, v_email, v_password) VALUES (?, ?, ?, ?)",
                       (fname, lname, email, hashed_pw))
        con.commit()
        con.close()
        # Redirect to signup page with success message that approval is pending.
        return redirect("/signup?success=account-creation-pending")
    # If GET request, render signup page.
    return render_template('signup.html')

def get_dropdown_data():
    # Function to get options for dropdown menus on sort and receivers pages.

    con = connect_database(DATABASE)
    cursor = con.cursor()

    # Display collections that are approved by admins but aren't yet linked to sorts.
    cursor.execute("SELECT box_id, collected_box_contents FROM collections WHERE approved = 1 AND box_id NOT IN (SELECT collected_box_id FROM sorts WHERE collected_box_id IS NOT NULL)")
    collection_options = cursor.fetchall()

    # Display sorts that are approved by admins but aren't yet linked to receivers.
    cursor.execute("SELECT sort_id, box_contents FROM sorts WHERE approved = 1 AND sort_id NOT IN (SELECT sort_id FROM receivers WHERE sort_id IS NOT NULL)")
    sort_options = cursor.fetchall()

    con.close()
    return collection_options, sort_options

@app.route('/admin_pending')
def admin_pending():
    # Admin dashboard showing all unapproved items for collections, sorts, receivers, and volunteers.
    # Connect to the database
    con = connect_database(DATABASE)
    # Create a cursor to run SQL commands
    cursor = con.cursor()

    # Select all collections that have not yet been approved
    cursor.execute("SELECT * FROM collections WHERE approved = 0")
    # Fetch all unapproved collections into a list
    pending_collections = cursor.fetchall()

    # Select all sorts that have not yet been approved
    cursor.execute("SELECT * FROM sorts WHERE approved = 0")
    # Fetch all unapproved sorts into a list
    pending_sorts = cursor.fetchall()

    # Select all receivers that have not yet been approved
    cursor.execute("SELECT * FROM receivers WHERE approved = 0")
    # Fetch all unapproved receivers into a list
    pending_receivers = cursor.fetchall()

    # Select all volunteers (signup accounts) that have not yet been approved
    cursor.execute("SELECT * FROM signup WHERE approved = 0")
    # Fetch all unapproved volunteer accounts into a list
    pending_volunteers = cursor.fetchall()

    # Close the database connection to free resources
    con.close()

    # Render admin_pending.html passing all pending items and user login/admin status.
    return render_template('admin_pending.html',
                           pending_collections=pending_collections,
                           pending_sorts=pending_sorts,
                           pending_receivers=pending_receivers,
                           pending_volunteers=pending_volunteers,
                           admin=is_admin(), login=is_login())


@app.route('/admin/collections/approve', methods=['GET', 'POST'])
def approve_collection():
    # Get the box_id from the form submitted by admin
    box_id = request.form.get('box_id')
    # Connect to the database
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Update the collections table to set approved = 1 for this box_id (mark as approved)
    cursor.execute("UPDATE collections SET approved = 1 WHERE box_id = ?", (box_id,))
    # Save changes
    con.commit()
    # Close connection
    con.close()
    # After approving, redirect admin back to the pending approvals page
    return redirect('/admin_pending')


@app.route('/admin/collections/reject', methods=['POST'])
def reject_collection():
    # Get the box_id from form to know which collection to reject (delete)
    box_id = request.form.get('box_id')
    # Connect to database
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Delete the collection entry with this box_id from the database
    cursor.execute("DELETE FROM collections WHERE box_id = ?", (box_id,))
    # Commit the deletion
    con.commit()
    # Close the database connection
    con.close()
    # Redirect back to the admin pending page after rejection
    return redirect('/admin_pending')


@app.route('/admin/sorts/approve', methods=['POST'])
def approve_sort():
    # Get sort_id of the sort entry to approve
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Mark the sort entry as approved by setting approved = 1
    cursor.execute("UPDATE sorts SET approved = 1 WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    # Redirect back to the admin pending page
    return redirect('/admin_pending')


@app.route('/admin/sorts/reject', methods=['POST'])
def reject_sort():
    # Get sort_id of the sort entry to delete
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Delete the sort entry with this sort_id
    cursor.execute("DELETE FROM sorts WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    # Redirect to admin pending page after rejecting
    return redirect('/admin_pending')


@app.route('/admin/receivers/approve', methods=['POST'])
def approve_receiver():
    # Get the sort_id related to the receiver entry to approve
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Approve the receiver entry by updating approved = 1
    cursor.execute("UPDATE receivers SET approved = 1 WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    # Redirect to admin pending approvals page
    return redirect('/admin_pending')


@app.route('/admin/receivers/reject', methods=['POST'])
def reject_receiver():
    # Get the sort_id to identify the receiver entry to delete
    sort_id = request.form.get('sort_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Delete the receiver entry where sort_id matches
    cursor.execute("DELETE FROM receivers WHERE sort_id = ?", (sort_id,))
    con.commit()
    con.close()
    # Redirect back to the pending approvals page
    return redirect('/admin_pending')


@app.route('/admin/volunteers/approve', methods=['POST'])
def approve_volunteer():
    # Get volunteer id to approve
    v_id = request.form.get('v_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Mark volunteer as approved by setting approved = 1
    cursor.execute("UPDATE signup SET approved = 1 WHERE v_id = ?", (v_id,))
    con.commit()
    con.close()
    # Redirect admin back to pending approvals page
    return redirect('/admin_pending')


@app.route('/admin/volunteers/reject', methods=['POST'])
def reject_volunteer():
    # Get volunteer id to reject (delete)
    v_id = request.form.get('v_id')
    con = connect_database(DATABASE)
    cursor = con.cursor()
    # Delete volunteer record from signup table
    cursor.execute("DELETE FROM signup WHERE v_id = ?", (v_id,))
    con.commit()
    con.close()
    # Redirect back to pending approvals
    return redirect('/admin_pending')


if __name__ == '__main__':
    # Run the Flask app (for development)
    app.run()
