import jdatetime
from pm.models import Job

def archive_old_done_jobs(days=14, dry_run=False):
    """
    بایگانی خودکار کارهای انجام‌شده که از زمان اتمام آن‌ها زمان مشخصی گذشته است.
    """
    # محاسبه زمان مرز (Threshold)
    threshold = jdatetime.datetime.now() - jdatetime.timedelta(days=days)
    
    # فیلتر کردن کوئری‌ست
    qs = Job.objects.filter(
        status='done',
        done_time__isnull=False,
        done_time__lte=threshold,
        archive=False,
    )

    count = qs.count()
    
    if count == 0:
        return "هیچ کاری برای بایگانی یافت نشد."

    if dry_run:
        return f"[dry-run] {count} کار واجد شرایط برای بایگانی هستند."

    # اجرای عملیات به‌روزرسانی به صورت تکی (Bulk Update)
    updated_count = qs.update(archive=True)
    
    return f"عملیات موفق: {updated_count} کار بایگانی شد."


p = archive_old_done_jobs(days=10, dry_run=True)
print(p)
#[dry-run] 205 کار واجد شرایط برای بایگانی هستند.