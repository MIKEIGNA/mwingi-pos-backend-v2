"""traqsale_cloud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static 
from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path
from django.conf.urls import include

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'),name='home'),
    path('magnupe/', admin.site.urls),
    path('', include("accounts.urls")),
    path('', include("billing.urls")),
    path('', include("profiles.urls")),
    path('', include("api.urls")),
    path('', include("sales.urls")),
    path('', include("loyverse.urls")), 
    
    path('sentry-debug/', trigger_error),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),] + urlpatterns

if settings.DEBUG: # new
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))] # silk