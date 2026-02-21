import socketio

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://192.168.19.161:3000', 'http://it.local', 'http://www.it.local', 'http://new.it.local'],
    logger=True,
    engineio_logger=True,
    max_http_buffer_size=1e8,
    allow_upgrades=True,
)
