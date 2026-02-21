import jdatetime
from django.db import models
from datetime import timedelta
from django.contrib import admin
from django_jalali.db import models as jmodels
from core.models import User, Post, Unit, ModifiedArrayField
from core.choices import ChoicesYearList, ChoicesMonthList, ChoicesPostLevel, ChoicesResponder
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum

def js_round(value):
    return int(Decimal(value).quantize(0, rounding=ROUND_HALF_UP))


class Profile(models.Model):
    class Meta:
        db_table = 'profile'
        verbose_name = 'پروفایل'
        verbose_name_plural = 'پروفایل'
        ordering = ['id']

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    ad = models.CharField(max_length=40, null=True, blank=True, verbose_name='Active Directory Username')
    is_permanent = models.BooleanField(default=False, verbose_name='کارمند رسمی')
    is_advisor = models.BooleanField(default=False, verbose_name='مشاور')
    is_agent = models.BooleanField(default=False, verbose_name='مأمور')
    is_sacrificer = models.BooleanField(default=False, verbose_name='ایثارگران')
    has_work = models.BooleanField(default=True, verbose_name='ثبت کارآیی در پرتال')
    is_soldier = models.BooleanField(default=False, verbose_name='سرباز امریه')
    is_corporate = models.BooleanField(default=False, verbose_name='نیروی شرکتی')
    has_sf_mobile = models.BooleanField(default=False, verbose_name='سوبسید تلفن همراه')
    has_sf_food = models.BooleanField(default=True, verbose_name='سوبسید غذا')
    attendance_min = models.PositiveSmallIntegerField(default=0, verbose_name='جمع ساعات حضور', help_text='ویژه مشاوران')
    sf1 = models.IntegerField(default=0, verbose_name='حقوق و رتبه پایه', help_text='از راهکاران به‌روز می‌شود')
    sf5 = models.IntegerField(default=0, verbose_name='فوق‌العاده شغل', help_text='از راهکاران به‌روز می‌شود')
    sf6 = models.IntegerField(default=0, verbose_name='فوق‌العاده جذب', help_text='از راهکاران به‌روز می‌شود')
    sf7 = models.IntegerField(default=0, verbose_name='فوق‌العاده ویژه', help_text='از راهکاران به‌روز می‌شود')
    sf8 = models.IntegerField(default=0, verbose_name='حق عائله‌مندی', help_text='از راهکاران به‌روز می‌شود')
    sf11 = models.IntegerField(default=0, verbose_name='حق اولاد', help_text='از راهکاران به‌روز می‌شود')
    sf14 = models.IntegerField(default=0, verbose_name='فوق‌العاده مخصوص', help_text='از راهکاران به‌روز می‌شود')
    sf20 = models.IntegerField(default=0, verbose_name='فوق‌العاده مدیریت', help_text='از راهکاران به‌روز می‌شود')
    sf27 = models.IntegerField(default=0, verbose_name='تفاوت تطبیق', help_text='از راهکاران به‌روز می‌شود')
    sf38 = models.IntegerField(default=0, verbose_name='فوق العاده ایثارگری ماده 51', help_text='از راهکاران به‌روز می‌شود')
    sf42 = models.IntegerField(default=0, verbose_name='تفاوت بند(ی) تبصره 12-سال 1398', help_text='از راهکاران به‌روز می‌شود')
    sf45 = models.IntegerField(default=0, verbose_name='تفاوت جزء(1)بند الف ت12-سال 1397', help_text='از راهکاران به‌روز می‌شود')
    sf49 = models.IntegerField(default=0, verbose_name='تفاوت تطبیق موضوع ب الف ت12-سال 1399', help_text='از راهکاران به‌روز می‌شود')
    sf51 = models.IntegerField(default=0, verbose_name='تفاوت تطبیق جز(3) بند الف ت 12-سال 1400', help_text='از راهکاران به‌روز می‌شود')
    sf52 = models.IntegerField(default=0, verbose_name='کاهش ناشی از اجرای جز(1) بند الف تبصره12', help_text='از راهکاران به‌روز می‌شود')
    sf64 = models.IntegerField(default=0, verbose_name='تفاوت تطبیق جز (1) بند الف ت 12-سال 1401', help_text='از راهکاران به‌روز می‌شود')
    sf65 = models.IntegerField(default=0, verbose_name='همترازی ایثارگری', help_text='از راهکاران به‌روز می‌شود')
    sf68 = models.IntegerField(default=0, verbose_name='ترمیم حقوق', help_text='از راهکاران به‌روز می‌شود')
    sf69 = models.IntegerField(default=0, verbose_name='تفاوت تطبیق موضوع جز (1) ب الف ت 12 ق ب 1402', help_text='از راهکاران به‌روز می‌شود')
    sf70 = models.IntegerField(default=0, verbose_name='حق الزحمه مشاوره', help_text='از راهکاران به‌روز می‌شود')
    sf_mobile = models.IntegerField(default=0, verbose_name='کمک هزینه تلفن همراه', help_text='از راهکاران به‌روز می‌شود')
    sf_food = models.IntegerField(default=0, verbose_name='حق غذا', help_text='از راهکاران به‌روز می‌شود')
    sf_commuting = models.IntegerField(default=0, verbose_name='بن غیرنقدی - ایاب و ذهاب', help_text='از راهکاران به‌روز می‌شود')
    sf_house = models.IntegerField(default=0, verbose_name='حق مسکن', help_text='از راهکاران به‌روز می‌شود')
    sf_management = models.IntegerField(default=0, verbose_name='حق مدیریت (جبران خدمت)')
    create_time = jmodels.jDateTimeField(auto_now_add=True)
    update_time = jmodels.jDateTimeField(auto_now=True)
    page_size = models.PositiveSmallIntegerField(default=10, editable=False, verbose_name='تعداد ردیف جدول')
    sms = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='کد احراز هویت')
    sms_sent_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان ارسال احراز هویت')

    def __str__(self):
        return self.user.get_full_name()

    @property
    @admin.display(description='کد پرسنلی')
    def personnel_code(self):
        return self.user.personnel_code

    @property
    @admin.display(boolean=True, description='فعال است')
    def is_active(self):
        return self.user.is_active

    @property
    def sms_expired(self):
        """انقضای پیامک بعد از دو دقیقه"""
        return (jdatetime.datetime.now() - self.sms_sent_time).seconds > 130 if self.sms_sent_time else False


