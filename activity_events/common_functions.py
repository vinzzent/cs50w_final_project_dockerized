
from zoneinfo import ZoneInfo
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.db.models import Q, CharField
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError

def apply_filters_to_queryset(request_data, queryset, fields_model, target_model):

    filter_fields = list(fields_model.objects.filter(filter=True).values_list('fieldname', flat=True))
    filter_fields = target_model.get_filtered_fields_dict(filter_fields)   
    filters = Q()

    for field_name, field_type in filter_fields.items():
        if field_type == 'DateTimeField':
            # Handle date range filter
            start_suffix = '__gte'
            start_date = request_data.get(f'{field_name}{start_suffix}')                
            if start_date:
                start_date = parse_datetime(f"{start_date[:10]}T00:00:00.000000").replace(tzinfo=ZoneInfo('UTC'))            
            end_suffix = '__lte'
            end_date = request_data.get(f'{field_name}{end_suffix}')
            if end_date:
                end_date = parse_datetime(f"{end_date[:10]}T23:59:59.999999").replace(tzinfo=ZoneInfo('UTC'))
            else:
                end_suffix = '__lt'
                end_date = request_data.get(f'{field_name}{end_suffix}')
                if end_date:               
                    end_date = parse_datetime(f"{end_date[:10]}T00:00:00.000000").replace(tzinfo=ZoneInfo('UTC'))
                    end_date = end_date + timedelta(days=1)
                else:
                    end_date = None
            
            if start_date:
                filters &= Q(**{f'{field_name}{start_suffix}': start_date})
            
            if end_date:
                filters &= Q(**{f'{field_name}{end_suffix}': end_date})

        else:
            value = request_data.get(field_name)                     
            if value:
                value = '' if value == '<blank>' else value
                # Handle other field types
                filters &= Q(**{field_name:value})

    queryset =  queryset.filter(filters)
        
    # Apply search functionality
    search_fields = list(fields_model.objects.filter(search=True).values_list('fieldname', flat=True))
    search_fields = target_model.get_filtered_fields_dict(search_fields)
    filters = Q()
        
    for field_name in search_fields:
        value = request_data.get('q')
        if value:
            filters |= Q(**{f'{field_name}__icontains': value})
        
    queryset = queryset.filter(filters)

    # Apply order by

    col_name = request_data.get('orderby_fields') or request_data.get('orderby_field')
    direction = request_data.get('orderby_directions') or request_data.get('orderby_direction')

    if col_name and direction:
        field = queryset.model._meta.get_field(col_name)
        if isinstance(field, CharField):
            queryset = queryset.annotate(
            lower_col_name=Lower(col_name)
        )
            if direction == 'desc':
                queryset = queryset.order_by('-lower_col_name')
            elif direction == 'asc':
                queryset = queryset.order_by('lower_col_name')
        else:
            # For non-CharField fields, just apply sorting direction directly
            if direction == 'desc':
                queryset = queryset.order_by(f'-{col_name}')
            elif direction == 'asc':
                queryset = queryset.order_by(col_name)

    return queryset


def get_latest_successful_task_time(sync_model=None, celery_model=None, task_name=None, sync_task_name_field=None, sync_timestamp_field=None, celery_task_name_field=None, celery_timestamp_field=None):  
    status_field = 'status'
    success_status='success'
    # Query sync_model for the latest successful task time
    sync_task_results = sync_model.objects.filter(
        Q(**{sync_task_name_field: task_name}),
        Q(**{f'{status_field}__iexact': success_status})
    ).order_by(f'-{sync_timestamp_field}')

    latest_sync_time = None
    if sync_task_results.exists():
        latest_sync_time = getattr(sync_task_results.first(), sync_timestamp_field)

    # Query celery_model for the latest successful task time
    task_result_results = celery_model.objects.filter(
        Q(**{f'{celery_task_name_field}__exact': task_name}),
        Q(**{f'{status_field}__iexact': success_status})
    ).order_by(f'-{celery_timestamp_field}')

    latest_celery_time = None
    if task_result_results.exists():
        latest_celery_time = getattr(task_result_results.first(), celery_timestamp_field)

    # Compare the two times and return the most recent one
    if latest_sync_time and latest_celery_time:
        return max(latest_sync_time, latest_celery_time)
    elif latest_sync_time:
        return latest_sync_time
    elif latest_celery_time:
        return latest_celery_time
    else:
        return None
    

def save_records_to_model(data_list, target_model, task_id=None):
    n_created_records = 0
    n_updated_records = 0
    failed_records = []

    for item in data_list:
        try:
            status = target_model.create_or_update_from_dict(
                item, task_id=task_id)[1]
            if status == 'created':
                n_created_records += 1
            else:
                n_updated_records += 1
        except (ValueError, ValidationError) as e:
            id = item.get('Id') or item.get('id')
            failed_records.append({
                id: str(e)
            })

    result = {
        'n_created_records': n_created_records,
        'n_updated_records': n_updated_records,
        'failed_records': failed_records
    }

    return result