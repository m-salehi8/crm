import os
import jdatetime
from .colors import *
from .choices import *
from io import BytesIO
from django import forms
from django.apps import apps
from django.db import models
from django.contrib import admin
from django.dispatch import receiver
from django.db.models import Q, Count
from django_jalali.db import models as jmodels
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, Group
from rest_framework.pagination import PageNumberPagination


class ModifiedArrayField(ArrayField):
    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
            "widget": forms.CheckboxSelectMultiple,
            **kwargs
        }
        return super(ArrayField, self).formfield(**defaults)


class Theme(models.Model):
    class Meta:
        verbose_name = 'تم'
        verbose_name_plural = 'تم‌های پیشفرض'
        ordering = ['id']

    title = models.CharField(max_length=50, verbose_name='نام')
    bg = models.ImageField(upload_to='theme_bg', verbose_name='عکس زمینه')
    main = models.CharField(max_length=7, verbose_name='رنگ اصلی')
    tint1 = models.CharField(max_length=7, verbose_name='رنگ 1')
    tint2 = models.CharField(max_length=7, verbose_name='رنگ 2')
    tint3 = models.CharField(max_length=7, verbose_name='رنگ 3')

    def __str__(self):
        return self.title

    @property
    def bg_url(self):
        return self.bg.name if self.bg else None


class Unit(models.Model):
    """واحدهای سازمانی"""
    class Meta:
        verbose_name = 'واحد'
        verbose_name_plural = 'واحدهای سازمانی'
        ordering = ['id']

    title = models.CharField(max_length=80, unique=True, verbose_name='نام')
    parent = models.ForeignKey(to='self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='واحد مافوق', help_text='مانند مدیریتهای ذیل معاونت')
    progress = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت')
    expected = models.PositiveSmallIntegerField(default=0, verbose_name='پیشرفت مطلوب', help_text='هر روز آپدیت می‌شود')
    overtime_quota = models.PositiveSmallIntegerField(default=0, verbose_name='سقف اضافه کار واحد')
    bonus_quota = models.PositiveBigIntegerField(default=0, verbose_name='سقف تشویقی واحد')
    overtime_bonus_open = models.BooleanField(default=False, verbose_name='قفل ویرایش اضافه کار و تشویقی')
    note1404 = models.TextField(null=True, blank=True, verbose_name='نکات اصلاحی')
    missions = models.ManyToManyField(to='prj.Mission', blank=True, related_name='units', verbose_name='مأموریت‌ها')

    def __str__(self):
        return self.title

    @property
    @admin.display(description='تأخیر')
    def delay(self):
        return max(0, self.expected - self.progress)

    @property
    def department(self):
        return self.parent or self

    @property
    @admin.display(description='تعداد پرسنل')
    def personnel_count(self):
        return User.objects.filter(post__unit=self).count()

    @property
    def work_personnel_count(self):
        now = jdatetime.datetime.now()
        return apps.get_model('hr', 'Work').objects.filter(year=now.year, month=now.month).filter(Q(user__post__unit=self) | Q(user__post__unit__parent=self)).filter(user__profile__is_advisor=False).count()

    @property
    def manager(self):
        if self.id == 1:
            return Post.objects.get(pk=2).active_user
        return Post.objects.filter(unit=self, is_manager=True).exclude(parent__unit=self).first().active_user


class Post(models.Model):
    """پست سازمانی"""
    class Meta:
        verbose_name = 'پست'
        verbose_name_plural = 'پست سازمانی'
        ordering = ['id']

    title = models.CharField(max_length=80, unique=True, verbose_name='عنوان')
    level = models.CharField(max_length=20, choices=ChoicesPostLevel, verbose_name='رده شغلی')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, related_name='posts', verbose_name='واحد')
    locations = models.ManyToManyField(to=Unit, blank=True, related_name='staffs', verbose_name='محل خدمت')
    parent = models.ForeignKey(to='self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مافوق')
    is_deputy = models.BooleanField(default=False, verbose_name='عضو شورای معاونان')
    is_manager = models.BooleanField(default=False, verbose_name='مدیر')
    position = models.CharField(max_length=20, choices=ChoicesPostPosition, verbose_name='موقعیت', help_text='ساختمان و طبقه')
    tell_local = models.CharField(max_length=20, null=True, blank=True, verbose_name='تلفن داخلی')
    tell = models.CharField(max_length=20, null=True, blank=True, verbose_name='خط مستقیم')

    def __str__(self):
        return self.title

    @property
    def active_user(self):
        return self.user if User.objects.filter(post=self).exists() else None

    @property
    @admin.display(description='نام کاربر فعلی')
    def active_user_name(self):
        return self.user.get_full_name() if User.objects.filter(post=self).exists() else None

    @property
    def active_user_photo(self):
        return self.user.photo_url if User.objects.filter(post=self).exists() else None

    @property
    def department(self):
        return self.unit.parent or self.unit


