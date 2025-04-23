from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import threading
import time
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')

# Global variables
cl = None
bot_thread = None
stop_event = threading.Event()

@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    global cl
    username = request.form['username']
    password = request.form['password']
    cl = Client()
    try:
        cl.login(username, password)
        return redirect(url_for('main_page'))
    except ChallengeRequired:
        return render_template('verify.html')
    except Exception as e:
        return f"Login failed: {str(e)}"

@app.route('/verify')
def verify_page():
    return render_template('verify.html')

@app.route('/continue_login', methods=['POST'])
def continue_login():
    global cl
    username = request.form['username']
    password = request.form['password']
    try:
        cl.login(username, password)
        return redirect(url_for('main_page'))
    except Exception as e:
        return f"Login failed: {str(e)}"

@app.route('/main')
def main_page():
    return render_template('main.html')

@app.route('/start_bot', methods=['POST'])
def start_bot():
    global bot_thread, stop_event
    if bot_thread is not None and bot_thread.is_alive():
        return 'Bot is already running'
    stop_event.clear()
    target_username = request.form['target_username']
    extract_type = request.form['extract_type']
    message = request.form['message']
    num_accounts = int(request.form['num_accounts'])
    delay = int(request.form['delay'])
    bot_thread = threading.Thread(target=run_bot, args=(target_username, extract_type, message, num_accounts, delay))
    bot_thread.start()
    return 'Bot started'

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    global stop_event
    stop_event.set()
    return 'Stopping bot'

def run_bot(target_username, extract_type, message, num_accounts, delay):
    try:
        user_id = cl.user_id_from_username(target_username)
        socketio.emit('log', f"Extracting {extract_type} for {target_username}")
        if extract_type == 'followers':
            accounts = cl.user_followers(user_id, amount=num_accounts)
        else:
            accounts = cl.user_following(user_id, amount=num_accounts)
        socketio.emit('log', f"Extracted {len(accounts)} accounts")
        for i, account in enumerate(accounts):
            if stop_event.is_set():
                socketio.emit('log', "Bot stopped by user")
                break
            socketio.emit('log', f"Sending message to {account.username} ({i+1}/{len(accounts)})")
            cl.direct_send(message, [account.pk])
            socketio.emit('log', f"Message sent to {account.username}")
            if i < len(accounts) - 1:
                time.sleep(delay)
        socketio.emit('log', "Bot completed")
    except Exception as e:
        socketio.emit('log', f"Error: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
