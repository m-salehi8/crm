from django.urls import path
from .views import *
from .cover import CvAPI


urlpatterns = [
    path('invoice-cover-list/', InvoiceCoverList.as_view()),
    path('invoice-category-list/', InvoiceCategoryList.as_view()),
    path('invoice-cover-detail/<int:pk>/', InvoiceCoverDetail.as_view()),
    path('get-cover-pdf/<int:pk>/', GetInvoiceCoverPdf.as_view()),
    path('get-cover-excel/<int:pk>/', GetInvoiceCoverExcel.as_view()),
    path('add-or-update-invoice/', AddOrUpdateInvoice.as_view()),
    path('remove-invoice/<int:pk>/', RemoveInvoice.as_view()),
    path('lock-cover/', LockCover.as_view()),
    path('toggle-cover-accepted/', ToggleCoverAccepted.as_view()),
    path('remove-cover/<int:pk>/', RemoveCover.as_view()),
    path('invoice-cover-user-list/', InvoiceCoverUserList.as_view()),
    path('add-or-update-invoice-cover/', AddOrUpdateInvoiceCover.as_view()),
    path('deposit-direct-invoice-cover/', DepositDirectInvoiceCover.as_view()),
    path('invoice-cover-task-list/<int:pk>/', InvoiceCoverTaskList.as_view()),

    path('', CvAPI.as_view()),
]
