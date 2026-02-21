import jdatetime
from django.db import models
from django.contrib import admin
from django.db.models import Sum, Avg
from core.models import User, Unit
from prj.models import Project, Phase
from django_jalali.db import models as jmodels
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.postgres.fields import ArrayField
from rest_framework.exceptions import ValidationError
from core.choices import ChoicesConfirmRejectModify


class Agreement(models.Model):
    title = models.CharField(max_length=50, verbose_name='عنوان')

    """توافقنامه"""
    class Meta:
        verbose_name = 'توافقنامه'
        verbose_name_plural = 'توافقنامه'
        ordering = ['id']

    def __str__(self):
        return self.title


class Contract(models.Model):
    """قراردادها"""
    class Meta:
        verbose_name = 'قرارداد'
        verbose_name_plural = 'قراردادها'
        ordering = ['-id']

    registrar = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='contracts', verbose_name='ثبت کننده قرارداد')
    project = models.ForeignKey(to=Project, on_delete=models.PROTECT, related_name='contracts', verbose_name='پروژه')
    agreement = models.ForeignKey(to=Agreement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='توافقنامه')
    no = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name='شماره قرارداد')
    type = models.CharField(max_length=10, choices=[('پژوهشی', 'پژوهشی'), ('اجرایی', 'اجرایی')], verbose_name='نوع قرارداد')
    genre = models.CharField(max_length=5, choices=[('حقوقی', 'حقوقی'), ('حقیقی', 'حقیقی')], verbose_name='شخصیت مجری')
    contractor = models.CharField(max_length=200, verbose_name='مجری')
    contractor_no = models.CharField(max_length=20, verbose_name='کد ملی یا شناسه شرکت')
    title = models.CharField(max_length=200, unique=True, verbose_name='عنوان و موضوع قرارداد')
    start_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ آغاز قرارداد')
    finish_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ پایان قرارداد')
    period = models.CharField(null=True, blank=True, verbose_name='مدت قرارداد', help_text='در صورت خالی بودن تاریخ آغاز و پایان، این فیلد باید تکمیل شود')
    price = models.PositiveBigIntegerField(verbose_name='مبلغ قرارداد')
    note = models.TextField(null=True, blank=True, verbose_name='شرح')
    body = CKEditor5Field(null=True, blank=True, verbose_name='متن قرارداد', config_name='extends')
    tags = ArrayField(models.CharField(max_length=100), default=list, blank=True, verbose_name='برچسب')
    cn_note = models.CharField(max_length=100, null=True, blank=True, verbose_name='توضیحات خصوصی واحد قراردادها')

    f_proposal = models.FileField(null=True, blank=True, default=None, verbose_name='پروپوزال')
    f_acquittance = models.FileField(null=True, blank=True, default=None, verbose_name='مفاصا')
    f_draft = models.FileField(null=True, blank=True, default=None, verbose_name='پیش‌نویس قرارداد')
    f_contract = models.FileField(null=True, blank=True, default=None, verbose_name='متن قرارداد')
    f_warranty = models.FileField(null=True, blank=True, default=None, verbose_name='ضمانتنامه')
    f_technical_attachment = models.FileField(null=True, blank=True, default=None, verbose_name='پیوست فنی')
    f_non_disclosure_agreement = models.FileField(null=True, blank=True, default=None, verbose_name='توافقنامه عدم افشا')
    f_exchange_letter = models.FileField(null=True, blank=True, default=None, verbose_name='نامه مبادله قرارداد')
    f_acquittance_letter = models.FileField(null=True, blank=True, default=None, verbose_name='نامه درخواست مفاصا')
    f_statute = models.FileField(null=True, blank=True, default=None, verbose_name='اساسنامه')
    f_newspaper = models.FileField(null=True, blank=True, default=None, verbose_name='روزنامه رسمی')
    f_etc1 = models.FileField(null=True, blank=True, default=None, verbose_name='سایر 1')
    f_etc2 = models.FileField(null=True, blank=True, default=None, verbose_name='سایر 2')
    f_etc3 = models.FileField(null=True, blank=True, default=None, verbose_name='سایر 3')

    locked = models.BooleanField(default=False, verbose_name='قفل و ارسال')
    manager_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر مدیر واحد')
    fund_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='تأیید دفتر برنامه و بودجه')
    convention_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر واحد قراردادها')
    need_committee = models.BooleanField(default=True, verbose_name='نیاز به کمیته پژوهش دارد')
    committee_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر کمیته پژوهش')
    deputy_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر معاون توسعه')
    head_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر رئیس')
    drafted = models.BooleanField(default=False, verbose_name='تهیه پیش‌نویس')
    draft_accept = models.BooleanField(null=True, blank=True, verbose_name='نظر واحد متقاضی درمورد پیش‌نویس')
    send_to_contractor_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ ارسال به پیمانکار')
    receive_from_contractor_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ دریافت از پیمانکار')
    signature_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ امضای مقام مجاز')
    secretariat_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ دبیرخانه')
    secretariat_no = models.IntegerField(null=True, blank=True, verbose_name='شماره دبیرخانه')
    warranty_type = models.CharField(max_length=15, choices=[('سفته', 'سفته'), ('ضمانتنامه بانکی', 'ضمانتنامه بانکی'), ('ضمانتنامه اداری', 'ضمانتنامه اداری'), ('سپرده انجام کار', 'سپرده انجام کار')], null=True, blank=True, verbose_name='نوع ضمانتنامه')
    warranty_start_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ آغاز ضمانت')
    warranty_end_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ پایان ضمانت')
    has_value_added = models.BooleanField(null=True, blank=True, verbose_name='مشمول مالیات بر ارزش افزوده')
    archived = models.BooleanField(default=False, verbose_name='بایگانی شده', help_text='قراردادهای رد شده + قراردادهای خاتمه یافته')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    def __str__(self):
        return self.title

    @property
    @admin.display(description='وضعیت')
    def status(self):
        if self.archived:
            return 'بایگانی'
        if self.secretariat_date:
            if self.warranty_type:
                return 'نهایی - درانتظار الصاق ضمانتنامه' if self.f_warranty in ['', None] else 'نهایی درانتظار الصاق مفاصا' if self.f_acquittance in ['', None] else 'نهایی'
            return 'نهایی - درانتظار تعیین نوع ضمانتنامه'
        if self.signature_date:
            return 'امضا شده، درانتظار ثبت دبیرخانه'
        if self.receive_from_contractor_date:
            return 'درانتظار امضای مقام مجاز'
        if self.send_to_contractor_date:
            return 'درانتظار امضای پیمانکار'
        if self.draft_accept:
            return 'در نوبت ارسال برای امضای پیمانکار'
        if self.draft_accept is False:
            return 'درانتظار اصلاح پیش‌نویس'
        if self.drafted:
            return 'درانتظار تأیید پیش‌نویس'

        if self.head_accept == 'تأیید':
            return 'درانتظار تهیه پیش‌نویس'
        if self.head_accept == 'عدم تأیید':
            return 'عدم تأیید توسط رئیس مرکز'
        if self.head_accept == 'عودت جهت اصلاح':
            return 'عودت توسط رئیس مرکز جهت اصلاح'

        if self.deputy_accept == 'تأیید':
            return 'درانتظار تأیید رئیس مرکز'
        if self.deputy_accept == 'عدم تأیید':
            return 'عدم تأیید توسط معاونت برنامه‌ریزی و توسعه'
        if self.deputy_accept == 'عودت جهت اصلاح':
            return 'عودت توسط معاونت برنامه‌ریزی و توسعه جهت اصلاح'

        if self.committee_accept == 'تأیید':
            return 'درانتظار تأیید معاونت برنامه‌ریزی و توسعه'
        if self.committee_accept == 'عدم تأیید':
            return 'عدم تأیید در کمیته پژوهش'
        if self.committee_accept == 'عودت جهت اصلاح':
            return 'عودت توسط کمیته پژوهش جهت اصلاح'

        if self.convention_accept == 'تأیید':
            return 'درانتظار بررسی در کمیته پژوهش' if self.need_committee else 'درانتظار تأیید معاونت برنامه‌ریزی و توسعه'
        if self.convention_accept == 'عدم تأیید':
            return 'عدم تأیید توسط واحد قراردادها'
        if self.convention_accept == 'عودت جهت اصلاح':
            return 'عودت توسط واحد قراردادها جهت اصلاح'

        if self.fund_accept == 'تأیید':
            return 'درانتظار بررسی واحد قراردادها'
        if self.fund_accept == 'عدم تأیید':
            return 'عدم تأیید توسط واحد بودجه'
        if self.fund_accept == 'عودت جهت اصلاح':
            return 'عودت توسط واحد بودجه جهت اصلاح'

        if self.manager_accept == 'تأیید':
            return 'درانتظار بررسی واحد بودجه'
        if self.manager_accept == 'عدم تأیید':
            return 'عدم تأیید توسط مدیر واحد'
        if self.manager_accept == 'عودت جهت اصلاح':
            return 'عودت توسط مدیر واحد جهت اصلاح'

        return 'درانتظار بررسی مدیر واحد' if self.locked else 'پیش‌نویس'

    @property
    def supplement_count(self):
        return self.supplements.count()

    def save(self, *args, **kwargs):
        if self._state.adding:
            year = jdatetime.datetime.now().year
            first_day = f'{year}-01-01'
            last_day = f'{year}-12-29'
            self.no = int(f'{200 + self.project.unit.id}{str(year)[2:]}{str(1001+Contract.objects.filter(project__unit=self.project.unit, start_date__gte=first_day, start_date__lte=last_day).count())[1:]}')
            while Contract.objects.filter(no=self.no).exists():
                self.no += 1
        super().save(*args, **kwargs)

    @property
    @admin.display(description='مبلغ کلی قرارداد')
    def _price(self):
        return round(int(self.price) + (self.supplements.aggregate(val=Sum('price'))['val'] or 0))

    @property
    @admin.display(description='تاریخ آغاز کلی قرارداد')
    def _start_date(self):
        sp = self.supplements.filter(start_date__isnull=False).order_by('create_date').first()
        return str(sp.start_date if sp else self.start_date if self.start_date else '')

    @property
    @admin.display(description='تاریخ پایان کلی قرارداد')
    def _finish_date(self):
        sp = self.supplements.filter(finish_date__isnull=False).order_by('create_date').last()
        return str(sp.finish_date if sp else self.finish_date if self.finish_date else '')

    @property
    @admin.display(description='پرداختی تاکنون')
    def sum_of_pay(self):
        return Pay.objects.filter(step__contract=self, paid=True).aggregate(val=Sum('bill'))['val'] or 0

    def percent_sum(self):
        return self.steps.aggregate(val=Sum('percent'))['val'] or 0


