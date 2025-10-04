import requests
import os
from dotenv import load_dotenv

# Cargamos el archivo .env para leer la clave
load_dotenv()

# Leemos la clave de la API desde las variables de entorno
api_key = os.getenv('OPENWEATHERMAP_API_KEY')

print(f"Probando la conexión con la clave: {api_key}")

if not api_key:
    print("\n❌ ERROR: No se pudo encontrar la clave 'OPENWEATHERMAP_API_KEY' en tu archivo .env")
    print("Asegúrate de que el archivo .env está en la misma carpeta y la variable está bien escrita.")
else:
    # Usamos coordenadas de prueba (Londres)
    lat = 51.5072
    lon = -0.1276
    
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    
    try:
        print(f"Realizando petición a: {url}")
        response = requests.get(url)
        
        # Esto es crucial: nos dirá si la API nos rechaza
        response.raise_for_status() 
        
        data = response.json()
        print("\n✅ ¡Éxito! La clave de API es válida y se recibieron datos:")
        print(data)
        
    except requests.exceptions.HTTPError as err:
        print(f"\n❌ ERROR: La API de OpenWeatherMap devolvió un error.")
        print(f"   - Código de estado: {err.response.status_code}")
        print(f"   - Respuesta del servidor: {err.response.text}")
        print("\n   => Un error '401' significa que tu clave de API es incorrecta o no está activa.")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: No se pudo conectar a OpenWeatherMap. Error de red: {e}")