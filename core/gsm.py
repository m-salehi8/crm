import json
import token
import requests
import jdatetime
import time
import random
import string
from django.db.models import Q, Count
from django.apps import apps
from core.models import User, SMS


TOKEN = 'Dn7c6o7mQztowEhqax9wTVfNtfimcgFN8'
GSM_SERVER_URL = 'http://192.168.19.161:5000/send-sms'

def random_string(length: int) -> str:
    characters = string.ascii_letters + string.digits   # حروف بزرگ/کوچیک + اعداد
    return ''.join(random.choice(characters) for _ in range(length))


def send_sms(mobile, text, user_id=None):
    if len(mobile) != 11:
        return False
    try:
        sms_id = random_string(8)
        res = requests.post(GSM_SERVER_URL, data=json.dumps({"mobile": mobile, "text": text, 'sms_id': sms_id}), headers={"Token": TOKEN, "Content-Type": "application/json"}, timeout=5)
        success = res.status_code == 200
        if res.status_code == 200:
            SMS.objects.create(user_id=user_id, text=text, mobile=mobile, sent=True, token=sms_id)
            return True
    except requests.RequestException as e:
        print(f'GSM send failed: {e}')
        success = False
    SMS.objects.create(user_id=user_id, text=text, mobile=mobile, sent=success)
    return False


def sms_service_is_ok():
    send_sms(mobile='09123266861', text=f'SMS Service in {str(jdatetime.date.today())} is ACTIVE', user_id=1)


def daily_food_reminder():
    tomorrow = jdatetime.date.today() + jdatetime.timedelta(days=1)
    try:
        nutrition = apps.get_model('fd.Nutrition').objects.get(date=tomorrow)
        total_reservations = apps.get_model('fd.Reserve').objects.filter(nutrition=nutrition).count()
        for user in ['09302436580', '09354369607', '09127994766']:
            text = 'مرکز ملی فضای مجازی، تعداد غذای رزرو شده برای تاریخ {day}  \n{total_reservations} عدد میباشد'.format(total_reservations=total_reservations, day=tomorrow.strftime("%Y/%m/%d"))
            send_sms(mobile=user, text=text, )
            time.sleep(1)
    except apps.get_model('fd.Nutrition').DoesNotExist:
        pass
    return True


def daily_reminder():
    if jdatetime.date.today().weekday() > 4:  # پنجشنبه و جمعه پیامک ارسال نشود
        return
    today = jdatetime.date.today()
    next_week = jdatetime.date.today() + jdatetime.timedelta(days=7)

    # شنبه: گزارش وضعیت وظایف
    if jdatetime.date.today().weekday() == 0:
        for user in User.objects.filter(post__isnull=False, mobile__isnull=False):
            new_task_count = user.tasks.filter(is_seen=False, job__status__in=['todo', 'doing'], job__archive=False).count()
            delayed_task_count = user.tasks.filter(job__deadline__isnull=False, job__deadline__lt=today, job__status__in=['todo', 'doing'], job__archive=False, is_committed=True).count()
            warning_task_count = user.tasks.filter(job__deadline__isnull=False, job__deadline__gte=today, job__deadline__lt=next_week, job__status__in=['todo', 'doing'], job__archive=False, is_committed=True).count()
            if new_task_count + delayed_task_count + warning_task_count > 0:
                text = 'وضعیت کارتابل وظایف شما:\r'
                if new_task_count > 0:
                    text += f'وظایف جدید: {new_task_count}\r'
                if delayed_task_count > 0:
                    text += f'وظایف دارای تأخیر: {delayed_task_count}\r'
                if warning_task_count > 0:
                    text += f'وظایف دارای مهلت کمتر از یک هفته: {warning_task_count}\r'
                text += 'برای مشاهده وظایف خود به پرتال مراجعه فرمایید'
                send_sms(mobile=user.mobile, text=text, user_id=user.id)

    # فرآیندهای منتظر اقدام
    for user in User.objects.annotate(val=Count('nodes', filter=Q(nodes__done_time=None))).filter(post__isnull=False, mobile__isnull=False, val__gt=0):
        node_count = user.nodes.filter(done_time=None).count()
        if node_count > 0:
            text = f'سلام. شما {node_count} فرآیند منتظر اقدام دارید. لطفا به پرتال مرکز بخش فرآیندها مراجعه فرمایید'
            send_sms(mobile=user.mobile, text=text, user_id=user.id)

    # قراردادهای منتظر اقدام
    for user in User.objects.filter(post__isnull=False, mobile__isnull=False):
        if user.todo_contract > 0:
            text = f'سلام. شما {user.todo_contract} قراداد منتظر بررسی یا اقدام دارید. لطفا به پرتال مرکز بخش قراردادها مراجعه فرمایید'
            send_sms(mobile=user.mobile, text=text, user_id=user.id)