class ContractParty(models.Model):
    """مدارک هویتی طرف قرارداد"""
    class Meta:
        verbose_name = 'طرف قرارداد'
        verbose_name_plural = 'مدارک هویتی طرف قرارداد'
        ordering = ['id']

    contract = models.ForeignKey(to=Contract, on_delete=models.CASCADE, related_name='parties', verbose_name='قرارداد')
    name = models.CharField(max_length=50, verbose_name='نام')
    f_nc = models.FileField(null=True, blank=True, verbose_name='کارت ملی')
    f_bc = models.FileField(null=True, blank=True, verbose_name='شناسنامه')
    f_d = models.FileField(null=True, blank=True, verbose_name='مدرک تحصیلی')
    f_msc = models.FileField(null=True, blank=True, verbose_name='کارت پایان خدمت وظیفه')

    def __str__(self):
        return self.name


class ContractTask(models.Model):
    """مراحل پیشرفت قرارداد"""
    class Meta:
        verbose_name = 'مرحله'
        verbose_name_plural = 'مراحل پیشرفت قرارداد'
        ordering = ['id']

    contract = models.ForeignKey(to=Contract, on_delete=models.CASCADE, related_name='tasks', verbose_name='قرارداد')
    status = models.CharField(max_length=50, verbose_name='مرحله')
    answer = models.CharField(max_length=20, null=True, blank=True, verbose_name='پاسخ')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان')
    note = models.TextField(null=True, blank=True, verbose_name='پیام')

    def __str__(self):
        return '{} - {}'.format(self.contract.title, self.user.get_full_name())

    @property
    def _time(self):
        return self.time.strftime('%Y-%m-%d %H:%M')


