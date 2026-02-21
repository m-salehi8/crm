"""
بایگانی خودکار کارهای انجام‌شده (status=done) که بیش از دو هفته است انجام شده‌اند.
برای اجرای شبانه با cron:
    0 2 * * * cd /path/to/portal && python manage.py archive_done_jobs
"""
import jdatetime
from django.core.management.base import BaseCommand
from pm.models import Job


class Command(BaseCommand):
    help = 'کارهای انجام‌شده (done) که دو هفته از انجامشان گذشته را بایگانی می‌کند.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=14,
            help='بعد از چند روز از زمان انجام، بایگانی شود (پیش‌فرض: 14 یعنی دو هفته)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='فقط تعداد را نشان بده، بایگانی نکن',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        threshold = jdatetime.datetime.now() - jdatetime.timedelta(days=days)
        qs = Job.objects.filter(
            status='done',
            done_time__isnull=False,
            done_time__lte=threshold,
            archive=False,
        )

        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('هیچ کاری برای بایگانی یافت نشد.'))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[dry-run] {count} کار برای بایگانی یافت شد (انجام نشد).')
            )
            return

        qs.update(archive=True)
        self.stdout.write(self.style.SUCCESS(f'{count} کار بایگانی شد.'))
