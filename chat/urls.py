from django.urls import path
from chat.views import *

urlpatterns = [
    path('member-list/', MemberList.as_view()),
    path('member-list-item/<int:room>/', MemberListItem.as_view()),
    path('room-chat-list/<int:pk>/', RoomChatList.as_view()),
    path('toggle-room-pin/', ToggleRoomPin.as_view()),
    path('member-detail/<int:pk>/', MemberDetail.as_view()),
]