class Work(models.Model):
    """کارکرد"""
    class Meta:
        verbose_name = 'کارکرد'
        verbose_name_plural = 'کارکرد'
        ordering = ['id']
        unique_together = ['user', 'year', 'month']

    user = models.ForeignKey(to=User, on_delete=models.PROTECT, verbose_name='کاربر')
    year = models.PositiveSmallIntegerField(choices=ChoicesYearList, verbose_name='سال')
    month = models.PositiveSmallIntegerField(choices=ChoicesMonthList, verbose_name='ماه')
    work_days = models.PositiveSmallIntegerField(default=30, verbose_name='تعداد روز کارکرد')
    gross_work = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='کارکرد ناخالص', help_text='با احتساب مرخصی‌ها')
    work = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='کارکرد خالص', help_text='بدون احتساب مرخصی‌ها')
    paid_leave = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='مرخصی استحقاقی')
    sick_leave = models.PositiveSmallIntegerField(default=0, verbose_name='مرخصی استعلاجی')
    telecommuting = models.PositiveSmallIntegerField(default=0, verbose_name='دورکاری')
    mission = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='مأموریت')
    delay = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='کسر کار')
    absence = models.PositiveSmallIntegerField(default=0, verbose_name='غیبت')
    work_overtime = models.DurationField(default=timedelta(hours=0, minutes=0), verbose_name='اضافه‌کار واقعی')
    overtime = models.PositiveSmallIntegerField(default=0, verbose_name='اضافه‌کار تشویقی')
    bonus = models.PositiveIntegerField(default=0, verbose_name='کارآیی')
    percent = models.PositiveSmallIntegerField(default=0, verbose_name='درصد تأیید کارکرد مشاور')
    amenity_percent = models.PositiveSmallIntegerField(default=100, verbose_name='درصد رفاهیات')
    meed = models.PositiveIntegerField(default=0, verbose_name='پاداش')
    meed_note = models.TextField(null=True, blank=True, verbose_name='علت پاداش')
    salary = models.PositiveIntegerField(default=0, verbose_name='خالص حقوق')

    def get_sum(self):
        p = self.user.profile

        return (
                p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf8 + p.sf11 +
                p.sf14 + p.sf20 + p.sf27 + p.sf38 + p.sf42 +
                p.sf45 + p.sf49 + p.sf51 + p.sf52 + p.sf64 +
                p.sf65 + p.sf68 + p.sf69 + p.sf70 +
                p.sf_food + p.sf_house + p.sf_mobile + p.sf_commuting
        )

    # ---------------------------------------------------
    # اضافه‌کار
    # ---------------------------------------------------
    def get_overtime_amount(self):
        p = self.user.profile

        base_for_overtime = (
                p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf42 + p.sf45
        )

        divisor = 100 if p.is_advisor else 176

        overtime = self.overtime * base_for_overtime / divisor
        return js_round(overtime)

    # ---------------------------------------------------
    # مزایای ناخالص
    # ---------------------------------------------------
    def get_gross(self):
        p = self.user.profile

        gross = (
                (self.get_sum() * self.work_days / 30)
                + (self.bonus * 10)
                + self.get_overtime_amount()
                + p.sf_management
        )

        return js_round(gross)

    # ---------------------------------------------------
    # مبلغ مشمول بیمه
    # ---------------------------------------------------
    def get_insurance_covered(self):
        p = self.user.profile

        insurance_covered = (
                p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf14 +
                p.sf20 + p.sf27 + p.sf38 + p.sf42 +
                p.sf45 + p.sf49 + p.sf51 + p.sf52 +
                p.sf64 + p.sf68 + p.sf69 + p.sf_house
        )

        return js_round(insurance_covered)

    # ---------------------------------------------------
    # بیمه
    # ---------------------------------------------------
    def get_insurance(self):
        p = self.user.profile

        if p.is_sacrificer or p.is_advisor or p.is_agent:
            return 0

        return js_round(self.get_insurance_covered() * 0.07)

    # ---------------------------------------------------
    # مالیات
    # ---------------------------------------------------
    def get_tax(self):
        p = self.user.profile

        gross = self.get_gross()
        insurance = self.get_insurance()

        tax_covered = (
                gross
                - p.sf65
                - p.sf11
                - p.sf8
                - p.sf_food
                - p.sf_mobile
                - p.sf_commuting
                - (insurance * 2 / 7)
        )

        tax_covered = max(0, tax_covered)

        if p.is_sacrificer:
            return 0

        tax = (
                max(0, min(tax_covered, 300_000_000) - 240_000_000) * 0.1 +
                max(0, min(tax_covered, 380_000_000) - 300_000_000) * 0.15 +
                max(0, min(tax_covered, 500_000_000) - 380_000_000) * 0.2 +
                max(0, min(tax_covered, 666_666_667) - 500_000_000) * 0.25 +
                max(0, min(tax_covered, 999_999_999_999) - 666_666_667) * 0.3
        )

        return js_round(tax)

    # ---------------------------------------------------
    # کسورات
    # ---------------------------------------------------
    def get_deductions(self):
        from hr.models import DeductionWork

        result = DeductionWork.objects.filter(
            user=self.user,
            year=self.year,
            month=self.month
        ).aggregate(total=Sum("value"))

        return result["total"] or 0

    # ---------------------------------------------------
    # محاسبه حقوق نهایی
    # ---------------------------------------------------
    def calculate_salary(self, save=True):

        gross = self.get_gross()
        insurance = self.get_insurance()
        tax = self.get_tax()
        deduction = self.get_deductions()

        net = (
                      gross
                      + (self.meed * 10)
                      - insurance
                      - tax
                      - deduction
              ) / 10

        net = js_round(net)

        if save:
            self.salary = net
            self.save(update_fields=["salary"])

        return net

    def __str__(self):
        return self.user.get_full_name()

    @property
    def history(self):
        # سوابق اضافه کار و کارآیی سه ماه گذشته
        log = Work.objects.order_by('-year', '-month', 'id').filter(user=self.user, id__lt=self.id)[:3:-1]
        return {
            'overtime': list(map(lambda w: w.overtime, log)),
            'bonus': list(map(lambda w: w.bonus, log)),
            'percent': list(map(lambda w: w.percent, log)),
        }


