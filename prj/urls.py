from django.urls import path
from .views import *

urlpatterns = [
    path('mission-list/', MissionList.as_view()),
    path('project-list/', ProjectList.as_view()),
    path('project-detail/<int:pk>/', ProjectDetail.as_view()),
    path('project-add-or-update/', ProjectAddOrUpdate.as_view()),
    path('project-remove/<int:pk>/', ProjectRemove.as_view()),
    path('phase-add-or-update/', PhaseAddOrUpdate.as_view()),
    path('phase-remove/', PhaseRemove.as_view()),
    path('phase-report-list/<int:pk>/', PhaseReportList.as_view()),
    path('project-confirm-or-accept/', ProjectConfirmOrAccept.as_view()),
    path('project-approve/', ProjectApprove.as_view()),
    path('project-detail/<int:project_id>/outcomes/',ProjectOutcomeListCreateAPIView.as_view()),
    path('project-detail/<int:project_id>/outcomes/<int:pk>/',ProjectOutcomeRetrieveUpdateDestroyAPIView.as_view()),

    path('report-list/', ReportList.as_view()),
    path('report-add/', ReportAdd.as_view()),
    path('report-remove/', ReportRemove.as_view()),
    path('report-accept/', ReportAccept.as_view()),
    path('report-approve/', ReportApprove.as_view()),

    path('project-allocations/<int:pk>/', ProjectAllocations.as_view()),
    path('allocation-list/', AllocationList.as_view()),
    path('allocate-project-list-in-department/<int:pk>/', AllocationProjectListInDepartment.as_view()),
    path('add-or-update-allocation/', AddOrUpdateAllocation.as_view()),
    path('remove-allocation/', RemoveAllocation.as_view()),

    path('my-active-project-list/', MyActiveProjectList.as_view()),
    path('all-active-project-list/', AllActiveProjectList.as_view()),
    path('active-project-list-in-units/', ActiveProjectListInUnits.as_view()),
    path('my-teammates/', MyTeammates.as_view()),
]
