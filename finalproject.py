#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template, flash

#App configuration items
DATABASE = "books.db"
SECRET_KEY = "key"
USERNAME = "johnny"
PASSWORD = "password"

app = Flask(__name__)
app.config.from_object(__name__)

#Function creates and establishes connection with DB.
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

#Request Database Connection
@app.before_request
def before_request():
    g.db = connect_db()

#Close Database Connection
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

#Creates the login route
@app.route('/')
def index():
    return redirect('/login')

#Function to capture errors and create session.
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'johnny':
            error = 'Username is Invalid.'
            return render_template('login.html', error=error)
        elif request.form['password'] != 'password':
            error = 'Password is Invalid.'
            return render_template('login.html', error=error)

        else:
            session['logged_in'] = True
            return redirect('/dashboard')

    else:
        return render_template('login.html', error=error)


#Function to create dashboard route and select books from catalogue.
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if session['logged_in'] is not True:
        return redirect('/login')
    else:
        cur = g.db.execute('Select id, book_isbn, book_title, book_author, book_pagecount, book_rating FROM books')
        books = [dict(id=row[0], book_title=row[2], book_author=row[3], book_pagecount=row[4], book_rating=row[5])
                    for row in cur.fetchall()]

        return render_template("dashboard.html", books=books)


#Function Searches Google Books by ISBN via API
@app.route('/isbn_search', methods=['GET', 'POST'])
def isbn_search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    elif request.method == 'GET':
        return render_template("searchbook.html")

    elif request.method == 'POST':
        error = None
        if request.form['btn'] == 'search':
            books_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
            final_url = books_url + str(request.form['isbn'])
            json_obj = urllib2.urlopen(final_url)
            data = json.load(json_obj)

            if data['totalItems'] == 0:
                error = 'No Results Found with ISBN!  Try Again.'
                return render_template('searchbook.html', error=error)

            else:
                for item in data['items']:
                    title = str(item['volumeInfo']['title'])
                    author = str(item['volumeInfo']['authors'][0])
                    pagecount = int(item['volumeInfo']['pageCount'])
                    rating = int(item['volumeInfo']['averageRating'])

                g.db.execute('INSERT INTO books (book_isbn, book_title, book_author, book_pagecount, book_rating) '
                             'values (?, ?, ?, ?, ?)',
                             [request.form['isbn'], title, author, pagecount,
                              rating])
                g.db.commit()
    return redirect(url_for('dashboard'))

#Function deletes the book from the catalogue
@app.route('/delete/<ID>', methods=['POST'])
def delete(ID):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    elif request.method == 'POST':
        g.db.execute('DELETE FROM books where ID =?', [ID])
        g.db.commit()

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)