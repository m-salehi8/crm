from django.urls import path
from .views import *

urlpatterns = [
    path('food-list/', FoodList.as_view()),
    path('add-or-update-food/', FoodCreateOrUpdate.as_view()),
    path('remove-food/', FoodRemove.as_view()),

    path('nutrition-list/', NutritionList.as_view()),
    path('nutrition-config/', NutritionConfig.as_view()),

    path('reserve-update/', ReserveUpdate.as_view()),
    path('reserve-list/', ReserveList.as_view()),
    path('reserve-add-or-update/', ReserveAddOrUpdate.as_view()),
    path('unreserved-users/<int:unit>/', UnreservedUsers.as_view()),

    path('food-user-list/', FoodUserList.as_view()),
    path('toggle-has-sf-food/', ToggleHasSfFood.as_view()),
    path('rate-food/', RateFood.as_view()),
]