class Step(models.Model):
    class Meta:
        verbose_name = 'فاز'
        verbose_name_plural = 'فازهای قرارداد'
        ordering = ['id']

    contract = models.ForeignKey(to=Contract, on_delete=models.CASCADE, related_name='steps', verbose_name='قرارداد')
    title = models.CharField(max_length=50, verbose_name='عنوان مرحله')
    price = models.BigIntegerField(default=0, verbose_name='مبلغ')
    start_date = jmodels.jDateField(verbose_name='تاریخ آغاز')
    finish_date = jmodels.jDateField(verbose_name='تاریخ پایان')

    def __str__(self):
        return str(self.percent)

    @property
    def percent(self):
        return round(10000 * self.price / int(self.contract.price)) / 100 if self.contract.price else 0

    @property
    def pay(self):
        return self.pays.filter(paid=True).aggregate(val=Sum('bill'))['val'] or 0


class Pay(models.Model):
    """پرداخت"""
    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت'
        ordering = ['-id']

    registrar = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='pays', null=True, blank=True, verbose_name='ثبت کننده درخواست')
    step = models.ForeignKey(to=Step, on_delete=models.CASCADE, related_name='pays', null=True, blank=True, verbose_name='مرحله قرارداد')
    bill_requested = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='مبلغ درخواست شده')
    date = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ')
    note = models.TextField(null=True, blank=True, verbose_name='شرح')
    file = models.FileField(null=True, blank=True, verbose_name='فایل')
    create_time = jmodels.jDateTimeField(auto_now_add=True, auto_now=False, verbose_name='تاریخ ایجاد')

    locked = models.BooleanField(default=True, verbose_name='قفل و ارسال', help_text='وقتی درخواست در مراحل بررسی رد شود این قفل باز میشود تا درخواست قابل ویرایش و اصلاح باشد')
    manager_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر مدیر واحد')
    convention_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر واحد قراردادها')
    bill = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='قابل پرداخت')
    fund_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='تأیید دفتر برنامه و بودجه')
    clerk_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر کارشناس مالی')
    deputy_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر معاون توسعه')
    need_head = models.BooleanField(default=False, verbose_name='نیاز به تأیید رئیس مرکز دارد')
    head_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر رئیس مرکز')
    finance_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر مدیرکل مالی')
    audit = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='ممیزی اسناد')
    paid = models.BooleanField(null=True, blank=True, verbose_name='پرداخت شد')
    tax = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='مالیات')
    insurance = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='سپرده بیمه')
    commitments = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='انجام کار/تعهدات')
    value_added = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='ارزش افزوده')
    net = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='خالص پرداختی')
    slip = models.FileField(null=True, blank=True, upload_to='invoice', verbose_name='فیش واریز')

    def __str__(self):
        return self.step.title

    @property
    def status(self):
        if self.locked is False:
            return 'منتظر اصلاح'

        if self.paid:
            return 'پرداخت شده'
        if self.paid is False:
            return 'عدم پرداخت'
        if self.audit == 'تأیید':
            return 'در نوبت پرداخت'
        if self.audit == 'عدم تأیید':
            return 'عدم تأیید ممیزی'
        if self.finance_accept == 'تأیید':
            return 'درانتظار ممیزی'
        if self.finance_accept == 'عدم تأیید':
            return 'عدم تأیید پرداخت'
        if self.head_accept == 'تأیید':
            return 'درانتظار بررسی مدیرکل مالی'
        if self.head_accept == 'عدم تأیید':
            return 'عدم تأیید رئیس مرکز'
        if self.deputy_accept == 'تأیید':
            return 'درانتظار بررسی رئیس مرکز' if self.need_head else 'درانتظار بررسی مدیرکل مالی'
        if self.deputy_accept == 'عدم تأیید':
            return 'عدم تأیید معاونت توسعه'
        if self.clerk_accept == 'تأیید':
            return 'درانتظار بررسی معاون توسعه'
        if self.clerk_accept == 'عدم تأیید':
            return 'عدم تأیید مدارک'
        if self.fund_accept == 'تأیید':
            return 'درانتظار بررسی مدارک'
        if self.fund_accept == 'عدم تأیید':
            return 'عدم تأیید بودجه'
        if self.convention_accept == 'تأیید':
            return 'درانتظار بررسی بودجه'
        if self.convention_accept == 'عدم تأیید':
            return 'عدم تأیید واحد قراردادها'
        if self.manager_accept == 'تأیید':
            return 'درانتظار بررسی واحد قراردادها'
        if self.manager_accept == 'عدم تأیید':
            return 'عدم تأیید مدیر واحد'
        return 'درانتظار بررسی مدیر واحد'

    @property
    def file_url(self):
        return self.file.name if self.file else None

    @property
    def slip_url(self):
        return self.slip.name if self.slip else None

    @property
    def percent_requested(self):
        return round(100 * self.bill_requested / self.step.price) if self.step.price else 0

    @property
    def percent(self):
        return round(100 * self.bill / self.step.price) if self.bill and self.step.price else 0


