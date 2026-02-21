import time
import jdatetime
from django.db import models
from core.gsm import send_sms
from django.contrib import admin
from difflib import SequenceMatcher
from django.dispatch import receiver
from core.models import User, Post, Unit
from django_jalali.db import models as jmodels
from django_ckeditor_5.fields import CKEditor5Field
from rest_framework.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.contrib.postgres.fields import ArrayField
from core.choices import ChoicesJobStatus, ChoicesJobUrgency, ChoiceFlowFiledType, ChoiceDispatchIfType, \
    ChoicesFlowPatternType, ChoicesSessionColor, ChoicesConfirmRejectModify


class Room(models.Model):
    """اتاق جلسه"""
    class Meta:
        verbose_name = 'اتاق جلسه'
        verbose_name_plural = 'اتاق جلسه'
        ordering = ['id']

    title = models.CharField(max_length=50, verbose_name='عنوان')
    location = models.CharField(max_length=50, verbose_name='مکان')
    capacity = models.PositiveSmallIntegerField(verbose_name='ظرفیت')
    facilities = models.TextField(null=True, blank=True, verbose_name='امکانات')
    posts = models.ManyToManyField(to=Post, blank=True, verbose_name='پست‌های مجاز')
    public = models.BooleanField(default=True, verbose_name='عمومی')
    color = models.CharField(max_length=20, default='cyan-lighten-4', choices=ChoicesSessionColor, verbose_name='رنگ')

    def __str__(self):
        return self.title