class User(AbstractUser):
    """کاربر"""
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربر'
        ordering = ['is_superuser', 'id']

    mobile = models.CharField(max_length=11, verbose_name='تلفن همراه')
    photo = models.ImageField(null=True, blank=True, upload_to='user_photo/', verbose_name='تصویر')
    thumbnail = models.ImageField(null=True, blank=True, upload_to='user_photo/thumbnail/', verbose_name='تصویر کوچک')
    post = models.OneToOneField(to=Post, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پست')
    personnel_code = models.PositiveSmallIntegerField(unique=True, null=True, blank=True, verbose_name='کد پرسنلی')
    nc = models.CharField(null=True, blank=True, verbose_name='کد ملی')
    birth_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تولد')
    is_interim = models.BooleanField(default=False, verbose_name='کاربر موقت')
    theme = models.ForeignKey(to=Theme, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='تم')
    bg = models.ImageField(null=True, blank=True, upload_to='user_bg', verbose_name='عکس زمینه')
    main = models.CharField(max_length=7, null=True, blank=True, verbose_name='رنگ اصلی')
    tint1 = models.CharField(max_length=7, null=True, blank=True, verbose_name='رنگ 1')
    tint2 = models.CharField(max_length=7, null=True, blank=True, verbose_name='رنگ 2')
    tint3 = models.CharField(max_length=7, null=True, blank=True, verbose_name='رنگ 3')
    menu_order = models.CharField(max_length=200, default='chat,flow,task,calendar,food,timesheet,food-manager,flow-manager,invoice,project,report,contract,allocation,pay,proclamation,article', editable=False, verbose_name='ترتیب نمایش آیتمهای منو')
    signature = models.ImageField(null=True, blank=True, upload_to="users_signature/", verbose_name="تصویر امضا")


    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.personnel_code})'

    @property
    def signature_url(self):
        if self.signature:
            return f"http://it.local/media/{self.signature}"
        return ""

    @property
    def photo_url(self):
        #  به تشخیص حراست عکسهای باکیفیت پرسنلی نباید ارسال بشه
        if self.photo and self.photo == f'user_photo/{self.personnel_code}.jpg':
            return self.thumbnail.name if self.thumbnail else 'user.png'
        return self.photo.name if self.photo else 'user.png'

    @property
    def thumbnail_url(self):
        return self.thumbnail.name if self.thumbnail else 'user.png'

    @property
    def is_head_of_unit(self):
        return self.post and self.post.parent and (self.post.parent.unit != self.post.unit or self.post.parent_id == 1)

    @property
    @admin.display(description='نام')
    def name(self):
        return self.get_full_name()

    @property
    def unit(self):
        return self.post.unit.parent_id or self.post.unit_id

    @property
    def unit_title(self):
        return self.post.unit.parent.title if self.post.unit.parent else self.post.unit.title

    @property
    def subunit(self):
        return self.post.unit_id if self.post.unit.parent else 0

    @property
    def todo_task(self):
        return self.tasks.filter(is_seen=False, is_committed=True, is_owner=False, job__archive=False).count()

    @property
    def todo_chat(self):
        _ = 0
        for m in self.member_set.filter(is_mute=False):
            _ += m.unseen_count
        return _

    @property
    def todo_flow(self):
        return self.nodes.filter(done_time=None).count()

    @property
    def todo_invoice(self):
        _ = self.invoicecover_set.filter(Q(confirm1=False) | Q(confirm2=False) | Q(confirm3=False) | Q(accepted=False))
        if self.groups.filter(name='invoice-confirm1').exists():
            _ = _ | apps.get_model('fn.InvoiceCover').objects.filter(locked=True, confirm1=None)
        if self.post.parent and self.post and self.post.parent and (self.post.parent.unit != self.post.unit or self.post.parent_id == 1):  # head of unit:
            _ = _ | apps.get_model('fn.InvoiceCover').objects.filter(unit=self.post.unit, confirm1=True, confirm2=None)
        if self.groups.filter(name='invoice-confirm3').exists():
            _ = _ | apps.get_model('fn.InvoiceCover').objects.filter(confirm2=True, confirm3=None)
        if self.groups.filter(name='invoice-accept').exists():
            _ = _ | apps.get_model('fn.InvoiceCover').objects.filter(confirm3=True, accepted=None)
        if self.groups.filter(name='invoice-deposit').exists():
            _ = _ | apps.get_model('fn.InvoiceCover').objects.filter(accepted=True, deposit_time=None)
        return _.distinct().count()

    @property
    def todo_timesheet(self):
        return apps.get_model('hr.Work').objects.exclude(user_id=self.id).filter(year=jdatetime.datetime.now().year, month=jdatetime.datetime.now().month).filter(Q(user__post__unit=self.post.unit) | Q(user__post__unit__parent=self.post.unit)).filter(bonus=0, overtime=0, percent=0).count()

    @property
    def todo_project(self):
        if self.groups.filter(name='pm').exists():
            return apps.get_model('prj.Project').objects.filter(approved=False, unit=self.post.unit).count() + (apps.get_model('prj.Project').objects.filter(accepted=True, approved=None).count() if self.groups.filter(name='project').exists() else 0)
        return 0

    @property
    def todo_report(self):
        if self.groups.filter(name='control').exists():
            return apps.get_model('prj.Report').objects.filter(approved=None).count()
        return 0

    def todo_contract_list(self):
        if self.post is None or not self.groups.filter(name='pm').exists():
            return apps.get_model('cn.Contract').objects.none()
        _ = self.contracts.filter(Q(manager_accept='عودت جهت اصلاح') | Q(fund_accept='عودت جهت اصلاح') | Q(convention_accept='عودت جهت اصلاح') | Q(committee_accept='عودت جهت اصلاح') | Q(deputy_accept='عودت جهت اصلاح') | Q(head_accept='عودت جهت اصلاح') | Q(drafted=True, draft_accept=None))
        if self.post.parent and (self.post.parent.unit != self.post.unit or self.post.parent_id == 1):  # مدیر واحد
            _ = _ | apps.get_model('cn.Contract').objects.filter(project__unit=self.post.unit).filter(locked=True, manager_accept='نامشخص')
        if self.groups.filter(name='contract-fund-accept').exists():  # مدیرکل بودجه
            _ = _ | apps.get_model('cn.Contract').objects.filter(manager_accept='تأیید', fund_accept='نامشخص')
        if self.groups.filter(name='contract-admin').exists():  # واحد قراردادها
            _ = _ | apps.get_model('cn.Contract').objects.filter(Q(fund_accept='تأیید', convention_accept='نامشخص') | Q(head_accept='تأیید', drafted=False) | Q(draft_accept=False) | Q(draft_accept=True, send_to_contractor_date=None) | Q(send_to_contractor_date__isnull=False, receive_from_contractor_date=None) | Q(receive_from_contractor_date__isnull=False, signature_date=None) | Q(signature_date__isnull=False, secretariat_date=None))
        if self.groups.filter(name='contract-committee-accept').exists():  # دبیر کمیته پژوهش
            _ = _ | apps.get_model('cn.Contract').objects.filter(convention_accept='تأیید', need_committee=True, committee_accept='نامشخص')
        if self.groups.filter(name='contract-deputy-accept').exists():  # معاون توسعه
            _ = _ | apps.get_model('cn.Contract').objects.filter(convention_accept='تأیید', need_committee=False, deputy_accept='نامشخص')
        if self.groups.filter(name='contract-head-accept').exists():  # رئیس مرکز
            _ = _ | apps.get_model('cn.Contract').objects.filter(deputy_accept='تأیید', head_accept='نامشخص')
        if self.groups.filter(name='contract-warranty-select').exists():  # کارشناس مالی، تعیین نوع ضمانتنامه
            _ = _ | apps.get_model('cn.Contract').objects.filter(secretariat_date__isnull=False, warranty_type=None)
        if self.groups.filter(name='contract-warranty-add').exists():  # کارشناس مالی، الصاق ضمانتنامه
            _ = _ | apps.get_model('cn.Contract').objects.filter(warranty_type__isnull=False, f_warranty__in=['', None])
        return _.distinct()

    @property
    def todo_contract(self):
        return self.todo_contract_list().count()

    def todo_pay_list(self):
        if self.post is None or not self.groups.filter(name='pm').exists():
            return apps.get_model('cn.Pay').objects.none()
        _ = self.pays.filter(locked=False)
        if self.post.parent and (self.post.parent.unit != self.post.unit or self.post.parent_id == 1):  # head of unit
            _ = _ | apps.get_model('cn.Pay').objects.filter(step__contract__project__unit=self.post.unit, locked=True, manager_accept='نامشخص')
        if self.groups.filter(name='contract-admin').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(manager_accept='تأیید', convention_accept='نامشخص')
        if self.groups.filter(name='contract-fund-accept').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(convention_accept='تأیید', fund_accept='نامشخص')
        if self.groups.filter(name='contract-warranty-add').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(fund_accept='تأیید', clerk_accept='نامشخص')
        if self.groups.filter(name='contract-deputy-accept').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(clerk_accept='تأیید', deputy_accept='نامشخص')
        if self.groups.filter(name='contract-head-accept').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(deputy_accept='تأیید', head_accept='نامشخص', need_head=True)
        if self.groups.filter(name='contract-finance-accept').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(Q(need_head=True, head_accept='تأیید') | Q(need_head=False, deputy_accept='تأیید')).filter(finance_accept='نامشخص')
        if self.groups.filter(name='contract-pay-audit').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(finance_accept='تأیید', audit='نامشخص')
        if self.groups.filter(name='contract-pay-deposit').exists():
            _ = _ | apps.get_model('cn.Pay').objects.filter(audit='تأیید', paid=None)
        return _.distinct()

    @property
    def todo_pay(self):
        return self.todo_pay_list().count()

    def todo_session_list(self):
        if self.post is None:
            return apps.get_model('pm', 'Session').objects.none()
        _ = self.sessions.filter(Q(manager_accept='عودت جهت اصلاح') | Q(deputy_accept='عودت جهت اصلاح'))
        if self.is_head_of_unit:
            _ = _ | apps.get_model('pm', 'Session').objects.filter(need_manager=True, manager_accept='نامشخص').filter(Q(unit=self.post.unit) | Q(unit=self.post.unit.parent))
        if self.groups.filter(name='contract-deputy-accept').exists():
            _ = _ | apps.get_model('pm', 'Session').objects.filter(need_deputy=True, deputy_accept='نامشخص')
        if self.groups.filter(name='room_catering').exists():
            _ = (_ | apps.get_model('pm', 'Session')
                 .objects.filter(Q(room=None) | Q(room__public=False) | Q(accept_room=True))
                 .filter(Q(need_breakfast=True) | Q(need_lunch=True) | Q(need_catering=True))
                 .filter(Q(need_manager=False, need_deputy=False, order_time=None) | Q(need_manager=True, manager_accept='تأیید', need_deputy=False, order_time=None) | Q(need_deputy=True, deputy_accept='تأیید', order_time=None)))
        return _.distinct()

    @property
    def todo_calendar(self):
        if self.groups.filter(name='room_admin').exists():
            n = apps.get_model('pm.Session').objects.filter(room__public=True, accept_room=None).count()
        else:
            n = 0
        return n + self.todo_session_list().count()

    @property
    def todo_evaluate(self):
        today = jdatetime.date.today()
        return apps.get_model('hr', 'Evaluation').objects.filter(group__user=self, year=today.year, month=today.month, is_done=False).count()

    def save(self, *args, **kwargs):
        if self.photo and self.photo != User.objects.get(pk=self.pk).photo:
            file_name, file_extension = os.path.splitext(self.photo.name)
            file_extension = file_extension.lower()
            image = Image.open(self.photo)
            image.thumbnail((100, 100), Image.LANCZOS)
            thumb_filename = file_name + '_thumb' + file_extension
            temp_thumb = BytesIO()
            image.convert('RGB').save(temp_thumb, 'JPEG')
            temp_thumb.seek(0)
            # set save=False, otherwise it will run in an infinite loop
            self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
            temp_thumb.close()
        if self.bg:
            pass
        else:
            self.bg = None
            self.main = None
            self.tint1 = None
            self.tint2 = None
            self.tint3 = None
        super(User, self).save(*args, **kwargs)

    @property
    def bg_url(self):
        return self.bg.name if self.bg else None

    def computer_ip(self):
        computer = Computer.objects.filter(user=self).first()
        if computer:
            return computer.ip
        return None


