import mimetypes
import os
from django.http import HttpResponse

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from loyverse.utils.loyverse_api import LoyverseApi

class LoyverseSyncView(LoginRequiredMixin, View):
    template_name = 'loyverse_landing.html'

    page_title = 'Loyverse Sync'
    success_message = 'Loyverse sync request was successful.'
    failure_message = 'Loyverse sync request was not successful.'

    def get(self, request):

        success = LoyverseApi.get_inventory()

        return render(
            request, 
            self.template_name, 
            {
                'page_title': self.page_title,
                'success': success,
                'message': self.success_message if success else self.failure_message
            }
        )

class DownloadLogFileView(LoginRequiredMixin, View):

    # Defined in the urls
    filename = ''

    def get(self, request):

        # Define Django project base directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define the full file path
        filepath = BASE_DIR + '/xlogs/' + self.filename
        # Open the file for reading content
        path = open(filepath, 'r' ,encoding="utf8")
        # Set the mime type
        mime_type, _ = mimetypes.guess_type(filepath)
        # Set the return value of the HttpResponse
        response = HttpResponse(path, content_type=mime_type)
        # Set the HTTP header for sending to browser
        response['Content-Disposition'] = "attachment; filename=%s" % self.filename
        # Return the response value
        return response
    

class DownloadFileView(LoginRequiredMixin, View):

    # Defined in the urls
    filename = ''

    def get(self, request):

        # Define Django project base directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define the full file path
        filepath = BASE_DIR + 'download_file.txt'
        # Open the file for reading content
        path = open(filepath, 'r' ,encoding="utf8")
        # Set the mime type
        mime_type, _ = mimetypes.guess_type(filepath)
        # Set the return value of the HttpResponse
        response = HttpResponse(path, content_type=mime_type)
        # Set the HTTP header for sending to browser
        response['Content-Disposition'] = "attachment; filename=%s" % self.filename
        # Return the response value
        return response

