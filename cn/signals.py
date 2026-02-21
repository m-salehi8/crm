from django.db.models.signals import post_save
from django.dispatch import receiver
from cn.models import ArticlePermit
from core.models import Notification


@receiver(post_save, sender=ArticlePermit)
def send_article_permit_request_notification(sender, instance, created, **kwargs):
    """
    Send notification to category admins when a new article access request is made
    """
    if created:
        admin_users = instance.article.category.owners.all()
        for user in admin_users:
            notif = Notification()
            notif.user = user
            notif.title = f'درخواست دسترسی برای مقاله'
            text = "کاربر {} برای مقاله {} درخواست دسترسی داده است. \n {}".format(
                instance.user.get_full_name(),
                instance.article.title,
                instance.note
            )
            notif.body = text
            notif.url = f'/cn/article-detail/{instance.article.id}/'  # Link to the article
            notif.save()


@receiver(post_save, sender=ArticlePermit)
def send_article_permit_response_notification(sender, instance, created, **kwargs):
    """
    Send notification to the requesting user when their article access request is approved or rejected
    """
    # Only trigger when the permit is updated (not created) and has been approved/rejected
    if not created and instance.accept is not None:
        # Get the requesting user
        requesting_user = instance.user

        # Create notification for the requesting user
        notif = Notification()
        notif.user = requesting_user

        if instance.accept:  # Approved
            notif.title = f'درخواست دسترسی مقاله تأیید شد'
            text = "درخواست دسترسی شما برای مقاله '{}' تأیید شده است.".format(instance.article.title)
        else:  # Rejected
            notif.title = f'درخواست دسترسی مقاله رد شد'
            text = "درخواست دسترسی شما برای مقاله '{}' رد شده است.".format(instance.article.title)

        notif.body = text
        notif.url = f'/cn/article-detail/{instance.article.id}/'  # Link to the article
        notif.save()























