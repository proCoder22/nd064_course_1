import sqlite3
from sqlite3.dbapi2 import connect

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from flask.wrappers import Response
from werkzeug.exceptions import abort
import logging

logging.basicConfig(level=logging.DEBUG)
# This variable will have total active DB connections at all times
active_database_connections = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global active_database_connections
    connection = sqlite3.connect('database.db')
    active_database_connections += 1
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global active_database_connections
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    active_database_connections -= 1
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    global active_database_connections
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    active_database_connections -= 1
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning("Non existing article is requested; 404 returned")
        return render_template('404.html'), 404
    else:
        app.logger.info("Article is requested: %s", post["title"])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("About Us page is retrieved")
    return render_template('about.html')

# Define the health check endpoint
@app.route("/healthz")
def healthz():
    global active_database_connections
    try:
        get_db_connection()
        # checking if post 1 exists assuming that there'll always be one record
        # this will also help in checking any database related issues
        get_post(1)
    except Exception as e:
        app.logger.error("Error Occured in Health Check")
        return jsonify({"result:" : "ERROR - unhealthy"}), 500
    active_database_connections -= 1
    return jsonify({"result:" : "OK - healthy"}), 200


#Define the metrics functionality
@app.route('/metrics')
def metrics():
    global active_database_connections
    response = {}
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response['active_database_connections'] = active_database_connections
    response['post_count'] = len(posts)
    return jsonify(response), 200


# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global active_database_connections
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info("New Article Created: %s", title)
            active_database_connections -= 1
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
