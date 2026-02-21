from django.db import transaction
from prj.models import Project, ProjectsTeam  # مسیر اپلیکیشن خودتو بزار

@transaction.atomic
def migrate_project_teams():
    projects = Project.objects.prefetch_related('team').all()

    for project in projects:
        users = list(project.team.all())
        if not users:
            continue

        count = len(users)

        # تقسیم مساوی درصد بین اعضا
        base_percentage = 100 // count
        remainder = 100 % count

        for index, user in enumerate(users):
            percentage = base_percentage

            # اگر تقسیم باقیمانده داشت، به چند نفر اول اضافه کن
            if index < remainder:
                percentage += 1

            ProjectsTeam.objects.get_or_create(
                project=project,
                user=user,
                defaults={
                    "participation_percentage": percentage
                }
            )

    print("Migration completed successfully.")
