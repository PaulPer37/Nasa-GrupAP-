import React, { useState } from "react";
import axios from "axios"; 

export const GeoCodingService = () => {
    const apiKey = import.meta.env.VITE_OPEN_WEATHER_API_KEY; 

    const [ciudad,setCiudad] = useState(""); 
    const [resultado, setResultado] = useState(null); 

    const getCoordinates = async () => {

        if(!ciudad){
            alert("Debes ingresar una ciudad para buscar sus coordenadas");
        }

        try{
            const url = `https://api.openweathermap.org/geo/1.0/direct?q=${ciudad}&limit=1&appid=${apiKey}`;
            const res = await axios.get(url); 
            setResultado(res.data[0]); 

        } catch{
            alert("Ocurrió un error al consultar las coordenadas"); 
            setResultado(null); 

        }

    }
    
    return (
                    <div style={{ padding: "20px" }}>
            <h2>Búsqueda de coordenadas</h2>
            <input 
                type="text" 
                placeholder="Ej: London" 
                value={ciudad} 
                onChange={(e) => setCiudad(e.target.value)} 
            />
            <button onClick={getCoordinates}>Buscar</button>

            {resultado && (
                <div>
                    <h3>Resultado:</h3>
                    <p><strong>Ciudad:</strong> {resultado.name}</p>
                    {resultado.state && <p><strong>Estado:</strong> {resultado.state}</p>}
                    <p><strong>País:</strong> {resultado.country}</p>
                    <p><strong>Lat:</strong> {resultado.lat}</p>
                    <p><strong>Lon:</strong> {resultado.lon}</p>
                </div>
            )}
        </div>


    ); 
      
}