class Session(models.Model):
    """جلسات"""
    class Meta:
        verbose_name = 'جلسه'
        verbose_name_plural = 'جلسات'
        ordering = ['-date']

    title = models.CharField(max_length=100, verbose_name='عنوان جلسه')
    project = models.ForeignKey(to='prj.Project', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پروژه')
    type = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(1, 'مهمانان ویژه'), (2, 'جلسه مدیریتی'), (3, 'جلسه کارشناسی')], verbose_name='نوع جلسه')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='sessions', verbose_name='مالک جلسه')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, related_name='sessions', verbose_name='واحد سازمانی')
    week = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='شماره هفته')
    date = jmodels.jDateField(verbose_name='تاریخ')
    start = models.DurationField(null=True, blank=True, verbose_name='آغاز')
    end = models.DurationField(null=True, blank=True, verbose_name='پایان')
    members = models.ManyToManyField(to=User, blank=True, verbose_name='حاضران جلسه')
    guests = ArrayField(base_field=models.CharField(max_length=100), default=list, blank=True, verbose_name='میهمانان')
    guest_count = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد میهمان')
    agenda = ArrayField(base_field=models.CharField(max_length=100), default=list, blank=True, verbose_name='دستور جلسه')
    sms = models.BooleanField(default=False, verbose_name='یادآوری پیامکی')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    cancel_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان اعلام لغو جلسه')
    # پذیرایی
    need_breakfast = models.BooleanField(default=False, verbose_name='درخواست صبحانه')
    need_lunch = models.BooleanField(default=False, verbose_name='درخواست ناهار')
    need_catering = models.BooleanField(default=False, verbose_name='درخواست پذیرایی')
    request_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان درخواست پذیرایی', help_text='با هربار ویرایش ریست میشود')
    need_manager = models.BooleanField(default=False, verbose_name='درخواست پذیرایی نیاز به تأیید مدیر واحد دارد')
    manager_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر مدیر واحد درمورد پذیرایی')
    manager_note = models.CharField(max_length=100, null=True, blank=True, verbose_name='توضیحات مدیر واحد')
    need_deputy = models.BooleanField(default=False, verbose_name='پذیرایی نیاز به تأیید معاونت دارد')
    deputy_accept = models.CharField(max_length=14, choices=ChoicesConfirmRejectModify, default='نامشخص', verbose_name='نظر معاون توسعه درمورد پذیرایی')
    deputy_note = models.CharField(max_length=100, null=True, blank=True, verbose_name='توضیحات معاون توسعه')
    order_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان بررسی', help_text='خالی یعنی هنوز بررسی نشده')
    breakfast = models.CharField(max_length=20, null=True, blank=True, verbose_name='صبحانه')
    lunch = models.CharField(max_length=20, null=True, blank=True, verbose_name='ناهار')
    catering = ArrayField(base_field=models.CharField(max_length=20), default=list, blank=True, verbose_name='پذیرایی')
    attendee_count = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد پذیرایی')
    breakfast_agents = models.ManyToManyField(to=User, blank=True, related_name='breakfast_sessions', verbose_name='مسئولان صبحانه')
    lunch_agents = models.ManyToManyField(to=User, blank=True, related_name='lunch_sessions', verbose_name='مسئولان ناهار')
    catering_agents = models.ManyToManyField(to=User, blank=True, related_name='catering_sessions', verbose_name='مسئولان پذیرایی')
    # فرآیند رزرو سالن جلسات عمومی
    place = models.CharField(max_length=100, null=True, blank=True, verbose_name='مکان برگزاری جلسه')
    room = models.ForeignKey(to=Room, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='اتاق')
    need_photography = models.BooleanField(default=False, verbose_name='نیاز به عکسبرداری')
    need_filming = models.BooleanField(default=False, verbose_name='نیاز به تصویربرداری')
    need_recording = models.BooleanField(default=False, verbose_name='نیاز به ضبط جلسه')
    need_news = models.BooleanField(default=False, verbose_name='نیاز به تهیه خبر')
    need_presentation = models.BooleanField(default=False, verbose_name='نیاز به ارائه')
    accept_room = models.BooleanField(null=True, blank=True, verbose_name='تأیید رزرو اتاق')
    accept_photography = models.BooleanField(null=True, blank=True, verbose_name='تأیید عکسبرداری')
    accept_filming = models.BooleanField(null=True, blank=True, verbose_name='تأیید تصویربرداری')
    accept_recording = models.BooleanField(null=True, blank=True, verbose_name='تأیید ضبط جلسه')
    accept_news = models.BooleanField(null=True, blank=True, verbose_name='تأیید تهیه خبر')
    accept_presentation = models.BooleanField(null=True, blank=True, verbose_name='تأیید ارائه')
    room_agents = models.ManyToManyField(to=User, blank=True, related_name='room_sessions', verbose_name='مسئولان هماهنگی سالن')
    photography_agents = models.ManyToManyField(to=User, blank=True, related_name='photography_sessions', verbose_name='مسئولان هماهنگی عکسبرداری')
    filming_agents = models.ManyToManyField(to=User, blank=True, related_name='filming_sessions', verbose_name='مسئولان هماهنگی تصویربرداری')
    recording_agents = models.ManyToManyField(to=User, blank=True, related_name='recording_sessions', verbose_name='مسئولان هماهنگی ضبط')
    news_agents = models.ManyToManyField(to=User, blank=True, related_name='news_sessions', verbose_name='مسئولان هماهنگی خبر')
    presentation_agents = models.ManyToManyField(to=User, blank=True, related_name='presentation_sessions', verbose_name='مسئولان هماهنگی ارائه')
    secretaries = models.ManyToManyField(to=User, blank=True, related_name='secretaries_sessions', verbose_name='دبیران جلسه')

    def __str__(self):
        return self.title

    @property
    def weekday(self):
        return self.date.j_weekdays_fa[self.date.weekday()]

    @property
    @admin.display(description='تعداد مصوبه')
    def approval_count(self):
        return self.approvals.count()

    @property
    def time(self):
        return f'{str(self.start)[:-3]}-{str(self.end)[:-3]}' if (self.start and self.end) else None

    @property
    def register_time(self):
        return self.create_time.strftime('%Y/%m/%d %H:%M')

    @property
    def member_count(self):
        return self.members.count()

    @property
    def is_room_approved(self):
        return self.room is None or self.accept_room is True

    @property
    def is_manager_approved(self):
        return (not self.need_manager) or self.manager_accept == 'تأیید'

    @property
    def is_deputy_approved(self):
        return (not self.need_deputy) or self.deputy_accept == 'تأیید'

    @property
    def is_fully_approved(self):
        return self.is_room_approved and self.is_manager_approved and self.is_deputy_approved