@receiver(signal=post_save, sender=User)
def after_user_save(sender, instance, created, **kwargs):
    # create user profile:
    if created:
        apps.get_model('hr.Profile').objects.create(id=instance.id, user=instance)
    """سیگنال برای آپدیت خودکار رنگ‌ها پس از ذخیره"""
    if hasattr(instance, 'bg') and instance.bg:
        try:
            image_path = instance.bg.path
            if os.path.exists(image_path):
                # استخراج و ذخیره رنگ‌ها
                dominant_color = get_dominant_color(image_path)
                main = "#{:02x}{:02x}{:02x}".format(*dominant_color)
                tint1, tint2, tint3 = generate_theme_colors(dominant_color)
                instance.tint1 = tint1
                instance.tint2 = tint2
                instance.tint3 = tint3
                # جلوگیری از حلقه‌ی بی‌نهایت با استفاده از update
                sender.objects.filter(pk=instance.pk).update(main=main, tint1=tint1, tint2=tint2, tint3=tint3)
        except Exception as e:
            print(f"Error updating theme colors: {e}")


class Key(models.Model):
    class Meta:
        verbose_name = 'کلید'
        verbose_name_plural = 'کلیدهای سامانه'
        ordering = ['id']

    key = models.CharField(max_length=50, unique=True, verbose_name='کلید')
    value = models.CharField(max_length=50, verbose_name='مقدار')
    description = models.CharField(max_length=200, verbose_name='شرح')

    def __str__(self):
        return self.key


