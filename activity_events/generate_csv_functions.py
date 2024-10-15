import os
import csv
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone
from .models import ActivityEvent, ActivityEventField
from .common_functions import apply_filters_to_queryset
from . import app_settings as aps

def generate_activity_events_csv_to_file(request_data):
    queryset, export_fields = filter_queryset_and_get_export_fields(request_data)
    result = write_csv_to_file(queryset, export_fields)
    return result

def filter_queryset_and_get_export_fields(request_data):
    queryset = ActivityEvent.objects.all()
    queryset = apply_filters_to_queryset(request_data, queryset, ActivityEventField, ActivityEvent)    
    # Get the fields marked for export, or fall back to all fields if none are marked
    export_fields = ActivityEventField.objects.filter(export=True)
    n_fields = aps.ACTIVITY_EVENTS_N_FIELDS 
    # Apply the slice operation based on the condition
    if export_fields.exists():
        export_fields = export_fields[:n_fields]  # Apply slicing and assign back
    else:
        export_fields = ActivityEventField.objects.all()[:n_fields]  # Apply slicing to all fields and assign back    
    # Convert to a list of field names
    export_fields = export_fields.values_list('fieldname', flat=True)
    return queryset, export_fields

def write_csv_to_http(queryset, export_fields, response):
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(export_fields)
    for event in queryset:
        row = [getattr(event, field) for field in export_fields]
        writer.writerow(row)            
    return response

def write_csv_to_file(queryset, export_fields):
    # Generate and save the CSV file
    export_path = os.path.join(aps.MEDIA_ROOT, aps.ACTIVITY_EVENTS_FOLDER)
    if not os.path.exists(export_path):
        os.makedirs(export_path)    
    # Generate a unique filename
    filename = f'activity_events_{uuid.uuid4()}_{timezone.now().strftime("%Y%m%d%H%M%S")}.csv'
    file_path = os.path.join(export_path, filename)        
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(export_fields)
        for event in queryset:
            row = [getattr(event, field) for field in export_fields]
            writer.writerow(row)
    return file_path

def remove_old_csv_files(retention_hours):
    directory_path = os.path.join(aps.MEDIA_ROOT, aps.ACTIVITY_EVENTS_FOLDER)
    current_time = timezone.now()
    cutoff_time = current_time - timedelta(hours=retention_hours)

    removed_files = []
    name_error_files = []
    deleted_count = 0
    name_errors_count = 0

    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            try:
                timestamp_str = filename.split('_')[-1].split('.')[0]
                file_datetime = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S').replace(tzinfo=ZoneInfo(aps.TIME_ZONE))
            except ValueError:
                name_errors_count += 1
                name_error_files.append(filename)
                continue

            if file_datetime < cutoff_time:
                file_path = os.path.join(directory_path, filename)
                os.remove(file_path)
                removed_files.append(filename)
                deleted_count += 1

    return {
        'n_deleted': deleted_count,
        'files_deleted': removed_files,
        'n_name_errors': name_errors_count,
        'name_error_files': name_error_files
    }