class Visitant(models.Model):
    class Meta:
        verbose_name = 'میهمانان جلسه'
        verbose_name_plural = 'میهمانان جلسه'
        ordering = ['id']

    session = models.ForeignKey(to=Session, on_delete=models.CASCADE, related_name='visitants', verbose_name='جلسه')
    name = models.CharField(max_length=100, verbose_name='نام')
    # با توجه به سناریوی جدید درخواست پذیرایی (تعیین جزئیات پذیرایی توسط خدادادی) این سه فیلد باید حذف شوند. صرفا برای حفط دیتای موجود حذف نشدند
    nf = models.ForeignKey(to='fd.NutritionFood', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='رزرو ناهار')
    nf_accept = models.BooleanField(null=True, blank=True, verbose_name='تأیید رزرو ناهار')
    lunch = models.CharField(max_length=30, null=True, blank=True, verbose_name='ناهار')

    def __str__(self):
        return self.name

    @property
    def lunch_name(self):
        return self.nf.food.name if self.nf else None

    def save(self, *args, **kwargs):
        if self.nf is None:
            self.nf_accept = None
        super().save(*args, **kwargs)


class SessionRate(models.Model):
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='session_rate', verbose_name='امتیاز دهنده')
    session = models.ForeignKey(to=Session, on_delete=models.CASCADE, related_name='session_user_rate', verbose_name='جلسه')
    rate = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'امتیاز جلسه'
        verbose_name_plural = 'امتیازهای چلسه'
        ordering = ['id']


class Approval(models.Model):
    """مصوبات"""
    class Meta:
        verbose_name = 'مصوبه'
        verbose_name_plural = 'مصوبات جلسات'
        ordering = 'id',

    session = models.ForeignKey(to=Session, on_delete=models.CASCADE, related_name='approvals', verbose_name='جلسه')
    title = models.TextField(verbose_name='عنوان')
    members = models.ManyToManyField(to=User, blank=True, verbose_name='مسئولان مصوبه')
    deadline = jmodels.jDateField(null=True, blank=True, verbose_name='مهلت اقدام')
    is_done = models.BooleanField(default=False, verbose_name='انجام شد', help_text='از وظیفه مربوطه آپدیت می‌شود')

    def __str__(self):
        return self.title


