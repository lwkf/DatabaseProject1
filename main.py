import sqlite3
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
DATABASE = 'database.db'

#################### DATABASE ####################

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

#################### INDEX PAGE #################### --> Show Movies & Shows
@app.route('/')
def index():
    return render_template('index.html')

# test db (use to check if db is working) (not needed in final version)
@app.route('/test')
def test():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    return jsonify(users)

#################### CREATE USER PAGE #################### --> User can create an account
@app.route('/createUser')
def createUser():
    return render_template('createUser.html')

@app.route('/createUser', methods=['POST'])
def createAccountPost():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (request.form['username'], request.form['password']))
    db.commit()
    # return to login page
    return render_template('login.html')

#################### LOGIN PAGE #################### --> User can login to their account
@app.route('/login')
def login():
    return render_template('loginUser.html')

@app.route('/login', methods=['POST'])
def loginPost():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (request.form['username'], request.form['password']))
    user = cursor.fetchone()
    if user:
        return render_template('index.html', username=user[1])
    return render_template('loginUser.html')

#################### USER PROFILE PAGE #################### --> User can view their profile details (username, email, comments)
@app.route('/userProfile')
def userProfile():
    return render_template('userProfile.html')

#################### MOVIE PAGE #################### --> User can view movie & show details (title, genre, rating, comments)
@app.route('/movie')
def movie():
    return render_template('movieShowcase.html')

#################### CATALOG PAGE #################### --> User can view all movies & shows
@app.route('/catalog')
def catalog():
    return render_template('catalog.html')

#################### LOGOUT PAGE #################### --> User can logout of their account
@app.route('/logout')
def logout():
    return render_template('loginUser.html')

# Run the app
if __name__ == '__main__':
    # Initialize the database
    init_db()
    app.run(debug=True)