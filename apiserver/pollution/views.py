# apiserver/pollution/views.py
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings # ¡Importamos la configuración de Django!
from django.shortcuts import render

def map_view(request):
    # Esta función simplemente renderiza y devuelve nuestro archivo HTML
    return render(request, 'mapa_interactivo.html')

@api_view(['GET'])
def get_pollution_data(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if not lat or not lon:
        return Response({'error': 'Latitud y longitud son requeridas'}, status=400)

    # --- Obtenemos la clave de forma SEGURA desde settings.py ---
    api_key = settings.OPENWEATHERMAP_API_KEY
    # -----------------------------------------------------------

    if not api_key:
        return Response({'error': 'La clave de API no está configurada en el servidor.'}, status=500)

    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return Response(data)
    except requests.exceptions.RequestException as e:
        return Response({'error': f'Error de conexión con OpenWeatherMap: {e}'}, status=502)