class Tag(models.Model):
    """تگ‌های شخصی برای وظایف"""
    class Meta:
        verbose_name = 'تگ'
        verbose_name_plural = 'تگ'
        ordering = ['order', 'id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='مالک')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    order = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

    @staticmethod
    def find_similar_tag(user, job_title, threshold=0.6):
        """
        پیدا کردن تگ مشابه بر اساس عنوان کار
        اگر تگی با شباهت بالای threshold پیدا شود، آن را برمی‌گرداند
        """
        if not job_title:
            return None

        user_tags = Tag.objects.filter(user=user)
        best_match = None
        best_ratio = 0

        for tag in user_tags:
            # محاسبه شباهت بین عنوان کار و عنوان تگ
            ratio = SequenceMatcher(None, job_title.lower(), tag.title.lower()).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = tag

        return best_match

    @staticmethod
    def find_exact_tag_match(user, tag_title):
        """
        پیدا کردن تگ دقیق بر اساس نام تگ
        اگر تگی با نام دقیقاً مشابه پیدا شود، آن را برمی‌گرداند
        """
        if not tag_title:
            return None

        try:
            return Tag.objects.get(user=user, title=tag_title)
        except Tag.DoesNotExist:
            return None

    @staticmethod
    def get_best_matching_tag(user, owner_tag_title=None, job_title=None):
        """
        پیدا کردن بهترین تگ مطابق برای کاربر
        ابتدا سعی می‌کند تگ دقیق با نام تگ مالک پیدا کند
        سپس سعی می‌کند تگ مشابه بر اساس عنوان کار پیدا کند
        """
        # ابتدا سعی می‌کنیم تگ دقیق با همان نام تگ مالک پیدا کنیم
        if owner_tag_title:
            exact_tag = Tag.find_exact_tag_match(user, owner_tag_title)
            if exact_tag:
                return exact_tag

        # اگر تگ دقیق پیدا نشد، سعی می‌کنیم تگ مشابه بر اساس عنوان کار پیدا کنیم
        if job_title:
            return Tag.find_similar_tag(user, job_title)

        return None


class FellowException(models.Model):
    """استثنائات ارجاع"""
    class Meta:
        verbose_name = 'استثناء'
        verbose_name_plural = 'استثنائات ارجاع'
        ordering = ['id']
        unique_together = ['fellower', 'fellowed']

    fellower = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='fellower', verbose_name='ارجاع دهنده')
    fellowed = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='fellowed', verbose_name='ارجاع گیرنده')

    def __str__(self):
        return self.fellower.get_full_name()


class Job(models.Model):
    """کار"""
    class Meta:
        verbose_name = 'کار'
        verbose_name_plural = 'کار'
        ordering = ['-id']

    project = models.ForeignKey(to='prj.Project', on_delete=models.CASCADE, default=1, verbose_name='پروژه')
    approval = models.OneToOneField(to=Approval, on_delete=models.CASCADE, null=True, blank=True, verbose_name='مصوبه')
    session = models.ForeignKey(to=Session, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True, verbose_name='جلسه', help_text='مربوط به وظایف رزرو سالن')
    title = models.CharField(max_length=400, verbose_name='عنوان')
    note = models.TextField(null=True, blank=True, verbose_name='شرح')
    deadline = jmodels.jDateField(null=True, blank=True, verbose_name='مهلت')
    status = models.CharField(max_length=20, choices=ChoicesJobStatus, default='todo', verbose_name='وضعیت')
    suspended = models.BooleanField(default=False, verbose_name='کار منتظر اقدام فرد دیکری است')
    urgency = models.PositiveSmallIntegerField(default=1, choices=ChoicesJobUrgency, verbose_name='فوریت')
    archive = models.BooleanField(default=False, verbose_name='بایگانی')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    done_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان انجام')
    confirm = models.BooleanField(default=False, verbose_name='تأیید انجام توسط مدیر')
    informees = models.ManyToManyField(to='core.User', blank=True, null=True, related_name='informees_job', verbose_name="مطلعین کار")
   # is_deleted = models.BooleanField(default=False, verbose_name="حذف شده")


    def __str__(self):
        return self.title

    @property
    @admin.display(description='مهلت')
    def respite(self):
        if not self.deadline:
            return None
        if isinstance(self.deadline, jdatetime.datetime):
            deadline = self.deadline
        else:
            deadline = str(self.deadline)
            deadline = jdatetime.date(int(deadline[:4]), int(deadline[5:7]), int(deadline[8:10]))
        return (deadline - jdatetime.datetime.now().date()).days

    def save(self, *args, **kwargs):
        if self.status == 'done' and self.done_time is None:
            self.done_time = jdatetime.datetime.now()
        if self.status != 'done':
            self.done_time = None
        super().save(*args, **kwargs)

    @property
    def has_chat(self):
        return bool(self.chats.count())


@receiver(signal=post_save, sender=Job)
def update_approval_is_done(sender, instance, **kwargs):
    job = instance
    if job.approval:
        job.approval.is_done = job.status == 'done'
        job.approval.save()


