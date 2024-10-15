from django.core.management.base import BaseCommand
from ...fetch_activity_events_functions import process_activity_events
from ... import app_settings as aps

class Command(BaseCommand):
    help = 'Fetches and updates activity events from last successful load'

    def add_arguments(self, parser):
        # Number of days before the current date with no default value
        parser.add_argument('--n_days_before', type=int, default=None, 
                            help='The number of days before the current date that defines the start of the period to be updated')

    def handle(self, *args, **kwargs):
        # Access n_days_before
        n_days_before = kwargs.get('n_days_before')

        try:
            # Call the function with n_days_before
            result = process_activity_events(
                n_days_before=n_days_before, 
                task_name=aps.ACTIVITY_EVENTS_FETCH_TASK_NAME, 
                sync_task=True
            )

            # Extract result information
            n_created = result.get('n_created_records', 0)
            n_updated = result.get('n_updated_records', 0)
            failed = result.get('failed_records', None)
            start_date = result.get('start_datetime').strftime("%Y-%m-%d %H:%M:%S")
            end_date = result.get('end_datetime').strftime("%Y-%m-%d %H:%M:%S")

            # Success message
            message = (f"Activity event records have been successfully retrieved and saved for the period: "
                       f"{start_date} - {end_date}. Number of created records: {n_created}. Number of updated records: {n_updated}. "
                       f"Failed records: {failed}.")
            self.stdout.write(self.style.SUCCESS(message))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))