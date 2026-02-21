import jdatetime
from django.db import models
from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User, Unit, Post
from django_jalali.db import models as jmodels
from core.choices import ChoicesWarehouseScale


class Food(models.Model):
    """لیست غذاها"""
    class Meta:
        verbose_name = 'غذا'
        verbose_name_plural = 'غذا'
        ordering = ['id']

    name = models.CharField(max_length=50, verbose_name='غذا')

    def __str__(self):
        return self.name

    @property
    @admin.display(description='تعداد سرو')
    def count(self):
        return self.nfs.count()


class Nutrition(models.Model):
    """برنامه غذایی"""
    class Meta:
        verbose_name = 'برنامه غذایی'
        verbose_name_plural = 'برنامه غذایی'
        ordering = 'date',

    date = jmodels.jDateField(unique=True, verbose_name='ناریخ')
    foods = models.ManyToManyField(to=Food, through='NutritionFood', blank=True, verbose_name='')

    def __str__(self):
        return str(self.date)

    @property
    @admin.display(description='روز هفته')
    def day_of_week(self):
        return self.date.j_weekdays_fa[self.date.weekday()]


class NutritionFood(models.Model):
    nutrition = models.ForeignKey(to=Nutrition, on_delete=models.CASCADE, related_name='nfs', verbose_name='برنامه غذایی')
    food = models.ForeignKey(to=Food, on_delete=models.CASCADE, related_name='nfs', verbose_name='غذا')
    price = models.PositiveSmallIntegerField(default=0, verbose_name='قیمت')

    def __str__(self):
        return self.food.name


class Reserve(models.Model):
    """رزرو غذا"""
    class Meta:
        verbose_name = 'رزرو غذا'
        verbose_name_plural = 'رزرو غذا'
        ordering = ['id']
        unique_together = ['user', 'nutrition']

    user = models.ForeignKey(to=User, on_delete=models.PROTECT, verbose_name='کاربر')
    post = models.ForeignKey(to=Post, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پست')
    subsidy = models.BooleanField(default=True, verbose_name='سوبسید غذا')
    nf = models.ForeignKey(to=NutritionFood, on_delete=models.PROTECT, null=True, blank=True, verbose_name='غذا')
    nutrition = models.ForeignKey(to=Nutrition, on_delete=models.PROTECT, verbose_name='برنامه غذایی')
    rate = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='امتیاز')
    note = models.CharField(max_length=100, null=True, blank=True, verbose_name='نظرسنجی')

    def __str__(self):
        return str(self.user.get_full_name())


class ReservePlus(models.Model):
    reserve = models.ForeignKey(to=Reserve, on_delete=models.CASCADE, related_name='pluses', verbose_name='رزرو')
    nf = models.ForeignKey(to=NutritionFood, on_delete=models.CASCADE, related_name='pluses', verbose_name='غذا')
    count = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد')


class Warehouse(models.Model):
    """کالای انبار"""
    class Meta:
        verbose_name = 'انبار'
        verbose_name_plural = 'انبار'
        ordering = ['id']

    title = models.CharField(max_length=40, verbose_name='عنوان کالا')
    scale = models.CharField(max_length=10, choices=ChoicesWarehouseScale, verbose_name='واحد شمارش')
    count = models.IntegerField(default=0, verbose_name='تعداد')
    place = models.CharField(max_length=10, null=True, blank=True, choices=[('آفاق', 'آفاق'), ('سعادت‌آباد', 'سعادت‌آباد')], verbose_name='انبار')
    order_point = models.PositiveIntegerField(null=True, blank=True, verbose_name='حد سفارش')
    type = models.CharField(null=True, blank=True, choices=[('سرمایه‌ای', 'سرمایه‌ای'), ('مصرفی خوراکی', 'مصرفی خوراکی'), ('مصرفی غیرخوراکی', 'مصرفی غیرخوراکی')], verbose_name='نوع')

    def __str__(self):
        return self.title


class Inventory(models.Model):
    """موجودی انبار"""
    class Meta:
        verbose_name = 'موجودی انبار'
        verbose_name_plural = 'موجودی انبار'
        ordering = ['id']

    warehouse = models.ForeignKey(to=Warehouse, on_delete=models.CASCADE, verbose_name='کالا')
    date = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ')
    type = models.CharField(max_length=6, choices=[('افزایش', 'افزایش'), ('کاهش', 'کاهش')], verbose_name='نوع')
    count = models.IntegerField(default=0, verbose_name='تعداد')
    price = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='قیمت', help_text='برای حالت افزایش')
    unit = models.ForeignKey(to=Unit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='واحد متقاضی', help_text='برای حالت کاهش')
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='کاربر متقاضی', help_text='برای حالت کاهش')

    def __str__(self):
        return str(self.count)


@receiver(signal=post_save, sender=Inventory)
def update_inventory(sender, instance, **kwargs):
    warehouse = instance.warehouse
    warehouse.count = (warehouse.inventory_set.filter(type='افزایش').aggregate(val=models.Sum('count'))['val'] or 0) - (warehouse.inventory_set.filter(type='کاهش').aggregate(val=models.Sum('count'))['val'] or 0)
    warehouse.save()

