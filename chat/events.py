import jdatetime
from .serializers import SerChatList, SerRoomMemberList
from .models import Member, Chat, Room
from backend.socketio_instance import sio
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token

user_sid_mapping = {}

def get_online_users():
    return list(user_sid_mapping.keys())


@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')
    query_string = environ.get('QUERY_STRING', '')
    query_params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
    auth_token = query_params.get('token', '')
    print(f'Auth token: {auth_token}')
    if not auth_token:
        return False
    user = await db_get_user(auth_token)
    if not user:
        return False
    await sio.save_session(sid, {'user_id': user.id})
    user_sid_mapping[user.id] = sid
    rooms = await db_get_user_rooms(user.id)
    for room_id in rooms:
        await sio.enter_room(sid, f'room_{room_id}')
    return True


@sio.event
async def message(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    chat = await db_save_message(user_id, data.get('id', 0), room_id, data.get('body'), data.get('file'), data.get('file_name'), data.get('parent'))
    if chat:
        await sio.emit('message', chat, room=f'room_{room_id}')


@sio.event
async def delete(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = await db_delete_message(data.get('id'), user_id)
    if room_id:
        await sio.emit('delete', {'id': data.get('id'), 'room': room_id}, room=f'room_{room_id}')


@sio.event
async def forward(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    for room_id in data.get('rooms', []):
        chat = await db_forward_message(data.get('id'), user_id, room_id)
        if chat:
            await sio.emit('message', chat, room=f'room_{room_id}')


@sio.event
async def enter_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    enter_time = await db_enter_room(user_id, room_id)
    await sio.emit('enter_room', {'user': user_id, 'room': room_id, 'time': enter_time}, room=f'room_{room_id}')


@sio.event
async def add_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = await db_add_room(user_id, data.get('type'), data.get('title'), data.get('logo'), data.get('bio'), data.get('user'), data.get('users'))
    await sio.enter_room(sid, f'room_{room_id}')
    if data.get('type') == 'chat':
        for _user, _sid in user_sid_mapping.items():
            if _user == data.get('user'):
                await sio.enter_room(_sid, f'room_{room_id}')
                break
    else:
        users = data.get('users', [])
        for _user, _sid in user_sid_mapping.items():
            if _user in users:
                await sio.enter_room(_sid, f'room_{room_id}')
    await sio.emit('join_room', {'room': room_id}, room=f'room_{room_id}')


@sio.event
async def update_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    result = await db_update_room(room_id, user_id, data.get('title'), data.get('bio'), data.get('logo'))
    await sio.emit('update_room', result, room=f'room_{room_id}')


@sio.event
async def update_member(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    member_id = data.get('member')
    result = await db_update_member(member_id, user_id, data.get('is_pinned'), data.get('is_mute'))
    await sio.emit('update_member', result, room=sid)


@sio.event
async def join_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    result = await db_join_room(user_id, room_id, data.get('user'))
    # اطلاع به مالک
    await sio.emit('add_member', {'room': room_id, 'member': result}, sid)
    # اطلاع به عضو جدید
    for _user, _sid in user_sid_mapping.items():
        if _user == result['user']:
            await sio.emit('join_room', {'room': room_id}, _sid)
            break


@sio.event
async def remove_member(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    removing_user_id = data.get('user')
    if await db_remove_member(user_id, room_id, removing_user_id):
        # اطلاع به مالک
        await sio.emit('remove_member', {'room': room_id, 'user': removing_user_id}, sid)
        # اطلاع به عضو حذف شده
        for _user, _sid in user_sid_mapping.items():
            if _user == removing_user_id:
                await sio.emit('leave_room', {'room': room_id}, _sid)
                break


@sio.event
async def leave_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    if await db_leave_room(user_id, room_id):
        await sio.emit('leave_room', {'room': room_id}, sid)


@sio.event
async def toggle_is_manager(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    member_user_id = data.get('member')
    result = await db_toggle_is_manager(user_id, room_id, member_user_id)
    if result:
        # اطلاع به مالک
        await sio.emit('toggle_is_manager', {'room': room_id, 'user': member_user_id, 'is_manager': result['is_manager']}, sid)
        # اطلاع به عضو حذف شده
        for _user, _sid in user_sid_mapping.items():
            if _user == member_user_id:
                await sio.emit('update_member', result, _sid)
                break


@sio.event
async def disconnect(sid):
    user_id = None
    for _user, _sid in user_sid_mapping.items():
        if sid == _sid:
            user_id = _user
            break
    if user_id:
        del user_sid_mapping[user_id]
    print(f'Client disconnected: {sid}')


# Database Methods:

@database_sync_to_async
def db_get_user(token):
    try:
        token = Token.objects.get(key=token)
        return token.user
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def db_save_message(user_id, chat_id, room_id, body, file, file_name, parent):
    try:
        member = Member.objects.get(user_id=user_id, room_id=room_id)
        if member.room.type == 'channel' and member.is_manager is False:
            return None
        if chat_id:
            chat = Chat.objects.get(id=chat_id, user_id=user_id)
            chat.body = body
            chat.save()
        else:
            chat = Chat.objects.create(user_id=user_id, room_id=room_id, body=body, parent_id=parent)
        if file:
            chat.file.save(file_name, ContentFile(file), save=True)
        member.my_last_seen_time = jdatetime.datetime.now()
        member.save()
        return SerChatList(chat).data
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_forward_message(chat_id, user_id, room_id):
    try:
        chat = Chat.objects.get(id=chat_id)
        chat2 = Chat.objects.create(room_id=room_id, user_id=user_id, ff_id=chat.user_id, body=chat.body, file=chat.file)
        return SerChatList(chat2).data
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_delete_message(pk, user_id):
    try:
        chat = Chat.objects.get(id=pk, user_id=user_id)
        room = chat.room_id
        chat.delete()
        return room
    except Chat.DoesNotExist:
        return False


@database_sync_to_async
def db_get_user_rooms(user_id):
    return list(Member.objects.filter(user_id=user_id).values_list('room_id', flat=True))


@database_sync_to_async
def db_enter_room(user_id, room_id):
    try:
        member = Member.objects.get(user_id=user_id, room_id=room_id)
        member.my_last_seen_time = jdatetime.datetime.now()
        member.save()
        return str(member.my_last_seen_time)
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_add_room(user_id, _type, title, logo, bio, user, users):
    try:
        if _type == 'chat':
            room = Room.objects.filter(type='chat', members__user_id=user_id).filter(members__user_id=user).first()
            if not room:
                room = Room.objects.create(type=_type)
                room.members.create(user_id=user_id, is_manager=True, is_owner=True)
                room.members.create(user_id=user, is_manager=True)
            return room.id
        room = Room.objects.create(type=_type, title=title, bio=bio)
        if logo:
            file_name = getattr(logo, 'name', 'file')
            if '.' not in file_name:
                file_name += '.png'
            room.logo.save(file_name, ContentFile(logo), save=True)
        room.members.create(user_id=user_id, is_owner=True, is_manager=True)
        for u in users:
            room.members.create(user_id=u)
        return str(room.id)
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_update_room(room, user_id, title, bio, logo):
    try:
        room = Room.objects.get(id=room, type__in=['channel', 'group'])
        if not room.members.filter(user_id=user_id, is_owner=True).exists():
            return False
        room.title = title
        room.bio = bio
        room.save()
        if logo:
            room.logo.save(f'logo{room.id}.png', ContentFile(logo), save=True)
        return {'room': room.id, 'title': room.title, 'bio': room.bio, 'logo': room.logo_url}
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_update_member(member, user_id, is_pinned, is_mute):
    try:
        member = Member.objects.get(id=member, user_id=user_id)
        member.is_pinned = is_pinned
        member.is_mute = is_mute
        member.save()
        return {'room': member.room_id, 'member': member.id, 'is_pinned': member.is_pinned, 'is_mute': member.is_mute, 'is_manager': member.is_manager}
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_join_room(user_id, room, new_user_id):
    try:
        member = Member.objects.get(room_id=room, user_id=user_id, is_owner=True)
        new_member = member.room.members.create(user_id=new_user_id)
        return SerRoomMemberList(new_member).data
    except Member.DoesNotExist:
        return None


@database_sync_to_async
def db_remove_member(user_id, room_id, member_id):
    if Member.objects.filter(room_id=room_id, user_id=user_id, is_owner=True).exists():
        Member.objects.get(room_id=room_id, user_id=member_id).delete()
        return True
    return False


@database_sync_to_async
def db_leave_room(user_id, room_id):
    Member.objects.get(room_id=room_id, user_id=user_id).delete()
    return True


@database_sync_to_async
def db_toggle_is_manager(user_id, room_id, member_user_id):
    if Member.objects.filter(room_id=room_id, user_id=user_id, is_owner=True).exists():
        member = Member.objects.get(user_id=member_user_id, room_id=room_id)
        member.is_manager = not member.is_manager
        member.save()
        return {'room': member.room_id, 'member': member.id, 'is_pinned': member.is_pinned, 'is_mute': member.is_mute, 'is_manager': member.is_manager}
    return None