class Proclamation(models.Model):
    """اطلاعیه‌ها"""
    class Meta:
        verbose_name = 'اطلاعیه'
        verbose_name_plural = 'اطلاعیه'
        ordering = ['-id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    unit = models.ForeignKey(to=Unit, on_delete=models.CASCADE, verbose_name='واحد')
    type = models.CharField(max_length=20, choices=ChoicesProclamationType, default='اطلاعیه', verbose_name='نوع')
    title = models.CharField(max_length=100, verbose_name='عنوان')
    body = CKEditor5Field(null=True, blank=True, verbose_name='متن', config_name='extends')
    poster = models.ImageField(null=True, blank=True, upload_to='proclamation/poster', verbose_name='پوستر')
    thumbnail = models.ImageField(null=True, blank=True, upload_to='proclamation/thumbnail/', verbose_name='تصویر کوچک')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    display_duration = models.PositiveBigIntegerField(null=True, blank=True, choices=ChoicesProclamationDisplayDuration, verbose_name='مدت نمایش')
    expire_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ انقضا')
    main_page_order = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="الویت نمابش در صفحه اول")
    view_count = models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')

    def increment_view_count(self, user):
        print("*" * 10)
        """افزایش تعداد بازدید برای کاربر مشخص (فقط یکبار برای هر کاربر)"""
        # بررسی اینکه آیا کاربر قبلاً این اطلاعیه را دیده است یا نه
        view, created = ProclamationSeen.objects.get_or_create(
            user=user,
            proclamation=self,
            defaults={'create_time': jdatetime.datetime.now().date()}
        )

        # اگر بازدید جدید است، تعداد بازدید را افزایش بده
        if created:
            print("&&"*10)
            self.view_count += 1
            self.save(update_fields=['view_count'])

        return created

    def has_user_viewed(self, user):
        """بررسی اینکه آیا کاربر این اطلاعیه را دیده است یا نه"""
        return ProclamationSeen.objects.filter(user=user, proclamation=self).exists()

    def get_viewed_users(self):
        """دریافت لیست کاربرانی که این اطلاعیه را دیده‌اند"""
        return ProclamationSeen.objects.filter(proclamation=self).select_related('user')

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        if self.type == 'فرانما':
            return '/faranama.png'
        first_gallery_image = self.gallery.first()
        if first_gallery_image:
            return first_gallery_image.file.name
        return 'df.png'





    @property
    def thumbnail_url(self):
        return self.thumbnail.name if self.thumbnail else 'information.png'

    @property
    def _time(self):
        return self.create_time.strftime('%Y/%m/%d %H:%M')

    @property
    def seen_count(self):
        return self.proclamationseen_set.count()

    @property
    @admin.display(description='زمان انتشار')
    def publish_time(self):
        return self.create_time.strftime('%Y-%m-%d %H:%M')

    def save(self, *args, **kwargs):
        if self.poster and self.poster != Proclamation.objects.get(pk=self.pk).poster:
            file_name, file_extension = os.path.splitext(self.poster.name)
            file_extension = file_extension.lower()
            image = Image.open(self.poster)
            image.thumbnail((100, 100), Image.LANCZOS)
            thumb_filename = file_name + '_thumb' + file_extension
            temp_thumb = BytesIO()
            image.convert('RGB').save(temp_thumb, 'JPEG')
            temp_thumb.seek(0)
            # set save=False, otherwise it will run in an infinite loop
            self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
            temp_thumb.close()

        if self.main_page_order:
            proc = Proclamation.objects.filter(main_page_order=self.main_page_order).exclude(pk=self.pk)
            if proc.exists():
                proc.update(main_page_order=None)

        super(Proclamation, self).save(*args, **kwargs)


