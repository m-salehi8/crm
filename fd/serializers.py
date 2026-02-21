from .models import *
from rest_framework import serializers


class SerFoodList(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ['id', 'name', 'count']


class SerNutritionFood(serializers.ModelSerializer):
    food_name = serializers.CharField(read_only=True, source='food.name')

    class Meta:
        model = NutritionFood
        fields = ['id', 'nutrition', 'food', 'food_name', 'price']


class SerNutrition(serializers.ModelSerializer):
    nfs = SerNutritionFood(read_only=True, many=True)

    class Meta:
        model = Nutrition
        fields = ['id', 'day_of_week', 'date', 'nfs']


class SerReservePlus(serializers.ModelSerializer):
    class Meta:
        model = ReservePlus
        fields = '__all__'


class SerReserve(serializers.ModelSerializer):
    pluses = SerReservePlus(read_only=True, many=True)

    class Meta:
        model = Reserve
        fields = ['id', 'user', 'post', 'nutrition', 'nf', 'rate', 'note', 'pluses']


class SerReserveList(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    department = serializers.CharField(read_only=True, source='post.department.id')
    department_title = serializers.CharField(read_only=True, source='post.department.title')
    position = serializers.CharField(read_only=True, source='user.post.position')
    pluses = SerReservePlus(read_only=True, many=True)

    class Meta:
        model = Reserve
        fields = ['id', 'user', 'name', 'department', 'department_title', 'nf', 'pluses', 'position']


class SerFoodUserList(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='get_full_name')
    post_title = serializers.CharField(read_only=True, source='post.title')
    level = serializers.CharField(read_only=True, source='post.level')
    department = serializers.IntegerField(read_only=True, source='post.department.id')
    department_title = serializers.CharField(read_only=True, source='post.department.title')
    has_sf_food = serializers.BooleanField(read_only=True, source='profile.has_sf_food')

    class Meta:
        model = User
        fields = ['id', 'name', 'post_title', 'level', 'department', 'department_title', 'has_sf_food']
