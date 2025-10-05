import requests
import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ==============================================================================
# --- CARGA INICIAL DEL MODELO Y DATOS (se ejecuta una sola vez) ---
# ==============================================================================
try:
    # Construimos las rutas a los archivos importantes
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # ¡IMPORTANTE! Asegúrate de que estos nombres de archivo coincidan con los tuyos
    MODEL_FILENAME = 'pollution_prediction_model.pkl'
    DATA_FILENAME = 'global_pm25_data_2020-2024_grid10.csv' # Ejemplo

    MODEL_PATH = BASE_DIR / MODEL_FILENAME
    DATA_PATH = BASE_DIR / DATA_FILENAME

    # Cargamos el modelo de ML y los datos históricos en memoria
    model = joblib.load(MODEL_PATH)
    historical_data = pd.read_csv(DATA_PATH)
    
    # Extraemos el tamaño de la cuadrícula de los datos para usarlo en las predicciones
    # Asumimos que la diferencia entre dos latitudes consecutivas es el tamaño de la cuadrícula
    GRID_SIZE = abs(historical_data['center_lat'].unique()[1] - historical_data['center_lat'].unique()[0])

    print("✅ Modelo de predicción y datos históricos cargados exitosamente.")
    print(f"   - Modelo: {MODEL_FILENAME}")
    print(f"   - Datos: {DATA_FILENAME}")
    print(f"   - Tamaño de cuadrícula detectado: {GRID_SIZE} grados")

except FileNotFoundError as e:
    print(f"❌ ERROR CRÍTICO: No se pudo cargar el modelo o los datos. El servidor no podrá hacer predicciones.")
    print(f"   - Archivo no encontrado: {e.filename}")
    print("   - Asegúrate de que los archivos .pkl y .csv estén en la carpeta raíz 'apiserver/'.")
    model = None
    historical_data = None

# ==============================================================================
# --- VISTA PARA MOSTRAR LA PÁGINA DEL MAPA ---
# ==============================================================================
def map_view(request):
    """
    Renderiza y devuelve el archivo HTML del mapa interactivo.
    """
    return render(request, 'mapa_interactivo.html')

# ==============================================================================
# --- API PARA DATOS EN TIEMPO REAL (OpenWeatherMap) ---
# ==============================================================================
@api_view(['GET'])
def get_pollution_data(request):
    """
    Obtiene datos de contaminación en tiempo real de OpenWeatherMap.
    """
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if not lat or not lon:
        return Response({'error': 'Latitud y longitud son requeridas'}, status=400)

    api_key = settings.OPENWEATHERMAP_API_KEY
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

# ==============================================================================
# --- API PARA PREDICCIONES FUTURAS (Machine Learning Híbrido) ---
# ==============================================================================
@api_view(['GET'])
def predict_enhanced_pollution(request):
    """
    Usa el modelo de ML y datos en tiempo real para predecir la contaminación futura.
    """
    if model is None or historical_data is None:
        return Response({'error': 'El modelo de predicción no está disponible.'}, status=503)

    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')
    if not lat_str or not lon_str:
        return Response({'error': 'Latitud y longitud son requeridas'}, status=400)

    lat = float(lat_str)
    lon = float(lon_str)

    # --- 1. OBTENER DATOS ACTUALES DE OPENWEATHERMAP ---
    try:
        api_key = settings.OPENWEATHERMAP_API_KEY
        owm_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        owm_response = requests.get(owm_url).json()
        # Nos enfocamos en PM2.5, que está en µg/m³
        current_pm25 = owm_response['list'][0]['components']['pm2_5']
    except Exception:
        return Response({'error': 'No se pudieron obtener los datos en tiempo real de OpenWeatherMap.'}, status=502)

    # --- 2. ENCONTRAR LA CELDA Y DATOS HISTÓRICOS CORRESPONDIENTES ---
    center_lat = (lat // GRID_SIZE) * GRID_SIZE + (GRID_SIZE / 2)
    center_lon = (lon // GRID_SIZE) * GRID_SIZE + (GRID_SIZE / 2)

    cell_data = historical_data[
        (historical_data['center_lat'] == center_lat) &
        (historical_data['center_lon'] == center_lon)
    ]
    if cell_data.empty:
        return Response({'error': 'No hay datos históricos para esta ubicación.'}, status=404)

    # --- 3. CALCULAR LA ANOMALÍA ACTUAL ---
    current_month = datetime.now().month
    historical_avg_for_current_month = cell_data[cell_data['month'] == current_month]['avg_pm25'].mean()
    
    anomaly = 0
    if pd.notna(historical_avg_for_current_month):
        # ¡CONVERSIÓN DE UNIDADES! NASA (kg/m³) a OpenWeatherMap (µg/m³)
        # 1 kg = 1e9 µg
        historical_avg_owm_units = historical_avg_for_current_month * 1e9
        anomaly = current_pm25 - historical_avg_owm_units
    
    # --- 4. OBTENER PREDICCIÓN BASE DEL MODELO DE ML ---
    last_record = cell_data.sort_values(by='year').iloc[-1]
    current_year = int(last_record['year'])
    
    prediction_features = pd.DataFrame({
        'center_lat': [center_lat], 'center_lon': [center_lon],
        'year': [current_year + 1], 'month': [current_month]
    })
    base_prediction_future_nasa_units = model.predict(prediction_features)[0]
    
    # Convertimos la predicción base a unidades de OpenWeatherMap
    base_prediction_future_owm_units = base_prediction_future_nasa_units * 1e9

    # --- 5. APLICAR CORRECCIÓN Y DEVOLVER RESULTADO ---
    final_prediction = base_prediction_future_owm_units + anomaly

    return Response({
        'requested_location': {'lat': lat, 'lon': lon},
        'grid_cell': {'center_lat': center_lat, 'center_lon': center_lon},
        'current_data_owm': {'pm2_5_µg_m3': current_pm25},
        'historical_average_nasa': {'pm2_5_µg_m3': historical_avg_owm_units if 'historical_avg_owm_units' in locals() else 'N/A'},
        'current_anomaly': {'pm2_5_µg_m3': anomaly},
        'ml_prediction_next_year': {
            'base_prediction_µg_m3': base_prediction_future_owm_units,
            'final_prediction_µg_m3': final_prediction
        }
    })