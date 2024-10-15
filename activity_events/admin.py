from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import ActivityEventField, ActivityEvent, SyncTask
from django.utils import timezone
from .populate_activity_fields_functions import populate_activity_fields
from .fetch_activity_events_functions import get_json_from_activity_events_api, process_activity_events
from .generate_csv_functions import write_csv_to_http
from django.core.exceptions import FieldError
from . import app_settings as aps


class ActivityEventFieldAdmin(admin.ModelAdmin):
    list_display = ('fieldname', 'fieldtype', 'displayname', 'displayorder', 'display', 'filter', 'orderby', 'search', 'export', 'chart', 'updated_at')
    search_fields = ('fieldname', 'fieldtype', 'displayname')
    list_filter = ('fieldtype', 'display', 'filter', 'orderby', 'export', 'chart')
    list_editable = ('displayname', 'displayorder', 'display', 'filter', 'orderby', 'search', 'export', 'chart')

    def has_delete_permission(self, request, obj=None):
        # Return False to disable delete permission.
        return True
    
    def has_add_permission(self, request):
        # Return False to prevent adding new records
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin_populate_activity_fields/', self.admin_site.admin_view(self.admin_populate_activity_fields), name='admin-populate-activity-fields'),
        ]
        return custom_urls + urls

    def admin_populate_activity_fields(self, request):        
        try:
            populate_activity_fields()  
            self.message_user(request, "Activity event fields populated successfully.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error occurred: {e}", messages.ERROR)
        return redirect('admin:activity_events_activityeventfield_changelist')  # Redirect to the changelist view
    

class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity', 'issuccess', 'userid', 'artifactname', 'itemname', 'updated_at')

    search_fields = ('activity', 'issuccess', 'itemname', 'datasetname' , 'workspacename', 'reportname',
                     'capacityname', 'operation', 'userid', 'artifactkind', 'artifactname', 'appname')
    list_filter = ('activity', 'issuccess', 'capacityname', 'userid', 'creationtime', 'created_at', 'updated_at')
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin_check_fetch_activity_events/', self.admin_site.admin_view(self.admin_check_fetch_activity_events), name='admin-check-fetch-activity-events'),
            path('admin_fetch_activity_events/', self.admin_site.admin_view(self.admin_fetch_activity_events), name='admin-fetch-activity-events'),
            path('admin_export_activity_events_csv/', self.admin_site.admin_view(self.admin_export_activity_events_csv), name='admin-export-activity-events-csv'),
        ]
        return custom_urls + urls
    

    def admin_check_fetch_activity_events(self, request):
        end_datetime = timezone.now()
        start_datetime = end_datetime - timezone.timedelta(hours=1)
        try:
            get_json_from_activity_events_api(start_datetime, end_datetime)
            success_message = "Successfully received response from API Activity Events."
            self.message_user(request, success_message, messages.SUCCESS)
        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.message_user(request, error_message, messages.ERROR)            
        return redirect('admin:activity_events_activityevent_changelist')
    

    def admin_fetch_activity_events(self, request):
        try:
            result = process_activity_events(task_name=aps.ACTIVITY_EVENTS_FETCH_TASK_NAME, sync_task=True)
            if result.get('has_failed_requests') or result.get('has_failed_records'):
                raise Exception(f'details:{result}')
            n_created = result.get('n_created_records')
            n_updated = result.get('n_updated_records')
            start = result.get('start_datetime').strftime("%Y-%m-%d %H:%M:%S")
            end = result.get('end_datetime').strftime("%Y-%m-%d %H:%M:%S")
            message = f"Success retrieving activity events. Period: {start} - {end}. Created: {n_created}. Updated: {n_updated}."                       
            self.message_user(request, message, messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error occurred: {e}", messages.ERROR)
        return redirect('admin:activity_events_activityevent_changelist')  # Redirect to the changelist view
    

    def admin_export_activity_events_csv(self, request):
        try:            
   
            cl = self.get_changelist_instance(request)
            queryset = cl.get_queryset(request)

            #field_names = field_names = [field.name for field in self.model._meta.fields]
            field_names = self.get_fields(request, cl)

            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="activity_events.csv"'

            # Generate the CSV response
            result = write_csv_to_http(queryset, field_names, response)                  
            return result

        except FieldError as e:
            # Handle errors related to field names, ordering, etc.
            self.message_user(request, f"Field error: {str(e)}", messages.ERROR)
            return None

        except Exception as e:
            self.message_user(request, f"An error occurred during export: {str(e)}", messages.ERROR)
            return None
    
class SyncTaskAdmin(admin.ModelAdmin):
    list_display = ('taskuuid', 'taskname', 'status', 'result', 'started_at', 'created_at')
    search_fields = ('taskname', 'status', 'result')
    list_filter = ('taskname', 'status', 'started_at', 'created_at')        
    

admin.site.register(ActivityEventField, ActivityEventFieldAdmin)
admin.site.register(ActivityEvent, ActivityEventAdmin)
admin.site.register(SyncTask, SyncTaskAdmin)