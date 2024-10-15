from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from ...generate_fake_data_functions import generate_and_save_fake_data_list
import argparse

def valid_date(s):
    try:
        return parse_datetime(s[:10])
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD.")

class Command(BaseCommand):
    help = 'Generates fake activity event records with customizable options for events, users, and date range.'

    def add_arguments(self, parser):
        # Number of events with default value of 6000
        parser.add_argument('--n_events', type=int, default=6000, help='Number of events being faked. Default is 6000.')
        # Number of users with default value of 30
        parser.add_argument('--n_users', type=int, default=30, help='Number of users being faked. Default is 100.')    
        # Start date defaults to 90 days before the end date
        parser.add_argument('--start_date', type=valid_date, default=None, help='Start date (format: YYYY-MM-DD). Defaults to 90 days before the end date.')
        # End date defaults to the current date
        parser.add_argument('--end_date', type=valid_date, default=None, help='End date (format: YYYY-MM-DD). Defaults to today.')

    def handle(self, *args, **kwargs):
        try:
            n_events = kwargs['n_events']

            confirmation = input(f"Are you sure you want to generate {n_events} fake records? (Y/n): ").strip().lower()
            if confirmation not in ('y', 'yes', ''):  # Consider 'y', 'yes', and empty string as affirmative
                self.stdout.write(self.style.WARNING("Operation canceled."))
                return

            n_users = kwargs['n_users']            
            end_date = kwargs.get('end_date') or timezone.now().date()            
            start_date = kwargs.get('start_date') or (end_date - timedelta(days=90))                     

            # Call your fake data generation function
            result = generate_and_save_fake_data_list(n_events, n_users, start_date, end_date)
            n_created = result.get('n_created_records', 0)
            n_updated = result.get('n_updated_records', 0)
            failed = result.get('failed_records', None)
            start = start_date.strftime("%Y-%m-%d")
            end = end_date.strftime("%Y-%m-%d")

            # Success message
            message = (f"Fake activity event records have been successfully injected for the period: "
                       f"{start} - {end}. Number of created records: {n_created}. Number of updated records: {n_updated}. "
                       f"Failed records: {failed}.")
            self.stdout.write(self.style.SUCCESS(message))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))