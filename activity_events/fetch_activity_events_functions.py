import requests
from api_credentials.util import get_access_token
from datetime import timedelta
from django_celery_results.models import TaskResult
from django.utils import timezone
from requests.exceptions import RequestException
from .models import ActivityEvent, SyncTask
from .common_functions import get_latest_successful_task_time, save_records_to_model
from . import app_settings as aps
import uuid


def process_activity_events(n_days_before=None, task_id=None, task_name=None, sync_task=False):

    max_past_days=aps.ACTIVITY_EVENTS_FETCH_MAX_PAST_DAYS
    buffer_hours = aps.ACTIVITY_EVENTS_FETCH_BUFFER_HOURS

    end_datetime = timezone.now()

    if sync_task:
        task_start = end_datetime
        task_id = f"synctask-{uuid.uuid4()}"    

    args_dict = {'sync_model': SyncTask,
        'celery_model': TaskResult,
        'task_name': aps.ACTIVITY_EVENTS_FETCH_TASK_NAME,
        'sync_task_name_field': 'taskname',
        'sync_timestamp_field': 'started_at',
        'celery_task_name_field': 'task_name',
        'celery_timestamp_field': 'date_created'}    

    if n_days_before is None:        
        last_successful_time = get_latest_successful_task_time(**args_dict)
        if last_successful_time is None:
            start_datetime = end_datetime - timedelta(days=max_past_days)
        else:            
            start_datetime = max(last_successful_time - timedelta(hours=buffer_hours), end_datetime - timedelta(days=max_past_days))
    else:
        n_days_before = min(n_days_before, max_past_days)
        start_datetime = end_datetime - timedelta(days=n_days_before)

    result = process_ativity_events_between_datetimes(
        start_datetime, end_datetime, task_id)
    
    result['start_datetime'] = start_datetime
    result['end_datetime'] = end_datetime

    created = 0
    updated = 0
    for item in result.get('details', []):
        created += item.get('n_created_records', 0)
        updated += item.get('n_updated_records', 0)

    result['n_created_records'] = created
    result['n_updated_records'] = updated

    if sync_task:
        status = 'success' if not result.get('has_failed_requests') and not result.get('has_failed_records') else 'failure'        
        sync_task = SyncTask.objects.create(
            taskuuid=task_id,
            taskname=task_name,
            status=status,
            result=result,
            started_at=task_start
    )
    
    return result


def process_ativity_events_between_datetimes(start_datetime, end_datetime, task_id):
   datetime_pairs = generate_datetime_pairs(start_datetime, end_datetime)
   result = process_ativity_events_from_dates_list(datetime_pairs, task_id)
   return result

   
def process_ativity_events_from_dates_list(dates_list, task_id):
    details = []

    has_failed_records = False
    has_failed_requests = False

    for start, end in dates_list:
        result = get_json_and_save_activity_events(start, end, task_id)
        result['start_datetime'] = start
        result['end_datetime'] = end
        if result.get('failed_records'):
            has_failed_records = True
        if result.get('failed_requests'):
            has_failed_records = True
        details.append(result)

    result = {'has_failed_requests': has_failed_requests,
              'has_failed_records': has_failed_records,
              'details': details
              }
    return result


def generate_datetime_pairs(start_datetime, end_datetime):
    # Generates date-time pairs for processing, where each pair represents a start and end datetime
    # Returns: List of tuples: Each tuple contains a start datetime and an end datetime for each day.

    datetime_pairs = []

    # Adjust the end time of the first day
    first_day_end = start_datetime.replace(
        hour=23, minute=59, second=59, microsecond=999999)
    datetime_pairs.append((start_datetime, first_day_end))

    # If the range covers more than one day, add intermediate days
    current_start = first_day_end + timedelta(microseconds=1)
    while current_start.date() < end_datetime.date():
        next_day_end = current_start + \
            timedelta(days=1) - timedelta(microseconds=1)
        datetime_pairs.append((current_start, next_day_end))
        current_start = next_day_end + timedelta(microseconds=1)

    if start_datetime.date() < end_datetime.date():
        last_day_start = end_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0)
        datetime_pairs.append((last_day_start, end_datetime))

    return datetime_pairs


def get_json_from_activity_events_api(start_datetime, end_datetime):
    api_url = 'https://api.powerbi.com/v1.0/myorg/admin/activityevents'
    all_json_data = []
    token = get_access_token()
    failed_requests = []
    is_cont_uri = False

    while True:
        try:
            data = fetch_activity_events(
                start_datetime, end_datetime, token, api_url, is_cont_uri)
            all_json_data.extend(data.get('activityEventEntities', []))

            last_result_set = data.get('lastResultSet')
            if last_result_set:
                break

            api_url = data.get('continuationUri')
            if not api_url:
                break

            is_cont_uri = True
        except (Exception, RequestException) as e:
            failed_requests.append({'url': api_url, 'error': str(e)})

    return all_json_data, failed_requests


def get_json_and_save_activity_events(start_datetime, end_datetime, task_id):
    data_list, failed_requests = get_json_from_activity_events_api(start_datetime, end_datetime)
    save_result = save_records_to_model(data_list, ActivityEvent, task_id)

    save_result['failed_requests'] = failed_requests

    return save_result


def fetch_activity_events(start_datetime, end_datetime, token, api_url, is_cont_uri):

    # Construct headers with the token
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    start = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    end = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # Prepare query parameters
    params = {
        'startDateTime': "'" + start + "'",
        'endDateTime': "'" + end + "'"
    }

    if is_cont_uri:
        params = {}  # Do not pass any parameters with continuation_uri

    try:
        # Make the API request
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for bad status codes

        # Extract JSON data from response
        data = response.json()

        return data

    except RequestException as e:
        raise e
    

def remove_old_activity_events(retention_days):
    # Count records before deletion
    count_before = ActivityEvent.objects.count()
    # Get the current time
    now = timezone.now()
    # Calculate the cutoff time
    cutoff_time = now - timedelta(days=retention_days)
    # Query the ActivityEvent model to get records older than the cutoff time
    old_records = ActivityEvent.objects.filter(creationtime__lt=cutoff_time)
    # Count the number of records to be deleted
    count_deleted = old_records.count()
    # Delete the old records
    old_records.delete()
    count_remaining = ActivityEvent.objects.count()
    # Return the number of deleted records
    return {'n_before':count_before, 'n_deleted':count_deleted, 'n_remaining':count_remaining}