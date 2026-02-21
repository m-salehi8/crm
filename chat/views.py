import jdatetime
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404, RetrieveAPIView
from chat.models import Room, Member
from chat.serializers import SerMemberList, SerChatList, SerMemberDetail


class MemberList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SerMemberList

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def get_queryset(self):
        return Member.objects.filter(user=self.request.user)


class MemberListItem(GenericAPIView):
    def get(self, request, room):
        member = get_object_or_404(Member, room_id=room, user=request.user)
        return Response(SerMemberList(member, context={'user': request.user}).data)


class RoomChatList(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        member = get_object_or_404(Member, user=request.user, pk=pk)
        member.my_last_seen_time = jdatetime.datetime.now()
        member.save()
        data = {
            'old': SerChatList(member.room.chats.select_related('room', 'user', 'ff', 'parent').filter(create_time__lte=member.my_last_seen_time).order_by('-id')[::-1], many=True).data,
            'new': SerChatList(member.room.chats.select_related('room', 'user', 'ff', 'parent').filter(create_time__gt=member.my_last_seen_time).order_by('id'), many=True).data,
        }
        return Response(data=data)


class ToggleRoomPin(GenericAPIView):
    def post(self, request):
        member = get_object_or_404(Member, user=request.user, room_id=request.data['room'])
        member.is_pinned = not member.is_pinned
        member.save()
        return Response(data=member.is_pinned)


class MemberDetail(RetrieveAPIView):
    serializer_class = SerMemberDetail

    def get_queryset(self):
        return Member.objects.filter(user=self.request.user)
