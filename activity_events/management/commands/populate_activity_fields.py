from django.core.management.base import BaseCommand
from ...populate_activity_fields_functions import populate_activity_fields


class Command(BaseCommand):
    help = 'Populate activity fields in ActivityEventField model based on ActivityEvent model'

    def handle(self, *args, **kwargs):
        try:
            result = populate_activity_fields()
            if result.get('has_failed_requests') or result.get('has_failed_records'):
                raise Exception(f'details:{result}')   
            message = 'Successfully populated activity fields. Fields status: '
            message += '{' + ', '.join(
            f"{field_name}: {action}" for field_name, action in result.items()) + '}'
            self.stdout.write(self.style.SUCCESS(message))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))