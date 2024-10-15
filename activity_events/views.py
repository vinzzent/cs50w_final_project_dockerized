import os
from datetime import timedelta
from django.views.generic import ListView
from django.db.models import Min, Max, Count
from django.db.models.functions import TruncHour
from django.utils.dateformat import DateFormat
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django_celery_results.models import TaskResult
from celery.result import AsyncResult
from rest_framework import generics
from .models import ActivityEvent, ActivityEventField, SyncTask
from .tasks import generate_csv
from .serializers import ActivityEventSerializer
from .common_functions import apply_filters_to_queryset, get_latest_successful_task_time
from . import app_settings as aps
#from django.utils.dateparse import parse_date

class ActivityEventListView(LoginRequiredMixin, ListView):
    model = ActivityEvent
    template_name = 'activity_event_list.html'
    context_object_name = 'events'
    paginate_by = aps.ACTIVITY_EVENTS_PAGINATED_BY    

    def get_queryset(self):
        queryset = super().get_queryset()
        request_data = self.request.GET
        # Apply the filters using the reusable method
        queryset = apply_filters_to_queryset(request_data, queryset, ActivityEventField, ActivityEvent)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch up to maximum number objects field definitions for displaying
        event_fields = ActivityEventField.objects.filter(display=True)    
        # Check if there are objects with display=True
        n_fields = aps.ACTIVITY_EVENTS_N_FIELDS
        if event_fields.exists():            
            # Return up to the maximum number of objects with display=True            
            event_fields = event_fields[:n_fields]
        else:
            # If no objects with display=True, return the maximum number objects regardless of the display field
            event_fields = ActivityEventField.objects.all()[:n_fields]
        context['event_fields'] = event_fields

        # Fetch fields that are marked for filtering
        filter_fields = ActivityEventField.objects.filter(filter=True)
        filter_values = {}
        
        for field in filter_fields:
            field_name = field.fieldname
            display_name = field.displayname
            if field.fieldtype == 'DateTimeField':
                # Fetch the min and max date for date fields
                min_date = ActivityEvent.objects.aggregate(Min(field_name))['%s__min' % field_name]                
                max_date = ActivityEvent.objects.aggregate(Max(field_name))['%s__max' % field_name]                
                min_date = DateFormat(min_date).format('Y-m-d')
                max_date = DateFormat(max_date).format('Y-m-d')                            
                filter_values[field_name] = {'displayname':display_name, 'start':f'{field_name}__gte', 'end':f'{field_name}__lte', 'values': {'min_date': min_date, 'max_date': max_date}}
            else:
                distinct_values = ActivityEvent.objects.order_by(field_name).values_list(field_name, flat=True).distinct()
                distinct_values = [value if value != '' else '<blank>' for value in distinct_values]
                filter_values[field_name] = {'displayname':display_name, 'values':distinct_values}

        orderby_values =  ActivityEventField.objects.filter(orderby=True)   
        orderby_fields = {'name':'orderby_fields', 'displayname':'Field', 'values':orderby_values}
        orderby_directions = {'name':'orderby_directions', 'displayname':'Direction', 'values': {'asc':'Ascending', 'desc':'Descending'}}          
        orderby= {'fields':orderby_fields, 'directions':orderby_directions}

        args_dict = {'sync_model': SyncTask,
        'celery_model': TaskResult,
        'task_name': aps.ACTIVITY_EVENTS_FETCH_TASK_NAME,
        'sync_task_name_field': 'taskname',
        'sync_timestamp_field': 'created_at',
        'celery_task_name_field': 'task_name',
        'celery_timestamp_field': 'date_done'}

        context['last_data_update_time'] = get_latest_successful_task_time(**args_dict)  
        context['filter_values'] = filter_values
        context['orderby'] = orderby       

        return context    

@login_required   
def export_csv_vw(request):
    request_data = request.GET
    try:
        task = generate_csv.delay(request_data)
        return JsonResponse({'task_id': task.id})
    except Exception as e:
        # Handle any other unexpected errors
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)
    
