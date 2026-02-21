from .views import *
from django.urls import path
# from .ai import TranscribeAudioView
from pm.tapi import TaskListV4


urlpatterns = [
    path('get-today/', get_today),

    # مدیریت وظایف
    path('my-fellow-list/', MyFellowList.as_view()),
    path('update-tag-list/', UpdateTagList.as_view()),
    path('job-tags/', GetOrUpdateUserTagList.as_view()),
    path('task-list/', TaskList.as_view()),
    path('task-list/v2/', TaskListV4.as_view()),
    path('update-tasks-status-and-order/', UpdateTasksStatusAndOrder.as_view()),
    path('task/<int:pk>/', TaskDetail.as_view()),
    path('remove-job/<int:pk>/', RemoveJob.as_view()),
    path('update-job/<int:pk>/', UpdateJob.as_view()),
    path('update-job-deadline-by-member/', UpdateJobDeadlineByMember.as_view()),
    path('job-media/', JobMedia.as_view()),
    path('add-job-appendix/', AddJobAppendix.as_view()),
    path('remove-job-appendix/<int:pk>/', RemoveJobAppendix.as_view()),
    path('job-chat-add/', JobChatAdd.as_view()),
    path('job-chat-remove/<int:pk>/', JobChatRemove.as_view()),
    path('change-task-tag/', ChangeTaskTag.as_view()),
    path('job-members-change/', JobMembersChange.as_view()),
    path('job-add/', JobAdd.as_view()),
    path('job-confirm-status/', JobConfirmStatus.as_view()),
    path('job-informees/', JobInformees.as_view()),

    # جلسات
    path('my-session-member-list/', MySessionMemberList.as_view()),
    path('session-list-in-month/', SessionListInMonth.as_view()),
    path('session-list/', SessionList.as_view()),
    path('session-detail/<int:pk>/', SessionDetail.as_view()),
    path('session-add-or-update/', SessionAddOrUpdate.as_view()),
    path('remove-session/<int:pk>/', RemoveSession.as_view()),
    path('session-catering-accept/', SessionCateringAccept.as_view()),
    path('servant-list/', ServantList.as_view()),
    path('order-session-catering/', OrderSessionCatering.as_view()),
    path('session/rate/', SessionAddOrUpdateRate.as_view()),

    path('approval-list/', ApprovalList.as_view()),
    path('my-room-list/', MyRoomList.as_view()),
    path('overlap-check/', OverlapCheck.as_view()),

    path('public-room-request-list/', PublicRoomRequestList.as_view()),
    path('public-room-request-accept/', PublicRoomRequestAccept.as_view()),

    # فرآیند
    path('node-list/', NodeList.as_view()),
    path('node-list-excel/', NodeListExcel.as_view()),
    path('my-flow-pattern-list/', MyFlowPatterList.as_view()),
    path('my-flow-pattern-list/v2/', FlowCategoryAPI.as_view()),
    path('all-flow-pattern-list/', AllFlowPatterList.as_view()),
    path('node/<int:pk>/', NodeDetail.as_view()),
    path('get-node-pdf/<int:pk>/', GetNodePdf.as_view()),
    path('node-save/', NodeSave.as_view()),
    path('node-remove/', NodeRemove.as_view()),
    path('node-revert/', NodeRevert.as_view()),
    path('start-new-flow/<int:pk>/', StartNewFlow.as_view()),
    path('flow-history/<int:pk>/', FlowHistory.as_view()),

    # فرآیندساز
    path('flow-pattern-add/', FlowPatternAdd.as_view()),
    path('flow-pattern-remove/<int:pk>/', FlowPatternRemove.as_view()),
    path('flow-pattern-list/', FlowPatternList.as_view()),
    path('flow-pattern-detail/<int:pk>/', FlowPatternDetail.as_view()),
    path('flow-pattern-fields/<int:pk>/', FlowPatternFields.as_view()),
    path('flow-pattern-nodes/<int:pk>/', FlowPatternNodes.as_view()),
    path('save-flow-pattern-detail/', SaveFlowPatternDetail.as_view()),
    path('save-flow-pattern-fields/', SaveFlowPatternFields.as_view()),
    path('save-flow-pattern-nodes/', SaveFlowPatternNodes.as_view()),
    path('post-list-for-flow-pattern-management/', PostListForFlowPatternManagement.as_view()),

    # ai
    # path('transcribe-audio/', TranscribeAudioView.as_view()),
]