class Timesheet(models.Model):
    """تایم شیت"""
    class Meta:
        verbose_name = 'تایم شیت'
        verbose_name_plural = 'تایم شیت'
        ordering = ['id']
        unique_together = ['work', 'project']

    work = models.ForeignKey(to=Work, on_delete=models.CASCADE, verbose_name='کارکرد')
    project = models.ForeignKey(to='prj.Project', on_delete=models.CASCADE, verbose_name='پروژه')
    note = models.TextField(null=True, blank=True, verbose_name='شرح', help_text='برای حالتی که پروژه خالی است')
    percent = models.PositiveSmallIntegerField(default=0, verbose_name='درصد')

    def __str__(self):
        return self.project.title


# ###################   360 Degree Assessment  ###################


class Assessment(models.Model):
    """ارزیابی 360 درجه کارمندان"""
    class Meta:
        verbose_name = 'ارزیابی'
        verbose_name_plural = 'ارزیابی 360 درجه'
        ordering = ['id']
        unique_together = ['year', 'who', 'whom']

    year = models.PositiveSmallIntegerField(choices=[(1403, 1403), (1404, 1404)], verbose_name='سال')
    who = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='assessment_who_set', verbose_name='ارزیابی کننده')
    whom = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='assessment_whom_set', verbose_name='ارزیابی شونده')
    done = models.BooleanField(default=False, verbose_name='ارزیابی ثبت شد')
    bio = models.CharField(null=True, blank=True, max_length=100, verbose_name='معرفی در یک جمله')
    strength = models.TextField(null=True, blank=True, verbose_name='نقاط قوت')
    weakness = models.TextField(null=True, blank=True, verbose_name='نکات قابل بهبود')
    note = models.TextField(null=True, blank=True, verbose_name='هر چه می‌خواهد دل تنگت', help_text='فقط در خودارزیابی')
    educations = models.TextField(null=True, blank=True, verbose_name='آموزش‌های مورد نیاز', help_text='فقط در خودارزیابی')
    create_time = jmodels.jDateTimeField(auto_now_add=True)
    update_time = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return self.whom.get_full_name()


