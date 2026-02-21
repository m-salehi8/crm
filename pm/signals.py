# signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Session, User
from core.models import Notification  # فرض بر وجود مدل نوتیفیکیشن


# برای ذخیره وضعیت قبلی جهت مقایسه
@receiver(pre_save, sender=Session)
def capture_old_state(sender, instance, **kwargs):
    if instance.pk:
        old_obj = Session.objects.get(pk=instance.pk)
        instance._old_accept_room = old_obj.accept_room
        instance._old_manager_accept = old_obj.manager_accept
        instance._old_deputy_accept = old_obj.deputy_accept
    else:
        instance._old_accept_room = None
        instance._old_manager_accept = 'نامشخص'
        instance._old_deputy_accept = 'نامشخص'


@receiver(post_save, sender=Session)
def handle_session_workflow(sender, instance, created, **kwargs):
    """
    مدیریت اتوماتیک فلو:
    1. تایید اتاق -> ارجاع به مدیر
    2. تایید مدیر -> ارجاع به معاون یا اجرا
    3. تایید معاون -> اجرا
    """

    # ----------------------------------------------------
    # گام ۱: تغییر وضعیت اتاق (توسط ادمین اتاق)
    # ----------------------------------------------------
    if instance._old_accept_room != instance.accept_room:
        if instance.accept_room is True:
            # اتاق تایید شد. حالا ببینیم پذیرایی میخواد؟
            if instance.need_manager and instance.manager_accept == 'نامشخص':
                # ارسال نوتیفیکیشن برای مدیر واحد
                manager = instance.user.post.unit.manager  # پیدا کردن مدیر
                if manager:
                    Notification.objects.create(
                        user=manager,
                        title="درخواست تایید پذیرایی",
                        body=f"جلسه {instance.title} نیاز به تایید پذیرایی دارد.",
                        url=f"/session/{instance.id}"
                    )
            elif instance.is_catering_approved:
                # پذیرایی نمیخواد یا قبلا اوکی شده -> خبر به عوامل اجرا
                notify_execution_team(instance)

        elif instance.accept_room is False:
            # اتاق رد شد -> خبر به کاربر
            Notification.objects.create(user=instance.user, title="رد رزرو اتاق", body=f"جلسه {instance.title} رد شد.")

    # ----------------------------------------------------
    # گام ۲: تغییر وضعیت مدیر (توسط مدیر واحد)
    # ----------------------------------------------------
    if instance._old_manager_accept != instance.manager_accept:
        if instance.manager_accept == 'تأیید':
            if instance.need_deputy and instance.deputy_accept == 'نامشخص':
                # مدیر تایید کرد، حالا نوبت معاون است
                # (اینجا باید کد پیدا کردن معاونت را بزنید)
                pass
            else:
                # معاونت لازم نیست -> همه چی حله
                notify_execution_team(instance)

    # ----------------------------------------------------
    # گام ۳: تغییر وضعیت معاون (توسط معاونت)
    # ----------------------------------------------------
    if instance._old_deputy_accept != instance.deputy_accept:
        if instance.deputy_accept == 'تأیید':
            # معاون هم تایید کرد -> اجرا
            notify_execution_team(instance)


def notify_execution_team(session):
    """تابع کمکی برای خبر دادن به واحد پذیرایی و خدمات"""
    # ارسال نوتیفیکیشن برای گروه room_catering و room_supervisor
    # کد مربوط به ارسال نوتیفیکیشن گروهی...
    pass