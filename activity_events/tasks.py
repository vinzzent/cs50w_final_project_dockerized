from celery import shared_task
from .fetch_activity_events_functions import process_activity_events, remove_old_activity_events
from .generate_csv_functions import generate_activity_events_csv_to_file, remove_old_csv_files
#from celery.utils.log import get_task_logger

#logger = get_task_logger(__name__)

@shared_task(bind=True)
def fetch_and_update_activity_events(self, n_days_before=None):
    task_id = self.request.id
    task_name = self.name
    result = process_activity_events(n_days_before=n_days_before, ask_id=task_id, task_name=task_name)

    if result.get('has_failed_requests') or result.get('has_failed_records'):
        raise Exception(f'details:{result}')   

    return result

@shared_task
def generate_csv(request_data):
    try:
        result = generate_activity_events_csv_to_file(request_data)
    except Exception as e:
         raise e(f"Error generating CSV: {e}")
    return result

@shared_task
def cleanup_old_csv_files(retention_hours):
    try:
        result = remove_old_csv_files(retention_hours)
    except Exception as e:
         raise e(f"Error removing csv files: {e}")
    return result

@shared_task
def cleanup_old_activity_events(retention_days):
    try:
        result = remove_old_activity_events(retention_days)
    except Exception as e:
         raise e(f"Error removing activity event records: {e}")
    return result