class PayTask(models.Model):
    """مراحل پرداخت"""
    class Meta:
        verbose_name = 'مراحل پرداخت'
        verbose_name_plural = 'مراحل پرداخت'
        ordering = ['id']

    pay = models.ForeignKey(to=Pay, on_delete=models.CASCADE, related_name='tasks', verbose_name='پرداخت')
    status = models.CharField(max_length=50, verbose_name='وضعیت')
    answer = models.CharField(max_length=20, null=True, blank=True, verbose_name='پاسخ')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    note = models.TextField(null=True, blank=True, verbose_name='پیام')

    def __str__(self):
        return '{} - {}'.format(self.pay.step.title, self.user.get_full_name())

    @property
    def _time(self):
        return self.create_time.strftime('%Y-%m-%d %H:%M')


class Supplement(models.Model):
    """الحاقیه"""
    class Meta:
        verbose_name = 'الحاقیه'
        verbose_name_plural = 'الحاقیه‌ها'
        ordering = ['id']

    contract = models.ForeignKey(to=Contract, on_delete=models.CASCADE, related_name='supplements', verbose_name='قرارداد')
    no = models.CharField(unique=True, max_length=100, verbose_name='شماره الحاقیه')
    date = jmodels.jDateField(verbose_name='تاریخ الحاقیه')
    price = models.BigIntegerField(null=True, blank=True, verbose_name='مبلغ الحاقیه')
    start_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ آغاز جدید')
    finish_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ پایان جدید')
    description = models.TextField(null=True, blank=True, verbose_name='شرح الحاقیه')

    manager_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر مدیر واحد')
    convention_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر واحد قراردادها')
    deputy_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر معاون توسعه')
    send_to_contractor_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ ارسال به پیمانکار')
    receive_from_contractor_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ دریافت از پیمانکار')
    signature_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ امضای مقام مجاز')
    secretariat_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ دبیرخانه')
    secretariat_no = models.IntegerField(null=True, blank=True, verbose_name='شماره دبیرخانه')
    create_date = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    def __str__(self):
        return 'الحاقیه {}'.format(self.date)


