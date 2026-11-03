"""YouTube Redirect Player: one shared playlist, played on every open screen.

The page plays the direct file links yt-dlp finds, and Socket.IO (a websocket
library) carries requests and play / pause / mute to every open player.
"""

import os
import secrets

from flask import Flask, copy_current_request_context, render_template, session
from flask_socketio import SocketIO, disconnect, emit

from playlist import playlist

# The Socket.IO namespace the player page joins.
NAMESPACE = '/test'

app = Flask(__name__)

# blueprint for playlist
app.register_blueprint(playlist, url_prefix='/playlist')

# Signs the session cookie. Without SECRET_KEY a fresh key is made at every start.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# websocket
socket_ = SocketIO(app, async_mode=None)


@app.route('/')
def index():
    """
    The player page (also the panel for trying the APIs).
    """
    return render_template('index.html', namespace=NAMESPACE)


@socket_.on('player_control', namespace=NAMESPACE)
def player_control(data):
    """
    播放器控制
    用來統計 session 數量及廣播至所有 session
    Relay a message to every player, with how many this connection has sent.
    """
    session['receive_count'] = session.get('receive_count', 0) + 1

    data['count'] = session['receive_count']

    emit('my_response', data, broadcast=True)


@socket_.on('disconnect_request', namespace=NAMESPACE)
def disconnect_request():
    """
    Session disconnect
    """

    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) - 1

    emit(
        'my_response', {
            'data': 'Disconnected!',
            'count': session['receive_count']
        },
        callback=can_disconnect
    )


@app.route('/pause')
def player_pause():
    """
    Websocket 暫停所有播放器播放
    Pause every open player.
    """

    socket_.emit(
        'my_response',
        {
            'data': 'pause'
        },
        namespace=NAMESPACE
    )
    return 'yee'


if __name__ == '__main__':
    # Development server with the same defaults as always (the Docker image runs
    # gunicorn instead). HOST and PORT override them, e.g. when 5000 is taken.
    socket_.run(
        app,
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', '5000')),
        debug=True,
    )
