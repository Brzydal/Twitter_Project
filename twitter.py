from datetime import datetime

from flask import (Flask, redirect,
                   render_template, request, session, url_for)
from models.comment import Comment
from models.crypto import check_password
from models.message import Message
from models.tweet import Tweet
from models.user import User
from mysql.connector import connect
from mysql.connector.errors import ProgrammingError

app = Flask(__name__)


def connect_db():
    """
    This method is connecting to database using: user, password, host and database as listed below
    :return: <mysql.connector.connection.MySQLConnection object> if connected or None otherwise

    """
    user = 'root'
    password = 'coderslab'
    host = 'localhost'
    database = 'twitter_db'
    try:
        cnx = connect(user=user, password=password, host=host, database=database)
        print("Connected...")
        return cnx
    except ProgrammingError:
        print("Not connected...")
 

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This method handles Login View.
    :return: Redirect to all_tweets view when login successful or back to login view if not.
    """
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cnx = connect_db()  
        cursor = cnx.cursor()
        sql = "SELECT user_id, hashed_password FROM Users WHERE email='{}'".format(username)
        result = cursor.execute(sql)
        data = cursor.fetchone()
        if data is None:
            error = 'Invalid username'
        elif not check_password(password, data[1]):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['user_id'] = data[0]
            return redirect(url_for('all_tweets'))
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    """
    This method handles Logout View.
    :return: Redirect to Login View.
    """
    if request.method == 'GET':
        session['logged_in'] = False
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This method handles Register View.
    :return: Redirect to all_tweets view when registration successful or back to Register View if not.
    """
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        
        cnx = connect_db()  
        cursor = cnx.cursor()
        sql = "SELECT user_id,hashed_password FROM Users WHERE email='{}'".format(email)
        result = cursor.execute(sql)
        data = cursor.fetchone()
        if data is None:
            if request.form['password1'] == request.form['password2']:
                password = request.form['password1']
                
                user = User()
                user.username = username
                user.email = email
                user.set_password(password, None)
                
                user.save_to_db(cursor)
                cnx.commit()
                
                session['logged_in'] = True
                session['user_id'] = cursor.lastrowid
                return redirect(url_for('all_tweets'))
            else:
                error = 'Different Passwords'
        else:
            error = 'User with this email already exist'
            
    return render_template('register.html', error=error)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    """
    This method handles User Edition View.
    :return: Redirect to all_tweets view when edition successful or back to Edit View if not.
    """

    if not session['logged_in']:
        return redirect(url_for('login'))

    cnx = connect_db()
    user = User.load_user_by_id(cnx.cursor(), session['user_id'])
    email = user.email
    error = None
    if request.method == 'POST':
        username = request.form['username']

        if request.form['password1'] == request.form['password2']:
            password = request.form['password1']

            user.username = username
            user.set_password(password, None)
            user.save_to_db(cnx.cursor())
            cnx.commit()
            return redirect(url_for('all_tweets'))
        else:
            error = 'Different Passwords'

    return render_template('edit.html', error=error, email=email)


@app.route("/all_tweets", methods=['GET', 'POST'])
def all_tweets():
    """
    This method handles All Tweets View.
    :return: If "GET" rendering template "all_tweets",
            If "POST" adding new Tweet to db and redirecting back to all_tweets.
    """

    if not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == "GET":
        cnx = connect_db()
        tweets = Tweet.load_all_tweets(cnx.cursor())
        return render_template('all_tweets.html', tweets=tweets)

    elif request.method == "POST":
        tweet = Tweet()
        tweet.user_id = session['user_id']
        tweet.text = request.form['new_tweet']
        tweet.creation_date = datetime.now()

        cnx = connect_db()
        tweet.add_tweet(cnx.cursor())
        cnx.commit()

        return redirect(url_for('all_tweets'))


