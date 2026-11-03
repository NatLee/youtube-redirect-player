"""The websocket side: what one player sends reaches every player."""

import main


def connect(client):
    return main.socket_.test_client(main.app, namespace=main.NAMESPACE, flask_test_client=client)


def responses(socket_client):
    return [event['args'][0] for event in socket_client.get_received(main.NAMESPACE)
            if event['name'] == 'my_response']


def test_player_control_reaches_every_player_with_a_count(client):
    alice, bob = connect(client), connect(main.app.test_client())

    alice.emit('player_control', {'data': 'pause'}, namespace=main.NAMESPACE)
    alice.emit('player_control', {'data': 'play'}, namespace=main.NAMESPACE)

    assert responses(bob) == [{'data': 'pause', 'count': 1}, {'data': 'play', 'count': 2}]
    assert [msg['data'] for msg in responses(alice)] == ['pause', 'play']


def test_a_new_request_carries_the_video_to_other_players(client):
    alice, bob = connect(client), connect(main.app.test_client())
    video = {'title': 'Demo', 'url': 'https://www.youtube.com/watch?v=a', 'is_request': True, 'user': 'alice'}

    alice.emit('player_control', {'data': 'new_request', 'src': video}, namespace=main.NAMESPACE)

    assert responses(bob) == [{'data': 'new_request', 'src': video, 'count': 1}]


def test_the_pause_route_pauses_every_player(client):
    alice, bob = connect(client), connect(main.app.test_client())

    response = client.get('/pause')

    assert response.get_data(as_text=True) == 'yee'
    assert responses(alice) == [{'data': 'pause'}]
    assert responses(bob) == [{'data': 'pause'}]


def test_disconnect_request_says_goodbye_and_disconnects(client):
    alice = connect(client)
    alice.emit('player_control', {'data': 'hello'}, namespace=main.NAMESPACE)
    alice.get_received(main.NAMESPACE)

    alice.emit('disconnect_request', namespace=main.NAMESPACE)

    assert responses(alice) == [{'data': 'Disconnected!', 'count': 0}]
