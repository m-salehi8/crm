from django.urls import path
from .views import *
from django.urls import path
from .views import *

urlpatterns = [
    path('agreement-list/', AgreementList.as_view()),
    path('contract-list/', ContractList.as_view()),
    path('new-contract-project-list/', NewContractProjectList.as_view()),
    path('contract-detail/<int:no>/', ContractDetail.as_view()),
    path('add-contract/', AddContract.as_view()),
    path('update-contract/', UpdateContract.as_view()),
    path('update-contract-appendices/', UpdateContractAppendices.as_view()),
    path('add-or-update-party/', AddOrUpdateParty.as_view()),

    path('remove-party/', RemoveParty.as_view()),
    path('save-contract-steps/', SaveContractSteps.as_view()),
    path('save-contract-supplements/', SaveContractSupplements.as_view()),
    path('contract-task-list/<int:no>/', ContractTaskList.as_view()),

    path('do-contract-action/', DoContractAction.as_view()),
    path('remove-contract/<int:pk>/', RemoveContract.as_view()),

    path('add-or-edit-pay/', AddOrEditPay.as_view()),
    path('do-pay-action/', DoPayAction.as_view()),
    path('pay-list/', PayList.as_view()),
    path('pay-detail/<int:pk>/', PayDetail.as_view()),
    path('contract-list-in-department/<int:pk>/', ContractListInDepartment.as_view()),
    path('step-list-in-contract/<int:pk>/', StepListInContract.as_view()),
    path('pay-task-list/<int:pk>/', PayTaskList.as_view()),
    path('remove-pay/<int:pk>/', RemovePay.as_view()),
    path('toggle-inquiry-status/', ToggleInquiryStatus.as_view()),
    path('toggle-cn-note/', ToggleCnNote.as_view()),

    path('article-category-list/', ArticleCategoryList.as_view()),
    path('article-category-detail/<int:pk>/', ArticleCategoryDetail.as_view()),
    path('article-detail/<int:pk>/', ArticleDetail.as_view()),
    path('rate-article/', RateArticle.as_view()),
    path('article-attachment-download/<int:pk>/', ArticleAttachmentDownload.as_view()),
    path('article-permit-request/', ArticlePermitRequest.as_view()),
    path('article-chat-add/', ArticleChatAdd.as_view()),
    path('article-chat-like/', ArticleChatLike.as_view()),

    path('article-permit-request-list/<int:pk>/', ArticlePermRequestList.as_view()),
    path('article-permit-accept/', ArticlePermitAccept.as_view()),
    path('article-save/', ArticleSave.as_view()),
    path('articles/', ArticleListAPI.as_view()),

]
