import jdatetime
from django.contrib.auth.models import Group

from hr.models import Profile
from .serializers import *
from django.db.models import Q
from rest_framework import status
from core.serializers import SerUserList
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404


class FoodList(GenericAPIView):
    """لیست غذاها"""
    def get(self, request):
        if request.user.groups.filter(name='food').exists():
            return Response(data=SerFoodList(Food.objects.all(), many=True).data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class FoodCreateOrUpdate(GenericAPIView):
    """ویرایش غذا یا ثبت غذای جدید"""
    def post(self, request):
        if request.user.groups.filter(name='food').exists():
            if request.data['id']:
                food = get_object_or_404(Food, id=request.data['id'])
                food.name = request.data['name']
                food.save()
            else:
                food = Food.objects.create(name=request.data['name'])
            return Response(data=SerFoodList(food).data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class FoodRemove(GenericAPIView):
    """حذف غذا"""
    def post(self, request):
        if request.user.groups.filter(name='food').exists():
            food = get_object_or_404(Food, id=request.data['id'])
            if food.count:
                return Response(data='قابل حذف نیست', status=status.HTTP_400_BAD_REQUEST)
            food.delete()
            return Response(data='done')
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


def get_food_permit_date():
    """برای این تاریخ و جلوتر می‌توان غذا رزرو کرد"""
    return jdatetime.datetime.now().date() + jdatetime.timedelta(days=2)


class NutritionList(GenericAPIView):
    """برنامه غذایی"""
    def get(self, request):
        today = jdatetime.datetime.now().date()
        year = int(request.GET.get('year', 0)) or today.year
        month = int(request.GET.get('month', 0)) or today.month
        current_month_start = jdatetime.date(year, month, 1)
        next_month_start = jdatetime.date(year + 1 if month == 12 else year, 1 if month == 12 else month + 1, 1)
        next_nutrition = Nutrition.objects.filter(date__gte=next_month_start).first()
        next_data = {'year': next_nutrition.date.year, 'month': next_nutrition.date.month, 'month_name': next_nutrition.date.j_months_fa[next_nutrition.date.month - 1]} if next_nutrition else {}
        previous_nutrition = Nutrition.objects.filter(date__lt=current_month_start).last()
        previous_data = {'year': previous_nutrition.date.year, 'month': previous_nutrition.date.month, 'month_name': previous_nutrition.date.j_months_fa[previous_nutrition.date.month - 1]} if previous_nutrition else {}
        current = {'year': current_month_start.year, 'month': current_month_start.month, 'month_name': current_month_start.j_months_fa[current_month_start.month - 1]}
        nutrition_list = SerNutrition(Nutrition.objects.filter(date__gte=current_month_start, date__lt=next_month_start), context={'user': request.user}, many=True).data
        reserve_list = SerReserve(request.user.reserve_set.filter(nutrition__date__gte=current_month_start, nutrition__date__lt=next_month_start), many=True).data
        for item in nutrition_list:
            tmp = list(filter(lambda r: r['nutrition'] == item['id'], reserve_list))
            if len(tmp):
                item['nf'] = tmp[0]['nf']
                item['rate'] = tmp[0]['rate']
                item['note'] = tmp[0]['note']
                for _item in item['nfs']:
                    _tmp = list(filter(lambda r: r['nf'] == _item['id'], tmp[0]['pluses']))
                    if len(_tmp):
                        _item['count'] = _tmp[0]['count']
                    else:
                        _item['count'] = 0
            else:
                item['nf'] = None
                for _item in item['nfs']:
                    _item['count'] = 0
        data = {
            'current': current,
            'next': next_data,
            'previous': previous_data,
            'permit_date': str(get_food_permit_date()),
            'cancel_permit_date': str(today + jdatetime.timedelta(days=2)),
            'list': nutrition_list,
        }
        return Response(data=data)


class NutritionConfig(GenericAPIView):
    def get(self, request):
        if not request.user.groups.filter(name='food').exists():
            return Response(data='شما دسترسی لازم ندارید')
        today = jdatetime.datetime.now().date()
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if year == 0:
            year = today.year
        if month == 0:
            month = today.month
        current_month_start = jdatetime.date(year, month, 1)
        next_month_start = jdatetime.date(year + 1 if month == 12 else year, 1 if month == 12 else month + 1, 1)
        nutrition_list = SerNutrition(Nutrition.objects.filter(date__gte=current_month_start, date__lt=next_month_start), many=True).data
        return Response(data={'year': year, 'month': month, 'list': nutrition_list})

    def post(self, request):
        if not request.user.groups.filter(name='food').exists():
            return Response(data='شما دسترسی لازم ندارید')
        nutrition, created = Nutrition.objects.get_or_create(date=request.data['date'])
        ids = list(map(lambda i: i['id'], request.data['nfs']))
        nutrition.nfs.exclude(id__in=ids).delete()
        for item in request.data['nfs']:
            if item['id']:
                nf = get_object_or_404(NutritionFood, id=item['id'])
                nf.food_id = item['food']
                nf.price = item['price']
                nf.save()
            else:
                NutritionFood.objects.create(nutrition=nutrition, food_id=item['food'], price=item['price'])
        return Response(data=SerNutrition(nutrition).data)


class ReserveUpdate(GenericAPIView):
    """رزرو غذا توسط همکار"""
    def post(self, request):
        today = jdatetime.datetime.now().date()
        permit_date = get_food_permit_date()
        cancel_permit_date = today + jdatetime.timedelta(days=2)
        for item in request.data:
            reserve, created = Reserve.objects.get_or_create(user=request.user, nutrition_id=item['id'])
            reserve.post = request.user.post
            reserve.subsidy = request.user.profile.has_sf_food
            if item['date'] >= str(permit_date):
                reserve.nf_id = item['nf']
                for nf in item['nfs']:
                    reserve_plus, created = reserve.pluses.get_or_create(nf_id=nf['id'])
                    reserve_plus.count = nf['count']
                    reserve_plus.save()
            elif item['date'] >= str(cancel_permit_date):
                if item['nf'] is None:
                    reserve.nf = None
                for nf in item['nfs']:
                    reserve_plus, created = reserve.pluses.get_or_create(nf_id=nf['id'])
                    if nf['count'] < reserve_plus.count:
                        reserve_plus.count = nf['count']
                        reserve_plus.save()
            reserve.save()
        return Response(data='done')


class ReserveList(GenericAPIView):
    def get(self, request):
        if not request.user.groups.filter(name='food').exists():
            return Response(data='denied', status=status.HTTP_403_FORBIDDEN)
        date = request.GET.get('date', None) or str(jdatetime.datetime.now().date())
        nutrition = get_object_or_404(Nutrition, date=date)
        data = {
            'date': date,
            'nfs': SerNutritionFood(nutrition.nfs.all(), many=True).data,
            'list': SerReserveList(nutrition.reserve_set.all(), many=True).data
        }
        return Response(data=data)


class ReserveAddOrUpdate(GenericAPIView):
    """تغییر رزرو غذا توسط ادمین"""
    def post(self, request):
        if not request.user.groups.filter(name='food').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        if request.data['id']:
            reserve = get_object_or_404(Reserve, pk=request.data['id'])
        else:
            user = get_object_or_404(User, pk=request.data['user'], post__isnull=False)
            nutrition = get_object_or_404(Nutrition, date=request.data['date'])
            reserve = Reserve.objects.create(user=user, nutrition=nutrition)
        reserve.nf_id = request.data['nf']
        reserve.save()
        nf_s = list(map(lambda i: i['id'], request.data['nfs']))
        reserve.pluses.exclude(nf_id__in=nf_s).delete()
        for nf in request.data['nfs']:
            plus, crested = ReservePlus.objects.get_or_create(reserve=reserve, nf_id=nf['id'])
            plus.count = nf['count']
            plus.save()
        return Response(data=SerReserveList(reserve).data)


class UnreservedUsers(GenericAPIView):
    def get(self, request, unit):
        if not request.user.groups.filter(name='food').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        pks = list(Reserve.objects.filter(Q(user__post__unit_id=unit) | Q(user__post__unit__parent_id=unit)).filter(nutrition__date=request.GET['date']).values_list('user_id', flat=True))
        user_list = User.objects.filter(Q(post__unit_id=unit) | Q(post__unit__parent_id=unit)).exclude(id__in=pks)
        return Response(data=SerUserList(user_list, many=True).data)


class FoodUserList(ListAPIView):
    serializer_class = SerFoodUserList

    def get_queryset(self):
        if self.request.user.groups.filter(name='food').exists():
            return User.objects.filter(post__isnull=False)
        return User.objects.filter(id=0)


class ToggleHasSfFood(GenericAPIView):
    def post(self, request):
        if request.user.groups.filter(name='food').exists():
            profile = get_object_or_404(Profile, pk=request.data['id'])
            profile.has_sf_food = not profile.has_sf_food
            profile.save()
            return Response(data=profile.has_sf_food)
        return Response(data='شما دسترسی لازم را ندارید', status=status.HTTP_403_FORBIDDEN)


class RateFood(GenericAPIView):
    def post(self, request):
        reserve = get_object_or_404(Reserve, nf=request.data['id'], user=request.user)
        reserve.rate = request.data.get('rate', None)
        reserve.note = request.data.get('note', None)
        reserve.save()
        return Response()