@login_required
def check_csv_status_vw(request, task_id):   
    result = AsyncResult(task_id)
    if result.state == 'SUCCESS':
        file_path = result.result
        file_name = os.path.basename(file_path)
        download_url = request.build_absolute_uri(f'/download_csv/{file_name}')
        return JsonResponse({'status': 'ready', 'url': download_url})
    else:
        return JsonResponse({'status': result.state})
    
@login_required
def download_csv_vw(request, file_name):
    file_path = os.path.join(aps.MEDIA_ROOT, aps.ACTIVITY_EVENTS_FOLDER, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    else:
        return HttpResponseNotFound("File not found")
    
@login_required
def charts_vw(request):
    # Get filtered fields with fieldname and displayname
    filtered_fields = dict(ActivityEventField.objects.filter(chart=True).values_list('fieldname', 'displayname'))

    if not filtered_fields:
        return JsonResponse({'error': 'No fields provided'}, status=400)

    # Get field types and prepare display names and types as lists
    fields = ActivityEvent.get_filtered_fields_dict(filtered_fields)
    displaynames, fieldtypes, fieldsextra, group_fields = [], [], [], []
    queryset = None

    for field_name, field_info_list in fields.items():
        if field_info_list[0] == 'DateTimeField':
            max_past_days = aps.ACTIVITY_EVENTS_CHART_MAX_PAST_DAYS                
            since = timezone.now() - timedelta(days=max_past_days)
            queryset = ActivityEvent.objects.filter(**{f'{field_name}__gte':since})
            break
    
    for field_name, field_info_list in fields.items():
        if field_info_list[0] == 'DateTimeField':
            new_field_name = f'{field_name}_at_hour_level'
            group_fields.append(new_field_name)
            queryset = queryset.annotate(**{new_field_name: TruncHour(field_name)})            
            min_max_values = queryset.aggregate(min_value=Min(field_name), max_value=Max(field_name))
            min_date = DateFormat(min_max_values['min_value']).format('Y-m-d') if min_max_values['min_value'] else None
            max_date = DateFormat(min_max_values['max_value']).format('Y-m-d') if min_max_values['max_value'] else None
            fieldsextra.append([min_date, max_date])                     
        else:
            group_fields.append(field_name)
            if queryset is None:
                queryset = ActivityEvent.objects.all()
            distinct_values = queryset.order_by(field_name).values_list(field_name, flat=True).distinct()
            distinct_values = [value if value != '' else '<blank>' for value in distinct_values]
            fieldsextra.append(distinct_values)

        fieldtypes.append(field_info_list[0])
        displaynames.append(field_name if field_info_list[1] == '' else field_info_list[1])
    

    queryset = queryset.values(*group_fields).annotate(count=Count('id')).order_by(*group_fields)
 
    # Convert queryset to a list of results
    results = [[item[field] for field in group_fields] + [item['count']] for item in queryset]

    args_dict = {'sync_model': SyncTask,
        'celery_model': TaskResult,
        'task_name': aps.ACTIVITY_EVENTS_FETCH_TASK_NAME,
        'sync_task_name_field': 'taskname',
        'sync_timestamp_field': 'created_at',
        'celery_task_name_field': 'task_name',
        'celery_timestamp_field': 'date_done'}

    last_data_update_time = get_latest_successful_task_time(**args_dict) 
    
    # Prepare the response dictionary
    response = {
        'fields': group_fields + ['count'],  # Include 'count' as a field
        'fieldtypes': fieldtypes + ['IntegerField'],  # Include count as IntegerField
        'displaynames': displaynames + ['Count'],  # List of display names with "Count"
        'fieldsextra': fieldsextra + [[]], # Include the extra fields data
        'dataset': results,
        'last_data_update_time': last_data_update_time        
    }

    return render(request, 'activity_events/activityevent_charts.html', {'data': response})


class ActivityEventAPIListView(generics.ListAPIView):
    serializer_class = ActivityEventSerializer

    def get_queryset(self):
        queryset = ActivityEvent.objects.all()
        request_data = self.request.query_params
        fields_model = ActivityEventField 
        target_model = ActivityEvent
        queryset = apply_filters_to_queryset(request_data, queryset, fields_model, target_model)
        return queryset