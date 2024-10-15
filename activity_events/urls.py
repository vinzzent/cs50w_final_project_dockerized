from django.urls import path
from .views import ActivityEventListView, export_csv_vw, check_csv_status_vw, download_csv_vw, charts_vw, ActivityEventAPIListView


app_name = 'activity_events'

urlpatterns = [
    path('', ActivityEventListView.as_view(), name='events_list'),    
    path('export_csv/', export_csv_vw, name='export_csv'),
    path('check_csv_status/<str:task_id>/', check_csv_status_vw, name='check_csv_status'),
    path('download_csv/<str:file_name>', download_csv_vw, name='download_csv'),
    path('charts/', charts_vw, name='charts'),
    path('api/', ActivityEventAPIListView.as_view(), name='api_events_list'),
]