class Question(models.Model):
    """پرسش‌های ارزیابی 360 درجه"""
    class Meta:
        verbose_name = 'پرسش'
        verbose_name_plural = 'ارزیابی 360 درجه - پرسش'
        ordering = ['id']

    body = models.CharField(max_length=200, verbose_name='پرسش')
    year = models.PositiveSmallIntegerField(choices=[(1403, 1403), (1404, 1404)], verbose_name='سال')
    levels = ModifiedArrayField(base_field=models.CharField(max_length=20, choices=ChoicesPostLevel), blank=True, default=list, verbose_name='رده‌های سازمانی')
    responders = ModifiedArrayField(base_field=models.CharField(max_length=10, choices=ChoicesResponder), blank=True, default=list, verbose_name='پاسخگو')
    respondent = models.CharField(max_length=15, choices=[('مدیر واحد', 'مدیر واحد'), ('سرپرست مستقیم', 'سرپرست مستقیم'), ('نیروی تحت امر', 'نیروی تحت امر'), ('خودارزیابی', 'خودارزیابی'), ('همکار', 'همکار')], null=True, blank=True, verbose_name='پاسخگو')
    choice_count = models.PositiveSmallIntegerField(default=6, verbose_name='تعداد گزینه پاسخ')

    def __str__(self):
        return self.body


class Answer(models.Model):
    class Meta:
        verbose_name = 'پاسخ'
        verbose_name_plural = 'ارزیابی 360 درجه - پاسخ'
        ordering = ['id']
        unique_together = ['assessment', 'question']

    assessment = models.ForeignKey(to=Assessment, on_delete=models.CASCADE, related_name='answers', verbose_name='ارزیابی')
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE, related_name='answers', verbose_name='پرسش')
    rate = models.PositiveSmallIntegerField(verbose_name='پاسخ')

    def __str__(self):
        return str(self.rate)