def session_reminder():
    hour = jdatetime.datetime.now().hour
    khodadadi = User.objects.get(pk=387)  # 387: خدادادی
    kheyri = User.objects.get(pk=103)  # 103: خیری
    if hour == 21:  # ساعت 21 جلسات فردا صبح و در سایر ساعات جلسات همان روز یادآوری ارسال می‌شود
        session_list = apps.get_model('pm.Session').objects.filter(date=jdatetime.date.today() + jdatetime.timedelta(days=1), start__lt='10:00:00')
    else:
        session_list = apps.get_model('pm.Session').objects.filter(date=jdatetime.date.today(), start__gte=f'{jdatetime.datetime.now().hour + 1}:00:00', start__lt=f'{jdatetime.datetime.now().hour + 2}:00:00')
    for session in session_list:
        if session.sms:
            for member in session.members.filter(mobile__isnull=False):
                send_sms(mobile=member.mobile, text=f'یادآوری جلسه {session.title}{' فردا' if hour == 21 else ''} - ساعت {str(session.start).split(':')[0]}:{str(session.start).split(':')[1]}', user_id=member.id)
        if session.order_time is not None:
            # یادآوری پذیرایی جلسه
            text = f'یادآوری پذیرایی جلسه {session.title}{' فردا' if hour == 21 else ''} - ساعت {str(session.start).split(':')[0]}:{str(session.start).split(':')[1]}'
            if bool(session.breakfast):
                text += f'\nصبحانه: {session.breakfast}'
            if bool(session.lunch):
                text += f'\nناهار: {session.lunch}'
            if len(session.catering) > 0:
                text += f'\nپذیرایی: {'، '.join(session.catering)}'
            text += f'\nتعداد: {session.members.count() + len(session.guest_count)} نفر'
            if session.room:
                text += f'\nمکان: {session.room.title}'
            send_sms(mobile=khodadadi.mobile, text=text, user_id=khodadadi.id)
            send_sms(mobile=kheyri.mobile, text=text, user_id=kheyri.id)
            for pk in set(session.breakfast_agents.values_list('id', flat=True) | session.lunch_agents.values_list('id', flat=True) | session.catering_agents.values_list('id', flat=True)):
                servant = User.objects.get(pk=pk)
                if servant.mobile:
                    send_sms(mobile=servant.mobile, text=text, user_id=pk)


def get_str_date():
    tomorrow = jdatetime.date.today() + jdatetime.timedelta(days=1)
    day = tomorrow.day
    month_name = jdatetime.date.j_months_fa[tomorrow.month - 1]
    return f"{day} {month_name}"

def render_session_sms_text(session, include_date_prefix=False):
    """
    رندر متن پیامک برای یک جلسه

    Args:
        session: شی Session
        include_date_prefix: اگر True باشد، "فردا" را به ابتدای متن اضافه می‌کند

    Returns:
        str: متن پیامک برای جلسه
    """
    time_str = ''
    if session.start:
        start_parts = str(session.start).split(':')
        start_time = f'{start_parts[0]}:{start_parts[1]}'

        if session.end:
            end_parts = str(session.end).split(':')
            end_time = f'{end_parts[0]}:{end_parts[1]}'
            time_str = f' - ساعت {start_time} تا {end_time}'
        else:
            time_str = f' - ساعت {start_time}'

    date_prefix = 'فردا ' if include_date_prefix else ''
    text = f'{date_prefix}جلسه {session.title}{time_str}'

    if session.room:
        text += f' - {session.room.title}'

    return text


def get_tomorrow_sessions(user):
    """
    دریافت جلسات فردا برای یک کاربر و ارسال پیامک با رعایت محدودیت 210 کاراکتر

    Args:
        user_id: شناسه کاربر

    Returns:
        bool: True در صورت موفقیت
        :param user:
    """
    Session = apps.get_model('pm.Session')
    SMS_MAX_LENGTH = 210

    if not user.mobile:
        return False

    tomorrow = jdatetime.date.today() + jdatetime.timedelta(days=1)

    sessions = Session.objects.filter(
        Q(date=tomorrow) &
        (Q(user=user) | Q(members__in=[user]))
    ).distinct().order_by('start')

    if not sessions.exists():
        return True

    session_texts = []
    for session in sessions:
        session_text = render_session_sms_text(session, include_date_prefix=True)
        session_texts.append(session_text)

    messages = []
    header = f'یادآوری جلسات فردا {get_str_date()}\n'
    current_message = header

    for session_text in session_texts:
        test_message = current_message + session_text + '\n'

        if len(test_message) <= SMS_MAX_LENGTH:
            current_message = test_message
        else:

            if current_message.strip() != header.strip():
                messages.append(current_message.rstrip())

            new_message_with_header = header + session_text + '\n'
            if len(new_message_with_header) <= SMS_MAX_LENGTH:
                current_message = new_message_with_header
            else:
                messages.append(session_text)
                current_message = header

    if current_message.strip() != header.strip():
        messages.append(current_message.rstrip())

    for i, message in enumerate(messages):
        send_sms(mobile=user.mobile, text=message, user_id=user.id)
        time.sleep(1)  # تأخیر بین ارسال پیامک‌ها
    return True


def send_tomorrow_sessions_sms():
    users = User.objects.filter(post__is_manager=True)
    for user in users:
        get_tomorrow_sessions(user)
