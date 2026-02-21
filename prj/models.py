import jdatetime
from django.db import models
from django.contrib import admin
from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User, Unit, Post
from django_jalali.db import models as jmodels
from django.core.exceptions import ValidationError


class Mission(models.Model):
    """مأموریت‌ها"""
    class Meta:
        verbose_name = 'مأموریت'
        verbose_name_plural = 'مأموریت‌ها'
        ordering = ['id']

    title = models.CharField(max_length=1000, unique=True, verbose_name='عنوان')
    type = models.CharField(max_length=10, null=True, blank=True, choices=[('توصیه', 'توصیه'), ('مستمر', 'مستمر'), ('زمانمند', 'زمانمند')], verbose_name='نوع')
    realization_year = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='سال تحقق')

    def __str__(self):
        return self.title


class Project(models.Model):
    """برنامه‌ها"""
    class Meta:
        verbose_name = 'برنامه'
        verbose_name_plural = 'برنامه‌ها'
        ordering = ['year', 'priority', 'unit', 'id']

    year = models.PositiveSmallIntegerField(default=1404, choices=[(1403, 1403), (1404, 1404), (1405, 1405)], verbose_name='سال برنامه‌ای')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, related_name='projects', verbose_name='واحد')
    title = models.CharField(max_length=170, verbose_name='عنوان')
    missions = models.ManyToManyField(to=Mission, blank=True, verbose_name='مأموریت')
    priority = models.PositiveSmallIntegerField(default=1, choices=[(1, 1), (2, 2), (3, 3)], verbose_name='اولویت')
    priority_percentage = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="درصد اولویت در واحد")
    note = models.TextField(null=True, blank=True, verbose_name='شرح برنامه')
    team = models.ManyToManyField(to=User, blank=True, verbose_name='تیم پروژه')
    progress = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت')
    expected = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت مطلوب', help_text='هر روز آپدیت می‌شود')

    confirmed = models.BooleanField(default=False, verbose_name='تأیید اولیه')
    confirm_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تأیید اولیه')

    accepted = models.BooleanField(null=True, blank=True, verbose_name='تأیید شده')
    accept_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تأیید')
    accept_note = models.TextField(null=True, blank=True, verbose_name='شرح تأیید')

    approved = models.BooleanField(null=True, blank=True, verbose_name='تصویب شده')
    approve_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تصویب')
    approve_note = models.TextField(null=True, blank=True, verbose_name='شرح تصویب')

    create_time = jmodels.jDateTimeField(auto_now_add=True)
    modify_time = jmodels.jDateTimeField(auto_now=True)
    note1404 = models.TextField(null=True, blank=True, verbose_name='نکات اصلاحی')

    def __str__(self):
        return str(self.title)

    @property
    @admin.display(description='تخصیص')
    def allocation(self):
        return self.allocations.aggregate(val=models.Sum('amount'))['val'] or 0

    @property
    @admin.display(description='بودجه - میلیون تومان')
    def cost(self):
        return self.phases.aggregate(val=models.Sum('cost'))['val'] or 0

    @property
    def start(self):
        return str(self.phases.aggregate(val=models.Min('start'))['val'])

    @property
    def finish(self):
        return str(self.phases.aggregate(val=models.Max('finish'))['val'])

    @property
    @admin.display(description='تأخیر')
    def delay(self):
        return max(0, self.expected - self.progress)




class ProjectsTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='teams')
    participation_percentage = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'تیم پروژه'
        verbose_name_plural = 'تیم پروژه'

    def __str__(self):
        return f"{self.user} در برنامه {self.project}"




class ProjectOutcome(models.Model):
    """نتایج کلیدی / خروجی / Impact هر برنامه"""

    project = models.ForeignKey(
        to='Project',
        on_delete=models.CASCADE,
        related_name='outcomes',
        verbose_name='برنامه'
    )

    title = models.CharField(
        max_length=255,
        verbose_name='عنوان نتیجه'
    )

    value = models.CharField(max_length=250, verbose_name='مقدار')

    def __str__(self):
        return f"{self.project.title} - {self.title}"

    class Meta:
        verbose_name = 'نتیجه برنامه'
        verbose_name_plural = 'نتایج برنامه'


