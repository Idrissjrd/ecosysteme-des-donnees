"""
Client to interact with the Rival Group (Group E - Vampires).
"""
import requests

RIVAL_API_URL = "http://127.0.0.1:16040/taille"

def get_vampire_size_from_api(fallback_value: float = 500.0) -> tuple[float, bool]:
    """
    Returns: (population_size, is_connected)
    """
    try:
        response = requests.get(RIVAL_API_URL, timeout=0.5)
        
        if response.status_code == 200:
            data = response.json()
            val = data.get("taille")
            if isinstance(val, list):
                val = val[0]
            
            # Validation: Only accept if value > 0.1
            if val is not None and float(val) > 0.1:
                return float(val), True  # <--- True = Connected
                
    except Exception:
        pass
    
    # Fallback mode
    return fallback_value, False  # <--- False = Offline/Simulation