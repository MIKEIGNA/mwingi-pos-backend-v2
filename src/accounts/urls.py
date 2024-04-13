from django.urls import path
from django.contrib.auth.views import (LogoutView, )
from django.views.generic import TemplateView


app_name = 'accounts' 
urlpatterns = [
    # Login, SignUp and Contact
    
    #path('accounts/login/', MyLoginView.as_view(), name='login'), 
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/too_many_requests/',TemplateView.as_view(template_name='accounts/too_many_requests.html'),name='accounts_too_many_requests'),
          
]

