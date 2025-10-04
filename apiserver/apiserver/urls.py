# apiserver/apiserver/urls.py
from django.contrib import admin
from django.urls import path
from pollution.views import get_pollution_data, map_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta es la URL que nuestro mapa llamará: /api/pollution/?lat=...&lon=...
    path('api/pollution/', get_pollution_data, name='get-pollution-data'),
    path('', map_view, name='map-view'),
]