class ProclamationGallery(models.Model):
    """تصاویر اطلاعیه"""
    class Meta:
        verbose_name = 'تصاویر اطلاعیه'
        verbose_name_plural = 'تصاویر اطلاعیه'
        ordering = ['id']

    proclamation = models.ForeignKey(to=Proclamation, on_delete=models.CASCADE, related_name='gallery', verbose_name='اطلاعیه')
    file = models.ImageField(verbose_name='فایل')

    def __str__(self):
        return self.file.name

    @property
    def file_url(self):
        return self.file.name


class ProclamationAppendix(models.Model):
    """پیوست‌های اطلاعیه"""
    class Meta:
        verbose_name = 'پیوست‌های اطلاعیه'
        verbose_name_plural = 'پیوست‌های اطلاعیه'
        ordering = ['id']

    proclamation = models.ForeignKey(to=Proclamation, on_delete=models.CASCADE, related_name='appendices', verbose_name='اطلاعیه')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    file = models.FileField(null=True, blank=True, verbose_name='فایل')

    def __str__(self):
        return self.title

    @property
    def file_url(self):
        return self.file.name if self.file else None


class ProclamationSeen(models.Model):
    """مشاهده اطلاعیه"""
    class Meta:
        verbose_name = 'اطلاعیه - مشاهده'
        verbose_name_plural = 'اطلاعیه - مشاهده'
        ordering = ['-id']

    proclamation = models.ForeignKey(to=Proclamation, on_delete=models.CASCADE, verbose_name='اطلاعیه')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    create_time = jmodels.jDateField(auto_now_add=True, verbose_name='زمان ایجاد')


