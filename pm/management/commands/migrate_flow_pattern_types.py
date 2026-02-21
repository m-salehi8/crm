from django.core.management.base import BaseCommand
from django.db import connection
from pm.models import FlowPatternType, FlowPattern


class Command(BaseCommand):
    help = 'Migrate existing flow pattern types to the new FlowPatternType model'

    def handle(self, *args, **options):
        self.stdout.write('Starting FlowPattern type migration...')

        # Get all unique types from FlowPattern model directly from database
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT type FROM pm_flowpattern WHERE type IS NOT NULL")
            unique_types = [row[0] for row in cursor.fetchall()]

        self.stdout.write(f'Found {len(unique_types)} unique types: {list(unique_types)}')

        for type_value in unique_types:
            if type_value:  # Skip empty values
                # Create or get FlowPatternType for this type value
                flow_type_obj, created = FlowPatternType.objects.get_or_create(
                    title=type_value,
                    defaults={'active': True}  # Assuming new types should be active by default
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created new FlowPatternType: {type_value}')
                    )
                else:
                    self.stdout.write(f'Found existing FlowPatternType: {type_value}')

        # Now update all FlowPattern records to use the new flow_type relationship
        self.stdout.write('Updating FlowPattern records to use new flow_type relationship...')

        # Get all flow patterns with their old type values directly from database
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, type FROM pm_flowpattern WHERE type IS NOT NULL")
            flow_patterns_data = cursor.fetchall()

        updated_count = 0
        for fp_id, type_value in flow_patterns_data:
            if type_value:
                # Get the corresponding FlowPatternType
                try:
                    flow_type_obj = FlowPatternType.objects.get(title=type_value)

                    # Update the flow pattern to use the new flow_type
                    FlowPattern.objects.filter(id=fp_id).update(flow_type=flow_type_obj)
                    updated_count += 1

                    if updated_count % 10 == 0:  # Print progress every 10 records
                        self.stdout.write(f'Updated {updated_count} FlowPattern records...')
                except FlowPatternType.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Warning: FlowPatternType with title \'{type_value}\' does not exist for FlowPattern ID {fp_id}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} FlowPattern records.')
        )
        self.stdout.write('Migration completed successfully!')

        # Print summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"- Total FlowPatternType entries: {FlowPatternType.objects.count()}")
        self.stdout.write(f"- Total FlowPattern entries: {FlowPattern.objects.count()}")
        self.stdout.write(
            f"- FlowPattern entries with flow_type set: {FlowPattern.objects.filter(flow_type__isnull=False).count()}")
        self.stdout.write(
            f"- FlowPattern entries without flow_type: {FlowPattern.objects.filter(flow_type__isnull=True).count()}")