from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token
from .dashboard_views import *
from .my_desk import *
from core.login_view import LoginAPIView, LogoutAPIView


urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('dashboard/', DashboardAPI.as_view()),
    path('dashboard/proclamation/', DashboardSliderAPIView.as_view()),

    path('dashboard/charts/procurement/', procurement_process_stats),
    path('dashboard/charts/petty-cash/', petty_cash_stats),
    path('dashboard/charts/hr/', human_resources_stats),
    path('dashboard/charts/program/', program_dashboard_card),
    path('dashboard/charts/contracts/', contract_stats),
    path('dashboard/charts/sessions/', meetings_stats),
    path('dashboard/charts/tasks/', tasks_stats),
    path('dashboard/charts/salary/', payroll_efficiency_stats),


    path('dashboard/cards/tasks/', mydesk_task_stats),
    path('dashboard/cards/login-activity/', LoginActivityCardView.as_view()),
    path('dashboard/cards/approvals/', ApprovalsCardView.as_view()),
    path('dashboard/cards/process/', ProcessCardView.as_view()),
    path('dashboard/cards/messages/', MessagesCardView.as_view()),
    path('dashboard/cards/sessions/', UpcomingSessionsCardView.as_view()),

    path('get-user/', GetUser.as_view()),
    path('change-password/', ChangePassword.as_view()),
    path('reset-password/', ResetPassword.as_view()),
    path('department-list/', DepartmentList.as_view()),
    path('user-photo-update/', UserPhotoUpdate.as_view()),
    path('proclamation-list/', ProclamationList.as_view()),
    path('proclamation-detail/<int:pk>/', ProclamationDetail.as_view()),

    path('proclamation-type-list/', ProclamationTypeList.as_view()),
    path('proclamation-manage-list/', ProclamationManageList.as_view()),
    path('proclamation-add-or-update/', ProclamationAddOrUpdate.as_view()),
    path('proclamation-remove/<int:pk>/', ProclamationRemove.as_view()),

    path('tell-list/', TellList.as_view()),
    path('my-colleague-list/', MyColleagueList.as_view()),
    path('all-user-list/', AllUserList.as_view()),
    path('my-related-user-list/', MyRelatedUserList.as_view()),

    path('tree-chart/<int:unit>/', TreeChart.as_view()),
    path('all-unit-list/', AllUnitList.as_view()),
    path('set-page-size/', SetPageSize.as_view()),

    path('set-notification-seen/', SetNotificationSeen.as_view()),
    path('remove-all-notifications/', RemoveAllNotifications.as_view()),
    path('my-notification-list/', MyNotificationList.as_view()),

    path('theme-list/', ThemeList.as_view()),
    path('login-bg/', LoginThemeApi.as_view()),
    path('set-theme/', SetTheme.as_view()),
    path('set-menu-order/', SetMenuOrder.as_view()),
    path('unseen-count/', SeenCountAPIView.as_view()),
    path('available_dashboards/', available_dashboards, name='available_dashboards'),

    path('available_cards/', AvailableDashboardsView.as_view(), name='available_cards'),
    path('sms/verify/', SmsVerifyWebhookApi.as_view(), )
]