class Notification(models.Model):
    class Meta:
        verbose_name = 'یادآور'
        verbose_name_plural = 'یادآور'
        ordering = '-id',

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='notifications', verbose_name='کاربر')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    body = models.CharField(max_length=200, verbose_name='متن')
    url = models.CharField(max_length=200, verbose_name='لینک مربوطه')
    task = models.ForeignKey(to='pm.Task', on_delete=models.CASCADE, null=True, blank=True, verbose_name='وظیفه')
    contract = models.ForeignKey(to='cn.Contract', on_delete=models.CASCADE, null=True, blank=True, verbose_name='قرارداد')
    pay = models.ForeignKey(to='cn.Pay', on_delete=models.CASCADE, null=True, blank=True, verbose_name='پرداخت قرارداد')
    node = models.ForeignKey(to='pm.Node', on_delete=models.CASCADE, null=True, blank=True, verbose_name='گره فرآیند')
    job_chat = models.ForeignKey(to='pm.JobChat', on_delete=models.CASCADE, null=True, blank=True, verbose_name='پیام وظیفه')
    created_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    seen_time = jmodels.jDateTimeField(null=True, blank=True, verbose_name='زمان دیده شدن')

    def __str__(self):
        return self.title


class HdPagination(PageNumberPagination):
    page_size_query_param = 'size'
    max_page_size = 100

    def get_page_size(self, request):
        return request.user.profile.page_size


class SMS(models.Model):
    class Meta:
        verbose_name = 'پیامک'
        verbose_name_plural = 'پیامک'
        ordering = ['-id']

    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('sending', 'Sending'),
        ('failed', 'Failed')

    )

    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True, editable=False,
                             verbose_name='کاربر')
    mobile = models.CharField(max_length=13, editable=False, verbose_name='شماره موبایل')
    text = models.TextField(null=True, blank=True, editable=False, verbose_name='متن پیامک')
    create_time = jmodels.jDateTimeField(auto_now_add=True, editable=False, verbose_name='زمان ارسال')
    sent = models.BooleanField(editable=False, verbose_name='نتیجه ارسال')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sending')
    token = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.mobile


