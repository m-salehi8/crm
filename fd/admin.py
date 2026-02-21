import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline
from .models import Food, Nutrition, Reserve, admin, NutritionFood, ReservePlus, Warehouse, Inventory


@admin.register(Food)
class AdminFood(ModelAdmin):
    list_display = ['name', 'count']
    search_fields = ['name']


@admin.register(NutritionFood)
class NutritionFoodAdmin(ModelAdmin):
    list_display = ['nutrition', 'food', 'price']
    search_fields = ['food__name']


class NutritionFoodInline(TabularInline):
    model = NutritionFood
    extra = 0


@admin.register(Nutrition)
class AdminNutrition(ModelAdmin):
    list_display = ['date', 'day_of_week']
    inlines = [NutritionFoodInline]


class AdminReservePlusInline(TabularInline):
    model = ReservePlus
    extra = 0


@admin.register(Reserve)
class AdminReserve(ModelAdmin):
    list_display = ['user', 'nutrition', 'nf']
    list_filter = ['user__post__unit']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    autocomplete_fields = ['user', 'nf', 'post']
    inlines = [AdminReservePlusInline]


class AdminInventoryInline(TabularInline):
    model = Inventory
    extra = 0
    raw_id_fields = ['user']


@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ['title', 'type', 'scale', 'count', 'place']
    list_filter = ['type', 'place', 'scale']
    search_fields = ['title']
    readonly_fields = ['count']
    inlines = [AdminInventoryInline]

