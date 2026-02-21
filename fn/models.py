from django.db import models
from core.models import Unit, User
from django_jalali.db import models as jmodels
from django.contrib import admin
from django.db.models import Sum, Min, Max, Case, When, F, FloatField


class InvoiceCover(models.Model):
    """روکش سند هزینه تنخواه"""
    class Meta:
        verbose_name = 'روکش سند هزینه'
        verbose_name_plural = 'روکش سند هزینه'
        ordering = ['-lock_time', '-id']

    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, verbose_name='واحد')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    no = models.PositiveBigIntegerField(null=True, blank=True, unique=True, verbose_name='شماره')
    locked = models.BooleanField(default=False, verbose_name='قفل شده')
    lock_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='تاریخ قفل')
    accepted = models.BooleanField(null=True, blank=True, verbose_name='تأیید شده', help_text='در تنخواه مستقیم: آخرین تأیید، توسط اداره‌کل مالی')
    accept_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='تاریخ تأیید')
    accept_note = models.TextField(null=True, blank=True, verbose_name='شرح تأیید')
    # فیلدهای تنخواه مستقیم
    type = models.CharField(max_length=6, choices=[('عادی', 'عادی'), ('مستقیم', 'مستقیم')], default='عادی', verbose_name='نوع')
    setadiran = models.BooleanField(default=False, verbose_name='خرید از سامانه ستاد')
    sheba = models.CharField(max_length=24, null=True, blank=True, verbose_name='شبا')
    sheba_owner = models.CharField(max_length=255, null=True, blank=True, verbose_name='نام صاحب شبا')

    business_license = models.FileField(null=True, blank=True, upload_to='invoice', verbose_name='جواز کسب')
    id_card = models.FileField(null=True, blank=True, upload_to='invoice', verbose_name='کارت ملی')
    factor = models.FileField(null=True, blank=True, upload_to='invoice', verbose_name='فاکتور')
    slip = models.FileField(null=True, blank=True, upload_to='invoice', verbose_name='فیش واریز')
    confirm1 = models.BooleanField(null=True, blank=True, verbose_name='تأیید خانم کرامتی')
    confirm2 = models.BooleanField(null=True, blank=True, verbose_name='تأیید مدیر واحد')
    confirm3 = models.BooleanField(null=True, blank=True, verbose_name='تأیید آقای جاودانی')
    confirm1_note = models.TextField(null=True, blank=True, verbose_name='توضیحات خانم کرامتی')
    confirm2_note = models.TextField(null=True, blank=True, verbose_name='توضیحات مدیر واحد')
    confirm3_note = models.TextField(null=True, blank=True, verbose_name='توضیحات آقای جاودانی')
    confirm1_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان تأیید خانم کرامتی')
    confirm2_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان تأیید آقای حق‌بین')
    confirm3_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان تأیید آقای جاودانی')
    deposit_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان واریز')

    def __str__(self):
        return str(self.no)

    def save(self, *args, **kwargs):
        if self._state.adding:
            pre = InvoiceCover.objects.filter(unit=self.unit).order_by('id').last()
            if pre:
                self.no = pre.no + 1
            else:
                self.no = int(self.unit_id) * 100000 + 1
        super().save(*args, **kwargs)

    @property
    @admin.display(description='تعداد سند')
    def invoice_count(self):
        return self.invoices.count()

    @property
    @admin.display(description='جمع')
    def total_price_sum(self):
        val = self.invoices.aggregate(val=Sum('price'))['val'] or 0
        return f'{val:,}'

    @property
    @admin.display(description='جمع')
    def price_sum(self):
        val = (self.invoices.aggregate(val=Sum('price'))['val'] or 0) - (self.invoices.annotate(sum=Case(When(value_added=True, then=F('price')/11), default=0, output_field=FloatField())).aggregate(val=Sum('sum'))['val'] or 0)
        return f'{val:,}'

    @property
    def value_added_sum(self):
        val = self.invoices.annotate(sum=Case(When(value_added=True, then=F('price')/11), default=0, output_field=FloatField())).aggregate(val=Sum('sum'))['val'] or 0
        return f'{val:,}'

    @property
    def begin_date(self):
        return self.invoices.aggregate(val=Min('date'))['val'] or '-'

    @property
    def end_date(self):
        return self.invoices.aggregate(val=Max('date'))['val'] or '-'

    @property
    def unit_manager(self):
        return self.unit.manager.get_full_name()

    @property
    def business_license_url(self):
        return self.business_license.name if self.business_license else None

    @property
    def id_card_url(self):
        return self.id_card.name if self.id_card else None

    @property
    def factor_url(self):
        return self.factor.name if self.factor else None

    @property
    def slip_url(self):
        return self.slip.name if self.slip else None


class InvoiceCategory(models.Model):
    """معین هزینه"""
    class Meta:
        verbose_name = 'معین هزینه'
        verbose_name_plural = 'معین هزینه'
        ordering = ['id']

    id = models.PositiveBigIntegerField(primary_key=True, verbose_name='کد')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    is_available = models.BooleanField(default=True, verbose_name='فعال است')

    def __str__(self):
        return self.title


class Invoice(models.Model):
    """فاکتور"""
    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتور'
        ordering = ['id']

    cover = models.ForeignKey(to=InvoiceCover, on_delete=models.PROTECT, related_name='invoices', verbose_name='روکش')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, null=True, blank=True, verbose_name='واحد سازمانی')
    category = models.ForeignKey(to=InvoiceCategory, on_delete=models.PROTECT, related_name='invoices', verbose_name='کد معین')
    no = models.CharField(max_length=20, null=True, blank=True, verbose_name='شماره سند')
    date = jmodels.jDateField(verbose_name='تاریخ')
    has_paper = models.BooleanField(default=True, verbose_name='فاکتور فیزیکی دارد')
    value_added = models.BooleanField(default=False, verbose_name='شامل ارزش افزوده')
    issuer = models.CharField(max_length=100, null=True, blank=True, verbose_name='طرف مقابل')
    description = models.TextField(null=True, blank=True, verbose_name='شرح فاکتور')
    price = models.PositiveBigIntegerField(verbose_name='مبلغ')

    def __str__(self):
        return f'{self.price:,}'

    @property
    def gross_price(self):
        return f'{(round(self.price / 1.1) if self.value_added else self.price):,}'

    @property
    def value_added_price(self):
        return f'{(round(self.price / 11) if self.value_added else 0):,}'


class InvoiceCoverTask(models.Model):
    """مراحل پرداخت تنخواه"""
    class Meta:
        verbose_name = 'مراحل پرداخت'
        verbose_name_plural = 'مراحل پرداخت'
        ordering = ['id']

    cover = models.ForeignKey(to=InvoiceCover, on_delete=models.CASCADE, related_name='tasks', verbose_name='روکش')
    status = models.CharField(max_length=50, verbose_name='وضعیت')
    accept = models.BooleanField(default=True, verbose_name='تأیید')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    note = models.TextField(null=True, blank=True, verbose_name='پیام')

    def __str__(self):
        return '{} - {}'.format(self.cover.no, self.user.get_full_name())

    @property
    def _time(self):
        return self.create_time.strftime('%Y-%m-%d %H:%M')