class Computer(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    active_directory_account = models.CharField(max_length=20)
    pc_name = models.CharField(max_length=20)
    ip = models.CharField(max_length=15)
    cpu = models.CharField(max_length=20)
    motherboard = models.CharField(max_length=30)
    ram = models.PositiveSmallIntegerField(choices=[(2, 2), (4, 4), (8, 8), (16, 16), (32, 32), (64, 64)])
    vga = models.CharField(max_length=20)
    hdd = models.CharField(max_length=5, null=True, blank=True)
    ssd = models.CharField(max_length=5, null=True, blank=True)
    os = models.CharField(max_length=20, choices=[('Windows 7', 'Windows 7'), ('Windows 10', 'Windows 10'), ('Windows 11', 'Windows 11'), ('Linux', 'Linux')])
    joined = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, null=True, blank=True)
    create_date = jmodels.jDateField(auto_now_add=True)
    update_date = jmodels.jDateField(auto_now=True)

    def __str__(self):
        return self.pc_name


class Menu(models.Model):
    class Meta:
        verbose_name = 'منو'
        verbose_name_plural = 'منو'
        ordering = ['key']

    key = models.CharField(max_length=20, primary_key=True, verbose_name='کلید')
    title = models.CharField(max_length=50, verbose_name='عنوان')
    icon = models.CharField(max_length=50, verbose_name='آیکون')
    levels = ModifiedArrayField(base_field=models.CharField(max_length=20, choices=ChoicesPostLevel), blank=True, default=list, verbose_name='رده‌های سازمانی', help_text='خالی یعنی همه مجازند')
    groups = models.ManyToManyField(to=Group, blank=True, default=list, verbose_name='گروه‌های مجاز', help_text='خالی یعنی همه مجازند')
    posts = models.ManyToManyField(to=Post, blank=True, default=list, verbose_name='پستهای مجاز', help_text='خالی یعنی همه مجازند')
    users = models.ManyToManyField(to=User, blank=True, default=list, verbose_name='کاربران مجاز', help_text='خالی یعنی همه مجازند')
    should_has_post = models.BooleanField(default=True, verbose_name='فقط کاربران دارای پست')
    interim_not_allowed = models.BooleanField(default=False, verbose_name='فقط کاربران دائم (غیر موقت)')

    def __str__(self):
        return self.title


class Dashboard(models.Model):
    class Meta:
        verbose_name = 'داشبورد'
        verbose_name_plural = 'داشبورد'
        ordering = ['id']

    title = models.CharField(max_length=50, verbose_name='عنوان')
    slug = models.CharField(unique=True, max_length=100, verbose_name="اسلاگ", null=True, blank=True)
    def __str__(self):
        return self.title


class DashboardAccess(models.Model):
    class Meta:
        verbose_name = 'دسترسی داشبورد'
        verbose_name_plural = 'دسترسی داشبورد'
        ordering = ['id']
        unique_together = ['dashboard', 'user']

    dashboard = models.ForeignKey(to=Dashboard, on_delete=models.CASCADE, verbose_name='داشبورد')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='کاربر')
    is_global = models.BooleanField(default=False, verbose_name='مشاهده اطلاعات کل مرکز', help_text='برای مشاهده فقط واحد خودش، تیک را بردارید')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش')

    def __str__(self):
        return self.dashboard.title


class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    view_name = models.CharField(max_length=200, blank=True)
    app_name = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'لاگ فعالیت کاربر'
        verbose_name_plural = 'لاگ فعالیت کاربر'
        ordering = ['-timestamp']

    #def __str__(self):
    #    return f"{self.user.username} @ {self.ip_address} ({self.timestamp.isoformat()})"


class UserAuthLog(models.Model):
    login_at = jmodels.jDateTimeField(verbose_name='تاریخ و زمان ورود', auto_now_add=True)
    logout_at = jmodels.jDateTimeField(verbose_name="تاریخ و زمان خروچ", null=True, blank=True)
    ip = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_histories")
    token = models.CharField(max_length=50)
    user_agent = models.TextField(blank=True, null=True)
    is_suspicious = models.BooleanField(default=False, verbose_name="مشکوک اصت نباز به اطلاع")