# هر Job چند Task دارد. فقط یکی از تسک‌ها مربوط به مسئول است، بقیه مربوط به افرادی که تسک به آنها ارجاع شده است
# علت این والد و فرزند سازی، سفارشی سازی ordering در فرانت است (با دراگ و دراپ)

class Task(models.Model):
    """وظیفه یا ارجاع ذیل کار"""
    class Meta:
        verbose_name = 'کار - ارجاع'
        verbose_name_plural = 'کار - ارجاع'
        ordering = ['order', 'id']
        unique_together = ['job', 'user']

    job = models.ForeignKey(to=Job, on_delete=models.CASCADE, related_name='tasks', verbose_name='کار')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='tasks', verbose_name='کاربر')
    tag = models.ForeignKey(to=Tag, on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True, verbose_name='تگ')
    is_owner = models.BooleanField(default=False, verbose_name='این کاربر مالک کار (دستور دهنده) است', help_text='هر کار فقط یک مالک دارد')
    is_committed = models.BooleanField(default=True, verbose_name='این کاربر مسئول انجام کار است', help_text='این فیلد برای وقتی که یک فرد به خودش ارجاع می‌دهد پیش‌بینی شده')
    is_seen = models.BooleanField(default=False, verbose_name='مشاهده شد', help_text='برای نمایش تعداد تسک جدید کاربر')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش در تگ')
    last_seen_chat = models.ForeignKey(to='pm.JobChat', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخرین گفتگوی مشاهده شده')
    create_time = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return self.job.title if self.job else '---'

    @property
    def owner(self):
        return self.job.tasks.get(is_owner=True).user

    @property
    def unseen_chat_count(self):
        return self.job.chats.filter(id__gt=self.last_seen_chat_id).count() if self.last_seen_chat_id else self.job.chats.count()


@receiver(signal=pre_save, sender=Task)
def after_task_save(sender, instance, **kwargs):
    # هر کار فقط یک مالک دارد
    if instance.is_owner:
        instance.job.tasks.update(is_owner=False)


class JobAppendix(models.Model):
    """پیوست و مستندات کار"""
    class Meta:
        verbose_name = 'کار - فایل پیوست'
        verbose_name_plural = 'کار - فایل پیوست'
        ordering = 'id',

    job = models.ForeignKey(to=Job, on_delete=models.CASCADE, related_name='appendices', verbose_name='کار')
    title = models.CharField(max_length=100, verbose_name='عنوان فایل')
    file = models.FileField(upload_to='job_appendix', verbose_name='فایل')

    def __str__(self):
        return self.title

    @property
    def file_url(self):
        return str(self.file)


class JobChat(models.Model):
    """گفتگوهای ذیل وظیفه"""
    class Meta:
        verbose_name = 'وظیفه - گفتگو'
        verbose_name_plural = 'وظیفه - گفتگو'
        ordering = ['-id']

    job = models.ForeignKey(to=Job, on_delete=models.CASCADE, related_name='chats', verbose_name='کار')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='فرستنده')
    body = models.TextField(null=True, blank=True, verbose_name='متن پیام')
    file = models.FileField(upload_to='chat_files', null=True, blank=True, verbose_name='فایل')
    send_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ارسال')

    def __str__(self):
        return self.body or '---'

    @property
    def file_url(self):
        return self.file.name if self.file else None

    def clean(self):
        if self.body is None and self.file is None:
            raise ValidationError('پیام بدون متن و فایل، قابل ذخیره نیست')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# مدل فرآیندها:
class FlowPatternType (models.Model):
    create_time = jmodels.jDateTimeField(auto_now_add=True)
    update_time = jmodels.jDateTimeField(auto_now=True)
    title = models.CharField(max_length=100, verbose_name='عنوان فرآیند')
    active = models.BooleanField(default=False, verbose_name='فرآیند فعال است')

    class Meta:
        verbose_name = 'Flow Type'
        verbose_name_plural = 'Flow Types'
        ordering = ['id']

    def __str__(self):
        return self.title