@app.route("/tweets_by_user_id/<user_id>", methods=['GET', 'POST'])
def tweets_by_user_id(user_id):
    """
    This method handles Tweets by User View.
    :param user_id:  Id of User for which we want to display Tweets.
    :return: If "GET", rendering template "tweet_by_user_id.html"
    """

    if not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == "GET":
        cnx = connect_db()
        tweets = Tweet.load_tweets_by_user_id(cnx.cursor(), user_id)
        user = User.load_user_by_id(cnx.cursor(), user_id)
        return render_template('tweet_by_user_id.html', tweets=tweets, user=user)


@app.route("/tweet_by_id/<tweet_id>", methods=['GET', 'POST'])
def tweet_by_id(tweet_id):
    """
    This method handles Tweet by its Id View.
    :param tweet_id: Id of Tweet for which we want to display Comments.
    :return: If "GET" rendering template "tweet_by_id" and displays all comments for that Tweet,
            If "POST" adds new Comment to db and redirecting back to tweet_by_id.
    """
    if not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == "GET":
        cnx = connect_db()
        tweet = Tweet.load_tweet_by_id(cnx.cursor(), tweet_id)
        user = User.load_user_by_id(cnx.cursor(), tweet.user_id)
        comments = Comment.load_comments_by_tweet_id(cnx.cursor(), tweet_id)
        return render_template('tweet_by_id.html', tweet=tweet, user=user, comments=comments)

    elif request.method == "POST":
            comment = Comment()
            comment.user_id = session['user_id']
            comment.tweet_id = tweet_id
            comment.text = request.form['new_comment']
            comment.creation_date = datetime.now()

            cnx = connect_db()
            comment.add_comment(cnx.cursor())
            cnx.commit()
            return redirect(('tweet_by_id/{}'.format(tweet_id)))


@app.route("/messages", methods=['GET', 'POST'])
def messages():
    """
    This method handles Messages View.
    :return: If "GET" rendering template "messages.html" and displays all Messages received and send by logged user,
    """
    if not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == "GET":
        cnx = connect_db()
        received = Message.load_messages_by_recipient_id(cnx.cursor(), session['user_id'])
        sent = Message.load_messages_by_sender_id(cnx.cursor(), session['user_id'])
        return render_template('messages.html', received=received, sent=sent)


@app.route("/message_by_id/<message_id>", methods=['GET', 'POST'])
def message_by_id(message_id):
    """
    This method handles Message by its Id View.
    :param message_id: Id of Message for which we want to display information.
    :return: If "GET" rendering template "message_by_id" and displays all information for that message,
    """
    if not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == "GET":
        cnx = connect_db()
        cursor = cnx.cursor()
        message = Message.load_message_by_id(cnx.cursor(), message_id)
        sql = "UPDATE Messages SET status= 1 WHERE id={};".format(message_id)
        print(sql)
        cursor.execute(sql)
        cnx.commit()
        return render_template('message_by_id.html', message=message)


@app.route("/new_message", methods=['GET', 'POST'])
def new_message():
    """
    This method handles New Message View.
    :return: If "GET" rendering template "new_message" with form for new message,
            If "POST" adds New Message to db and redirecting back to messages.
    """
    if not session['logged_in']:
        return redirect(url_for('login'))

    error = None
    mail = request.args.get('recipient_email')
    if request.method == "POST":
        mail = request.form['recipient_email']
        cnx = connect_db()
        cursor = cnx.cursor()
        sql = "SELECT user_id FROM Users WHERE email='{}';".format(mail)
        cursor.execute(sql)
        recipient_id = cursor.fetchone()

        if recipient_id is None:
            error = 'Specified recipient does not exist...'
        elif recipient_id[0] == session['user_id']:
            error = 'You cannot send message to Yourself...'
        else:
            message = Message()
            message.sender_id = session['user_id']
            message.recipient_id = recipient_id[0]
            message.title = request.form['title']
            message.text = request.form['new_message']
            message.status = 0
            message.creation_date = datetime.now()

            message.send_message(cnx.cursor())
            cnx.commit()
            return redirect('messages')
    return render_template('new_message.html', error=error, mail=mail)

        
# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


if __name__ == "__main__":
    app.run()
