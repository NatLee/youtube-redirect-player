
from flask import Flask, render_template, session, copy_current_request_context

from flask_socketio import SocketIO, emit, disconnect

from playlist import playlist


app = Flask(__name__)

# blueprint for playlist
app.register_blueprint(playlist, url_prefix='/playlist')

# secret key
app.config['SECRET_KEY'] = 'yee'

# websocket
socket_ = SocketIO(app, async_mode=None)

@app.route('/')
def index():
    """
    API panel for testing
    """
    return render_template('index.html')

@socket_.on('player_control', namespace='/test')
def player_control(data):
    """
    播放器控制
    用來統計session數量及廣播至所有seesion
    """
    session['receive_count'] = session.get('receive_count', 0) + 1

    data['count'] = session['receive_count']

    emit('my_response', data, broadcast=True)

@socket_.on('disconnect_request', namespace='/test')
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
    Websocket暫停所有播放器播放
    """

    socket_.emit(
        'my_response',
        {
            'data': 'pause'
        },
        namespace='/test'
    )
    return 'yee'


if __name__ == '__main__':

    socket_.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )
