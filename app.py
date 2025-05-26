from flask import Flask, render_template

app = Flask(__name__)



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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')


if __name__ == '__main__':
    app.run()