class Deduction(models.Model):
    class Meta:
        verbose_name = 'کسورات'
        verbose_name_plural = 'کسورات'
        ordering = ['id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    year = models.PositiveSmallIntegerField(verbose_name='سال')
    month = models.PositiveSmallIntegerField(verbose_name='ماه')
    insurance = models.PositiveIntegerField(verbose_name='بیمه تکمیلی')
    loan = models.PositiveIntegerField(verbose_name='اقساط وام')
    fund = models.PositiveIntegerField(verbose_name='صندوق کارکنان')
    other = models.PositiveIntegerField(verbose_name='سایر')

    def __str__(self):
        return self.user.get_full_name()


class DeductionType(models.Model):
    """انواع کسورات"""

    class Meta:
        verbose_name = 'نوع کسور'
        verbose_name_plural = 'انواع کسورات'
        ordering = ['order']

    code = models.CharField(max_length=20, unique=True, verbose_name='کد')
    title = models.CharField(max_length=100, verbose_name='عنوان')
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')

    def __str__(self):
        return f" {self.title}"


class DeductionWork(models.Model):
    class Meta:
        verbose_name = 'کسورات'
        verbose_name_plural = 'کسورات'
        ordering = ['id']
        # تغییر unique_together برای جلوگیری از ثبت تکراری
        unique_together = ['user', 'year', 'month', 'type']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    year = models.PositiveSmallIntegerField(verbose_name='سال')
    month = models.PositiveSmallIntegerField(verbose_name='ماه')
    type = models.ForeignKey(
        to=DeductionType,
        on_delete=models.PROTECT,
        verbose_name='نوع کسور'
    )
    value = models.PositiveIntegerField(default=0, verbose_name='مقدار (عددی)')
    create_time = jmodels.jDateTimeField(auto_now_add=True)
    update_time = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.type.title}"

# ###################   9 Box Evaluation Model (Performance Potential)  ###################


class EvaluationGroup(models.Model):
    class Meta:
        verbose_name = 'گروه ارزیابی'
        verbose_name_plural = 'ارزیابی ماهانه - گروه ارزیابی'
        ordering = ['id']

    user = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='evaluations', verbose_name='ارزیابی کننده')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    members = models.ManyToManyField(to=User, verbose_name='ارزیابی شوندگان')
    importance = models.PositiveSmallIntegerField(default=3, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='ضریب اهمیت')

    def __str__(self):
        return self.title

    @property
    @admin.display(ordering='تعداد ارزیابی شوندگان')
    def member_count(self):
        return self.members.count()


class Evaluation(models.Model):
    class Meta:
        verbose_name = 'ارزیابی ماهانه'
        verbose_name_plural = 'ارزیابی ماهانه'
        ordering = ['id']
        unique_together = ['group', 'year', 'month']

    group = models.ForeignKey(to=EvaluationGroup, on_delete=models.CASCADE, verbose_name='گروه ارزیابی')
    year = models.PositiveSmallIntegerField(choices=ChoicesYearList, verbose_name='سال')
    month = models.PositiveSmallIntegerField(choices=ChoicesMonthList, verbose_name='ماه')
    is_done = models.BooleanField(default=False, verbose_name='ارزیابی شد')

    def __str__(self):
        return f'{self.year}-{self.month} {self.group.title}'

    @property
    def evaluator(self):
        return self.group.user.get_full_name()


class EvaluationAnswer(models.Model):
    class Meta:
        verbose_name = 'ارزیابی'
        verbose_name_plural = 'ارزیابی'
        ordering = ['evaluation', 'rank']
        unique_together = ['evaluation', 'user']

    evaluation = models.ForeignKey(to=Evaluation, on_delete=models.CASCADE, related_name='answers', verbose_name='ارزیابی ماهانه')
    user = models.ForeignKey(to=User, on_delete=models.PROTECT, verbose_name='ارزیابی شونده')
    rank = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='رتبه عملکردی')
    performance = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='عملکرد')
    potential = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(1, 1), (2, 2), (3, 3)], verbose_name='قابلیت ارتقا')
    note = models.TextField(null=True, blank=True, verbose_name='شرح')

    def __str__(self):
        return self.user.get_full_name()


class EvaluationAnswerTimesheet(models.Model):
    answer = models.ForeignKey(to=EvaluationAnswer, on_delete=models.CASCADE, related_name='timesheets', verbose_name='ارزیابی')
    project = models.ForeignKey(to='prj.Project', on_delete=models.CASCADE, verbose_name='پروژه')
    percent = models.PositiveSmallIntegerField(default=0, verbose_name='درصد')

    def __str__(self):
        return self.project.title