class Phase(models.Model):
    """اقدامات"""
    class Meta:
        verbose_name = 'اقدام'
        verbose_name_plural = 'اقدامات'
        ordering = ['project', 'step', ]

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name='phases', verbose_name='برنامه')
    title = models.CharField(max_length=200, verbose_name='فعالیت')
    type = models.CharField(max_length=10, choices=[('پژوهشی', 'پژوهشی'), ('اجرایی', 'اجرایی')], verbose_name='نوع')
    method = models.CharField(max_length=10, choices=[('برون‌سپاری', 'برون‌سپاری'), ('درون‌سپاری', 'درون‌سپاری'), ('ترکیبی', 'ترکیبی')], verbose_name='نحوه اجرا')
    step = models.SmallIntegerField(null=True, blank=True, verbose_name='ترتیب اقدام')
    priority = models.PositiveSmallIntegerField(default=1, choices=[(1, 1), (2, 2), (3, 3)], verbose_name='اولویت')
    importance = models.SmallIntegerField(default=1, verbose_name='اهمیت')
    cost = models.BigIntegerField(default=0, verbose_name='هزینه', help_text='میلیون تومان')
    start = jmodels.jDateField(verbose_name='آغاز')
    finish = jmodels.jDateField(verbose_name='پایان')
    hr = models.DecimalField(default=0, max_digits=6, decimal_places=2, verbose_name='نیروی انسانی مورد نیاز')
    ph = models.PositiveIntegerField(default=0, verbose_name='نفر ساعت')
    goal = models.CharField(max_length=200, verbose_name='هدف کمی')
    goal_value = models.CharField(max_length=200, null=True, blank=True, verbose_name="مقدار هدف کمی")
    progress = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت')
    expected = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت مطلوب')

    create_time = jmodels.jDateTimeField(auto_now_add=True)
    modify_time = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # def clean(self):
    #     if self.finish < self.start:
    #         raise ValidationError('تاریخ پایان نباید پیش از تاریخ آغاز باشد')

    def save(self, *args, **kwargs):
        self.full_clean()
        if self._state.adding:
            self.step = self.project.phases.count() + 1
        super(Phase, self).save(*args, **kwargs)

    @property
    @admin.display(description='تأخیر')
    def delay(self):
        return max(0, self.expected - self.progress)

    @property
    def report_count(self):
        return self.reports.count()


class PhaseTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phases')
    phase = models.ForeignKey(to=Phase, on_delete=models.CASCADE, related_name='teams')
    participation_percentage = models.PositiveSmallIntegerField()


    class Meta:
        verbose_name = 'تیم فاز'
        verbose_name_plural = 'تیم فاز'

    def __str__(self):
        return f"{self.user} در فاز {self.phase}"


class Report(models.Model):
    """گزارش پیشرفت"""
    class Meta:
        verbose_name = 'گزارش'
        verbose_name_plural = 'گزارش پیشرفت'
        ordering = ['-id']

    phase = models.ForeignKey(to=Phase, on_delete=models.CASCADE, related_name='reports', verbose_name='فاز')
    claim_note = models.TextField(verbose_name='شرح گزارش')
    claim_date = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ گزارش')
    progress_claimed = models.PositiveSmallIntegerField(verbose_name='پیشرفت اعلام شده')

    accepted = models.BooleanField(null=True, blank=True, verbose_name='تأیید')
    progress_accepted = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='پیشرفت مورد تأیید')
    accept_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تأیید')
    accept_note = models.TextField(null=True, blank=True, verbose_name='شرح تأیید')

    approved = models.BooleanField(null=True, blank=True, verbose_name='تصویب')
    progress_approved = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='پیشرفت مصوب')
    approve_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تصویب')
    approve_note = models.TextField(null=True, blank=True, verbose_name='شرح تصویب')

    def save(self, *args, **kwargs):
        if self.pk:
            initial = Report.objects.filter(pk=self.pk).first()
            if initial.accepted is None and self.accepted is not None:
                self.accept_date = jdatetime.datetime.now().date()
            if initial.approved is None and self.approved is not None:
                self.approve_date = jdatetime.datetime.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phase.title


@receiver(signal=post_save, sender=Report)
def update_phase_and_project_and_unit_progress(sender, instance, **kwargs):
    if instance.approved:
        phase = instance.phase
        last_report = phase.reports.order_by('id').filter(approved=True).last()
        phase.progress = last_report.progress_approved
        phase.save()
        project = phase.project
        project.progress = round((project.phases.annotate(val=F('progress') * F('importance')).aggregate(sum=Sum('val'))['sum'] or 0) / 100)
        project.save()
        unit = project.unit
        unit.progress = round(unit.projects.filter(year=1404).aggregate(sum=Sum('progress'))['sum'] or 0) / max(unit.projects.count(), 1)
        unit.save()
        # معاونت توسعه خودش برنامه ندارد و پیشرفت ش میانگین پیشرفت ادارات کل تابعه است
        if unit.id in [20, 21, 22]:
            unit2 = Unit.objects.get(pk=7)
            unit2.progress = round(Project.objects.filter(unit_id__in=[20, 21, 22], year=1404).aggregate(sum=Sum('progress'))['sum'] or 0) / max(Project.objects.filter(unit_id__in=[20, 21, 22]).count(), 1)
            unit2.save()


class ReportAppendix(models.Model):
    """پیوست گزارش"""
    class Meta:
        verbose_name = 'پیوست گزارش'
        verbose_name_plural = 'پیوست گزارش'
        ordering = ['id']

    report = models.ForeignKey(to=Report, on_delete=models.CASCADE, related_name='appendices', verbose_name='گزارش')
    file = models.FileField(upload_to='report_files', verbose_name='فایل')

    def __str__(self):
        return self.file.name