class FlowPattern(models.Model):
    """الگوی فرآیند"""
    class Meta:
        verbose_name = 'Flow'
        verbose_name_plural = 'Flows'
        ordering = ['id']

    title = models.CharField(max_length=100, verbose_name='عنوان فرآیند')
    type = models.CharField(max_length=50, default='فناوری اطلاعات', choices=ChoicesFlowPatternType, verbose_name='نوع')
    posts = models.ManyToManyField(to=Post, blank=True, verbose_name='پست‌های مجاز شروع فرآیند')
    form_width = models.PositiveSmallIntegerField(default=500, verbose_name='پهنای فرم')
    quota_per_user = models.PositiveSmallIntegerField(default=1, verbose_name='تعداد مجاز ثبت فرآیند توسط کاربر')
    active = models.BooleanField(default=False, verbose_name='فرآیند فعال است')
    preamble = CKEditor5Field(default='', verbose_name='مقدمه (توضیحات)', config_name='extends')
    poster = models.ImageField(null=True, blank=True, upload_to='flow_pattern', verbose_name='پوستر')
    image = models.ImageField(null=True, blank=True, upload_to='flow_pattern', verbose_name='شمای کلی فرآیند')
    flow_type = models.ForeignKey(FlowPatternType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class Field(models.Model):
    """الگوی فیلد"""
    class Meta:
        verbose_name = 'Field'
        verbose_name_plural = 'Fields'
        ordering = ['order', 'id']

    flow_pattern = models.ForeignKey(to=FlowPattern, on_delete=models.CASCADE, related_name='fields', verbose_name='فرآیند')
    label = models.CharField(max_length=100, verbose_name='عنوان')
    hint = models.CharField(max_length=100, null=True, blank=True, verbose_name='راهنما')
    type = models.CharField(max_length=12, choices=ChoiceFlowFiledType, verbose_name='نوع')
    choices = ArrayField(models.CharField(max_length=50), default=list, blank=True, verbose_name='انتخاب‌ها', help_text='مخصوص نوع «انتخاب»')
    table = models.CharField(max_length=50, null=True, blank=True, verbose_name='نام جدول', help_text='مخصوص سرستونهای جدول - می‌تواند در یک فرآیند چندین پاسخ داشته باشد')
    row_min = models.PositiveSmallIntegerField(default=1, verbose_name='تعداد حداقل ردیف', help_text='برای نوع «جدول»')
    row_max = models.PositiveSmallIntegerField(default=10, verbose_name='تعداد حداکثر ردیف', help_text='برای نوع «جدول»')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش در فرم')
    is_archived = models.BooleanField(default=False, verbose_name='بایگانی شده')

    def __str__(self):
        return self.label


class NodePattern(models.Model):
    """الگوی گره"""
    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'
        ordering = ['order', 'id']

    flow_pattern = models.ForeignKey(to=FlowPattern, on_delete=models.CASCADE, related_name='nodes', verbose_name='فرآیند')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    is_first = models.BooleanField(default=False, verbose_name='گره آغاز فرآیند')
    is_archived = models.BooleanField(default=False, verbose_name='بایگانی شده')
    is_bottleneck = models.BooleanField(default=False, verbose_name='گلوگاه')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش در فرم')
    next = models.ForeignKey(to='self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='گره بعدی', help_text='فقط وقتی که کاربر می‌خواهد ارجاع شوندگان را از fellowlist انتخاب کند. ضمناً باید گره بعدی، گره خاتمه باشد و ادامه پیدا نکند')
    sms = models.BooleanField(default=False, verbose_name='نیاز به یادآوری پیامکی')
    respite = models.PositiveSmallIntegerField(default=1, verbose_name='مهلت اقدام')

    def __str__(self):
        return self.title


class NodeField(models.Model):
    """تقاطع الگوی گره و الگوی فیلد"""
    class Meta:
        verbose_name = 'Node Field'
        verbose_name_plural = 'Node Field'
        ordering = ['field', 'id']
        unique_together = ['node', 'field']

    node = models.ForeignKey(to=NodePattern, on_delete=models.CASCADE, related_name='fields', verbose_name='گره')
    field = models.ForeignKey(to=Field, on_delete=models.CASCADE, verbose_name='فیلد')
    editable = models.BooleanField(default=False, verbose_name='قابل ویرایش')
    required = models.BooleanField(default=False, verbose_name='اجباری')

    def __str__(self):
        return self.field.label

    def clean(self):
        if self.field.flow_pattern != self.node.flow_pattern:
            raise ValidationError('این فیلد برای این فرآیند نیست')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(NodeField, self).save(*args, **kwargs)


class Dispatch(models.Model):
    """الگوی شرط"""
    class Meta:
        verbose_name = 'Dispatch'
        verbose_name_plural = 'Dispatch'
        ordering = ['id']

    start = models.ForeignKey(to=NodePattern, on_delete=models.CASCADE, related_name='dispatches_in', verbose_name='گره آغاز')
    end = models.ForeignKey(to=NodePattern, on_delete=models.CASCADE, related_name='dispatches_out', verbose_name='گره پایان')
    send_to_owner = models.BooleanField(default=False, verbose_name='ارسال به کاربر')
    send_to_parent = models.BooleanField(default=False, verbose_name='ارسال به مدیر مستقیم')
    send_to_manager = models.BooleanField(default=False, verbose_name='ارسال به مدیر واحد')
    send_to_posts = models.ManyToManyField(to=Post, blank=True, verbose_name='پست‌های مقصد')
    if_operator = models.CharField(max_length=3, choices=[('and', 'and'), ('or', 'or')], default='and', verbose_name='نوع شرط', help_text='برای حالت اتصال مشروط')

    def __str__(self):
        return self.start.title

    def clean(self):
        if self.start.flow_pattern != self.end.flow_pattern:
            raise ValidationError('آغاز و پایان اتصال باید مربوط به یک فرآیند باشد')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Dispatch, self).save(*args, **kwargs)


class DispatchIf(models.Model):
    """شرط"""
    class Meta:
        verbose_name = 'شرط'
        verbose_name_plural = 'شرط'
        ordering = ['id']

    dispatch = models.ForeignKey(to=Dispatch, on_delete=models.CASCADE, related_name='ifs', verbose_name='اتصال')
    type = models.CharField(max_length=20, choices=ChoiceDispatchIfType, verbose_name='نوع شرط')
    key = models.ForeignKey(to=Field, on_delete=models.CASCADE, verbose_name='فیلد شرط')
    value = models.CharField(max_length=100, null=True, blank=True, verbose_name='مقدار شرط')
    values = ArrayField(models.CharField(max_length=100), default=list, blank=True, verbose_name='مقادیر شرط')

    def clean(self):
        if self.key.flow_pattern != self.dispatch.start.flow_pattern:
            raise ValidationError('فیلد انتخاب شده برای این فرآیند نیست')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(DispatchIf, self).save(*args, **kwargs)


class Flow(models.Model):
    """فرآیند"""
    class Meta:
        verbose_name = 'فرآیند'
        verbose_name_plural = 'فرآیند'
        ordering = ['id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='flows', verbose_name='کاربر')
    flow_pattern = models.ForeignKey(to=FlowPattern, on_delete=models.CASCADE, related_name='flows', verbose_name='فرآیند')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    def __str__(self):
        return self.flow_pattern.title

    def user_name(self):
        return self.user.get_full_name()


class Node(models.Model):
    """گره"""
    class Meta:
        verbose_name = 'فرآیند'
        verbose_name_plural = 'فرآیند - گره'
        ordering = ['id']

    flow = models.ForeignKey(to=Flow, on_delete=models.CASCADE, related_name='nodes', verbose_name='درخواست')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='nodes', verbose_name='کاربر')
    post = models.ForeignKey(to=Post, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پست')
    node_pattern = models.ForeignKey(to=NodePattern, on_delete=models.CASCADE, related_name='nodes', verbose_name='گره')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    seen_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان مشاهده توسط کاربر')
    done_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان تأیید توسط کاربر')

    def __str__(self):
        return self.node_pattern.title

    @property
    def removable(self):
        return self.flow.nodes.exclude(user=self.user).filter(done_time__isnull=False).count() == 0

    @property
    def revertable(self):
        if self.done_time is None:
            return False
        ends = Dispatch.objects.filter(start=self.node_pattern).values_list('end', flat=True)
        return not Node.objects.filter(node_pattern_id__in=ends, flow=self.flow, create_time__gte=self.done_time, create_time__lt=(self.done_time+jdatetime.timedelta(seconds=1)), seen_time__isnull=False).exists()


class Answer(models.Model):
    """پاسخ فیلد"""
    class Meta:
        verbose_name = 'پاسخ'
        verbose_name_plural = 'فرآیند - پاسخ'
        ordering = ['id']

    flow = models.ForeignKey(to=Flow, on_delete=models.CASCADE, related_name='answers', verbose_name='درخواست')
    field = models.ForeignKey(to=Field, on_delete=models.CASCADE, related_name='answers', verbose_name='فیلد')
    body = models.TextField(null=True, blank=True, verbose_name='پاسخ')
    file = models.FileField(null=True, blank=True, upload_to='flow_files', verbose_name='')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='شماره ردیف در جدول')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    def __str__(self):
        return self.body if self.body else str(self.file)


@receiver(signal=post_save, sender=Answer)
def after_answer_save(sender, instance, created, **kwargs):
    # ارسال پیامک برای راننده و متقاضی در فرآیند درخواست خودرو
    try:
        if instance.body and instance.field_id == 2210 and Answer.objects.get(field_id=2212, flow=instance.flow).body == 'موافقت می شود.':
            start_time = Answer.objects.filter(field_id=2219, flow=instance.flow).first()
            if start_time is None:
                start_time = Answer.objects.get(field_id=2206, flow=instance.flow).body
            driver_personnel_code = instance.body.split('.')[0]
            driver = User.objects.filter(personnel_code=driver_personnel_code).first()
            # پیامک به راننده
            if driver:
                text = 'اطلاعات سفر\n'
                text += f'محدوده: {Answer.objects.filter(field_id=2274, flow=instance.flow).first().body}\n'
                text += f'نوع: {Answer.objects.filter(field_id=2311, flow=instance.flow).first().body}\n'
                text += f'مسافر: {Answer.objects.filter(field_id=2277, flow=instance.flow).first().body} - {instance.flow.user.post.unit.title}\n'
                text += f'زمان سفر: {start_time}\n'
                text += f'مقصد: {Answer.objects.get(field_id=2209, flow=instance.flow).body}\n'
                send_sms(mobile=driver.mobile, text=text, user_id=driver.id)
                time.sleep(3)
            # پیامک به متقاضی
            text = 'اطلاعات رزرو خودرو\n'
            text += f'راننده: {instance.body}\n'
            text += f'زمان سفر: {start_time}\n'
            text += f'مقصد: {Answer.objects.get(field_id=2209, flow=instance.flow).body}\n'
            if driver:
                text += f'راننده: {driver.get_full_name()} {driver.mobile}'
            send_sms(mobile=instance.flow.user.mobile, text=text, user_id=instance.flow.user.id)
    except Exception as e:
        print(e)


def archive_done_jobs_after_month():
    Job.objects.filter(status='done', done_time__isnull=False, done_time__lte=jdatetime.datetime.today() - jdatetime.timedelta(days=15)).update(archive=True)