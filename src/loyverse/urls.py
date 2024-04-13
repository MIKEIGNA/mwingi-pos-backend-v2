from django.urls import path

from .views import (
    DownloadFileView,
    DownloadLogFileView,
    LoyverseSyncView
)

app_name = 'loyverse' 
urlpatterns = [
    path(
        'loyverse/sync', 
        LoyverseSyncView.as_view(), 
        name='sync'
    ),
    path(
        'download/logfile/critical', 
        DownloadLogFileView.as_view(filename='page_critical.log'), 
        name='download_log_file_critical'
    ),
    path(
        'download/logfile/pageviews', 
        DownloadLogFileView.as_view(filename='page_views.log'), 
        name='download_log_pageviews'
    ),
    path(
        'download/logfile/software-tasks', 
        DownloadLogFileView.as_view(filename='software_task_critical.log'), 
        name='download_log_software_tasks'
    ),



    path(
        'download/file', 
        DownloadFileView.as_view(filename='software_task_critical.log'), 
        name='download_file'
    ),

]

