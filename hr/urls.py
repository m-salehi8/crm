from .views import *
from django.urls import path
from .rahkaran import UpdateProfiles, UpdateWorks

urlpatterns = [
    path("salary/<int:user_id>/<int:year>/<int:month>/",WorkFullDetailAPI.as_view(), name="work-salary-detail"),
    path('upload-work-file/', SimpleExcelUpload.as_view()),

    path('work-unit-list/', WorkUnitList.as_view()),
    path('personnel-list/', PersonnelList.as_view()),
    path('blank-post-list/', BlankPostList.as_view()),
    path('update-personnel/<int:pk>/', UpdatePersonnel.as_view()),
    path('toggle-unit-overtime-bonus-open/', ToggleUnitOvertimeBonusOpenHasVisitant.as_view()),
    path('update-unit-overtime-bonus/<int:pk>/', UpdateUnitOvertimeBonus.as_view()),

    path('work-list/', WorkList.as_view()),
    path('save-talents/', SaveTalents.as_view()),
    path('save-work/', SaveWork.as_view()),

    path('update-profiles/', UpdateProfiles.as_view()),
    path('update-works/', UpdateWorks.as_view()),
    path('profile/<int:pk>/<int:year>/<int:month>/', ProfileDetail.as_view()),

    path('assessment-list/', AssessmentList.as_view()),
    path('assessment-detail/<int:pk>/', AssessmentDetail.as_view()),

    path('create-evaluation-for-current-month/', CreatEvaluationsForCurrentMonth.as_view()),
    path('evaluation-list/', EvaluationList.as_view()),
    path('save-evaluation-list/', SaveEvaluationList.as_view()),
]