# ********** پایگاه دانش **********


class ArticleCategory(models.Model):
    class Meta:
        verbose_name = 'نوع'
        verbose_name_plural = 'مقاله - نوع'
        ordering = ['id']

    title = models.CharField(max_length=80, verbose_name='عنوان')
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE, related_name='children', null=True, blank=True, verbose_name='والد')
    owners = models.ManyToManyField(to=User, blank=True, verbose_name='ادمین‌ها')
    description = models.TextField(null=True, blank=True, verbose_name='شرح')

    def __str__(self):
        return self.title


class Article(models.Model):
    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقاله'
        ordering = ['id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, verbose_name='واحد')
    category = models.ForeignKey(to=ArticleCategory, on_delete=models.CASCADE, related_name='articles', verbose_name='نوع')
    step = models.ForeignKey(to=Step, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='فاز قرارداد')
    title = models.CharField(max_length=80, verbose_name='عنوان')
    subtitle = models.CharField(max_length=80, verbose_name='زیرعنوان')
    tags = ArrayField(models.CharField(max_length=100), default=list, blank=True, verbose_name='برچسب')
    poster = models.ImageField(null=True, blank=True, upload_to='article_poster', verbose_name='پوستر')
    summary = models.TextField(verbose_name='چکیده')
    is_available = models.BooleanField(default=True, verbose_name='نمایش داده شود')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    update_time = jmodels.jDateTimeField(auto_now=True, verbose_name='زمان ویرایش')

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        return self.poster.name if self.poster else 'article.jpg'

    @property
    def attachment_count(self):
        return self.attachments.count()

    @property
    def chat_count(self):
        return self.chats.count()

    @property
    def rate(self):
        return {
            'count': self.rates.count(),
            'average': self.rates.aggregate(val=Avg('rate'))['val'],
        }

    @property
    def permit_count(self):
        return self.permits.count()


class ArticleAttachment(models.Model):
    class Meta:
        verbose_name = 'پیوست'
        verbose_name_plural = 'مقاله - پیوست'
        ordering = ['id']

    article = models.ForeignKey(to=Article, on_delete=models.CASCADE, related_name='attachments', verbose_name='مقاله')
    title = models.CharField(max_length=80, verbose_name='عنوان')
    file = models.FileField(null=True, blank=True, upload_to='article_attachments', verbose_name='فایل')
    author = models.CharField(max_length=80, null=True, blank=True, verbose_name='مؤلف')
    create_time = jmodels.jDateTimeField(auto_now_add=True, auto_now=False, verbose_name='زمان ایجاد')

    def __str__(self):
        return self.title


class ArticlePermit(models.Model):
    class Meta:
        verbose_name = 'درخواست'
        verbose_name_plural = 'مقاله - درخواست'
        ordering = ['id']
        unique_together = ('article', 'user')

    article = models.ForeignKey(to=Article, on_delete=models.CASCADE, related_name='permits', verbose_name='مقاله')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    note = models.CharField(max_length=100, verbose_name='شرح درخواست')
    accept = models.BooleanField(null=True, blank=True, verbose_name='تأیید')
    create_time = jmodels.jDateTimeField(auto_now_add=True, auto_now=False, verbose_name='زمان ایجاد')
    update_time = jmodels.jDateTimeField(auto_now=True, verbose_name='زمان ویرایش')

    def __str__(self):
        return self.user.get_full_name()


class ArticleChat(models.Model):
    class Meta:
        verbose_name = 'گفتگو'
        verbose_name_plural = 'مقاله - گفتگو'
        ordering = ['-id']

    article = models.ForeignKey(to=Article, on_delete=models.CASCADE, related_name='chats', verbose_name='مقاله')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    body = models.TextField(verbose_name='متن')
    create_time = jmodels.jDateTimeField(auto_now_add=True, auto_now=False, verbose_name='زمان ایجاد')

    def __str__(self):
        return self.body


class ArticleChatLike(models.Model):
    class Meta:
        verbose_name = 'پسند'
        verbose_name_plural = ' مقاله - پسند گفتگو'
        ordering = ['id']
        unique_together = ('chat', 'user')

    chat = models.ForeignKey(to=ArticleChat, on_delete=models.CASCADE, related_name='likes', verbose_name='گفتگو')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    like = models.BooleanField(default=True, verbose_name='پسند')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    def __str__(self):
        return self.user.get_full_name()

    def save(self, *args, **kwargs):
        if self.user == self.chat.user:
            raise ValidationError('شما نمی‌توانید پیام خودتان را پسند یا ناپسند کنید')
        super().save(*args, **kwargs)


class ArticleRate(models.Model):
    class Meta:
        verbose_name = 'امتیاز مقاله'
        verbose_name_plural = 'مقاله - امتیاز'
        ordering = ['id']
        unique_together = ('article', 'user')

    article = models.ForeignKey(to=Article, on_delete=models.CASCADE, related_name='rates', verbose_name='مقاله')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    rate = models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='امتیاز')
    create_time = jmodels.jDateTimeField(auto_now_add=True, auto_now=False, verbose_name='زمان ایجاد')

    def __str__(self):
        return str(self.rate)