class DailyUpdateLog(models.Model):
    """لاگ به‌روزرسانی روزانه پیشرفت مورد انتظار فازها و پروژه‌ها"""
    class Meta:
        verbose_name = 'لاگ'
        verbose_name_plural = 'لاگ به‌روزرسانی روزانه'
        ordering = ['-start']

    start = jmodels.jDateTimeField(auto_now_add=True, verbose_name='آغاز')
    finish = jmodels.jDateTimeField(null=True, blank=True, verbose_name='پایان')
    updated_count = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد پروژه به‌روز شده')

    def __str__(self):
        return str(self.start)


def daily_update():
    """به‌روزرسانی روزانه پیشرفت مورد انتظار فازها و پروژه‌ها"""
    log = DailyUpdateLog.objects.create()
    today = jdatetime.datetime.now().date()
    # به‌روزرسانی پیشرفت مطلوب فازها
    for phase in Phase.objects.all():
        phase.expected = max(0, min(100, round((today - phase.start).days * 100 / max(1, (phase.finish - phase.start).days))))
        phase.save()
    # به‌روزرسانی پیشرفت مطلوب پروژه‌ها
    for project in Project.objects.all():
        project.expected = (project.phases.annotate(val=F('expected') * F('importance')).aggregate(sum=Sum('val'))['sum'] or 0) / 100
        project.save()
    # به‌روزرسانی پیشرفت مطلوب نقطه‌ای واحدها
    for unit in Unit.objects.all():
        projects = unit.projects.filter(year=today.year)
        unit.expected = (projects.aggregate(sum=Sum('expected'))['sum'] or 0) / max(projects.count(), 1)
        unit.save()
    # معاونت توسعه خودش برنامه ندارد و پیشرفت ش میانگین پیشرفت ادارات کل تابعه است
    unit = Unit.objects.get(pk=7)
    projects = Project.objects.filter(unit_id__in=[20, 21, 22])
    unit.expected = (projects.aggregate(sum=Sum('expected'))['sum'] or 0) / max(projects.count(), 1)
    unit.save()
    log.updated_count = Project.objects.all().count()
    log.finish_expected = jdatetime.datetime.now()
    log.save()


class Allocation(models.Model):
    """پرداخت"""
    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت'
        ordering = ['-id']

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name='allocations', verbose_name='برنامه')
    title = models.CharField(max_length=200, verbose_name='شرح پرداخت')
    date = jmodels.jDateField(verbose_name='تاریخ')
    amount = models.PositiveBigIntegerField(verbose_name='مبلغ')

    def __str__(self):
        return '{} - {} میلیون تومان'.format(self.project.title, self.amount)


class Document(models.Model):
    class Meta:
        verbose_name = 'سند راهبردی'
        verbose_name_plural = 'سند راهبردی'
        ordering = ['id']

    title = models.CharField(max_length=200, verbose_name='اقدام کلان')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, verbose_name='واحد متولی')
    trustee = models.CharField(max_length=200, verbose_name='دستگاه متولی')
    get_draft = models.BooleanField(default=False, verbose_name='دریافت پیش‌نویس')
    post_to_colleagues = models.BooleanField(default=False, verbose_name='ارسال به دستگاه‌های همکار')
    post_comments = models.BooleanField(default=False, verbose_name='ارسال نظرات به اعضا')
    committee_approve = models.BooleanField(default=False, verbose_name='بررسی در کمیته')
    post_to_commission = models.BooleanField(default=False, verbose_name='بررسی در کمیسیون')
    commission_approve = models.BooleanField(default=False, verbose_name='تصویب در کمیسیون')
    post_to_approval_authority = models.BooleanField(default=False, verbose_name='بررسی در مرجع')
    approve = models.BooleanField(default=False, verbose_name='تصویب در مرجع')
    approval_authority = models.CharField(max_length=100, verbose_name='مرجع تصویب')
    status = models.TextField(null=True, blank=True, verbose_name='آخرین وضعیت')

    def __str__(self):
        return self.title


class DocumentColleague(models.Model):
    class Meta:
        verbose_name = 'دستگاه همکار'
        verbose_name_plural = 'دستگاه همکار'
        ordering = ['id']

    document = models.ForeignKey(to=Document, on_delete=models.CASCADE, verbose_name='سند راهبردی')
    title = models.CharField(max_length=100, verbose_name='دستگاه')
    commented = models.BooleanField(default=False, verbose_name='ارسال نظر')

    def __str__(self):
        return self.title


class DocumentLog(models.Model):
    class Meta:
        verbose_name = 'لاگ اقدامات'
        verbose_name_plural = 'لاگ اقدامات'
        ordering = ['id']

    document = models.ForeignKey(to=Document, on_delete=models.CASCADE, verbose_name='سند راهبردی')
    step = models.CharField(max_length=20, choices=[('دریافت پیش‌نویس', 'دریافت پیش‌نویس'), ('ارسال نظرات به اعضا', 'ارسال نظرات به اعضا'), ('ارسال به کمیسیون', 'ارسال به کمیسیون'), ('ارسال به مرجع تصویب', 'ارسال به مرجع تصویب'), ('تصویب در مرجع', 'تصویب در مرجع')], verbose_name='')
    note = models.TextField(verbose_name='شرح')
    date = jmodels.jDateField(verbose_name='تاریخ')
