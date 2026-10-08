from django.contrib import admin
from django.urls import path, include
from hospital.health import healthcheck

urlpatterns = [
        path('healthz/', healthcheck, name='healthcheck'),
        path('admin/', admin.site.urls),
        path('', include('hospital.urls')),
    ]
