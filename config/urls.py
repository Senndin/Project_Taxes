"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings
import os

def index_view(request, *args, **kwargs):
    dist_path = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
    if os.path.exists(dist_path):
        return HttpResponse(open(dist_path, 'rb').read(), content_type='text/html')
    else:
        return HttpResponse("Frontend build not found. Did the Heroku Node.js buildpack run? Make sure to run 'heroku buildpacks:add --index 1 heroku/nodejs'", status=501)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("tax_service.urls")),
    re_path(r'^.*', index_view),
]
