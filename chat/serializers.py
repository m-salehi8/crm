from rest_framework import serializers
from chat.models import Member, Chat, Room


class SerMemberList(serializers.ModelSerializer):
    room = serializers.SerializerMethodField()

    def get_room(self, member):
        return {
            'id': member.room_id,
            'title': member.room.members.exclude(user_id=self.context['user'].id).first().user.get_full_name() if member.room.type == 'chat' else member.room.title,
            'type': member.room.type,
            'logo': member.room.members.exclude(user_id=self.context['user'].id).first().user.photo_url if member.room.type == 'chat' else member.room.logo_url,
            'bio': member.room.bio
        }

    class Meta:
        model = Member
        fields = ['id', 'user', 'is_owner', 'is_manager', 'is_mute', 'is_pinned', 'unseen_count', 'others_last_seen_time', 'room', 'last_chat_time']


class SerChatList(serializers.ModelSerializer):
    user_name = serializers.CharField(read_only=True, source='user.get_full_name')
    ff_name = serializers.CharField(read_only=True, source='ff.get_full_name')
    user_photo = serializers.CharField(read_only=True, source='user.photo_url')
    parent = serializers.SerializerMethodField()
    send_time = serializers.SerializerMethodField()

    def get_parent(self, obj):
        if obj.parent:
            return {'id': obj.parent.id, 'user_name': obj.parent.user.get_full_name(), 'user_photo': obj.parent.user.photo_url, 'body': obj.parent.body, 'file_url': obj.parent.file_url}
        return None

    def get_send_time(self, obj):
        return str(obj.create_time)[:19]

    class Meta:
        model = Chat
        fields = ['id', 'room', 'user', 'user_name', 'ff_name', 'user_photo', 'body', 'file_url', 'send_time', 'updated', 'parent']


class SerRoomMemberList(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    post = serializers.CharField(read_only=True, source='user.post.title')
    photo_url = serializers.CharField(read_only=True, source='user.photo_url')

    class Meta:
        model = Member
        fields = ['id', 'user', 'post', 'photo_url', 'name', 'is_owner', 'is_manager']


class SerMemberDetail(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True, source='room.title')
    logo_url = serializers.CharField(read_only=True, source='room.logo_url')
    type = serializers.CharField(read_only=True, source='room.type')
    bio = serializers.CharField(read_only=True, source='room.bio')
    members = serializers.SerializerMethodField()

    def get_members(self, member):
        return SerRoomMemberList(member.room.members, many=True).data

    class Meta:
        model = Member
        fields = ['id', 'is_owner', 'is_manager', 'is_mute', 'is_pinned', 'room', 'title', 'logo_url', 'type', 'bio', 'members']
